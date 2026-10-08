"""Execute Korean ARM hooks and audit translations without building a ROM."""
from __future__ import annotations

import json
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))

import yaml
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn import UcError
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_CPSR,
)

from patch_engine.armips_runner import run_armips_bundle
from patch_engine.apply_korean import check_arm9_patched, load_source, plan_translation, _write_strings
from patch_engine.korean_codec import (
    DenseEncoder, dense_code, translation_issues, parse_str_file, parse_ssb_strings,
)

MODULE = ROOT / "true_patches/korean"
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR]
SOURCE, DEST, ARGS = 0x02200000, 0x02201000, 0x02202000
SP, RETURN = 0x027E1000, 0x021FF000


class Machine:
    def __init__(self, arm9: bytes, overlay: bytes, load: int):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(0x02000000, 0x400000)
        self.uc.mem_map(0x027E0000, 0x4000)
        self.uc.mem_write(0x02000000, arm9)
        self.uc.mem_write(load, overlay)
        self.stops = set()
        self.stopped = False
        self.limit = None
        self.overreads = []
        self.uc.hook_add(UC_HOOK_CODE, self.code)
        self.uc.hook_add(UC_HOOK_MEM_READ, self.read)

    def code(self, uc, address, size, _):
        if address in self.stops:
            self.stopped = True
            uc.emu_stop()

    def read(self, uc, access, address, size, value, _):
        if self.limit is not None and SOURCE <= address < SOURCE + 0x400:
            if address + size > self.limit:
                self.overreads.append((address, size))

    def run(self, entry: int, stops: set[int], values: dict[int, int]):
        for i, reg in enumerate(REGS):
            self.uc.reg_write(reg, 0x11220000 + i * 0x101)
        self.uc.reg_write(UC_ARM_REG_CPSR, 0x1F)
        self.uc.reg_write(UC_ARM_REG_SP, SP)
        self.uc.reg_write(UC_ARM_REG_LR, RETURN)
        self.uc.mem_write(SP, b"\0" * 0x800)
        for reg, value in values.items():
            self.uc.reg_write(reg, value)
        self.stops, self.stopped = stops, False
        self.uc.emu_start(entry, 0, count=30000)
        assert self.stopped, f"hook did not return: {entry:#x}"

    def preprocess(self, text: bytes, stale: bytes = b"[digits_c:0]\0"):
        self.uc.mem_write(SOURCE, text + b"\0" + stale + b"\0" * 128)
        self.limit = SOURCE + len(text) + 1
        self.overreads = []
        self.run(0x020223F0, {RETURN}, {
            UC_ARM_REG_R0: DEST, UC_ARM_REG_R1: 256,
            UC_ARM_REG_R2: SOURCE, UC_ARM_REG_R3: 0x440,
        })
        self.limit = None
        n = self.uc.reg_read(UC_ARM_REG_R0)
        assert n == len(text), (text, n)
        assert bytes(self.uc.mem_read(DEST, n)) == text
        assert not self.overreads, (text, self.overreads)


def main():
    rom_path = ROOT / "PatchTesting/Export Rom/Explorers of Alpha+_kor.nds"
    rom = NintendoDSRom.fromFile(rom_path)
    overlays = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    ov = overlays[36]
    # Recover the test fixture's existing allocation, never pin a patch address.
    signature = bytes.fromhex("ff1000e2801051e2")
    offset = bytes(ov.data).index(signature)
    assert bytes(ov.data).count(signature) == 1
    cave = ov.ramAddress + offset
    cfg = yaml.safe_load((MODULE / "manifest.yaml").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="korean_safety_test_") as tmp:
        work = Path(tmp)
        arm9, ov36 = work / "arm9.bin", work / "overlay_0036.bin"
        arm9.write_bytes(rom.arm9)
        ov36.write_bytes(ov.data)
        generated = work / "generated.inc"
        generated.write_text(
            f".definelabel KoreanCaveAddress, 0x{cave:X}\n"
            f"KoreanCaveSize equ {cfg['cave']['code_bytes']}\n"
            ".definelabel KoGlyphTable, 0x023E0000\n"
            f"KoGlyphCount equ {len(rom.getFileByName('FONT/ko_glyph.bin')) // 28}\n",
            encoding="utf-8",
        )
        run_armips_bundle(armips=ROOT / "tools/armips.exe", asm_dir=MODULE / "asm",
                          asm_entry="main.asm", binaries={"arm9.bin": arm9,
                          "overlay_0036.bin": ov36}, generated_inc=generated)
        check_arm9_patched(arm9.read_bytes(), cfg['arm9_sites'], cave,
                          cave + cfg['cave']['code_bytes'])
        candidate = Machine(arm9.read_bytes(), ov36.read_bytes(), ov.ramAddress)

    crystal = bytes.fromhex("918f208ddd8fcc208987")
    # Actual crash residue: a shorter dungeon name replaced a weather message.
    residue = bytes.fromhex("8fa0298a97208ea590b492bf208af98ca58ed10a48508be420")
    old = Machine(bytes(rom.arm9), bytes(ov.data), ov.ramAddress)
    try:
        old.preprocess(crystal, residue + b"[digits_c:0]\0")
    except (UcError, AssertionError):
        pass
    else:
        raise AssertionError("existing ROM did not reproduce the crash fixture")
    candidate.preprocess(crystal, residue + b"[digits_c:0]\0")
    for idx in range(23 * 127):
        code = dense_code(idx)
        candidate.preprocess(bytes([code >> 8, code & 255]))
    for text in [b"ASCII", b"\x81\x40", b"\x88", b"\x88[CS:E]X[CR]",
                 b"\x87", b"\x9e", b"\x9f", b"\x88\xff"]:
        # Markup is interpreted by PreprocessString; test a plain malformed tail.
        if b"[" not in text:
            candidate.preprocess(text)

    for text, length in [(b"\x88\x80\0", 2), (b"\x88\0STALE", 1),
                         (b"\x88[CS:E]", 1), (b"A\0", 1),
                         (b"\x9f\0", 1), (b"\x88\xff\0", 1)]:
        candidate.uc.mem_write(SOURCE, text)
        candidate.run(0x020161E0, {0x020161E4}, {UC_ARM_REG_R4: SOURCE})
        assert candidate.uc.reg_read(UC_ARM_REG_R4) == SOURCE + length
        candidate.run(0x020158E0, {0x020158E4, 0x02015A2C},
                      {UC_ARM_REG_R6: SOURCE})
        assert candidate.uc.reg_read(UC_ARM_REG_R6) == SOURCE + length

    for code, expected in [(0x41, b"A"), (0x8880, b"\x88\x80"),
                            (0x89FE, b"\x89\xfe"), (0x9EFE, b"\x9e\xfe")]:
        candidate.uc.mem_write(ARGS, struct.pack("<I", code))
        candidate.run(0x020892BC, {0x020892C8}, {UC_ARM_REG_R0: ARGS + 4})
        n = candidate.uc.reg_read(UC_ARM_REG_R6)
        assert bytes(candidate.uc.mem_read(SP + 0x2C, n)) == expected

    for text, pair in [(b"\x81\x40", True), (b"\x88\x80", True),
                       (b"\x88\0", False), (b"\x88[", False),
                       (b"\x9f\x80", False), (b"A\0", False)]:
        candidate.uc.mem_write(SOURCE, text)
        candidate.run(0x020206C8, {0x020206E0, 0x020206F0},
                      {UC_ARM_REG_R0: text[0], UC_ARM_REG_R6: SOURCE})
        # A stopped hook's destination distinguishes join from single-byte.
        from unicorn.arm_const import UC_ARM_REG_PC
        assert candidate.uc.reg_read(UC_ARM_REG_PC) == (0x020206E0 if pair else 0x020206F0)

    assert not translation_issues("[item:1]", "[item:1] 효과 [item:1]")
    assert not translation_issues("[kind:]", "[kind:0]")
    assert translation_issues("[item:1]", "[item:0]")
    assert translation_issues("[string:0]", "[string0]")
    assert translation_issues("plain", "[digits_c:0]")
    assert translation_issues("[hero]", "o]")
    assert translation_issues("Yes", "", allow_empty=False)
    english = NintendoDSRom.fromFile(ROOT / "PatchTesting/Export Rom/Explorers of Alpha+.nds")
    source = load_source(MODULE, cfg)
    plan = plan_translation(english, source)
    assert not plan.rejected, plan.rejected
    plan.rejected.append({"where": "test", "index": 0, "issues": ["invalid slot"]})
    try:
        _write_strings(None, plan, DenseEncoder(source.ziti))
    except RuntimeError:
        pass
    else:
        raise AssertionError("unsafe translations were allowed to apply")
    plan.rejected.clear()
    # Exercise full string serialization in memory; no ROM is saved or built.
    encoder = DenseEncoder(source.ziti)
    _write_strings(english, plan, encoder)
    assert parse_str_file(english.getFileByName('MESSAGE/text_e.str')) == [
        encoder.encode(s) for s in plan.final_text_e()
    ]
    script_count = 0
    for path in plan.scripts:
        wanted = [encoder.encode(s) for s in plan.final_script(path)]
        assert parse_ssb_strings(english.getFileByName(path)).strings == wanted
        assert all(b'\0' not in s for s in wanted)
        script_count += len(wanted)
    print(json.dumps({"dense_copy_cases": 23 * 127, "crash_residue": "passed",
                      "draw_width_boundaries": "passed", "percent_c": "passed",
                      "translation_guard": "passed", "unsafe_translations": len(plan.rejected),
                      "text_strings_roundtripped": len(plan.text_e),
                      "script_strings_roundtripped": script_count,
                      "ROM_written": False}, indent=2))


if __name__ == "__main__":
    main()
