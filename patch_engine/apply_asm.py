from __future__ import annotations

import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import (
    get_files_from_rom_with_extension,
    get_ppmdu_config_for_rom,
    read_u32,
    set_binary_in_rom,
)
from skytemple_files.data.str.handler import StrHandler

from .armips_runner import run_armips_bundle, run_armips_module, write_generated_inc_text
from .cave_allocator import allocate_cave, CaveSlot
from .cave_manifest import parse_forbidden_ranges, parse_max_file_offset
from .ov29_layout import write_ov29_to_rom
from .overlay_caves import (
    OV29_NAMES,
    allocate_overlay_cave,
    binary_load,
    get_rom_binary,
    normalize_cave_binary,
    overlay_filename,
    write_rom_binary,
)
from .arm9_layout import (
    ORB_ARM9_DISPLAY_SIZE,
    orb_arm9_cave_forbidden_yaml,
    preferred_orb_arm9_file_offset,
    state_has_tm_read_arm9_cave,
)
from .cave_reservations import (
    FileRange,
    format_file_offset_inc,
    reserved_file_ranges,
)
from .hook_registry import (
    assert_hooks_on_binary,
    collect_hook_records,
    resolve_prior_target,
)
from .manifest import load_yaml, resolve_symbol
from .prebuild import run_prebuild
from .state import AppliedModule, BuildState, CaveAllocation, HookRecord


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _binary_load(profile: dict[str, Any], name: str) -> int:
    return binary_load(profile, name)


def _get_rom_binary(rom: NintendoDSRom, config, name: str) -> bytearray:
    return get_rom_binary(rom, name)


def _set_rom_binary(rom: NintendoDSRom, config, name: str, data: bytes) -> None:
    write_rom_binary(rom, config, name, data)


def _patch_strings(rom: NintendoDSRom, module_dir: Path, manifest: dict[str, Any]) -> None:
    strings_cfg = manifest.get("strings") or {}
    if not strings_cfg:
        return
    doc = load_yaml(module_dir / strings_cfg.get("yaml", "strings.yaml"))
    config = get_ppmdu_config_for_rom(rom)
    for item in doc.get("entries") or []:
        string_id = int(item["id"])
        text = str(item["text"])
        for filename in get_files_from_rom_with_extension(rom, "str"):
            if not filename.endswith("text_e.str"):
                continue
            strings = StrHandler.deserialize(rom.getFileByName(filename))
            strings.strings[string_id] = text
            rom.setFileByName(filename, StrHandler.serialize(strings))


def _patch_orb_item_moves(rom: NintendoDSRom, manifest: dict[str, Any]) -> None:
    """Point orb items at a different move, and make spare moves self-targeted."""
    move_ids = manifest.get("item_move_ids") or {}
    user_moves = [int(m) for m in (manifest.get("user_range_moves") or [])]
    if not move_ids and not user_moves:
        return
    from skytemple_files.data.item_p.handler import ItemPHandler
    from skytemple_files.data.waza_p.handler import WazaPHandler

    if move_ids:
        for filename in ("BALANCE/item_p.bin", "UTILITY/item_p.bin"):
            item_p = ItemPHandler.deserialize(rom.getFileByName(filename))
            for key, move_id in move_ids.items():
                item_p.item_list[int(key)].move_id = int(move_id)
            rom.setFileByName(filename, ItemPHandler.serialize(item_p))
    if user_moves:
        for filename in (
            "BALANCE/waza_p.bin",
            "UTILITY/waza_p.bin",
            "BALANCE/waza_p2.bin",
            "UTILITY/waza_p2.bin",
        ):
            waza = WazaPHandler.deserialize(rom.getFileByName(filename))
            for mid in user_moves:
                move = waza.moves[mid]
                move.base_power = 0
                move.category = 2
                move.accuracy = 125
                for settings in (move.settings_range, move.settings_range_ai):
                    settings.target = 3
                    settings.range = 7
                    settings.condition = 0
                    settings.unused = 0
            rom.setFileByName(filename, WazaPHandler.serialize(waza))


def _waza_move_count(raw: bytes) -> int:
    from skytemple_files.container.sir0.handler import Sir0Handler
    from skytemple_files.data.waza_p._model import MOVE_ENTRY_BYTELEN

    sir0 = Sir0Handler.deserialize(raw)
    move_ptr = read_u32(sir0.content, sir0.data_pointer)
    learn_ptr = read_u32(sir0.content, sir0.data_pointer + 4)
    span = learn_ptr - move_ptr
    count, rem = divmod(span, MOVE_ENTRY_BYTELEN)
    if count < 1 or rem >= 16:
        raise RuntimeError(f"waza move table is not aligned: span={span}")
    return count


def _apply_waza_accuracies(
    rom: NintendoDSRom, module_dir: Path, manifest: dict[str, Any]
) -> dict[str, Any] | None:
    data_cfg = manifest.get("data") or {}
    rel = data_cfg.get("accuracies_json")
    if not rel:
        return None
    values = {
        int(k): int(v)
        for k, v in json.loads((module_dir / str(rel)).read_text(encoding="utf-8")).items()
    }
    extra_rel = data_cfg.get("accuracy_overrides_json")
    if extra_rel:
        values.update(
            {
                int(k): int(v)
                for k, v in json.loads((module_dir / str(extra_rel)).read_text(encoding="utf-8")).items()
            }
        )
    paths = list(
        data_cfg.get("waza_paths")
        or [
            "BALANCE/waza_p.bin",
            "UTILITY/waza_p.bin",
            "BALANCE/waza_p2.bin",
            "UTILITY/waza_p2.bin",
        ]
    )
    from skytemple_files.data.waza_p.handler import WazaPHandler
    import skytemple_files.data.waza_p._model as waza_p_model

    writes = 0
    for filename in paths:
        if filename not in rom.filenames:
            continue
        raw = rom.getFileByName(filename)
        waza_p_model.MOVE_COUNT = _waza_move_count(raw)
        wp = WazaPHandler.deserialize(raw)
        for mid, acc in values.items():
            if mid >= len(wp.moves):
                continue
            if int(wp.moves[mid].accuracy) != acc:
                wp.moves[mid].accuracy = acc  # type: ignore[assignment]
                writes += 1
        rom.setFileByName(filename, WazaPHandler.serialize(wp))
    return {"writes": writes, "moves": len(values), "paths": paths}


def _parse_fixed(value: Any) -> int | None:
    if value is None:
        return None
    return int(value, 16) if isinstance(value, str) else int(value)


def _orb_arm9_forbidden(cave_cfg: dict[str, Any]) -> list[FileRange]:
    forbidden = parse_forbidden_ranges(cave_cfg)
    seen = {(r.start, r.end) for r in forbidden}
    for entry in orb_arm9_cave_forbidden_yaml():
        block = FileRange(entry["start"], entry["end"])
        if (block.start, block.end) not in seen:
            forbidden.append(block)
    return forbidden


def _orb_arm9_cave_params(
    cave_cfg: dict[str, Any],
    state: BuildState | None,
    *,
    module_id: str | None = None,
) -> tuple[int, int, list[FileRange]]:
    need = int(cave_cfg.get("estimated_bytes", ORB_ARM9_DISPLAY_SIZE))
    manifest_preferred = _parse_fixed(cave_cfg.get("preferred"))
    if state_has_tm_read_arm9_cave(state):
        preferred = preferred_orb_arm9_file_offset(state)
    elif manifest_preferred is not None:
        preferred = manifest_preferred
    else:
        preferred = preferred_orb_arm9_file_offset(state)
    max_off = parse_max_file_offset(cave_cfg)
    return need, preferred, _orb_arm9_forbidden(cave_cfg)


_ZGAUGE_WRAM = 0x022B6A00
_PUSH_R1_R2_LR = 0xE92D4006
_BRANCH_SELF = 0xEAFFFFFE


def _arm_branch(src: int, dest: int, *, link: bool) -> int:
    imm = (dest - src - 8) >> 2
    if imm < -0x800000 or imm > 0x7FFFFF:
        raise RuntimeError(f"branch from {src:#x} to {dest:#x} is out of range")
    return (0xEB000000 if link else 0xEA000000) | (imm & 0xFFFFFF)


def _link_z_scarf(ov36: bytearray, *, cave_load: int, cave_off: int, cave_size: int, load: int) -> None:
    """Point ZMove_AddZGauge at Eq_ScaleZGaugeGain, and that stub back at +4."""
    back = None
    end = cave_off + cave_size
    for off in range(cave_off + 4, end, 4):
        word = struct.unpack_from("<I", ov36, off)[0]
        prev = struct.unpack_from("<I", ov36, off - 4)[0]
        if word == _BRANCH_SELF and prev == _PUSH_R1_R2_LR:
            back = load + off
            break
    if back is None:
        raise RuntimeError("Z-Scarf return stub missing from the equipment cave")

    site = None
    for off in range(0, len(ov36) - 8, 4):
        if struct.unpack_from("<I", ov36, off)[0] != _PUSH_R1_R2_LR:
            continue
        ldr = struct.unpack_from("<I", ov36, off + 4)[0]
        if (ldr & 0xFFFFF000) != 0xE59F1000:
            continue
        pool = load + off + 4 + 8 + (ldr & 0xFFF)
        pool_off = pool - load
        if pool_off < 0 or pool_off + 4 > len(ov36):
            continue
        if struct.unpack_from("<I", ov36, pool_off)[0] != _ZGAUGE_WRAM:
            continue
        site = load + off
        break
    if site is None:
        raise RuntimeError("ZMove_AddZGauge not found; apply z_move_v2 before better_equipment")

    struct.pack_into("<I", ov36, site - load, _arm_branch(site, cave_load, link=False))
    struct.pack_into("<I", ov36, back - load, _arm_branch(back, site + 4, link=False))


def _read_table_count(table_asm: Path) -> int:
    if not table_asm.is_file():
        raise FileNotFoundError(f"charge table asm missing: {table_asm}")
    return table_asm.read_text(encoding="utf-8").count(".halfword")


@dataclass
class CaveSlotWrapper:
    slot: CaveSlot
    binary: str
    label: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "binary": self.binary,
            "label": self.label,
            "file_offset": self.slot.file_offset,
            "file_offset_hex": f"0x{self.slot.file_offset:X}",
            "load_address": self.slot.load_address,
            "load_address_hex": f"0x{self.slot.load_address:X}",
        }


def _parse_symbol_offset(value: Any) -> int:
    return int(value, 16) if isinstance(value, str) else int(value)


def _export_cave_symbols(
    cave_cfg: dict[str, Any],
    slot: CaveSlot,
) -> dict[str, str]:
    """RAM addresses for symbols exported by this module (e.g. room_charge v1 helpers)."""
    exports: dict[str, str] = {}
    raw = cave_cfg.get("export_symbols") or {}
    if isinstance(raw, dict):
        items = raw.items()
    else:
        items = ((entry["name"], entry["offset"]) for entry in raw)
    for name, offset in items:
        off = _parse_symbol_offset(offset)
        exports[str(name)] = f"0x{slot.load_address + off:X}"
    return exports


def _symbol_import_lines(manifest: dict[str, Any], state: BuildState | None) -> list[str]:
    """Resolve manifest symbol_imports from earlier modules' exported cave symbols."""
    names = manifest.get("symbol_imports") or []
    if isinstance(names, dict):
        names = list(names)
    found: dict[str, str] = {}
    if state:
        for mod in state.applied:
            for blob in mod.data or []:
                if not isinstance(blob, dict):
                    continue
                for key, value in blob.items():
                    if key not in names or key in found:
                        continue
                    if isinstance(value, str) and value.startswith("0x"):
                        found[key] = value
                    elif isinstance(value, int):
                        found[key] = f"0x{value:X}"
    lines: list[str] = []
    for name in names:
        lines.append(f".definelabel {name}, {found.get(name, '0')}")
    return lines


def _build_record(
    module_id: str,
    manifest: dict[str, Any],
    cave_wrappers: list[CaveSlotWrapper],
    hook_records: list[dict[str, Any]],
) -> AppliedModule:
    caves = [
        CaveAllocation(
            overlay=w.binary,
            file_offset=w.slot.file_offset,
            size=w.slot.size,
            load_address=w.slot.load_address,
        )
        for w in cave_wrappers
    ]
    return AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=caves,
        hooks=[
            HookRecord(
                name=h["name"],
                site=h["site"],
                kind=h["kind"],
                target_symbol=h["target_symbol"],
                chain=h["chain"],
            )
            for h in hook_records
        ],
        data=[{"cave_layout": [w.to_dict() for w in cave_wrappers]}],
    )


def _read_label_from_inc(path: Path, label: str) -> int | None:
    if not path.is_file():
        return None
    prefix = f".definelabel {label},"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return int(line.split(",", 1)[1].strip(), 16)
    return None


def _prepare_arm9_tail(
    rom: NintendoDSRom,
    module_dir: Path,
    tail_cfg: dict[str, Any],
) -> CaveSlot:
    """Grow arm9 and write a layout include for code that must live in arm9."""
    need = int(tail_cfg.get("estimated_bytes", 0x400))
    label = str(tail_cfg.get("label", "Arm9TailAddress"))
    inc_rel = str(tail_cfg.get("layout_inc", "asm/generated/arm9_layout.inc"))
    inc_path = module_dir / inc_rel
    inc_path.parent.mkdir(parents=True, exist_ok=True)
    arm9 = bytearray(rom.arm9)
    existing = _read_label_from_inc(inc_path, label)
    if existing is not None:
        off = existing - 0x02000000
        if 0 <= off <= len(arm9) - 64 and any(arm9[off : off + 8]):
            inc_path.write_text(
                f"; Reused arm9 tail\n.definelabel {label}, 0x{existing:X}\n",
                encoding="utf-8",
            )
            return CaveSlot(file_offset=off, size=need, load_address=existing)
    start = (len(arm9) + 3) & ~3
    extra = start + need - len(arm9)
    if extra > 0:
        arm9.extend(b"\x00" * extra)
        rom.arm9 = bytes(arm9)
    ram = 0x02000000 + start
    inc_path.write_text(
        f"; Auto-generated arm9 tail\n.definelabel {label}, 0x{ram:X}\n",
        encoding="utf-8",
    )
    return CaveSlot(file_offset=start, size=need, load_address=ram)


def apply_asm_single(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    rom: NintendoDSRom,
    config,
    armips_exe: Path,
    prior_hook_sites: set[int],
    state: BuildState | None = None,
    rom_in: Path | None = None,
) -> tuple[AppliedModule, NintendoDSRom]:
    prebuild = manifest.get("prebuild") or []
    if prebuild:
        if rom_in is None:
            raise RuntimeError(f"{module_id}: prebuild requires rom_in")
        run_prebuild(module_dir, rom_in, prebuild)

    arm9_tail_slot = None
    tail_cfg = manifest.get("arm9_tail") or {}
    if tail_cfg:
        arm9_tail_slot = _prepare_arm9_tail(rom, module_dir, tail_cfg)

    cave_cfg: dict[str, Any] = manifest.get("cave") or {}
    cave_binary = normalize_cave_binary(cave_cfg)
    cave_blob = get_rom_binary(rom, cave_binary)
    slot, cave_blob = allocate_overlay_cave(
        binary=cave_binary,
        overlay_data=cave_blob,
        profile=profile,
        state=state,
        cave_cfg=cave_cfg,
        module_id=module_id,
        arm9_data=bytes(rom.arm9) if cave_binary in ("ov29", "overlay29", "overlay_0029") else None,
    )
    cave_blob[slot.file_offset : slot.file_offset + slot.size] = bytes(slot.size)

    hooks_cfg: list[dict[str, Any]] = manifest.get("hooks") or []
    for hook in hooks_cfg:
        hook.setdefault("binary", "ov29")

    hook_binaries = {hook.get("binary", "ov29") for hook in hooks_cfg}
    binaries: dict[str, bytearray] = {cave_binary: cave_blob}
    for bname in hook_binaries:
        if bname not in binaries:
            binaries[bname] = get_rom_binary(rom, bname)
        load = binary_load(profile, bname)
        bhooks = [h for h in hooks_cfg if h.get("binary", "ov29") == bname]
        assert_hooks_on_binary(bytes(binaries[bname]), load, bhooks, profile, prior_hook_sites)

    asm_cfg = manifest["asm"]
    asm_path = module_dir / asm_cfg["entry"]
    asm_dir = asm_path.parent
    asm_entry = asm_path.name

    label = str(cave_cfg.get("base_label", "RoomChargeCodeFileOff"))
    gen_text = format_file_offset_inc(
        module_id=module_id,
        label=label,
        file_offset=slot.file_offset,
    )
    prior_lines: list[str] = []
    for hook in hooks_cfg:
        prior_label = hook.get("prior_label")
        if not prior_label:
            continue
        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "ov29")
        load = binary_load(profile, bname)
        word = struct.unpack_from("<I", binaries[bname], site - load)[0]
        prior = resolve_prior_target(site, word, hook)
        prior_lines.append(f".definelabel {prior_label}, 0x{prior:X}")
    prior_lines.extend(_symbol_import_lines(manifest, state))
    if prior_lines:
        gen_text = gen_text.rstrip("\n") + "\n" + "\n".join(prior_lines) + "\n"

    with tempfile.TemporaryDirectory(prefix="true_patches_gen_") as tmp:
        gen_inc = Path(tmp) / "generated.inc"
        write_generated_inc_text(gen_inc, gen_text)
        tmp_path = Path(tmp)
        paths = {overlay_filename(name): tmp_path / overlay_filename(name) for name in binaries}
        for name, path in paths.items():
            blob = binaries[next(k for k in binaries if overlay_filename(k) == name)]
            path.write_bytes(bytes(blob))

        if len(paths) == 1:
            only_name = next(iter(paths))
            run_armips_module(
                armips=armips_exe,
                asm_dir=asm_dir,
                asm_entry=asm_entry,
                overlay_path=paths[only_name],
                overlay_filename=only_name,
                generated_inc=gen_inc,
            )
        else:
            run_armips_bundle(
                armips=armips_exe,
                asm_dir=asm_dir,
                asm_entry=asm_entry,
                binaries=paths,
                generated_inc=gen_inc,
            )

        for name, blob in binaries.items():
            blob[:] = paths[overlay_filename(name)].read_bytes()

    if manifest.get("link_z_gauge"):
        cave_name = normalize_cave_binary(cave_cfg)
        _link_z_scarf(
            binaries[cave_name],
            cave_load=slot.load_address,
            cave_off=slot.file_offset,
            cave_size=slot.size,
            load=binary_load(profile, cave_name),
        )

    for name, blob in binaries.items():
        write_rom_binary(rom, config, name, bytes(blob))
    _patch_strings(rom, module_dir, manifest)
    acc_info = _apply_waza_accuracies(rom, module_dir, manifest)
    guest_level_edits = None
    se_pc_level_edits = None
    guest_edits = None
    strong_edits = None
    se_hp_edits = None
    snover_edits = None
    kecleon_edits = None
    if module_id == "base_stats_speed":
        from true_patches.base_stats_speed.generate_tables import (
            patch_deep_star_snover_level_rom,
            patch_exclusive_stat_boosts_rom,
            patch_guest_calcstat_rom,
            patch_guest_level_overrides_rom,
            patch_kecleon_levels_rom,
            patch_se_pc_level_overrides_rom,
            patch_strong_enemy_levels_rom,
        )
        from true_patches.base_stats_speed.patch_se_calcstat_hp import (
            patch_strong_enemy_calcstat_hp_rom,
        )

        guest_level_edits = patch_guest_level_overrides_rom(rom)
        se_pc_level_edits = patch_se_pc_level_overrides_rom(rom)
        guest_edits = patch_guest_calcstat_rom(rom)
        strong_edits = patch_strong_enemy_levels_rom(rom)
        # After level remap: Same Species / listed FR SE HP → CalcStat.
        se_hp_edits = patch_strong_enemy_calcstat_hp_rom(rom)
        snover_edits = patch_deep_star_snover_level_rom(rom)
        kecleon_edits = patch_kecleon_levels_rom(rom)
        exclusive_boost_edits = patch_exclusive_stat_boosts_rom(rom)
    else:
        exclusive_boost_edits = None
    hook_records = collect_hook_records(hooks_cfg, profile, slot.load_address)
    wrappers = [CaveSlotWrapper(slot, normalize_cave_binary(cave_cfg), label)]
    if arm9_tail_slot is not None:
        wrappers.append(
            CaveSlotWrapper(
                arm9_tail_slot,
                "arm9",
                str(tail_cfg.get("label", "Arm9TailAddress")),
            )
        )
    record = _build_record(module_id, manifest, wrappers, hook_records)
    exports = _export_cave_symbols(cave_cfg, slot)
    if exports and record.data:
        record.data[0].update(exports)
        if arm9_tail_slot is not None:
            record.data[0][str(tail_cfg.get("label", "Arm9TailAddress"))] = (
                f"0x{arm9_tail_slot.load_address:X}"
            )
        if acc_info:
            record.data[0]["waza_gen9_accuracy"] = acc_info
        if guest_level_edits is not None:
            record.data[0]["guest_level_overrides"] = guest_level_edits
        if se_pc_level_edits is not None:
            record.data[0]["se_pc_level_overrides"] = se_pc_level_edits
        if guest_edits is not None:
            record.data[0]["guest_calcstat"] = guest_edits
        if strong_edits is not None:
            record.data[0]["strong_enemy_levels"] = strong_edits
        if se_hp_edits is not None:
            record.data[0]["strong_enemy_calcstat_hp"] = se_hp_edits
        if snover_edits is not None:
            record.data[0]["deep_star_snover_level"] = snover_edits
        if kecleon_edits is not None:
            record.data[0]["kecleon_levels"] = kecleon_edits
        if exclusive_boost_edits is not None:
            record.data[0]["exclusive_stat_boosts"] = exclusive_boost_edits
    return record, rom


def apply_asm_bundle(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    rom: NintendoDSRom,
    config,
    armips_exe: Path,
    prior_hook_sites: set[int],
    rom_in: Path,
    state: BuildState | None = None,
) -> tuple[AppliedModule, NintendoDSRom]:
    asm_cfg = manifest.get("asm") or {}
    prebuild = manifest.get("prebuild") or []
    if prebuild:
        run_prebuild(module_dir, rom_in, prebuild)

    hooks_cfg: list[dict[str, Any]] = manifest.get("hooks") or []
    for hook in hooks_cfg:
        hook.setdefault("binary", "ov29")

    cave_cfg = asm_cfg.get("cave") or {}
    cave_binary = normalize_cave_binary(cave_cfg)
    bundle_bins = ["ov29", "ov31"]
    for extra in [cave_binary, *(h["binary"] for h in hooks_cfg)]:
        if extra not in bundle_bins:
            bundle_bins.append(extra)
    binaries: dict[str, bytearray] = {
        name: get_rom_binary(rom, name) for name in bundle_bins
    }

    for bname, data in binaries.items():
        load = binary_load(profile, bname)
        bhooks = [h for h in hooks_cfg if h.get("binary", "ov29") == bname]
        assert_hooks_on_binary(bytes(data), load, bhooks, profile, prior_hook_sites)

    table_count = _read_table_count(module_dir / "asm" / "generated" / "orb_charge_table_ov29.asm")
    cave_blob = binaries[cave_binary]
    slot, cave_blob = allocate_overlay_cave(
        binary=cave_binary,
        overlay_data=cave_blob,
        profile=profile,
        state=state,
        cave_cfg=cave_cfg,
        module_id=module_id,
    )
    binaries[cave_binary] = cave_blob
    label = cave_cfg.get("cave_ram_label", "OrbChargesOv29CodeAddress")
    gen_text = (
        f"; Auto-generated by true_patches for {module_id}\n"
        f".definelabel {label}, 0x{slot.load_address:X}\n"
        f"OrbChargeTableCount equ {table_count}\n"
    )

    asm_root = module_dir / asm_cfg.get("dir", "asm")
    asm_entry = asm_cfg.get("entry", "main.asm")

    with tempfile.TemporaryDirectory(prefix="true_patches_bundle_") as tmp:
        tmp_path = Path(tmp)
        paths = {
            overlay_filename(name): tmp_path / overlay_filename(name) for name in bundle_bins
        }
        for name, path in paths.items():
            blob_key = next(k for k in binaries if overlay_filename(k) == name)
            path.write_bytes(bytes(binaries[blob_key]))

        gen_inc = tmp_path / "generated.inc"
        write_generated_inc_text(gen_inc, gen_text)

        run_armips_bundle(
            armips=armips_exe,
            asm_dir=asm_root,
            asm_entry=asm_entry,
            binaries={name: path for name, path in paths.items()},
            generated_inc=gen_inc,
        )

        for bname in binaries:
            binaries[bname][:] = paths[overlay_filename(bname)].read_bytes()

    for bname, data in binaries.items():
        write_rom_binary(rom, config, bname, bytes(data))

    _patch_strings(rom, module_dir, manifest)
    _patch_orb_item_moves(rom, manifest)

    hook_records: list[dict[str, Any]] = []
    for hook in hooks_cfg:
        load = _binary_load(profile, hook.get("binary", "ov29"))
        hook_records.extend(collect_hook_records([hook], profile, load))

    wrapper = CaveSlotWrapper(slot, cave_binary, label)
    record = _build_record(module_id, manifest, [wrapper], hook_records)
    exports = _export_cave_symbols(cave_cfg, slot)
    if exports and record.data:
        record.data[0].update(exports)
    return record, rom


def apply_asm_multi(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    rom: NintendoDSRom,
    config,
    armips_exe: Path,
    prior_hook_sites: set[int],
    rom_in: Path,
    state: BuildState | None = None,
) -> tuple[AppliedModule, NintendoDSRom]:
    asm_cfg = manifest.get("asm") or {}
    if asm_cfg.get("use_bundle"):
        return apply_asm_bundle(
            module_id=module_id,
            module_dir=module_dir,
            manifest=manifest,
            profile=profile,
            rom=rom,
            config=config,
            armips_exe=armips_exe,
            prior_hook_sites=prior_hook_sites,
            rom_in=rom_in,
            state=state,
        )

    prebuild = manifest.get("prebuild") or []
    if prebuild:
        run_prebuild(module_dir, rom_in, prebuild)

    hooks_cfg: list[dict[str, Any]] = manifest.get("hooks") or []
    for hook in hooks_cfg:
        hook.setdefault("binary", "ov29")

    components: list[dict[str, Any]] = manifest["asm"]["components"]
    binaries: dict[str, bytearray] = {
        comp["binary"]: _get_rom_binary(rom, config, comp["binary"]) for comp in components
    }

    for bname, data in binaries.items():
        load = _binary_load(profile, bname)
        bhooks = [h for h in hooks_cfg if h.get("binary", "ov29") == bname]
        assert_hooks_on_binary(bytes(data), load, bhooks, profile, prior_hook_sites)

    table_count = _read_table_count(module_dir / "asm" / "generated" / "orb_charge_table_ov29.asm")
    generated_lines = [
        f"; Auto-generated by true_patches for {module_id}",
        f"OrbChargeTableCount equ {table_count}",
    ]

    cave_wrappers: list[CaveSlotWrapper] = []
    pending_reserved: dict[str, list] = {
        comp["binary"]: list(
            reserved_file_ranges(state, comp["binary"], exclude_module=module_id)
        )
        for comp in components
    }

    for comp in components:
        bname = comp["binary"]
        data = binaries[bname]
        load = _binary_load(profile, bname)
        cave_cfg = comp.get("cave") or {}
        if module_id in ("orb_charges", "orb_charges_v2", "orb_charges_v4") and bname == "arm9":
            need, preferred, forbidden = _orb_arm9_cave_params(
                cave_cfg, state, module_id=module_id
            )
            slot = allocate_cave(
                bytes(data),
                load,
                need,
                alignment=int(cave_cfg.get("alignment", 4)),
                preferred_file_offset=preferred,
                reserved_file_offsets=pending_reserved[bname],
                forbidden_file_offsets=forbidden,
                max_file_offset=parse_max_file_offset(cave_cfg),
            )
        elif normalize_cave_binary(cave_cfg) == bname or (
            bname in OV29_NAMES and normalize_cave_binary(cave_cfg) in OV29_NAMES
        ):
            slot, data = allocate_overlay_cave(
                binary=bname,
                overlay_data=data,
                profile=profile,
                state=state,
                cave_cfg=cave_cfg,
                module_id=module_id,
            )
            binaries[bname] = data
        else:
            forbidden = parse_forbidden_ranges(cave_cfg)
            slot = allocate_cave(
                bytes(data),
                load,
                int(cave_cfg.get("estimated_bytes", 512)),
                alignment=int(cave_cfg.get("alignment", 4)),
                preferred_file_offset=_parse_fixed(cave_cfg.get("preferred")),
                reserved_file_offsets=pending_reserved[bname],
                forbidden_file_offsets=forbidden,
                max_file_offset=parse_max_file_offset(cave_cfg),
            )
        pending_reserved[bname].append(
            FileRange(slot.file_offset, slot.file_offset + slot.size)
        )
        label = comp.get("cave_ram_label")
        cave_wrappers.append(CaveSlotWrapper(slot, bname, label))
        if label == "OrbChargesOv29CodeAddress":
            generated_lines.insert(
                1, f".definelabel OrbChargesOv29CodeAddress, 0x{slot.load_address:X}"
            )
        elif label in ("OrbChargesArm9DisplayCodeAddress", "OrbChargesArm9CodeAddress"):
            generated_lines.append(
                f".definelabel {label}, 0x{slot.load_address:X}"
            )

    if not any(w.label == "OrbChargesOv29CodeAddress" for w in cave_wrappers):
        raise RuntimeError("missing ov29 OrbChargesOv29CodeAddress component")

    gen_text = "\n".join(generated_lines) + "\n"
    asm_root = module_dir / "asm"

    with tempfile.TemporaryDirectory(prefix="true_patches_multi_") as tmp:
        gen_inc = Path(tmp) / "generated.inc"
        write_generated_inc_text(gen_inc, gen_text)

        for comp in components:
            bname = comp["binary"]
            fname = overlay_filename(bname)
            bin_path = Path(tmp) / fname
            bin_path.write_bytes(bytes(binaries[bname]))
            run_armips_module(
                armips=armips_exe,
                asm_dir=asm_root,
                asm_entry=Path(comp["entry"]).name,
                overlay_path=bin_path,
                overlay_filename=fname,
                generated_inc=gen_inc,
            )
            binaries[bname][:] = bin_path.read_bytes()

    for bname, data in binaries.items():
        _set_rom_binary(rom, config, bname, bytes(data))

    _patch_strings(rom, module_dir, manifest)

    hook_records: list[dict[str, Any]] = []
    for hook in hooks_cfg:
        bname = hook.get("binary", "ov29")
        load = _binary_load(profile, bname)
        hook_records.extend(collect_hook_records([hook], profile, load))

    return _build_record(module_id, manifest, cave_wrappers, hook_records), rom


def verify_asm_module(
    rom_path: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    state_mod: AppliedModule | None,
) -> None:
    rom = NintendoDSRom(rom_path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")

    if state_mod and state_mod.caves:
        for cave in state_mod.caves:
            if cave.overlay in ("ov29", "overlay29"):
                ov = bytes(rom.files[table[29].fileID])
                chunk = ov[cave.file_offset : cave.file_offset + 64]
            elif cave.overlay in ("ov36", "overlay36", "overlay_0036"):
                ov = bytes(rom.files[table[36].fileID])
                chunk = ov[cave.file_offset : cave.file_offset + 64]
            elif cave.overlay in ("arm9", "arm9.bin"):
                ov = bytes(rom.arm9)
                off = cave.file_offset
                chunk = ov[off : off + 64]
            else:
                continue
            if not any(chunk):
                raise AssertionError(f"cave {cave.overlay} @ {cave.file_offset:#x} empty")

    overlay_load = int(profile.get("overlay29_load", 0x022DC240))
    ov31_load = int(profile.get("overlay31_load", 0x02382820))
    ov36_load = int(profile.get("overlay36_load", 0x023A7080))
    arm9_load = int(profile.get("arm9_load", 0x02000000))
    ov11_load = int(profile.get("overlay11_load", 0x022DC240))
    ov11 = bytes(rom.files[table[11].fileID])
    ov29 = bytes(rom.files[table[29].fileID])
    ov31 = bytes(rom.files[table[31].fileID])
    ov36 = bytes(rom.files[table[36].fileID])
    arm9 = bytes(rom.arm9)

    for hook in manifest.get("hooks") or []:
        from .manifest import resolve_symbol

        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "ov29")
        if bname in ("arm9", "arm9.bin"):
            blob, load = arm9, arm9_load
        elif bname in ("ov11", "overlay11", "overlay_0011"):
            blob, load = ov11, ov11_load
        elif bname in ("ov31", "overlay31"):
            blob, load = ov31, ov31_load
        elif bname in ("ov36", "overlay36", "overlay_0036"):
            blob, load = ov36, ov36_load
        else:
            blob, load = ov29, overlay_load
        off = site - load
        word = struct.unpack_from("<I", blob, off)[0]
        patched = hook.get("patched_word")
        if patched is not None:
            if isinstance(patched, str):
                patched = int(patched, 16)
            if word != patched:
                raise AssertionError(
                    f"hook {hook['name']} @ {site:#x}: expected patched "
                    f"{patched:#010x}, found {word:#010x}"
                )
            continue
        if (word >> 25) & 0x7 != 0b101 or (word >> 28) == 0xF:
            raise AssertionError(f"hook {hook['name']} @ {site:#x} not branch/bl: {word:#010x}")
