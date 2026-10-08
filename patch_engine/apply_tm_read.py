from __future__ import annotations

import struct
import tempfile
from pathlib import Path
from typing import Any

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import (
    get_files_from_rom_with_extension,
    get_ppmdu_config_for_rom,
    set_binary_in_rom,
)
from skytemple_files.data.str.handler import StrHandler

from .armips_runner import run_armips_bundle, write_generated_inc_text
from .cave_manifest import parse_max_file_offset
from .overlay_caves import (
    allocate_overlay_cave,
    binary_load,
    get_rom_binary,
    normalize_cave_binary,
    overlay_filename,
    overlay_index,
    write_rom_binary,
)
from .cave_reservations import reserved_file_ranges
from .hook_registry import (
    assert_hooks_on_binary,
    collect_hook_records,
    hook_word_kind,
    resolve_prior_target,
)
from .manifest import load_yaml, resolve_symbol
from .prebuild import run_prebuild
from .apply_asm import _export_cave_symbols
from .state import AppliedModule, BuildState, CaveAllocation, HookRecord

OV29_LOAD = 0x022DC240
OV31_LOAD = 0x02382820

# tm_read ov29 cave: stubs at +0x0 / +0x8 when room_charge v1 is not in build.state.
TM_READ_STUB_IS_ROOM_CHARGE_MOVE_OFF = 0x0
TM_READ_STUB_GET_ROOM_CHARGE_STATE_OFF = 0x8
TM_READ_POST_VALIDATE_RESTORE_NOOP_OFF = 0x10


def _parse_fixed(value: Any) -> int | None:
    if value is None:
        return None
    return int(value, 16) if isinstance(value, str) else int(value)


def _binary_load(profile: dict[str, Any], name: str) -> int:
    return binary_load(profile, name)


def _overlay_id(name: str) -> int:
    if name in ("ov29", "overlay29", "overlay_0029"):
        return 29
    if name in ("ov31", "overlay31", "overlay_0031"):
        return 31
    raise ValueError(f"not an overlay binary: {name!r}")


def _get_binary_bytes(rom: NintendoDSRom, config, name: str) -> bytes:
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov_id = _overlay_id(name)
    return rom.files[table[ov_id].fileID]


def _set_binary_bytes(rom: NintendoDSRom, config, name: str, data: bytes) -> None:
    write_rom_binary(rom, config, name, data)


def _read_table_count(table_asm: Path) -> int:
    if not table_asm.is_file():
        raise FileNotFoundError(f"TM charge table missing: {table_asm}")
    return table_asm.read_text(encoding="utf-8").count(".halfword")


def _estimate_ov29_cave_bytes(table_count: int, cave_cfg: dict[str, Any]) -> int:
    code = int(cave_cfg.get("code_bytes", 1152))
    row_bytes = int(cave_cfg.get("table_row_bytes", 4))
    pad = int(cave_cfg.get("table_padding", 64))
    need = code + table_count * row_bytes + pad
    alignment = int(cave_cfg.get("alignment", 4))
    return ((need + alignment - 1) // alignment) * alignment


def _resolve_room_charge_two_turn_ext(state: BuildState | None) -> int:
    if state:
        for mod in state.applied:
            if mod.id != "room_charge_v3":
                continue
            for entry in mod.data or []:
                addr = entry.get("RoomChargeTwoTurnExtTable")
                if addr:
                    return int(addr, 16)
    return 0


def _resolve_room_charge_helpers(
    state: BuildState | None,
    ov29_base: int,
) -> tuple[int, int, str]:
    """Return (IsRoomChargeMove, GetRoomChargeState, source) for generated.inc.

    room_charge / room_charge_pending: exports IsRoomChargeMove / GetRoomChargeState
    from the ov36 cave (via build.state).
    room_charge_v3: no exports — stubs remain (mov r0,#0). Read deferral for 2-turn /
    room-wide moves uses TmRead_IsTwoTurnMove (TWO_TURN table) and IsChargingTwoTurnMove
    in TmRead_TryRestoreSlot instead of GetRoomChargeState.
    """
    if state:
        for mod in state.applied:
            if mod.id not in ("room_charge", "room_charge_pending"):
                continue
            data = (mod.data or [{}])[0]
            is_rc = data.get("IsRoomChargeMove")
            get_st = data.get("GetRoomChargeState")
            if is_rc and get_st:
                return (
                    int(is_rc, 16),
                    int(get_st, 16),
                    mod.id,
                )
    return (
        ov29_base + TM_READ_STUB_IS_ROOM_CHARGE_MOVE_OFF,
        ov29_base + TM_READ_STUB_GET_ROOM_CHARGE_STATE_OFF,
        "stub",
    )


CLEAR_TWO_TURN_STATUS = 0x02318D58
LEVEL_UP_BODY = 0x02303040
RESTORE_PP_BODY = 0x022F9A78
TEACH_ITEM_RESUME = 0x0231DA84


def _bl_target(site: int, word: int) -> int | None:
    if (word >> 24) != 0xEB:
        return None
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return site + 8 + imm * 4


def _resolve_tm_force_restore_exports(
    overlay: bytes,
    *,
    overlay_load: int,
    cave_load: int,
    cave_size: int,
) -> dict[str, str]:
    """Locate ForceRestore / LevelUp / RestorePp / TeachItem cave entries after armips."""
    start = cave_load - overlay_load
    end = start + cave_size
    force_hits: list[int] = []
    # TmRead_ForceRestorePending: push {r4,lr}; ... bl ClearTwoTurnStatus
    for off in range(start, max(start, end - 8), 4):
        if struct.unpack_from("<I", overlay, off)[0] != 0xE92D4010:
            continue
        for delta in range(4, 0x28, 4):
            if off + delta + 4 > end:
                break
            w = struct.unpack_from("<I", overlay, off + delta)[0]
            tgt = _bl_target(overlay_load + off + delta, w)
            if tgt == CLEAR_TWO_TURN_STATUS:
                force_hits.append(overlay_load + off)
                break
    if len(force_hits) != 1:
        raise RuntimeError(
            f"TmRead_ForceRestorePending: expected 1 match, found {len(force_hits)} "
            f"({[hex(h) for h in force_hits]})"
        )
    force_addr = force_hits[0]

    def _find_force_caller(after_body: int, label: str) -> int:
        # push {r0-r3,lr}; bl ForceRestore; pop {r0-r3,lr}; ...
        hits: list[int] = []
        for off in range(start, max(start, end - 16), 4):
            if struct.unpack_from("<I", overlay, off)[0] != 0xE92D400F:
                continue
            bl = struct.unpack_from("<I", overlay, off + 4)[0]
            if _bl_target(overlay_load + off + 4, bl) != force_addr:
                continue
            # next interesting branch/b after pop
            hits.append(overlay_load + off)
        if len(hits) < 1:
            raise RuntimeError(f"{label}: no ForceRestore caller found")
        # Disambiguate by following final b/bl target
        matched: list[int] = []
        for addr in hits:
            off = addr - overlay_load
            for delta in range(8, 0x20, 4):
                w = struct.unpack_from("<I", overlay, off + delta)[0]
                top = w >> 24
                if top not in (0xEA, 0xEB):
                    continue
                imm = w & 0xFFFFFF
                if imm & 0x800000:
                    imm -= 0x1000000
                tgt = overlay_load + off + delta + 8 + imm * 4
                if tgt == after_body:
                    matched.append(addr)
                    break
        if len(matched) != 1:
            raise RuntimeError(
                f"{label}: expected 1 match ending at {after_body:#x}, found "
                f"{len(matched)} ({[hex(h) for h in matched]})"
            )
        return matched[0]

    level_up = _find_force_caller(LEVEL_UP_BODY, "TmRead_LevelUpForceRestore")
    restore_pp = _find_force_caller(RESTORE_PP_BODY, "TmRead_RestorePpForceRestore")
    teach = _find_force_caller(TEACH_ITEM_RESUME, "TmRead_TeachItemForceRestore")
    return {
        "TmRead_ForceRestorePending": f"0x{force_addr:X}",
        "TmRead_LevelUpForceRestore": f"0x{level_up:X}",
        "TmRead_RestorePpForceRestore": f"0x{restore_pp:X}",
        "TmRead_TeachItemForceRestore": f"0x{teach:X}",
    }


def _build_generated_inc(
    *,
    module_id: str,
    ov29_base: int,
    table_count: int,
    is_room_charge_move: int,
    get_room_charge_state: int,
    room_charge_two_turn_ext: int,
    room_charge_helper_source: str,
) -> str:
    lines = [
        f"; Auto-generated by true_patches for {module_id}",
        f"; room_charge helpers: {room_charge_helper_source}",
        f".definelabel TmReadOv29CodeAddress, 0x{ov29_base:X}",
        f"TmChargeTableCount equ {table_count}",
        f".definelabel TmReadIsRoomChargeMove, 0x{is_room_charge_move:X}",
        f".definelabel TmReadGetRoomChargeState, 0x{get_room_charge_state:X}",
        f".definelabel TmReadRoomChargeTwoTurnExtTable, 0x{room_charge_two_turn_ext:X}",
        f".definelabel PriorPostValidateRestore, 0x{ov29_base + TM_READ_POST_VALIDATE_RESTORE_NOOP_OFF:X}",
    ]
    return "\n".join(lines) + "\n"


def patch_strings(rom: NintendoDSRom, module_dir: Path, manifest: dict[str, Any]) -> None:
    strings_cfg = manifest.get("strings") or {}
    doc = load_yaml(module_dir / strings_cfg.get("yaml", "strings.yaml"))
    config = get_ppmdu_config_for_rom(rom)
    for item in doc.get("entries") or []:
        string_id = int(item["id"])
        text = str(item["text"])
        for filename in get_files_from_rom_with_extension(rom, "str"):
            if not filename.endswith("text_e.str"):
                continue
            strings = StrHandler.deserialize(
                rom.getFileByName(filename), string_encoding=config.string_encoding
            )
            strings.strings[string_id] = text
            rom.setFileByName(filename, StrHandler.serialize(strings))


def apply_tm_read_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    rom: NintendoDSRom,
    armips: Path,
    state: BuildState | None,
    rom_in: Path,
    prior_hook_sites: set[int],
) -> AppliedModule:
    prebuild = manifest.get("prebuild") or []
    if prebuild:
        run_prebuild(module_dir, rom_in, prebuild)

    config = get_ppmdu_config_for_rom(rom)
    hooks_cfg: list[dict[str, Any]] = manifest.get("hooks") or []
    for hook in hooks_cfg:
        hook.setdefault("binary", "ov29")

    ov11_data = bytearray(get_rom_binary(rom, "ov11"))
    ov29_data = bytearray(_get_binary_bytes(rom, config, "ov29"))
    ov31_data = bytearray(_get_binary_bytes(rom, config, "ov31"))

    for bname, blob, load in (
        ("ov11", ov11_data, _binary_load(profile, "ov11")),
        ("ov29", ov29_data, _binary_load(profile, "ov29")),
        ("ov31", ov31_data, _binary_load(profile, "ov31")),
    ):
        bhooks = [h for h in hooks_cfg if h.get("binary", "ov29") == bname]
        assert_hooks_on_binary(bytes(blob), load, bhooks, profile, prior_hook_sites)

    table_asm = module_dir / "asm" / "generated" / "tm_charge_table_ov29.asm"
    table_count = _read_table_count(table_asm)

    ov29_cave_cfg = manifest.get("ov29_cave") or {}
    ov29_need = _estimate_ov29_cave_bytes(table_count, ov29_cave_cfg)

    cave_binary = normalize_cave_binary(ov29_cave_cfg)
    ov36_data = bytearray(get_rom_binary(rom, cave_binary))
    ov29_slot, ov36_data = allocate_overlay_cave(
        binary=cave_binary,
        overlay_data=ov36_data,
        profile=profile,
        state=state,
        cave_cfg={**ov29_cave_cfg, "estimated_bytes": ov29_need},
        module_id=module_id,
    )

    is_rc_move, get_rc_state, rc_source = _resolve_room_charge_helpers(state, ov29_slot.load_address)
    rc_two_turn_ext = _resolve_room_charge_two_turn_ext(state)

    prior_lines: list[str] = []
    hook_binaries = {
        "ov11": (bytes(ov11_data), _binary_load(profile, "ov11")),
        "ov29": (bytes(ov29_data), _binary_load(profile, "ov29")),
        "ov31": (bytes(ov31_data), _binary_load(profile, "ov31")),
    }
    for hook in hooks_cfg:
        prior_label = hook.get("prior_label")
        if not prior_label:
            continue
        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "ov29")
        blob, load = hook_binaries[bname]
        off = site - load
        word = struct.unpack_from("<I", blob, off)[0]
        prior = resolve_prior_target(site, word, hook)
        prior_lines.append(f".definelabel {prior_label}, 0x{prior:X}")

    gen_text = _build_generated_inc(
        module_id=module_id,
        ov29_base=ov29_slot.load_address,
        table_count=table_count,
        is_room_charge_move=is_rc_move,
        get_room_charge_state=get_rc_state,
        room_charge_two_turn_ext=rc_two_turn_ext,
        room_charge_helper_source=rc_source,
    )
    if prior_lines:
        gen_text = gen_text.rstrip("\n") + "\n" + "\n".join(prior_lines) + "\n"

    asm_dir = module_dir / (manifest.get("asm") or {}).get("dir", "asm")
    asm_entry = (manifest.get("asm") or {}).get("entry", "main.asm")

    with tempfile.TemporaryDirectory(prefix="true_patches_tmread_") as tmp:
        tmp_path = Path(tmp)
        ov11_path = tmp_path / "overlay_0011.bin"
        ov29_path = tmp_path / "overlay_0029.bin"
        ov31_path = tmp_path / "overlay_0031.bin"
        ov36_path = tmp_path / overlay_filename(cave_binary)
        ov11_path.write_bytes(bytes(ov11_data))
        ov29_path.write_bytes(bytes(ov29_data))
        ov31_path.write_bytes(bytes(ov31_data))
        ov36_path.write_bytes(bytes(ov36_data))

        gen_inc = tmp_path / "generated.inc"
        write_generated_inc_text(gen_inc, gen_text)

        run_armips_bundle(
            armips=armips,
            asm_dir=asm_dir,
            asm_entry=asm_entry,
            binaries={
                "overlay_0011.bin": ov11_path,
                "overlay_0029.bin": ov29_path,
                "overlay_0031.bin": ov31_path,
                overlay_filename(cave_binary): ov36_path,
            },
            generated_inc=gen_inc,
        )

        ov36_out = ov36_path.read_bytes()
        force_exports = _resolve_tm_force_restore_exports(
            ov36_out,
            overlay_load=_binary_load(profile, cave_binary),
            cave_load=ov29_slot.load_address,
            cave_size=ov29_slot.size,
        )

        _set_binary_bytes(rom, config, "ov11", ov11_path.read_bytes())
        _set_binary_bytes(rom, config, "ov29", ov29_path.read_bytes())
        _set_binary_bytes(rom, config, "ov31", ov31_path.read_bytes())
        _set_binary_bytes(rom, config, cave_binary, ov36_out)

    patch_strings(rom, module_dir, manifest)

    hook_records: list[dict[str, Any]] = []
    for hook in hooks_cfg:
        load = _binary_load(profile, hook.get("binary", "ov29"))
        hook_records.extend(collect_hook_records([hook], profile, load))

    caves = [
        CaveAllocation(
            overlay=cave_binary,
            file_offset=ov29_slot.file_offset,
            size=ov29_slot.size,
            load_address=ov29_slot.load_address,
        ),
    ]

    tm_data: dict[str, Any] = {
        "cave_base_ov29": f"0x{ov29_slot.load_address:X}",
        "tm_table_count": table_count,
        "room_charge_helpers": rc_source,
        "TmReadIsRoomChargeMove": f"0x{is_rc_move:X}",
        "TmReadGetRoomChargeState": f"0x{get_rc_state:X}",
        "TmReadRoomChargeTwoTurnExtTable": f"0x{rc_two_turn_ext:X}",
    }
    tm_data.update(force_exports)

    applied = AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=caves,
        hooks=[
            HookRecord(
                name=h["name"],
                site=h["site"],
                kind=h.get("kind", "overwrite"),
                target_symbol=h.get("target_symbol", h["name"]),
                chain=h.get("chain", "first"),
            )
            for h in hook_records
        ],
        data=[tm_data],
    )
    exports = _export_cave_symbols(ov29_cave_cfg, ov29_slot)
    if exports and applied.data:
        applied.data[0].update(exports)
    # Prefer post-armips ForceRestore addresses over stale fixed offsets.
    applied.data[0].update(force_exports)
    return applied


def verify_tm_read_module(
    rom_path: Path,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    state_mod: AppliedModule | None,
) -> None:
    if not state_mod or not state_mod.caves:
        raise AssertionError("tm_read state missing combat cave allocation")

    rom = NintendoDSRom(rom_path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _id, _n: b"")
    ov11 = bytes(rom.files[table[11].fileID])
    ov29 = bytes(rom.files[table[29].fileID])
    ov31 = bytes(rom.files[table[31].fileID])

    cave = state_mod.caves[0]
    cave_blob = bytes(rom.files[table[overlay_index(cave.overlay)].fileID])

    if not any(cave_blob[cave.file_offset : cave.file_offset + 64]):
        raise AssertionError(f"tm_read {cave.overlay} cave empty")

    overlay_load = int(profile.get("overlay29_load", OV29_LOAD))
    ov31_load = int(profile.get("overlay31_load", OV31_LOAD))

    from .manifest import resolve_symbol

    for hook in manifest.get("hooks") or []:
        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "ov29")
        if bname in ("ov31", "overlay31"):
            blob, load = ov31, ov31_load
        elif bname in ("ov11", "overlay11", "overlay_0011"):
            blob, load = ov11, _binary_load(profile, "ov11")
        else:
            blob, load = ov29, overlay_load
        off = site - load
        word = struct.unpack_from("<I", blob, off)[0]
        if (word >> 24) not in (0xEA, 0xEB):
            raise AssertionError(f"hook {hook['name']} @ {site:#x} not branch/bl: {word:#010x}")

    strings_cfg = manifest.get("strings") or {}
    doc = load_yaml(module_dir / strings_cfg.get("yaml", "strings.yaml"))
    for item in doc.get("entries") or []:
        string_id = int(item["id"])
        expected = str(item["text"])
        for filename in get_files_from_rom_with_extension(rom, "str"):
            if filename.endswith("text_e.str"):
                strings = StrHandler.deserialize(rom.getFileByName(filename))
                if strings.strings[string_id] != expected:
                    raise AssertionError(
                        f"string {string_id}: {strings.strings[string_id]!r} != {expected!r}"
                    )
                break
