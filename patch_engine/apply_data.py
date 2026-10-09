from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from ndspy.rom import NintendoDSRom
from range_typed_integers import u16
from skytemple_files.common.util import get_binary_from_rom, get_ppmdu_config_for_rom, set_binary_in_rom
from skytemple_files.data.item_p.handler import ItemPHandler
from skytemple_files.hardcoded.fixed_floor import HardcodedFixedFloorTables

from .data_patches import DataPatchRecord
from .manifest import load_module_manifest
from .state import AppliedModule, BuildState, load_state, save_state


def sell_price_from_buy(buy: int, *, divisor: int = 4, sig_digits_floor: int = 2) -> int:
    """25% of buy (integer divide), then floor to sig_digits_floor significant digits."""
    if buy <= 0:
        return 0
    n = buy // divisor
    if n <= 0:
        return 0
    if n < 10 or sig_digits_floor <= 1:
        return n
    mag = 10 ** (int(math.floor(math.log10(n))) - (sig_digits_floor - 1))
    return (n // mag) * mag


def apply_difficulty_unlock_unionall(
    rom: NintendoDSRom,
    manifest: dict[str, Any],
) -> DataPatchRecord:
    """Bypass Expert/Hardcore Darkrai Performance(18) gates in unionall.ssb."""
    data_cfg = manifest.get("data") or {}
    if data_cfg.get("handler") != "difficulty_unlock_unionall":
        raise ValueError(f"unknown data handler: {data_cfg.get('handler')!r}")

    path = str(data_cfg.get("path") or "SCRIPT/COMMON/unionall.ssb")
    raw = bytearray(rom.getFileByName(path))
    applied: list[dict[str, Any]] = []
    for ent in data_cfg.get("patches") or []:
        find = bytes.fromhex(str(ent["find"]))
        replace = bytes.fromhex(str(ent["replace"]))
        if len(find) != len(replace):
            raise RuntimeError(f"patch {ent.get('name')}: find/replace length mismatch")
        idx = raw.find(find)
        if idx < 0:
            # already patched?
            if raw.find(replace) >= 0:
                applied.append({"name": ent.get("name"), "status": "already", "offset": None})
                continue
            raise RuntimeError(f"patch {ent.get('name')}: pattern not found in {path}")
        if raw.find(find, idx + 1) >= 0:
            raise RuntimeError(f"patch {ent.get('name')}: pattern not unique in {path}")
        raw[idx : idx + len(find)] = replace
        applied.append({"name": ent.get("name"), "status": "patched", "offset": idx})
    rom.setFileByName(path, bytes(raw))
    return DataPatchRecord(
        overlay="script",
        table="unionall.ssb",
        entries=len(applied),
        fields_changed=sum(1 for a in applied if a["status"] == "patched"),
        details={"path": path, "patches": applied},
    )


def _sprite_entries(manifest: dict[str, Any], module_dir: Path) -> list[tuple[int, Path]]:
    data_cfg = manifest.get("data") or {}
    out: list[tuple[int, Path]] = []
    for ent in data_cfg.get("sprites") or []:
        idx = int(ent["index"])
        path = module_dir / str(ent["file"])
        if not path.is_file():
            raise RuntimeError(f"sprite file missing: {path}")
        out.append((idx, path))
    return out


def apply_ground_sprite_replace(
    rom: NintendoDSRom,
    manifest: dict[str, Any],
    module_dir: Path,
) -> DataPatchRecord:
    """Replace entries of a BIN_PACK sprite container (MONSTER/m_ground.bin) with bundled files."""
    from skytemple_files.common.types.file_types import FileType

    data_cfg = manifest.get("data") or {}
    if data_cfg.get("handler") != "ground_sprite_replace":
        raise ValueError(f"unknown data handler: {data_cfg.get('handler')!r}")
    pack_path = str(data_cfg.get("pack") or "MONSTER/m_ground.bin")
    pack = FileType.BIN_PACK.deserialize(rom.getFileByName(pack_path))

    applied: list[dict[str, Any]] = []
    changed = 0
    for idx, path in _sprite_entries(manifest, module_dir):
        if idx >= len(pack):
            raise RuntimeError(f"{pack_path}: index {idx} out of range ({len(pack)} entries)")
        new = path.read_bytes()
        old = bytes(pack[idx])
        if old == new:
            applied.append({"index": idx, "file": path.name, "status": "already", "size": len(new)})
            continue
        pack[idx] = new
        changed += 1
        applied.append(
            {"index": idx, "file": path.name, "status": "patched", "old_size": len(old), "size": len(new)}
        )
    if changed:
        rom.setFileByName(pack_path, FileType.BIN_PACK.serialize(pack))
    return DataPatchRecord(
        overlay="data",
        table=pack_path,
        entries=len(applied),
        fields_changed=changed,
        details={"pack": pack_path, "sprites": applied},
    )


def verify_ground_sprite_replace(rom_path: Path, manifest: dict[str, Any], module_dir: Path) -> None:
    from skytemple_files.common.types.file_types import FileType

    data_cfg = manifest.get("data") or {}
    pack_path = str(data_cfg.get("pack") or "MONSTER/m_ground.bin")
    rom = NintendoDSRom(rom_path.read_bytes())
    pack = FileType.BIN_PACK.deserialize(rom.getFileByName(pack_path))
    for idx, path in _sprite_entries(manifest, module_dir):
        if bytes(pack[idx]) != path.read_bytes():
            raise AssertionError(f"{pack_path}[{idx}] does not match {path.name}")


def apply_fixed_room_orbs(
    rom: NintendoDSRom,
    manifest: dict[str, Any],
) -> DataPatchRecord:
    """Enable orbs + warp + trawl flags on every fixed-floor properties row (overlay10)."""
    data_cfg = manifest.get("data") or {}
    if data_cfg.get("handler") != "fixed_floor_properties_all_true":
        raise ValueError(f"unknown data handler: {data_cfg.get('handler')!r}")

    config = get_ppmdu_config_for_rom(rom)
    overlay10 = bytearray(get_binary_from_rom(rom, config.bin_sections.overlay10))
    props = HardcodedFixedFloorTables.get_fixed_floor_properties(overlay10, config)

    field_names = data_cfg.get(
        "property_fields",
        ["orbs_enabled", "unk8", "unk9"],
    )
    changed_rows = 0
    for prop in props:
        before = tuple(getattr(prop, name) for name in field_names)
        for name in field_names:
            setattr(prop, name, True)
        after = tuple(getattr(prop, name) for name in field_names)
        if before != after:
            changed_rows += 1

    HardcodedFixedFloorTables.set_fixed_floor_properties(overlay10, props, config)
    set_binary_in_rom(rom, config.bin_sections.overlay10, bytes(overlay10))

    return DataPatchRecord(
        overlay="ov10",
        table="FIXED_ROOM_PROPERTIES_TABLE",
        entries=len(props),
        fields_changed=changed_rows,
        details={
            "property_fields": field_names,
            "all_set_true": True,
        },
    )


def apply_shop_sell_price(
    rom: NintendoDSRom,
    manifest: dict[str, Any],
) -> DataPatchRecord:
    data_cfg = manifest.get("data") or {}
    if data_cfg.get("handler") != "shop_sell_price_item_p":
        raise ValueError(f"unknown data handler: {data_cfg.get('handler')!r}")

    rule = data_cfg.get("rule") or {}
    divisor = int(rule.get("divisor", 4))
    sig_digits = int(rule.get("significant_digits_floor", 2))
    files: list[str] = list(
        data_cfg.get("files") or ["BALANCE/item_p.bin", "UTILITY/item_p.bin"]
    )

    per_file: dict[str, int] = {}
    total_changed = 0
    entry_count = 0
    patched_files: list[str] = []

    for path in files:
        try:
            raw = rom.getFileByName(path)
        except KeyError:
            continue
        item_p = ItemPHandler.deserialize(raw)
        entry_count = max(entry_count, len(item_p.item_list))
        changed = 0
        for entry in item_p.item_list:
            new_sell = min(sell_price_from_buy(entry.buy_price, divisor=divisor, sig_digits_floor=sig_digits), 0xFFFF)
            if entry.sell_price != new_sell:
                entry.sell_price = u16(new_sell)
                changed += 1
        rom.setFileByName(path, ItemPHandler.serialize(item_p))
        per_file[path] = changed
        total_changed += changed
        patched_files.append(path)

    if not patched_files:
        raise RuntimeError(f"no item_p files found in ROM: {files!r}")

    return DataPatchRecord(
        overlay="data",
        table="item_p",
        entries=entry_count,
        fields_changed=total_changed,
        details={
            "files": patched_files,
            "per_file": per_file,
            "rule": {"divisor": divisor, "significant_digits_floor": sig_digits},
        },
    )


def _u32(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off : off + 4], "little")


def _set_u32(buf: bytearray, off: int, value: int) -> None:
    buf[off : off + 4] = int(value).to_bytes(4, "little")


def _cmp_imm_word(vanilla_word: int, limit: int) -> int:
    """Replace a rotate-0 cmp immediate (vanilla #6) with `limit` (must fit in imm8)."""
    if limit < 0 or limit > 0xFF:
        raise ValueError(f"body-size limit {limit} is not an ARM imm8")
    imm12 = vanilla_word & 0xFFF
    if imm12 != 0x006:
        raise ValueError(f"expected cmp #6 (imm12 0x006), got {imm12:#x} in {vanilla_word:#010x}")
    return (vanilla_word & ~0xFFF) | limit


def apply_team_body_size_limit(
    rom: NintendoDSRom,
    manifest: dict[str, Any],
) -> DataPatchRecord:
    """Raise the team body-size total compares from 6 to the configured limit."""
    from .overlay_caves import get_rom_binary, write_rom_binary

    data_cfg = manifest.get("data") or {}
    if data_cfg.get("handler") != "team_body_size_limit":
        raise ValueError(f"unknown data handler: {data_cfg.get('handler')!r}")

    limit = int(data_cfg.get("limit", 16))
    config = get_ppmdu_config_for_rom(rom)
    blobs: dict[str, bytearray] = {}
    applied: list[dict[str, Any]] = []

    for ent in data_cfg.get("sites") or []:
        binary = str(ent["binary"])
        address = int(ent["address"])
        vanilla_word = int(ent["vanilla_word"])
        load = 0x02000000 if binary == "arm9" else 0x022DC240
        if binary == "ov29":
            load = 0x022DC240
        off = address - load
        if binary not in blobs:
            blobs[binary] = get_rom_binary(rom, binary)
        blob = blobs[binary]
        current = _u32(blob, off)
        patched = _cmp_imm_word(vanilla_word, limit)
        if current == patched:
            status = "already"
        elif current == vanilla_word:
            _set_u32(blob, off, patched)
            status = "patched"
        else:
            raise RuntimeError(
                f"{ent.get('name')} @ {address:#x}: expected {vanilla_word:#010x} "
                f"or {patched:#010x}, found {current:#010x}"
            )
        applied.append(
            {
                "name": ent.get("name"),
                "binary": binary,
                "address": address,
                "status": status,
                "word": patched,
            }
        )

    for binary, blob in blobs.items():
        write_rom_binary(rom, config, binary, bytes(blob))

    return DataPatchRecord(
        overlay="arm9+ov29",
        table="team_body_size_limit",
        entries=len(applied),
        fields_changed=sum(1 for a in applied if a["status"] == "patched"),
        details={"limit": limit, "sites": applied},
    )


def verify_team_body_size_limit(rom_path: Path, manifest: dict[str, Any]) -> None:
    from .overlay_caves import get_rom_binary

    rom = NintendoDSRom(rom_path.read_bytes())
    data_cfg = manifest.get("data") or {}
    limit = int(data_cfg.get("limit", 16))
    blobs: dict[str, bytes] = {}
    for ent in data_cfg.get("sites") or []:
        binary = str(ent["binary"])
        address = int(ent["address"])
        vanilla_word = int(ent["vanilla_word"])
        load = 0x02000000 if binary == "arm9" else 0x022DC240
        patched = _cmp_imm_word(vanilla_word, limit)
        if binary not in blobs:
            blobs[binary] = bytes(get_rom_binary(rom, binary))
        current = _u32(blobs[binary], address - load)
        if current != patched:
            raise AssertionError(
                f"{ent.get('name')} @ {address:#x}: expected {patched:#010x}, found {current:#010x}"
            )


def apply_data_module(
    module_id: str,
    rom_in: Path,
    rom_out: Path,
    *,
    state_path: Path | None = None,
    force_reapply: bool = False,
) -> BuildState:
    root = Path(__file__).resolve().parent.parent / "true_patches"
    manifest = load_module_manifest(root / module_id)

    profile_id = manifest.get("rom_profile", "us_vanilla")
    overlay_load = 0x022DC240

    state = load_state(state_path) if state_path else None
    if state is None:
        state = BuildState(rom_profile=profile_id, overlay29_load=overlay_load)
    elif state.rom_profile != profile_id:
        raise RuntimeError(f"state profile {state.rom_profile!r} != {profile_id!r}")

    if state.get_module(module_id) and not force_reapply:
        raise RuntimeError(
            f"module {module_id!r} already in state; pass force_reapply=True to redo"
        )

    for req in manifest.get("requires") or []:
        if not state.get_module(req):
            raise RuntimeError(f"module {module_id!r} requires {req!r} applied first")

    rom = NintendoDSRom(rom_in.read_bytes())
    handler = (manifest.get("data") or {}).get("handler")
    if handler == "fixed_floor_properties_all_true":
        record = apply_fixed_room_orbs(rom, manifest)
    elif handler == "shop_sell_price_item_p":
        record = apply_shop_sell_price(rom, manifest)
    elif handler == "difficulty_unlock_unionall":
        record = apply_difficulty_unlock_unionall(rom, manifest)
    elif handler == "team_body_size_limit":
        record = apply_team_body_size_limit(rom, manifest)
    elif handler == "ground_sprite_replace":
        record = apply_ground_sprite_replace(rom, manifest, root / module_id)
    else:
        raise NotImplementedError(f"data handler {handler!r}")

    state.upsert_module(
        AppliedModule(
            id=module_id,
            version=int(manifest.get("version", 1)),
            data=[record.to_dict()],
        )
    )

    rom_out.write_bytes(rom.save())
    if state_path:
        save_state(state_path, state)
    return state


def verify_data_module(
    rom_path: Path,
    module_dir: Path,
    manifest: dict[str, Any] | None = None,
) -> None:
    if manifest is None:
        manifest = load_module_manifest(module_dir)
    handler = (manifest.get("data") or {}).get("handler")
    if handler == "fixed_floor_properties_all_true":
        verify_fixed_room_orbs(rom_path, manifest)
    elif handler == "shop_sell_price_item_p":
        verify_shop_sell_price(rom_path, manifest)
    elif handler == "difficulty_unlock_unionall":
        verify_difficulty_unlock_unionall(rom_path, manifest)
    elif handler == "team_body_size_limit":
        verify_team_body_size_limit(rom_path, manifest)
    elif handler == "ground_sprite_replace":
        verify_ground_sprite_replace(rom_path, manifest, Path(module_dir))
    else:
        raise NotImplementedError(f"verify for data handler {handler!r}")


def verify_difficulty_unlock_unionall(rom_path: Path, manifest: dict[str, Any]) -> None:
    rom = NintendoDSRom(rom_path.read_bytes())
    data_cfg = manifest.get("data") or {}
    path = str(data_cfg.get("path") or "SCRIPT/COMMON/unionall.ssb")
    raw = rom.getFileByName(path)
    for ent in data_cfg.get("patches") or []:
        replace = bytes.fromhex(str(ent["replace"]))
        find = bytes.fromhex(str(ent["find"]))
        if raw.find(replace) < 0:
            raise AssertionError(f"{path}: patched pattern missing for {ent.get('name')}")
        if raw.find(find) >= 0:
            raise AssertionError(f"{path}: vanilla gate still present for {ent.get('name')}")


def verify_fixed_room_orbs(rom_path: Path, manifest: dict[str, Any]) -> None:
    rom = NintendoDSRom(rom_path.read_bytes())
    config = get_ppmdu_config_for_rom(rom)
    overlay10 = get_binary_from_rom(rom, config.bin_sections.overlay10)
    props = HardcodedFixedFloorTables.get_fixed_floor_properties(overlay10, config)

    field_names = (manifest.get("data") or {}).get(
        "property_fields",
        ["orbs_enabled", "unk8", "unk9"],
    )
    bad = [
        idx
        for idx, prop in enumerate(props)
        if not all(getattr(prop, name) for name in field_names)
    ]
    if bad:
        raise AssertionError(
            f"fixed room properties not all enabled ({len(bad)}/{len(props)} bad); "
            f"first indices: {bad[:8]}"
        )


def verify_shop_sell_price(rom_path: Path, manifest: dict[str, Any]) -> None:
    rom = NintendoDSRom(rom_path.read_bytes())
    data_cfg = manifest.get("data") or {}
    rule = data_cfg.get("rule") or {}
    divisor = int(rule.get("divisor", 4))
    sig_digits = int(rule.get("significant_digits_floor", 2))
    files: list[str] = list(
        data_cfg.get("files") or ["BALANCE/item_p.bin", "UTILITY/item_p.bin"]
    )

    checked_files = 0
    for path in files:
        try:
            raw = rom.getFileByName(path)
        except KeyError:
            continue
        item_p = ItemPHandler.deserialize(raw)
        bad: list[tuple[int, int, int]] = []
        for idx, entry in enumerate(item_p.item_list):
            expected = min(
                sell_price_from_buy(entry.buy_price, divisor=divisor, sig_digits_floor=sig_digits),
                0xFFFF,
            )
            if entry.sell_price != expected:
                bad.append((idx, entry.sell_price, expected))
        if bad:
            sample = bad[:5]
            raise AssertionError(
                f"{path}: {len(bad)} sell_price mismatch(es); samples: {sample}"
            )
        checked_files += 1

    if checked_files == 0:
        raise AssertionError(f"no item_p files to verify: {files!r}")
