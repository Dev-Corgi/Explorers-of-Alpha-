from __future__ import annotations

import struct
import tempfile
from pathlib import Path
from typing import Any

from ndspy.code import loadOverlayTable, saveOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import (
    get_files_from_rom_with_extension,
    get_ppmdu_config_for_rom,
    set_binary_in_rom,
)
from range_typed_integers import i16
from skytemple_files.data.data_st.handler import DataSTHandler
from skytemple_files.data.str.handler import StrHandler

from .armips_runner import run_armips_bundle, write_generated_inc_text
from .cave_allocator import allocate_cave
from .cave_manifest import parse_forbidden_ranges, parse_max_file_offset
from .arm9_layout import spinda_arm9_legacy_range
from .cave_reservations import FileRange, reserved_file_ranges
from .hook_registry import collect_hook_records, hook_word_kind, resolve_prior_target
from .manifest import load_yaml, resolve_symbol
from .state import AppliedModule, BuildState, CaveAllocation, HookRecord

ARM9_LOAD = 0x02000000
OV19_LOAD = 0x0238A140
OV29_LOAD = 0x022DC240

BOOT_DATA_START = 0x02094AE8
VANILLA_BOOT_WORD = 0xFF000000
LEGACY_ARM9_CODE_FILE = 0x94624
LEGACY_RESET_CAVE_FILE = 0xA3550
LEGACY_ARM9_CODE_MAX = (BOOT_DATA_START - ARM9_LOAD) - LEGACY_ARM9_CODE_FILE
LEGACY_RESET_CAVE_MAX = 0x3B0
RESET_CAVE_SENTINEL = 0x646E6920

SPINDA_DRINK_CAVE_FILE = 0xAF490
SPINDA_DRINK_CAVE_SIZE = 516

VANILLA_SAVE_ALLOC = 0xB65C
SAVE_SIZE_LITS = (0x02049218, 0x0204932C, 0x020495FC)
HOOK_LOAD_EV = 0x020495E0
HOOK_WRITE = 0x02049030
VANILLA_LOAD_HOOK_WORD = 0xEA000000
VANILLA_WRITE_HOOK_WORD = 0xEB004038

LEGACY_SCRATCH_BASE = 0x0209FB30
DUNGEON_STAT_SNAP_OFFSET = 0x400
DUNGEON_STAT_PEEL_OFFSET = 0x434
DUNGEON_STAT_SCRATCH_OFFSET = 0x480
# Alpha GetItemIdFromList cache: 6 lists x 0x2F8 B, rewritten at runtime.
ALPHA_ITEM_LIST_CACHE = (0x0209F904, 0x020A0AD4)
ALPHA_PADDING_BYTE = 0xCC


def _scratch_base(dungeon_stat_cave: int | None) -> int:
    if dungeon_stat_cave is None:
        return LEGACY_SCRATCH_BASE
    return dungeon_stat_cave + DUNGEON_STAT_SCRATCH_OFFSET

# IsGummi (0x0200CBF4): White Gummi 0x77 through Wonder Gummi 0x88, plus Mystic 0x8A.
# Wonder Gummi is ふしぎなグミ (Mysterious Gummi) and is not a drink ingredient.
GUMMI_WHITE_ID = 0x77
GUMMI_WONDER_ID = 0x88
GUMMI_MYSTIC_ID = 0x8A
# ov19 loads UTILITY/itembar.bin for the Drink list; BALANCE keeps the same table.
ITEMBAR_PATHS = ("UTILITY/itembar.bin", "BALANCE/itembar.bin")


def _parse_fixed(value: Any) -> int | None:
    if value is None:
        return None
    return int(value, 16) if isinstance(value, str) else int(value)


def _binary_load(profile: dict[str, Any], name: str) -> int:
    if name in ("ov19", "overlay19", "overlay_0019"):
        return int(profile.get("overlay19_load", OV19_LOAD))
    if name in ("ov29", "overlay29", "overlay_0029"):
        return int(profile.get("overlay29_load", OV29_LOAD))
    if name in ("ov11", "overlay11", "overlay_0011"):
        return int(profile.get("overlay11_load", OV29_LOAD))
    if name in ("arm9", "arm9.bin"):
        return int(profile.get("arm9_load", ARM9_LOAD))
    raise ValueError(f"unknown binary {name!r}")


def _overlay_id(name: str) -> int:
    if name in ("ov19", "overlay19", "overlay_0019"):
        return 19
    if name in ("ov29", "overlay29", "overlay_0029"):
        return 29
    if name in ("ov11", "overlay11", "overlay_0011"):
        return 11
    raise ValueError(f"not an overlay binary: {name!r}")


def _get_binary_bytes(rom: NintendoDSRom, config, name: str) -> bytes:
    if name in ("arm9", "arm9.bin"):
        return bytes(rom.arm9)
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov_id = _overlay_id(name)
    return rom.files[table[ov_id].fileID]


def _set_binary_bytes(rom: NintendoDSRom, config, name: str, data: bytes) -> None:
    if name in ("arm9", "arm9.bin"):
        set_binary_in_rom(rom, config.bin_sections.arm9, data)
        return
    ov_id = _overlay_id(name)
    section = getattr(config.bin_sections, f"overlay{ov_id}")
    set_binary_in_rom(rom, section, data)


def _preferred_arm9_code(state: BuildState | None, manifest: dict[str, Any]) -> int | None:
    legacy = spinda_arm9_legacy_range()
    reserved = reserved_file_ranges(state, "arm9") if state else []
    blocked = any(r.start < legacy.end and r.end > legacy.start for r in reserved)
    if not blocked:
        return legacy.start
    cfg = manifest.get("arm9_code_cave") or {}
    return _parse_fixed(cfg.get("preferred"))


def _assert_spinda_hooks(
    *,
    hooks: list[dict[str, Any]],
    profile: dict[str, Any],
    binaries: dict[str, tuple[bytes, int]],
    prior_hook_sites: set[int],
    force_reapply: bool = False,
) -> None:
    for hook in hooks:
        chain = hook.get("chain", "first")
        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "arm9")
        blob, load = binaries[bname]
        off = site - load
        if off < 0 or off + 4 > len(blob):
            raise RuntimeError(f"hook {hook['name']} @ {site:#x} out of range")
        if site in prior_hook_sites and chain == "first":
            raise RuntimeError(
                f"hook {hook['name']} @ {site:#x} already used; use chain=append or apply order"
            )
        if chain == "append" and site in prior_hook_sites:
            continue
        word = struct.unpack_from("<I", blob, off)[0]
        if "vanilla_word" in hook:
            expected = hook["vanilla_word"]
            if isinstance(expected, str):
                expected = int(expected, 16)
            if word != expected:
                if force_reapply and (word >> 24) in (0xEA, 0xEB):
                    continue
                raise RuntimeError(
                    f"hook {hook['name']} @ {site:#x}: expected {expected:#010x}, found {word:#010x}"
                )
            continue
        expected = hook.get("replace")
        if expected:
            kind = hook_word_kind(word)
            if kind != expected:
                raise RuntimeError(
                    f"hook {hook['name']} @ {site:#x}: expected {expected}, found {kind or word:#010x}"
                )


def _build_generated_inc(
    *,
    module_id: str,
    arm9_code: int,
    reset_cave: int,
    team_submenu_table: int,
    dungeon_stat_cave: int | None = None,
) -> str:
    scratch = _scratch_base(dungeon_stat_cave)
    lines = [
        f"; Auto-generated by true_patches for {module_id}",
        f".definelabel SpindaEvArm9CodeAddress, 0x{arm9_code:X}",
        f".definelabel SpindaEvResetCaveAddress, 0x{reset_cave:X}",
        f".definelabel SpindaEvTeamSubmenuTable, 0x{team_submenu_table:X}",
        f"SummaryRosterIndexAddress equ 0x{scratch:08X}",
        f"EvDrinkSelectedStatAddress equ 0x{scratch + 4:08X}",
        f"EvDrinkLastChoiceAddress equ 0x{scratch + 5:08X}",
        f"EvDrinkHpBeforeAddress equ 0x{scratch + 6:08X}",
        f"EvDrinkSpeBeforeAddress equ 0x{scratch + 7:08X}",
        f"EvDrinkBoostCacheAddress equ 0x{scratch + 8:08X}",
    ]
    if dungeon_stat_cave is not None:
        lines.append(f".definelabel SpindaEvDungeonStatCave, 0x{dungeon_stat_cave:X}")
    return "\n".join(lines) + "\n"


def _zero_unreserved(data: bytearray, start: int, end: int, reserved: list[FileRange]) -> None:
    pos = start
    while pos < end:
        skip = next((r for r in reserved if r.start <= pos < r.end), None)
        if skip:
            pos = skip.end
            continue
        if pos < len(data):
            data[pos] = 0
        pos += 1


def prepare_arm9(
    arm9: bytearray,
    manifest: dict[str, Any],
    *,
    reserved: list[FileRange] | None = None,
) -> None:
    reserved = reserved or []
    prep = manifest.get("prepare") or {}
    if prep.get("restore_save_hooks", True):
        for lit in SAVE_SIZE_LITS:
            struct.pack_into("<I", arm9, lit - ARM9_LOAD, VANILLA_SAVE_ALLOC)
        struct.pack_into("<I", arm9, HOOK_LOAD_EV - ARM9_LOAD, VANILLA_LOAD_HOOK_WORD)
        struct.pack_into("<I", arm9, HOOK_WRITE - ARM9_LOAD, VANILLA_WRITE_HOOK_WORD)
    if prep.get("zero_legacy_caves", True):
        _zero_unreserved(
            arm9,
            LEGACY_ARM9_CODE_FILE,
            LEGACY_ARM9_CODE_FILE + LEGACY_ARM9_CODE_MAX,
            reserved,
        )
        _zero_unreserved(
            arm9,
            LEGACY_RESET_CAVE_FILE,
            LEGACY_RESET_CAVE_FILE + LEGACY_RESET_CAVE_MAX,
            reserved,
        )


def _restore_arm9_boot_tail(arm9: bytearray, module_dir: Path) -> None:
    """Restore ARM9 bytes from boot data through tm_read cave (exclusive)."""
    boot_off = BOOT_DATA_START - ARM9_LOAD
    tail_path = module_dir / "data" / "arm9_boot_tail.bin"
    if not tail_path.is_file():
        raise FileNotFoundError(f"arm9 boot tail not found: {tail_path}")
    tail = tail_path.read_bytes()
    end = boot_off + len(tail)
    if end > len(arm9):
        raise RuntimeError(
            f"arm9 boot tail ({len(tail)} B @ {boot_off:#x}) exceeds arm9 size {len(arm9)}"
        )
    arm9[boot_off:end] = tail


def _zero_cave(data: bytearray, file_offset: int, size: int) -> None:
    end = min(len(data), file_offset + size)
    if file_offset < end:
        data[file_offset:end] = b"\x00" * (end - file_offset)


def _extend_ov19(ov19: bytearray, min_size: int) -> None:
    if len(ov19) < min_size:
        ov19.extend(b"\x00" * (min_size - len(ov19)))


OV19_INNER16_RESTORE_START = 0x0238B478 - OV19_LOAD
OV19_INNER16_RESTORE_END = 0x0238B518 - OV19_LOAD
OV19_TEAM_MENU_PTR_OFF = 0x0238B474 - OV19_LOAD
OV19_ROSTER_STORE_HOOK_A = 0x0238AB3C
OV19_ROSTER_STORE_HOOK_B = 0x0238AB68
VANILLA_ROSTER_STORE_WORD = 0xE58800D4
def _load_vanilla_ov19_slice(module_dir: Path) -> bytes | None:
    root = module_dir.parent.parent
    for rel in (
        Path("PatchTesting") / "Explorers of Alpha" / "Explorers of Alpha.nds",
    ):
        vanilla_path = root / rel
        if not vanilla_path.is_file():
            continue
        rom = NintendoDSRom(vanilla_path.read_bytes())
        table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19]
        return bytes(rom.files[table.fileID])
    return None


def _restore_ov19_roster_store_hooks(ov19: bytearray, *, ov19_load: int) -> None:
    """Revert v9+ roster hooks outside inner16 restore range."""
    for site in (OV19_ROSTER_STORE_HOOK_A, OV19_ROSTER_STORE_HOOK_B):
        off = site - ov19_load
        if 0 <= off + 4 <= len(ov19):
            struct.pack_into("<I", ov19, off, VANILLA_ROSTER_STORE_WORD)


def _restore_ov19_inner16_tail(
    ov19: bytearray,
    *,
    vanilla_ov19: bytes | None,
    team_table_load: int,
) -> None:
    """Restore B478–B517; point B474 at extended E380 stat label table."""
    if vanilla_ov19 is None:
        return
    if len(vanilla_ov19) < OV19_INNER16_RESTORE_END or len(ov19) < OV19_INNER16_RESTORE_END:
        return
    ov19[OV19_INNER16_RESTORE_START:OV19_INNER16_RESTORE_END] = vanilla_ov19[
        OV19_INNER16_RESTORE_START:OV19_INNER16_RESTORE_END
    ]
    struct.pack_into("<I", ov19, OV19_TEAM_MENU_PTR_OFF, team_table_load)


def _string_yaml_paths(module_dir: Path, strings_cfg: dict[str, Any]) -> list[Path]:
    yaml_cfg = strings_cfg.get("yaml", "strings.yaml")
    if isinstance(yaml_cfg, str):
        names = [yaml_cfg]
    else:
        names = list(yaml_cfg)
    return [module_dir / name for name in names]


def _is_drink_ingredient(item_id: int) -> bool:
    if item_id == GUMMI_WONDER_ID:
        return False
    if GUMMI_WHITE_ID <= item_id < GUMMI_WONDER_ID:
        return True
    return item_id == GUMMI_MYSTIC_ID


def patch_drink_ingredients(rom: NintendoDSRom) -> None:
    """Drink ingredient menu lists BAR entries. Keep type gummis; drop Wonder Gummi."""
    for path in ITEMBAR_PATHS:
        bar = DataSTHandler.deserialize(rom.getFileByName(path))
        for item_id in range(bar.nb_struct_ids()):
            if not _is_drink_ingredient(item_id):
                bar.set_item_struct_id(item_id, i16(-1))
        rom.setFileByName(path, DataSTHandler.serialize(bar))


def patch_strings(rom: NintendoDSRom, module_dir: Path, manifest: dict[str, Any]) -> None:
    strings_cfg = manifest.get("strings") or {}
    entries: list[dict[str, Any]] = []
    for yaml_path in _string_yaml_paths(module_dir, strings_cfg):
        if not yaml_path.is_file():
            raise FileNotFoundError(f"strings yaml not found: {yaml_path}")
        doc = load_yaml(yaml_path)
        entries.extend(doc.get("entries") or [])
    if not entries:
        return
    config = get_ppmdu_config_for_rom(rom)
    max_id = max(int(item["id"]) for item in entries)
    for filename in get_files_from_rom_with_extension(rom, "str"):
        if not filename.endswith("text_e.str"):
            continue
        strings = StrHandler.deserialize(
            rom.getFileByName(filename), string_encoding=config.string_encoding
        )
        if len(strings.strings) <= max_id:
            strings.strings.extend([""] * (max_id + 1 - len(strings.strings)))
        for item in entries:
            strings.strings[int(item["id"])] = str(item["text"])
        rom.setFileByName(filename, StrHandler.serialize(strings))
        return
    raise RuntimeError("text_e.str not found in ROM")


def apply_spinda_ev_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    rom: NintendoDSRom,
    armips: Path,
    state: BuildState | None,
    prior_hook_sites: set[int],
    force_reapply: bool = False,
) -> AppliedModule:
    config = get_ppmdu_config_for_rom(rom)
    hooks_cfg: list[dict[str, Any]] = manifest.get("hooks") or []

    arm9_data = bytearray(_get_binary_bytes(rom, config, "arm9"))
    ov19_data = bytearray(_get_binary_bytes(rom, config, "ov19"))
    ov29_data = bytearray(_get_binary_bytes(rom, config, "ov29"))
    ov11_data = bytearray(_get_binary_bytes(rom, config, "ov11"))

    arm9_reserved = reserved_file_ranges(state, "arm9", exclude_module=module_id)
    prepare_arm9(arm9_data, manifest, reserved=arm9_reserved)

    ov19_cfg = manifest.get("ov19_extend") or {}
    min_ov19 = int(ov19_cfg.get("min_size", 17024))
    table_file_off = int(ov19_cfg.get("table_file_offset", 16960))
    _extend_ov19(ov19_data, min_ov19)

    binaries = {
        "arm9": (bytes(arm9_data), _binary_load(profile, "arm9")),
        "ov19": (bytes(ov19_data), _binary_load(profile, "ov19")),
        "ov29": (bytes(ov29_data), _binary_load(profile, "ov29")),
        "ov11": (bytes(ov11_data), _binary_load(profile, "ov11")),
    }
    _assert_spinda_hooks(
        hooks=hooks_cfg,
        profile=profile,
        binaries=binaries,
        prior_hook_sites=prior_hook_sites,
        force_reapply=force_reapply,
    )

    code_cfg = manifest.get("arm9_code_cave") or {}
    reset_cfg = manifest.get("arm9_reset_cave") or {}

    code_slot = allocate_cave(
        bytes(arm9_data),
        _binary_load(profile, "arm9"),
        int(code_cfg.get("estimated_bytes", LEGACY_ARM9_CODE_MAX)),
        alignment=int(code_cfg.get("alignment", 4)),
        preferred_file_offset=_preferred_arm9_code(state, manifest),
        reserved_file_offsets=arm9_reserved,
        forbidden_file_offsets=parse_forbidden_ranges(code_cfg),
        max_file_offset=parse_max_file_offset(code_cfg),
        check_vanilla_xrefs=False,
    )
    reset_slot = allocate_cave(
        bytes(arm9_data),
        _binary_load(profile, "arm9"),
        int(reset_cfg.get("estimated_bytes", LEGACY_RESET_CAVE_MAX)),
        alignment=int(reset_cfg.get("alignment", 4)),
        preferred_file_offset=_parse_fixed(reset_cfg.get("preferred")),
        reserved_file_offsets=arm9_reserved,
        forbidden_file_offsets=parse_forbidden_ranges(reset_cfg),
        max_file_offset=parse_max_file_offset(reset_cfg),
        check_vanilla_xrefs=False,
    )

    stat_cfg = manifest.get("arm9_dungeon_stat_cave") or {}
    stat_slot = None
    if stat_cfg:
        stat_pref = _parse_fixed(stat_cfg.get("preferred"))
        stat_need = int(stat_cfg.get("estimated_bytes", 512))
        if stat_pref is not None:
            region = arm9_data[stat_pref : stat_pref + stat_need]
            reusable = len(region) == stat_need and (
                force_reapply
                or all(b in (0, ALPHA_PADDING_BYTE) for b in region)
            )
            if reusable:
                _zero_cave(arm9_data, stat_pref, stat_need)
        stat_slot = allocate_cave(
            bytes(arm9_data),
            _binary_load(profile, "arm9"),
            int(stat_cfg.get("estimated_bytes", 512)),
            alignment=int(stat_cfg.get("alignment", 4)),
            preferred_file_offset=_parse_fixed(stat_cfg.get("preferred")),
            reserved_file_offsets=arm9_reserved,
            forbidden_file_offsets=parse_forbidden_ranges(stat_cfg),
            max_file_offset=parse_max_file_offset(stat_cfg),
            check_vanilla_xrefs=False,
        )
        cache_lo = ALPHA_ITEM_LIST_CACHE[0] - _binary_load(profile, "arm9")
        cache_hi = ALPHA_ITEM_LIST_CACHE[1] - _binary_load(profile, "arm9")
        if stat_slot.file_offset < cache_hi and stat_slot.file_offset + stat_slot.size > cache_lo:
            raise RuntimeError(
                f"dungeon-stat cave @ file {stat_slot.file_offset:#x} overlaps "
                f"Alpha item-list cache {cache_lo:#x}-{cache_hi:#x}"
            )
        _zero_cave(arm9_data, stat_slot.file_offset, stat_slot.size)

    _zero_cave(arm9_data, code_slot.file_offset, code_slot.size)
    _zero_cave(arm9_data, reset_slot.file_offset, reset_slot.size)

    ov19_load = _binary_load(profile, "ov19")
    team_table_load = ov19_load + table_file_off

    gen_text = _build_generated_inc(
        module_id=module_id,
        arm9_code=code_slot.load_address,
        reset_cave=reset_slot.load_address,
        team_submenu_table=team_table_load,
        dungeon_stat_cave=stat_slot.load_address if stat_slot else None,
    )
    prior_lines: list[str] = []
    blobs = {
        "arm9": arm9_data,
        "ov19": ov19_data,
        "ov29": ov29_data,
        "ov11": ov11_data,
    }
    for hook in hooks_cfg:
        prior_label = hook.get("prior_label")
        if not prior_label:
            continue
        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "arm9")
        load = _binary_load(profile, bname)
        word = struct.unpack_from("<I", blobs[bname], site - load)[0]
        prior = resolve_prior_target(site, word, hook)
        prior_lines.append(f".definelabel {prior_label}, 0x{prior:X}")
    if prior_lines:
        gen_text = gen_text.rstrip("\n") + "\n" + "\n".join(prior_lines) + "\n"

    asm_dir = module_dir / (manifest.get("asm") or {}).get("dir", "asm")
    asm_entry = (manifest.get("asm") or {}).get("entry", "main.asm")

    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")

    with tempfile.TemporaryDirectory(prefix="true_patches_spinda_") as tmp:
        tmp_path = Path(tmp)
        arm9_path = tmp_path / "arm9.bin"
        ov19_path = tmp_path / "overlay_0019.bin"
        ov29_path = tmp_path / "overlay_0029.bin"
        ov11_path = tmp_path / "overlay_0011.bin"
        arm9_path.write_bytes(bytes(arm9_data))
        ov19_path.write_bytes(bytes(ov19_data))
        ov29_path.write_bytes(bytes(ov29_data))
        ov11_path.write_bytes(bytes(ov11_data))

        gen_inc = tmp_path / "generated.inc"
        write_generated_inc_text(gen_inc, gen_text)

        run_armips_bundle(
            armips=armips,
            asm_dir=asm_dir,
            asm_entry=asm_entry,
            binaries={
                "arm9.bin": arm9_path,
                "overlay_0019.bin": ov19_path,
                "overlay_0029.bin": ov29_path,
                "overlay_0011.bin": ov11_path,
            },
            generated_inc=gen_inc,
        )

        arm9_buf = bytearray(arm9_path.read_bytes())
        boot_off = BOOT_DATA_START - ARM9_LOAD
        pre_boot = struct.unpack_from("<I", arm9_buf, boot_off)[0]
        if pre_boot != VANILLA_BOOT_WORD:
            raise RuntimeError(
                f"arm9 code cave overflowed into boot data "
                f"(word @ {BOOT_DATA_START:#x} is {pre_boot:#010x})"
            )
        reset_end = LEGACY_RESET_CAVE_FILE + LEGACY_RESET_CAVE_MAX
        reset_tail = struct.unpack_from("<I", arm9_buf, reset_end)[0]
        if reset_tail != RESET_CAVE_SENTINEL:
            raise RuntimeError(
                f"arm9 reset cave overflowed "
                f"(word @ file {reset_end:#x} is {reset_tail:#010x}, "
                f"expected {RESET_CAVE_SENTINEL:#010x})"
            )
        stat_bytes = b""
        if stat_slot is not None:
            stat_end = stat_slot.file_offset + stat_slot.size
            if any(arm9_buf[stat_end - 16 : stat_end]):
                raise RuntimeError(
                    f"arm9 dungeon-stat cave overflowed past file {stat_end:#x}"
                )
            stat_bytes = bytes(arm9_buf[stat_slot.file_offset : stat_end])

        ov19_out = bytearray(ov19_path.read_bytes())
        ov29_out = ov29_path.read_bytes()
        ov11_out = ov11_path.read_bytes()

        _restore_ov19_inner16_tail(
            ov19_out,
            vanilla_ov19=_load_vanilla_ov19_slice(module_dir),
            team_table_load=team_table_load,
        )
        _restore_ov19_roster_store_hooks(ov19_out, ov19_load=ov19_load)
        _restore_arm9_boot_tail(arm9_buf, module_dir)
        if stat_slot is not None:
            arm9_buf[stat_slot.file_offset : stat_slot.file_offset + len(stat_bytes)] = stat_bytes
        boot_off = BOOT_DATA_START - ARM9_LOAD
        boot_word = struct.unpack_from("<I", arm9_buf, boot_off)[0]
        if boot_word != VANILLA_BOOT_WORD:
            raise RuntimeError(
                f"arm9 boot word @ {BOOT_DATA_START:#x} corrupted "
                f"(got {boot_word:#010x}, expected {VANILLA_BOOT_WORD:#010x}); "
                f"code cave overflow past {BOOT_DATA_START:#x}"
            )

        _set_binary_bytes(rom, config, "arm9", bytes(arm9_buf))
        _set_binary_bytes(rom, config, "ov19", bytes(ov19_out))
        _set_binary_bytes(rom, config, "ov29", ov29_out)
        _set_binary_bytes(rom, config, "ov11", ov11_out)
        table[19].ramSize = len(ov19_out)
        rom.files[table[19].fileID] = ov19_out
        rom.files[table[29].fileID] = ov29_out
        rom.files[table[11].fileID] = ov11_out
        rom.arm9OverlayTable = saveOverlayTable(table)

    patch_strings(rom, module_dir, manifest)
    if module_id == "spinda_ev_speed":
        patch_drink_ingredients(rom)

    hook_records: list[dict[str, Any]] = []
    for hook in hooks_cfg:
        load = _binary_load(profile, hook.get("binary", "arm9"))
        hook_records.extend(collect_hook_records([hook], profile, load))

    caves = [
        CaveAllocation(
            overlay="arm9",
            file_offset=code_slot.file_offset,
            size=code_slot.size,
            load_address=code_slot.load_address,
        ),
        CaveAllocation(
            overlay="arm9",
            file_offset=reset_slot.file_offset,
            size=reset_slot.size,
            load_address=reset_slot.load_address,
        ),
    ]
    if stat_slot is not None:
        caves.append(
            CaveAllocation(
                overlay="arm9",
                file_offset=stat_slot.file_offset,
                size=stat_slot.size,
                load_address=stat_slot.load_address,
            )
        )

    return AppliedModule(
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
        data=[
            {
                "arm9_code_cave": f"0x{code_slot.load_address:X}",
                "arm9_reset_cave": f"0x{reset_slot.load_address:X}",
                "ov19_team_submenu_table": f"0x{team_table_load:X}",
                **(
                    {
                        "set_string_accuracy": "0x02024360",
                        "accuracy_stars": "1 star / 10 Accuracy, leftover half",
                    }
                    if module_id == "spinda_ev_speed"
                    else {}
                ),
            }
        ],
    )


def _bl_target(word: int, pc: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + imm * 4


def verify_spinda_ev_module(
    rom_path: Path,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    state_mod: AppliedModule | None,
) -> None:
    if not state_mod or len(state_mod.caves) < 2:
        raise AssertionError("spinda_ev state missing arm9 cave allocations")

    rom = NintendoDSRom(rom_path.read_bytes())
    arm9 = bytes(rom.arm9)
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov19 = bytes(rom.files[table[19].fileID])

    arm9_caves = [c for c in state_mod.caves if c.overlay == "arm9"]
    code_cave = next((c for c in arm9_caves if c.file_offset == LEGACY_ARM9_CODE_FILE), None)
    reset_cave = next((c for c in arm9_caves if c.file_offset == LEGACY_RESET_CAVE_FILE), None)
    if code_cave is None or reset_cave is None:
        raise AssertionError("spinda_ev state missing code or reset arm9 cave")

    code_off = code_cave.file_offset
    if not any(arm9[code_off : code_off + 0x40]):
        raise AssertionError("spinda_ev arm9 code cave empty")

    boot_off = BOOT_DATA_START - ARM9_LOAD
    boot_word = struct.unpack_from("<I", arm9, boot_off)[0]
    if boot_word != VANILLA_BOOT_WORD:
        raise AssertionError(
            f"arm9 boot word @ {BOOT_DATA_START:#x} is {boot_word:#010x} "
            f"(expected {VANILLA_BOOT_WORD:#010x})"
        )
    reset_end = LEGACY_RESET_CAVE_FILE + LEGACY_RESET_CAVE_MAX
    reset_tail = struct.unpack_from("<I", arm9, reset_end)[0]
    if reset_tail != RESET_CAVE_SENTINEL:
        raise AssertionError(
            f"arm9 reset cave overflowed "
            f"(word @ file {reset_end:#x} is {reset_tail:#010x})"
        )

    reset_off = reset_cave.file_offset
    if not any(arm9[reset_off : reset_off + 0x40]):
        raise AssertionError("spinda_ev reset cave empty")

    stat_cfg = manifest.get("arm9_dungeon_stat_cave") or {}
    scratch_base = LEGACY_SCRATCH_BASE
    if stat_cfg:
        stat_cave = next(
            (
                c
                for c in arm9_caves
                if c.file_offset not in (LEGACY_ARM9_CODE_FILE, LEGACY_RESET_CAVE_FILE)
            ),
            None,
        )
        if stat_cave is None:
            raise AssertionError("spinda_ev dungeon-stat cave missing")
        expected_off = _parse_fixed(stat_cfg.get("preferred"))
        expected_size = int(stat_cfg.get("estimated_bytes", 512))
        if stat_cave.file_offset != expected_off or stat_cave.size != expected_size:
            raise AssertionError(
                f"dungeon-stat cave @ {stat_cave.file_offset:#x} size {stat_cave.size}"
            )
        cache_lo, cache_hi = (a - ARM9_LOAD for a in ALPHA_ITEM_LIST_CACHE)
        if stat_cave.file_offset < cache_hi and stat_cave.file_offset + stat_cave.size > cache_lo:
            raise AssertionError("dungeon-stat cave overlaps Alpha item-list cache")
        if not any(arm9[stat_cave.file_offset : stat_cave.file_offset + 0x40]):
            raise AssertionError("dungeon-stat cave empty")
        tail = stat_cave.file_offset + stat_cave.size
        if any(arm9[tail - 16 : tail]):
            raise AssertionError("dungeon-stat cave overflowed")
        snap = stat_cave.file_offset + DUNGEON_STAT_SNAP_OFFSET
        if any(arm9[snap : snap + 52]):
            raise AssertionError("dungeon stat snapshot must stay 0 in the ROM")
        scratch_off = stat_cave.file_offset + DUNGEON_STAT_SCRATCH_OFFSET
        if any(arm9[scratch_off : scratch_off + 12]):
            raise AssertionError("spinda scratch words must stay 0 in the ROM")
        scratch_base = stat_cave.load_address + DUNGEON_STAT_SCRATCH_OFFSET
        ov29 = bytes(rom.files[table[29].fileID])
        ov29_load = _binary_load(profile, "ov29")
        free_site = resolve_symbol(profile, "DungeonFree")
        free_word = struct.unpack_from("<I", ov29, free_site - ov29_load)[0]
        if (free_word >> 24) not in (0xEA, 0xEB):
            raise AssertionError(f"DungeonFree @ {free_site:#x} is {free_word:#010x}")
        stub = _bl_target(free_word, free_site)
        if not (
            stat_cave.load_address
            <= stub
            < stat_cave.load_address + DUNGEON_STAT_SNAP_OFFSET
        ):
            raise AssertionError(
                f"DungeonFree jumps {stub:#x}, not the dungeon-stat cave"
            )
        if manifest.get("id") == "spinda_ev_speed":
            ov29 = bytes(rom.files[table[29].fileID])
            ov29_load = _binary_load(profile, "ov29")
            rank_site = resolve_symbol(profile, "MoveHitRankApply")
            rank_word = struct.unpack_from("<I", ov29, rank_site - ov29_load)[0]
            rank_tgt = _bl_target(rank_word, rank_site)
            code_lo = code_cave.load_address
            code_hi = code_cave.load_address + code_cave.size
            if not (code_lo <= rank_tgt < code_hi):
                raise AssertionError(
                    f"Z-Move never-miss @ {rank_site:#x} jumps {rank_tgt:#x}, "
                    "not the arm9 code cave"
                )
            code_bytes = arm9[code_cave.file_offset : code_cave.file_offset + code_cave.size]
            if struct.pack("<I", 559) not in code_bytes:
                raise AssertionError("arm9 code cave missing Z-Move shell id 559")
            found_grav = False
            gravity_fn = 0x02338390
            for i in range(0, len(code_bytes) - 3, 4):
                word = struct.unpack_from("<I", code_bytes, i)[0]
                if (word >> 24) == 0xEB and _bl_target(
                    word, code_cave.load_address + i
                ) == gravity_fn:
                    found_grav = True
                    break
            if not found_grav:
                raise AssertionError("arm9 code cave missing GravityIsActive call")
            peel = stat_cave.file_offset + DUNGEON_STAT_PEEL_OFFSET
            if any(arm9[peel : peel + 52]):
                raise AssertionError("dungeon stat peel buffer must stay 0 in the ROM")

    drink_off = SPINDA_DRINK_CAVE_FILE
    if any(arm9[drink_off : drink_off + SPINDA_DRINK_CAVE_SIZE]):
        raise AssertionError("drink cave @ AF490 must stay zero")

    if struct.pack("<I", scratch_base + 8) not in arm9[code_off : code_off + code_cave.size]:
        raise AssertionError("EvDrinkBoostCache pool missing in code cave")

    if manifest.get("id") == "spinda_ev_speed":
        acc_off = 0x02024360 - ARM9_LOAD
        acc_win = arm9[acc_off : acc_off + 0xC8]
        if struct.pack("<I", 0x020A3544) not in acc_win:
            raise AssertionError("SetStringAccuracy missing HalfStarString")
        if struct.pack("<I", 0x27A0) in acc_win:
            raise AssertionError("SetStringAccuracy still has Always Hit id")

    apply_word = struct.unpack_from("<I", arm9, resolve_symbol(profile, "SpindaEvGummiApplyHook") - ARM9_LOAD)[0]
    apply_tgt = _bl_target(apply_word, resolve_symbol(profile, "SpindaEvGummiApplyHook"))
    if apply_tgt != reset_cave.load_address:
        raise AssertionError(
            f"gummi APPLY must target reset cave {reset_cave.load_address:#x}, got {apply_tgt:#x}"
        )

    ov19_load = _binary_load(profile, "ov19")
    table_file_off = int((manifest.get("ov19_extend") or {}).get("table_file_offset", 16960))
    menu_ptr = struct.unpack_from("<I", ov19, resolve_symbol(profile, "SpindaEvTeamSubmenuMenuPtr") - ov19_load)[0]
    expected_table = ov19_load + table_file_off
    if menu_ptr != expected_table:
        raise AssertionError(f"team submenu ptr {menu_ptr:#x} != table {expected_table:#x}")

    strings_cfg = manifest.get("strings") or {}
    entries: list[dict[str, Any]] = []
    for yaml_path in _string_yaml_paths(module_dir, strings_cfg):
        doc = load_yaml(yaml_path)
        entries.extend(doc.get("entries") or [])
    for item in entries:
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

    if manifest.get("id") == "spinda_ev_speed":
        for path in ITEMBAR_PATHS:
            bar = DataSTHandler.deserialize(rom.getFileByName(path))
            shown = [i for i in range(bar.nb_struct_ids()) if bar.get_item_struct_id(i) >= 0]
            expected = [i for i in range(bar.nb_struct_ids()) if _is_drink_ingredient(i)]
            if shown != expected:
                raise AssertionError(f"{path}: drink ingredients {shown} != gummis {expected}")
            if GUMMI_WONDER_ID in shown:
                raise AssertionError(f"{path}: Wonder Gummi (Mysterious Gummi) still listed")

    for hook in manifest.get("hooks") or []:
        if not hook.get("target_symbol"):
            continue
        site = resolve_symbol(profile, hook["symbol"])
        bname = hook.get("binary", "arm9")
        if bname == "arm9":
            blob, load = arm9, ARM9_LOAD
        elif bname in ("ov19", "overlay19"):
            blob, load = ov19, ov19_load
        elif bname in ("ov11", "overlay11", "overlay_0011"):
            ov11 = bytes(rom.files[table[11].fileID])
            blob, load = ov11, _binary_load(profile, "ov11")
        else:
            ov29 = bytes(rom.files[table[29].fileID])
            blob, load = ov29, _binary_load(profile, "ov29")
        off = site - load
        word = struct.unpack_from("<I", blob, off)[0]
        top = word >> 24
        if top not in (0xEA, 0xEB):
            raise AssertionError(f"hook {hook['name']} @ {site:#x} not branch/bl: {word:#010x}")
