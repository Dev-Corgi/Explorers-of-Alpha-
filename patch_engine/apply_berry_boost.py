from __future__ import annotations

import re
import shutil
import struct
import subprocess
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
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.str.handler import StrHandler
from skytemple_files.graphics.fonts.font_sir0.handler import FontSir0Handler

from .armips_runner import write_generated_inc_text
from .cave_allocator import allocate_cave
from .cave_manifest import parse_max_file_offset
from .overlay_caves import (
    allocate_overlay_cave,
    get_rom_binary,
    normalize_cave_binary,
    overlay_filename,
    write_rom_binary,
)
from .cave_reservations import format_load_address_inc, reserved_file_ranges
from .manifest import load_rom_profile, load_yaml
from .prebuild import run_prebuild
from .state import AppliedModule, BuildState, CaveAllocation

OV29_LOAD = 0x022DC240

ITEM_CD_PATHS: tuple[str, ...] = ("BALANCE/item_cd.bin", "UTILITY/item_cd.bin")

PATTERN_B_STAT_SITES_VANILLA: tuple[tuple[str, int, int], ...] = (
    ("BoostOffensiveStat_entry", 0x023139A4, 0xEA029E20),
    ("BoostDefensiveStat_entry", 0x02313B10, 0xEA029DD3),
    ("FocusStatUp_entry", 0x023140EC, 0xEA029C95),
)

PATTERN_A_HOOKS: tuple[tuple[str, int], ...] = (
    ("ApplyCheriBerryEffect", 0x0231CBEC),
    ("ApplyPechaBerryEffect", 0x0231CC18),
    ("ApplyRawstBerryEffect", 0x0231CC4C),
    ("ApplyChestoBerryEffect", 0x0231CC78),
    ("ApplyItemEffect_ItemCdLoader", 0x0231B9A8),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _effect_lib() -> Path:
    return (
        _repo_root()
        / ".venv"
        / "Lib"
        / "site-packages"
        / "skytemple_files"
        / "_resources"
        / "patches"
        / "asm_patches"
        / "eos_move_effects"
    )


def _parse_addr(value: Any) -> int:
    return int(value, 16) if isinstance(value, str) else int(value)


def _stub_filename(item_id: int) -> str:
    return f"item_{item_id}_stub.asm"


def _overlay29_bytes(rom: NintendoDSRom) -> bytes:
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _id, _name: b"")
    return rom.files[table[29].fileID]


def _run_armips(cwd: Path, entry: str, armips: Path) -> None:
    result = subprocess.run(
        [str(armips), entry],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"armips failed ({entry}):\n"
            + (result.stdout or "")
            + "\n"
            + (result.stderr or "")
        )


def _load_cave_symbol_slots(module_dir: Path, manifest: dict[str, Any]) -> list[tuple[str, int]]:
    item_cd_cfg = manifest.get("item_cd") or {}
    berries_doc = load_yaml(module_dir / item_cd_cfg.get("yaml", "berries.yaml"))
    slots: list[tuple[str, int]] = []
    for effect in berries_doc.get("effects") or []:
        symbol = str(effect["cave_symbol"])
        offset = _parse_addr(effect["cave_offset"])
        slots.append((symbol, offset))
    if not slots:
        raise RuntimeError("berries.yaml has no effects with cave_symbol/cave_offset")
    return slots


def _build_generated_inc(
    module_id: str,
    cave_cfg: dict[str, Any],
    slot: Any,
    symbol_offsets: list[tuple[str, int]],
) -> str:
    return format_load_address_inc(
        module_id=module_id,
        base_label=str(cave_cfg.get("base_label", "BerryBoostCodeAddress")),
        base_load=slot.load_address,
        slots=symbol_offsets,
    )


def patch_overlay29(
    rom: NintendoDSRom,
    *,
    module_dir: Path,
    manifest: dict[str, Any],
    gen_inc_text: str,
    armips: Path,
    cave_binary: str,
) -> None:
    overlay_cfg = manifest.get("overlay") or {}
    asm_dir = module_dir / overlay_cfg.get("asm_dir", "asm/overlay")
    entry = overlay_cfg.get("entry", "BerryBoostCave.asm")

    config = get_ppmdu_config_for_rom(rom)
    effect_lib = _effect_lib()
    if not effect_lib.is_dir():
        raise FileNotFoundError(f"eos_move_effects lib not found: {effect_lib}")

    with tempfile.TemporaryDirectory(prefix="true_patches_berry_ov_") as tmp:
        work = Path(tmp) / "arm"
        shutil.copytree(asm_dir, work)
        shutil.copytree(effect_lib / "lib", work / "lib", dirs_exist_ok=True)
        write_generated_inc_text(work / "common" / "generated.inc", gen_inc_text)
        write_generated_inc_text(work / "generated.inc", gen_inc_text)
        (work / overlay_filename(cave_binary)).write_bytes(
            get_rom_binary(rom, cave_binary)
        )
        (work / "main.asm").write_text(f'.include "{entry}"\n', encoding="utf-8")
        _run_armips(work, "main.asm", armips)
        write_rom_binary(
            rom, config, cave_binary, (work / overlay_filename(cave_binary)).read_bytes()
        )


def _assemble_item_cd_stub(
    *,
    module_dir: Path,
    item_id: int,
    gen_inc_text: str,
    armips: Path,
) -> bytes:
    effect_lib = _effect_lib()
    if not effect_lib.is_dir():
        raise FileNotFoundError(f"eos_move_effects lib not found: {effect_lib}")

    stub_name = _stub_filename(item_id)
    stub_src = module_dir / "asm" / "generated" / stub_name
    if not stub_src.is_file():
        raise FileNotFoundError(
            f"missing generated stub {stub_name}; run prebuild generate_berry_stubs.py"
        )

    with tempfile.TemporaryDirectory(prefix="true_patches_berry_item_cd_") as tmp:
        work = Path(tmp) / "src"
        work.mkdir()
        shutil.copytree(module_dir / "asm" / "src" / "common", work / "common")
        shutil.copy2(stub_src, work / stub_name)
        shutil.copytree(effect_lib / "lib", work / "lib", dirs_exist_ok=True)
        write_generated_inc_text(work / "common" / "generated.inc", gen_inc_text)
        _run_armips(work, stub_name, armips)
        out = work / "code_out.bin"
        if not out.is_file():
            raise RuntimeError(f"armips did not produce code_out.bin for {stub_name}")
        return out.read_bytes()


def _decode_bl_target(word: int, pc: int) -> int:
    imm24 = word & 0xFFFFFF
    if imm24 & 0x800000:
        imm24 -= 0x1000000
    return pc + 8 + (imm24 * 4)


def patch_item_cd(
    rom: NintendoDSRom,
    *,
    module_dir: Path,
    manifest: dict[str, Any],
    gen_inc_text: str,
    armips: Path,
) -> list[int]:
    item_cd_cfg = manifest.get("item_cd") or {}
    berries_doc = load_yaml(module_dir / item_cd_cfg.get("yaml", "berries.yaml"))
    effect_ids: list[int] = []

    stub_cache: dict[int, bytes] = {}
    for effect in berries_doc.get("effects") or []:
        item_id = int(effect["item_id"])
        effect_id = int(effect["effect_id"])
        if item_id not in stub_cache:
            stub_cache[item_id] = _assemble_item_cd_stub(
                module_dir=module_dir,
                item_id=item_id,
                gen_inc_text=gen_inc_text,
                armips=armips,
            )
        effect_ids.append(effect_id)

    for path in ITEM_CD_PATHS:
        cd = DataCDHandler.deserialize(rom.getFileByName(path))
        for effect in berries_doc.get("effects") or []:
            item_id = int(effect["item_id"])
            effect_id = int(effect["effect_id"])
            cd.set_effect_code(effect_id, stub_cache[item_id])
        rom.setFileByName(path, DataCDHandler.serialize(cd))

    return effect_ids


_TAG_RE = re.compile(r"\[[^\]]*\]")


def _text_width_fn(rom: NintendoDSRom):
    font = FontSir0Handler.deserialize(rom.getFileByName("FONT/kanji.dat"))
    widths = {e.char: e.width for e in font.entries if e.table == 0}

    def width(line: str) -> int:
        total = 0
        for ch in _TAG_RE.sub("", line):
            try:
                total += widths.get(ch.encode("cp1252")[0], 10)
            except UnicodeEncodeError:
                total += 10
        return total

    return width


def _check_line_widths(item_id: int, block_name: str, body: str, limit: int, width) -> None:
    for line in body.split("\n"):
        px = width(line)
        if px > limit:
            raise RuntimeError(
                f"berry_boost item {item_id} {block_name}: line is {px}px (max {limit}px): {line!r}"
            )


def patch_strings(rom: NintendoDSRom, module_dir: Path, manifest: dict[str, Any]) -> None:
    strings_cfg = manifest.get("strings") or {}
    doc = load_yaml(module_dir / strings_cfg.get("yaml", "strings.yaml"))
    footer = str(doc.get("detail_footer", "")).lstrip("\n")
    footer_newlines = int(doc.get("detail_footer_newlines", 5))
    max_long = int(doc.get("max_long_line_px", 184))
    max_short = int(doc.get("max_short_line_px", 142))
    max_links = int(doc.get("max_links_per_page", 4))
    width = _text_width_fn(rom)
    config = get_ppmdu_config_for_rom(rom)

    for item in doc.get("items") or []:
        item_id = int(item["id"])
        blocks = dict(item.get("blocks") or {})
        if "Item Short Descriptions" in blocks:
            _check_line_widths(
                item_id, "Item Short Descriptions", str(blocks["Item Short Descriptions"]), max_short, width
            )
        if footer and "Item Long Descriptions" in blocks:
            body = str(blocks["Item Long Descriptions"]).rstrip()
            _check_line_widths(item_id, "Item Long Descriptions", body, max_long, width)
            links = len(re.findall(r"\[LS:", body))
            if links > max_links:
                raise RuntimeError(
                    f"berry_boost item {item_id}: long description has {links} [LS:] links (max {max_links})"
                )
            if body.count("\n") >= footer_newlines:
                raise RuntimeError(
                    f"berry_boost item {item_id}: long description has more than {footer_newlines} lines"
                )
            pad = max(1, footer_newlines - body.count("\n"))
            blocks["Item Long Descriptions"] = body + "\n" * pad + footer
        for filename in get_files_from_rom_with_extension(rom, "str"):
            if not filename.endswith("text_e.str"):
                continue
            strings = StrHandler.deserialize(
                rom.getFileByName(filename), string_encoding=config.string_encoding
            )
            for block_name, body in blocks.items():
                block = config.string_index_data.string_blocks[block_name]
                strings.strings[block.begin + item_id] = body
            rom.setFileByName(filename, StrHandler.serialize(strings))


def build_record(
    module_id: str,
    manifest: dict[str, Any],
    slot: Any,
    *,
    symbol_offsets: list[tuple[str, int]],
    effect_ids: list[int],
) -> AppliedModule:
    label = str((manifest.get("cave") or {}).get("base_label", "BerryBoostCodeAddress"))
    data: dict[str, Any] = {
        "pattern": "b",
        "layout": "item_cd_stubs+ov29_cave",
        "cave_base": f"0x{slot.load_address:X}",
        label: f"0x{slot.load_address:X}",
        "effect_ids": effect_ids,
    }
    for name, offset in symbol_offsets:
        data[name] = f"0x{slot.load_address + offset:X}"

    return AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=[
            CaveAllocation(
                overlay=normalize_cave_binary(manifest.get("cave") or {}),
                file_offset=slot.file_offset,
                size=slot.size,
                load_address=slot.load_address,
            )
        ],
        hooks=[],
        data=[data],
    )


def _parse_fixed(value: Any) -> int | None:
    if value is None:
        return None
    return int(value, 16) if isinstance(value, str) else int(value)


def apply_berry_boost_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    rom: NintendoDSRom,
    armips: Path,
    state: BuildState | None = None,
    rom_in: Path | None = None,
) -> AppliedModule:
    prebuild = manifest.get("prebuild") or []
    if prebuild:
        if rom_in is None:
            raise RuntimeError("berry_boost prebuild requires rom_in path")
        run_prebuild(module_dir, rom_in, prebuild)

    cave_cfg = manifest.get("cave") or {}
    cave_binary = normalize_cave_binary(cave_cfg)
    cave_blob = get_rom_binary(rom, cave_binary)
    slot, cave_blob = allocate_overlay_cave(
        binary=cave_binary,
        overlay_data=cave_blob,
        profile=load_rom_profile(
            Path(__file__).resolve().parent,
            manifest.get("rom_profile", "us_vanilla"),
        ),
        state=state,
        cave_cfg=cave_cfg,
        module_id=module_id,
    )

    config = get_ppmdu_config_for_rom(rom)
    write_rom_binary(rom, config, cave_binary, bytes(cave_blob))

    symbol_offsets = _load_cave_symbol_slots(module_dir, manifest)
    overlay_gen_inc = _build_generated_inc(module_id, cave_cfg, slot, [])
    item_cd_gen_inc = _build_generated_inc(module_id, cave_cfg, slot, symbol_offsets)
    patch_overlay29(
        rom,
        module_dir=module_dir,
        manifest=manifest,
        gen_inc_text=overlay_gen_inc,
        armips=armips,
        cave_binary=cave_binary,
    )
    effect_ids = patch_item_cd(
        rom,
        module_dir=module_dir,
        manifest=manifest,
        gen_inc_text=item_cd_gen_inc,
        armips=armips,
    )
    patch_strings(rom, module_dir, manifest)
    return build_record(
        module_id,
        manifest,
        slot,
        symbol_offsets=symbol_offsets,
        effect_ids=effect_ids,
    )


def verify_berry_boost_module(
    rom_path: Path,
    module_dir: Path,
    manifest: dict[str, Any],
    state_mod: AppliedModule | None,
) -> None:
    if not state_mod or not state_mod.caves:
        raise AssertionError("berry_boost state missing cave allocation")

    rom = NintendoDSRom(rom_path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _id, _name: b"")
    ov29 = bytes(rom.files[table[29].fileID])
    cave = state_mod.caves[0]
    state_data = state_mod.data[0] if state_mod.data else {}

    if state_data.get("pattern") != "b":
        raise AssertionError(
            f"berry_boost state pattern is {state_data.get('pattern')!r}, expected 'b'"
        )

    chunk = ov29[cave.file_offset : cave.file_offset + 64]
    if not any(chunk):
        raise AssertionError(f"berry_boost cave @ file {cave.file_offset:#x} is empty")

    for name, site, expected in PATTERN_B_STAT_SITES_VANILLA:
        off = site - OV29_LOAD
        word = struct.unpack_from("<I", ov29, off)[0]
        if word != expected:
            raise AssertionError(
                f"berry stat API site {name} @ {site:#x} patched unexpectedly: "
                f"{word:#010x}, expected vanilla {expected:#010x}"
            )

    cave_load = cave.load_address
    cave_end = cave_load + cave.size
    for name, site in PATTERN_A_HOOKS:
        off = site - OV29_LOAD
        word = struct.unpack_from("<I", ov29, off)[0]
        if (word >> 24) == 0xEA:
            target = _branch_target(word, site)
            if cave_load <= target < cave_end:
                raise AssertionError(
                    f"berry pattern A hook still present on {name} @ {site:#x} -> {target:#x}"
                )

    if state_data:
        expected_base = state_data.get("BerryBoostCodeAddress") or state_data.get("cave_base")
        if expected_base and _parse_addr(expected_base) != cave_load:
            raise AssertionError(
                f"BerryBoostCodeAddress mismatch: state {expected_base}, cave {cave_load:#x}"
            )

    symbol_offsets = _load_cave_symbol_slots(module_dir, manifest)
    for sym_name, offset in symbol_offsets:
        expected_addr = cave_load + offset
        state_addr = state_data.get(sym_name)
        if state_addr and _parse_addr(state_addr) != expected_addr:
            raise AssertionError(
                f"{sym_name} state {state_addr} != yaml offset {expected_addr:#x}"
            )

    berries_doc = load_yaml(
        module_dir / (manifest.get("item_cd") or {}).get("yaml", "berries.yaml")
    )
    effect_ids = [int(x) for x in (state_data.get("effect_ids") or [])]
    if not effect_ids:
        effect_ids = [int(x["effect_id"]) for x in berries_doc.get("effects") or []]

    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/item_cd.bin"))
    for effect_id in effect_ids:
        code = cd.get_effect_code(effect_id)
        if len(code) < 12:
            raise AssertionError(f"item_cd effect {effect_id} too short ({len(code)} bytes)")
        bl_pc = 0x0231BE50 + 8
        bl_word = struct.unpack_from("<I", code, 8)[0]
        if (bl_word >> 24) != 0xEB:
            raise AssertionError(
                f"item_cd effect {effect_id} missing bl stub @ offset 8: {bl_word:#010x}"
            )
        target = _decode_bl_target(bl_word, bl_pc)
        if not (cave_load <= target < cave_end):
            raise AssertionError(
                f"item_cd effect {effect_id} bl target {target:#x} outside cave [{cave_load:#x}, {cave_end:#x})"
            )


def _branch_target(word: int, pc: int) -> int:
    imm24 = word & 0xFFFFFF
    if imm24 & 0x800000:
        imm24 |= 0xFF000000
    return pc + 8 + (imm24 << 2)
