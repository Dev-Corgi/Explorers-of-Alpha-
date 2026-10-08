from __future__ import annotations

import struct
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import (
    get_files_from_rom_with_extension,
    get_ppmdu_config_for_rom,
    read_u32,
)
from skytemple_files.container.sir0.handler import Sir0Handler
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.str.handler import StrHandler
import skytemple_files.data.waza_p._model as waza_p_model
from skytemple_files.data.waza_p._model import MOVE_ENTRY_BYTELEN, WazaMove, WazaP
from skytemple_files.data.waza_p.handler import WazaPHandler

VANILLA_MOVE_COUNT = 559
EXTENDED_MOVE_COUNT = 560
WAZA_P_GROUPS = (
    ("BALANCE/waza_p.bin", "UTILITY/waza_p.bin"),
    ("BALANCE/waza_p2.bin", "UTILITY/waza_p2.bin"),
)
WAZA_P_PATHS = WAZA_P_GROUPS[0]
WAZA_CD_PATHS = ("BALANCE/waza_cd.bin", "UTILITY/waza_cd.bin")
ANIM_BIN_PATHS = ("BALANCE/anim.bin", "UTILITY/anim.bin")
ANIM_SEC2_PTR_OFF = 8
ANIM_SEC2_END_OFF = 12
ANIM_SEC2_RECORD_LEN = 24


def _use_extended_move_count() -> None:
    waza_p_model.MOVE_COUNT = EXTENDED_MOVE_COUNT


def load_shell_move_config(module_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    data_cfg = manifest.get("data") or {}
    yaml_path = module_dir / str(data_cfg.get("shell_move_file", "data/shell_move.yaml"))
    if not yaml_path.is_file():
        raise FileNotFoundError(f"shell move config not found: {yaml_path}")
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    pool = doc.get("calc_damage_pool") or {}
    return {
        "move_id": int(doc["move_id"]),
        "name": str(doc["name"]),
        "template_move_id": int(doc.get("template_move_id", 467)),
        "waza_cd_effect_id": int(doc.get("waza_cd_effect_id", 0)),
        "calc_damage_pool_file_offset": int(pool["file_offset"], 16)
        if isinstance(pool.get("file_offset"), str)
        else int(pool["file_offset"]),
        "calc_damage_pool_vanilla_move_id": int(pool.get("vanilla_move_id", 467)),
    }


def _load_moves_uncapped(raw: bytes, count: int) -> list[WazaMove]:
    sir0 = Sir0Handler.deserialize(raw)
    move_ptr = read_u32(sir0.content, sir0.data_pointer)
    return [
        WazaMove(sir0.content[off : off + MOVE_ENTRY_BYTELEN])
        for off in range(move_ptr, move_ptr + count * MOVE_ENTRY_BYTELEN, MOVE_ENTRY_BYTELEN)
    ]


def _build_shell_move(template: WazaMove, move_id: int) -> WazaMove:
    shell = deepcopy(template)
    shell.move_id = move_id
    return shell


def _build_waza_p_patch(waza_raw: bytes, cd_item_count: int, *, move_id: int, template_id: int) -> tuple[WazaP, str]:
    if cd_item_count < VANILLA_MOVE_COUNT:
        raise RuntimeError(f"waza_cd item count too small: {cd_item_count}")
    if cd_item_count > move_id + 1:
        raise RuntimeError(f"waza_cd item count unexpectedly large: {cd_item_count}")

    read_count = VANILLA_MOVE_COUNT if cd_item_count == VANILLA_MOVE_COUNT else cd_item_count
    moves = _load_moves_uncapped(waza_raw, read_count)
    if cd_item_count == VANILLA_MOVE_COUNT:
        if len(moves) != VANILLA_MOVE_COUNT:
            raise RuntimeError(f"waza_p move count mismatch: {len(moves)}")
        shell = _build_shell_move(moves[template_id], move_id)
        moves.append(shell)
        action = "appended"
    else:
        if len(moves) != move_id + 1:
            raise RuntimeError(f"extended waza_p move count mismatch: {len(moves)}")
        shell = _build_shell_move(moves[template_id], move_id)
        moves[move_id] = shell
        action = "updated"
    if len(moves) != EXTENDED_MOVE_COUNT:
        raise RuntimeError(f"waza_p move list {len(moves)} != {EXTENDED_MOVE_COUNT}")
    waza_p_model.MOVE_COUNT = read_count
    wp = WazaPHandler.deserialize(waza_raw)
    wp.moves = moves
    return wp, action


def _apply_waza_cd_patch(
    rom: NintendoDSRom,
    *,
    move_id: int,
    effect_id: int,
    item_count: int,
) -> None:
    cd_payload: bytes | None = None
    for cd_path in WAZA_CD_PATHS:
        cd = DataCDHandler.deserialize(rom.getFileByName(cd_path))
        if cd.nb_items() != item_count:
            raise RuntimeError(f"{cd_path} item count {cd.nb_items()} != {item_count}")
        if item_count == VANILLA_MOVE_COUNT:
            cd.add_item_effect_id(effect_id)
        else:
            cd.set_item_effect_id(move_id, effect_id)
        if cd.nb_items() != move_id + 1:
            raise RuntimeError(f"{cd_path} items after patch {cd.nb_items()} != {move_id + 1}")
        payload = DataCDHandler.serialize(cd)
        if cd_payload is None:
            cd_payload = payload
        elif payload != cd_payload:
            raise RuntimeError(f"{cd_path} serialize mismatch vs prior waza_cd patch")
        rom.setFileByName(cd_path, payload)


def patch_waza_shell_move(rom: NintendoDSRom, cfg: dict[str, Any]) -> dict[str, Any]:
    _use_extended_move_count()
    move_id = int(cfg["move_id"])
    template_id = int(cfg["template_move_id"])
    effect_id = int(cfg["waza_cd_effect_id"])

    cd_item_count = DataCDHandler.deserialize(rom.getFileByName(WAZA_CD_PATHS[0])).nb_items()
    actions: list[str] = []
    for group in WAZA_P_GROUPS:
        wp, action = _build_waza_p_patch(
            rom.getFileByName(group[0]),
            cd_item_count,
            move_id=move_id,
            template_id=template_id,
        )
        waza_payload = WazaPHandler.serialize(wp)
        for waza_path in group:
            rom.setFileByName(waza_path, waza_payload)
        actions.append(f"{group[0]}:{action}")

    _apply_waza_cd_patch(
        rom,
        move_id=move_id,
        effect_id=effect_id,
        item_count=cd_item_count,
    )

    return {
        "shell_move_id": move_id,
        "shell_move_action": ",".join(actions),
        "extended_move_count": EXTENDED_MOVE_COUNT,
        "waza_p_paths": [path for group in WAZA_P_GROUPS for path in group],
        "waza_cd_paths": list(WAZA_CD_PATHS),
        "waza_p_bytes": len(waza_payload),
        "waza_cd_items": move_id + 1,
        "waza_cd_effect_id": effect_id,
    }


def patch_shell_move_name(rom: NintendoDSRom, move_id: int, name: str) -> None:
    config = get_ppmdu_config_for_rom(rom)
    block = config.string_index_data.string_blocks["Move Names"]
    string_index = block.begin + move_id
    for filename in get_files_from_rom_with_extension(rom, "str"):
        if not filename.endswith("text_e.str"):
            continue
        strings = StrHandler.deserialize(
            rom.getFileByName(filename), string_encoding=config.string_encoding
        )
        strings.strings[string_index] = name
        rom.setFileByName(filename, StrHandler.serialize(strings))


def _anim_sec2_record_offset(data: bytes, move_id: int) -> int:
    start = struct.unpack_from("<I", data, ANIM_SEC2_PTR_OFF)[0]
    end = struct.unpack_from("<I", data, ANIM_SEC2_END_OFF)[0]
    off = start + move_id * ANIM_SEC2_RECORD_LEN
    if off < start or off + ANIM_SEC2_RECORD_LEN > end:
        raise RuntimeError(
            f"anim.bin move {move_id} record @{off:#x} outside section 2 {start:#x}-{end:#x}"
        )
    return off


def _read_anim_record(data: bytes, move_id: int) -> bytes:
    off = _anim_sec2_record_offset(data, move_id)
    return data[off : off + ANIM_SEC2_RECORD_LEN]


def patch_anim_shell_move(
    rom: NintendoDSRom,
    *,
    move_id: int,
    template_id: int,
) -> dict[str, Any]:
    payload: bytes | None = None
    template_entry: bytes | None = None
    previous_entry: bytes | None = None
    for anim_path in ANIM_BIN_PATHS:
        data = bytearray(rom.getFileByName(anim_path))
        if template_entry is None:
            template_entry = _read_anim_record(bytes(data), template_id)
        if previous_entry is None:
            previous_entry = _read_anim_record(bytes(data), move_id)
        shell_off = _anim_sec2_record_offset(bytes(data), move_id)
        data[shell_off : shell_off + ANIM_SEC2_RECORD_LEN] = template_entry
        out = bytes(data)
        if payload is None:
            payload = out
        elif payload != out:
            raise RuntimeError(f"{anim_path} anim patch mismatch vs {ANIM_BIN_PATHS[0]}")
        rom.setFileByName(anim_path, out)
    if template_entry == previous_entry:
        action = "already_patched"
    else:
        action = "patched"
    return {
        "paths": list(ANIM_BIN_PATHS),
        "template_move_id": template_id,
        "shell_move_id": move_id,
        "template_entry_hex": template_entry.hex(),
        "previous_entry_hex": previous_entry.hex() if previous_entry else "",
        "action": action,
    }


def patch_calc_damage_type_pool(
    ov29: bytearray,
    *,
    file_offset: int,
    shell_move_id: int,
    vanilla_move_id: int,
) -> dict[str, Any]:
    if file_offset < 0 or file_offset + 2 > len(ov29):
        raise RuntimeError(f"CalcDamage pool offset out of range: {file_offset:#x}")
    current = struct.unpack_from("<H", ov29, file_offset)[0]
    if current not in (vanilla_move_id, shell_move_id):
        raise RuntimeError(
            f"CalcDamage pool @ {file_offset:#x}: expected {vanilla_move_id} or "
            f"{shell_move_id}, found {current}"
        )
    if current != vanilla_move_id:
        struct.pack_into("<H", ov29, file_offset, vanilla_move_id)
        action = "restored"
    else:
        action = "already_vanilla"
    return {
        "file_offset": file_offset,
        "previous_move_id": current,
        "vanilla_move_id": vanilla_move_id,
        "action": action,
    }


def patch_shell_move_data(
    rom: NintendoDSRom,
    ov29: bytearray,
    module_dir: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    cfg = load_shell_move_config(module_dir, manifest)
    waza_meta = patch_waza_shell_move(rom, cfg)
    patch_shell_move_name(rom, int(cfg["move_id"]), str(cfg["name"]))
    anim_meta = patch_anim_shell_move(
        rom,
        move_id=int(cfg["move_id"]),
        template_id=int(cfg["template_move_id"]),
    )
    pool_meta = patch_calc_damage_type_pool(
        ov29,
        file_offset=int(cfg["calc_damage_pool_file_offset"]),
        shell_move_id=int(cfg["move_id"]),
        vanilla_move_id=int(cfg["calc_damage_pool_vanilla_move_id"]),
    )
    return {
        "shell_move": cfg,
        "waza_p": waza_meta,
        "anim_bin": anim_meta,
        "calc_damage_pool": pool_meta,
    }


def verify_shell_move_data(
    rom: NintendoDSRom,
    ov29: bytes,
    module_dir: Path,
    manifest: dict[str, Any],
) -> None:
    _use_extended_move_count()
    cfg = load_shell_move_config(module_dir, manifest)
    move_id = int(cfg["move_id"])
    template_id = int(cfg["template_move_id"])
    for group in WAZA_P_GROUPS:
        group_payload: bytes | None = None
        for waza_path in group:
            raw = rom.getFileByName(waza_path)
            if group_payload is None:
                group_payload = raw
            elif raw != group_payload:
                raise AssertionError(f"{waza_path} payload mismatch vs {group[0]}")
            moves_check = _load_moves_uncapped(raw, move_id + 1)
            if len(moves_check) != EXTENDED_MOVE_COUNT:
                raise AssertionError(f"{waza_path} move count {len(moves_check)} != {EXTENDED_MOVE_COUNT}")
            shell = moves_check[move_id]
            template = moves_check[template_id]
            if shell.move_id != move_id:
                raise AssertionError(f"{waza_path} shell move_id {shell.move_id} != {move_id}")
            if shell.to_bytes()[:0x16] != template.to_bytes()[:0x16] or shell.to_bytes()[0x18:] != template.to_bytes()[0x18:]:
                raise AssertionError(f"{waza_path} shell stats differ from move {template_id}")
            if shell.category != 1:
                raise AssertionError(f"{waza_path} shell category {shell.category} != 1")

    for cd_path in WAZA_CD_PATHS:
        cd = DataCDHandler.deserialize(rom.getFileByName(cd_path))
        if cd.nb_items() != move_id + 1:
            raise AssertionError(f"{cd_path} items {cd.nb_items()} != {move_id + 1}")
        if cd.get_item_effect_id(move_id) != int(cfg["waza_cd_effect_id"]):
            raise AssertionError(f"{cd_path} effect for move {move_id} mismatch")

    config = get_ppmdu_config_for_rom(rom)
    block = config.string_index_data.string_blocks["Move Names"]
    strings = StrHandler.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"), string_encoding=config.string_encoding
    )
    if strings.strings[block.begin + move_id].strip() != str(cfg["name"]):
        raise AssertionError("Move Names shell string mismatch")
    if strings.strings[block.begin + template_id].strip() == str(cfg["name"]):
        raise AssertionError("Judgement move name was overwritten with the Z-Move name")

    pool_off = int(cfg["calc_damage_pool_file_offset"])
    pool_val = struct.unpack_from("<H", ov29, pool_off)[0]
    vanilla_move_id = int(cfg["calc_damage_pool_vanilla_move_id"])
    if pool_val != vanilla_move_id:
        raise AssertionError(
            f"CalcDamage pool {pool_val:#x} != Judgement {vanilla_move_id:#x}"
        )

    template_entry = _read_anim_record(rom.getFileByName(ANIM_BIN_PATHS[0]), template_id)
    anim_payload: bytes | None = None
    for anim_path in ANIM_BIN_PATHS:
        raw = rom.getFileByName(anim_path)
        if anim_payload is None:
            anim_payload = raw
        elif raw != anim_payload:
            raise AssertionError(f"{anim_path} anim.bin payload mismatch vs {ANIM_BIN_PATHS[0]}")
        shell_entry = _read_anim_record(raw, move_id)
        if shell_entry != template_entry:
            raise AssertionError(
                f"{anim_path} anim entry for move {move_id} != template {template_id}"
            )
