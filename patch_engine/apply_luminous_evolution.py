"""Link the shop-local Spring runtime and apply the module's script/text edits."""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from ndspy.code import loadOverlayTable, saveOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.md.handler import MdHandler
from range_typed_integers import u16

from .armips_runner import run_armips_bundle
from .cave_allocator import allocate_cave
from .cave_reservations import FileRange, reserved_file_ranges
from .korean_codec import parse_str_file, build_str_file, decode_english
from .state import AppliedModule, CaveAllocation, HookRecord
from true_patches.luminous_evolution.policy import relationship_tables
from true_patches.luminous_evolution.scripts import apply_scripts

LOAD = 0x0238A140
CAVE_SIZE = 0x4000
RUNTIME_LIMIT = 0x3800


def _word(data, address, base):
    return struct.unpack_from("<I", data, address - base)[0]


def _branch(site, target, link=False):
    delta = target - site - 8
    if delta % 4 or not -0x2000000 <= delta < 0x2000000:
        raise RuntimeError("ARM branch out of range")
    return (0xEB000000 if link else 0xEA000000) | ((delta >> 2) & 0xFFFFFF)


def _array(name, values, ctype="unsigned short"):
    return f"static const {ctype} {name}[]={{" + ",".join(map(str, values)) + "};\n"


def build_runtime(module_dir, work, cave, ov16, rom, texts):
    compiler = shutil.which("arm-none-eabi-gcc")
    if not compiler:
        raise RuntimeError("luminous_evolution needs arm-none-eabi-gcc")
    prefix = str(Path(compiler).with_name("arm-none-eabi-"))
    suffix = ".exe" if compiler.endswith(".exe") else ""
    relationships = json.loads((module_dir / "data/forms.json").read_text())
    groups = relationships["groups"]
    md = MdHandler.deserialize(rom.getFileByName("BALANCE/monster.md"))
    previous, group_map, targets, secondary = relationship_tables(
        md.entries, groups, relationships["regression_overrides"])
    labels = [0] * 600
    for item in texts["text_e"]:
        if "species" in item:
            labels[item["species"]] = item["index"] + 1
    constants = {
        "SPRING_STATE_PTR": _word(ov16, 0x0238B0CC, LOAD),
        "SUBMENU_WINDOW": _word(ov16, 0x0238B0D8, LOAD),
        "SUBMENU_FLAGS": _word(ov16, 0x0238B0DC, LOAD),
        "TEAM_COUNT": _word(ov16, 0x0238CC60, LOAD),
        "MD_COUNT": len(md.entries), "ORIGINAL_TARGET_LABEL": cave + RUNTIME_LIMIT + 0x100,
        "STR_REGRESSION": 19701, "STR_FORM": 19702,
        "STR_REG_CONFIRM": 19703, "STR_FORM_CONFIRM": 19704,
        "STR_REG_SUCCESS": 19705, "STR_FORM_SUCCESS": 19706,
        "STR_FORM_SELECT": 19707,
    }
    header = "".join(f"#define {k} 0x{v:X}\n" for k, v in constants.items())
    header += _array("previous_species", previous)
    header += _array("form_groups", group_map, "unsigned char")
    header += _array("form_secondary", secondary, "unsigned char")
    header += _array("form_labels", labels)
    header += "static const unsigned short form_targets[][4]={" + ",".join(
        "{" + ",".join(map(str, row)) + "}" for row in targets) + "};\n"
    (work / "generated.h").write_text(header, encoding="ascii")
    linker = work / "spring.ld"
    linker.write_text(f"SECTIONS {{ . = 0x{cave:X}; .text : {{ *(.text*) *(.rodata*) }} "
                      ".data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } SpringRuntimeEnd = .; "
                      "/DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } }", encoding="ascii")
    elf = work / "spring.elf"
    args = [compiler, "-mcpu=arm946e-s", "-marm", "-Os", "-ffreestanding", "-fno-builtin",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables", "-nostdlib", "-Wall",
            "-Wextra", "-Werror", "-I", str(work), str(module_dir / "runtime/spring.c"),
            "-Wl,-T," + str(linker), "-o", str(elf)]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    binary = work / "spring.bin"
    subprocess.run([prefix + "objcopy" + suffix, "-O", "binary", str(elf), str(binary)], check=True)
    symbols = {}
    for line in subprocess.check_output([prefix + "nm" + suffix, "--defined-only", str(elf)], text=True).splitlines():
        address, kind, name = line.split()
        if name.startswith("Spring_") and kind == "T":
            symbols[name] = int(address, 16)
        if name == "SpringRuntimeEnd" and int(address, 16) > cave + RUNTIME_LIMIT:
            raise RuntimeError("Spring runtime BSS exceeds cave")
    if binary.stat().st_size > RUNTIME_LIMIT:
        raise RuntimeError("Spring runtime exceeds cave")
    return binary, symbols


def apply_luminous_evolution_module(module_id, module_dir, manifest, rom, armips, state, **_):
    config = get_ppmdu_config_for_rom(rom)
    tables = loadOverlayTable(rom.arm9OverlayTable, lambda i, f: rom.files[f])
    ov = tables[16]
    if ov.bssSize:
        raise RuntimeError("ov16 BSS changed; cannot safely extend")
    source = bytes(ov.data)
    # Search the appended aligned zero region at application time. It is local
    # to ov16 and cannot collide with any ov36 reservation or other shop overlay.
    extended = source + bytes(CAVE_SIZE + 16)
    slot = allocate_cave(extended, LOAD, CAVE_SIZE, alignment=16,
                         preferred_file_offset=(len(source)+15)&~15,
                         forbidden_file_offsets=[FileRange(0, len(source))],
                         reserved_file_offsets=reserved_file_ranges(state, "ov16"))
    if slot.file_offset + CAVE_SIZE > 0x023A7080 - LOAD:
        raise RuntimeError("extended ov16 would overlap ov36")
    extended = extended[:slot.file_offset + CAVE_SIZE]
    texts = json.loads((module_dir / "data/texts.json").read_text(encoding="utf-8"))
    # Alpha also stores the Stone requirements directly on Luxio/Luxray's MD
    # entries. Disconnecting the runtime hook alone would leave Shinx blocked.
    md = MdHandler.deserialize(rom.getFileByName("BALANCE/monster.md"))
    requirements = json.loads((module_dir / "data/stone_requirements.json").read_text())["entries"]
    for entry in requirements:
        monster = md.entries[entry["species"]]
        if (monster.pre_evo_index != entry["previous"] or monster.evo_method != 3 or
                monster.evo_param1 != entry["stone"] or monster.evo_param2 != 0):
            raise RuntimeError("Alpha Shinx Stone requirements changed")
        monster.evo_method = u16(1)
        monster.evo_param1 = u16(entry["level"])
    if any(e.evo_method == 3 and e.evo_param1 in (427, 428) for e in md.entries):
        raise RuntimeError("unhandled Ascend Stone evolution requirement")
    rom.setFileByName("BALANCE/monster.md", MdHandler.serialize(md))
    arm9 = bytes(rom.arm9)
    # Guard every changed instruction against the canonical Alpha input. Prior
    # modules must not replace these sites without an explicit integration.
    reference = NintendoDSRom.fromFile(str(module_dir.parent.parent / "PatchTesting/Explorers of Alpha/Explorers of Alpha.nds"))
    base_tables = loadOverlayTable(reference.arm9OverlayTable, lambda i, f: reference.files[f])
    base16 = bytes(base_tables[16].data)
    arm_sites = [0x02052AC4, 0x02059B0C, 0x0205A230, 0x0205A234,
                 0x02039F30, 0x02039F74, 0x02039FF0]
    ov_sites = [0x0238C148, 0x0238A318, 0x0238B318, 0x0238C57C, 0x0238CBD0,
                0x0238C484, 0x0238ABB4, 0x0238BBB4, 0x0238AC04, 0x0238BC04, 0x0238CB30,
                0x0238AB14, 0x0238BB14]
    for blob, old, sites, load in [(arm9, reference.arm9, arm_sites, 0x02000000),
                                    (source, base16, ov_sites, LOAD)]:
        for site in sites:
            if _word(blob, site, load) != _word(old, site, load):
                raise RuntimeError(f"Spring hook already changed: {site:#x}")
    if arm9[0x5A340:0x5A430] != reference.arm9[0x5A340:0x5A430]:
        raise RuntimeError("resident species writer changed")
    with tempfile.TemporaryDirectory(prefix="spring_link_") as temporary:
        work = Path(temporary)
        binary, symbols = build_runtime(module_dir, work, slot.load_address, source, rom, texts)
        asm = work / "asm"
        shutil.copytree(module_dir / "asm", asm)
        shutil.copy2(binary, asm / "spring.bin")
        stubs = slot.load_address + RUNTIME_LIMIT
        generated = work / "generated.inc"
        generated.write_text("".join(f".definelabel {k}, 0x{v:X}\n" for k, v in {
            **symbols, "SpringCave": slot.load_address, "SpringStubs": stubs,
            "OriginalTargetLabel": stubs + 0x100}.items()), encoding="ascii")
        arm_path, ov_path = work / "arm9.bin", work / "overlay_0016.bin"
        arm_path.write_bytes(arm9)
        ov_path.write_bytes(extended)
        run_armips_bundle(armips=armips, asm_dir=asm, asm_entry="main.asm",
                          binaries={"arm9.bin": arm_path, "overlay_0016.bin": ov_path},
                          generated_inc=generated)
        patched = bytearray(ov_path.read_bytes())
        assembled_arm9 = arm_path.read_bytes()
        if _word(assembled_arm9, 0x02052AC4, 0x02000000) != 0xE2812008:
            raise RuntimeError("assembler did not disconnect the Stone hook")
        if patched[slot.file_offset:slot.file_offset+binary.stat().st_size] != binary.read_bytes():
            raise RuntimeError("assembler did not install the Spring runtime")
        # Shop messages use the same ID convention as GetStringFromId (+1).
        message_sites = []
        for offset in range(0, 0x2BC8, 4):
            site = LOAD + offset
            if _word(source, site, LOAD) == _branch(site, 0x0202F1B4, True):
                struct.pack_into("<I", patched, offset, _branch(site, symbols["Spring_Message"], True))
                message_sites.append(site)
        if len(message_sites) < 20:
            raise RuntimeError("Spring message call inventory changed")
        # Width/height are byte fields +6/+7; zero allows native auto-sizing.
        window_offset = _word(source, 0x0238B0D8, LOAD) - LOAD
        patched[window_offset+6:window_offset+8] = b"\0\0"
        rom.arm9 = bytearray(assembled_arm9)
        ov.data = patched
        ov.ramSize = len(patched)
        ov.compressed = False
        rom.files[ov.fileID] = ov.save(compress=False)
        rom.arm9OverlayTable = saveOverlayTable(tables)
    encoded = parse_str_file(rom.getFileByName("MESSAGE/text_e.str"))
    for item in texts["text_e"]:
        index = item["index"]
        while len(encoded) <= index:
            encoded.append(b"")
        if "before" in item:
            if decode_english(encoded[index]) != item["before"]:
                raise RuntimeError(f"Spring text changed at {index}")
        elif encoded[index].strip():
            raise RuntimeError(f"Spring string index already occupied: {index}")
        encoded[index] = item["en"].encode("ascii")
    rom.setFileByName("MESSAGE/text_e.str", build_str_file(encoded))
    script_changes = apply_scripts(rom, config, texts)
    digest = hashlib.sha256(patched[slot.file_offset:]).hexdigest()
    arm_expected = {str(site): _word(rom.arm9, site, 0x02000000) for site in arm_sites}
    ov_expected = {str(site): _word(patched, site, LOAD) for site in ov_sites+message_sites}
    hooks = [HookRecord(f"Spring_{site:X}", site, "patch", "luminous_evolution", "first")
             for site in arm_sites + ov_sites + message_sites]
    return AppliedModule(module_id, manifest.get("version", 1),
                         [CaveAllocation("ov16", slot.file_offset, CAVE_SIZE, slot.load_address)], hooks,
                         [{"symbols": symbols, "cave_sha256": digest, "scripts": script_changes,
                           "arm9_words": arm_expected, "ov16_words": ov_expected,
                           "writer_sha256": hashlib.sha256(rom.arm9[0x5A340:0x5A430]).hexdigest(),
                           "text_indices": [i["index"] for i in texts["text_e"]]}])


def verify_luminous_evolution_module(rom_path, module_dir, manifest, record):
    if record is None or not record.caves:
        raise RuntimeError("Spring module has no linker record")
    rom = rom_path if isinstance(rom_path, NintendoDSRom) else NintendoDSRom.fromFile(str(rom_path))
    tables = loadOverlayTable(rom.arm9OverlayTable, lambda i, f: rom.files[f])
    data = tables[16].data
    cave = record.caves[0]
    if hashlib.sha256(data[cave.file_offset:cave.file_offset+cave.size]).hexdigest() != record.data[0]["cave_sha256"]:
        raise RuntimeError("Spring cave verification failed")
    if _word(rom.arm9, 0x02052AC4, 0x02000000) != 0xE2812008:
        raise RuntimeError("Ascend Stone hook still active")
    for blob, base, name in [(rom.arm9, 0x02000000, "arm9_words"), (data, LOAD, "ov16_words")]:
        for address, expected in record.data[0][name].items():
            if _word(blob, int(address), base) != expected:
                raise RuntimeError(f"Spring instruction changed at {int(address):#x}")
    if hashlib.sha256(rom.arm9[0x5A340:0x5A430]).hexdigest() != record.data[0]["writer_sha256"]:
        raise RuntimeError("Spring record writer changed")
    md = MdHandler.deserialize(rom.getFileByName("BALANCE/monster.md"))
    if any(e.evo_method == 3 and e.evo_param1 in (427, 428) for e in md.entries):
        raise RuntimeError("an Ascend Stone MD requirement remains")
