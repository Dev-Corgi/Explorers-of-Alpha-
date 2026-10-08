#!/usr/bin/env python3
"""Measure z_move ov29 cave: core vs ZMoveExecuteEffects.asm."""

from __future__ import annotations

import re
import struct
import subprocess
import tempfile
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom, get_binary_from_rom

ROOT = Path(__file__).resolve().parent.parent
ASM = ROOT / "true_patches" / "z_move" / "asm"
ROM = ROOT / "true_patches" / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
ARMIPS = ROOT / "tools" / "armips.exe"
CAVE_OFF = 0x548E0
CAVE_MAX_END = 0x5648C  # end of vanilla zero block (code @ 5648C)
LOAD = 0x022DC240


def count_instructions(text: str) -> int:
    pat = re.compile(
        r"^\s+(mov|ldr|str|bl|beq|bne|bgt|blt|bge|ble|cmp|push|pop|add|sub|"
        r"and|orr|bic|ldrb|strb|ldrh|strh|stm|ldm|blx|bx|mvn|tst|teq|"
        r"lsr|lsl|asr|ror|adc|sbc|rsb|mla|smull|umull)\b",
        re.M | re.I,
    )
    branches = len(re.findall(r"^\s+b(?:eq|ne|gt|lt|ge|le|hi|ls|cs|cc|mi|pl|vs|vc|hi|ls)?\s", text, re.M | re.I))
    return len(pat.findall(text)) + branches


def split_ov29() -> tuple[str, str, str]:
    ov29 = (ASM / "ZMoveOv29.asm").read_text(encoding="utf-8")
    marker = '.include "ZMoveExecuteEffects.asm"'
    if marker not in ov29:
        raise RuntimeError("include marker not found")
    before, after = ov29.split(marker, 1)
    effects = (ASM / "ZMoveExecuteEffects.asm").read_text(encoding="utf-8")
    return before, effects, after


def assemble_cave(label: str, cave_body: str) -> int:
    return _cave_used_bytes(_assemble_bytes(label, cave_body), CAVE_OFF)


def _assemble_bytes(label: str, cave_body: str) -> bytes:
    if not ARMIPS.is_file():
        raise FileNotFoundError(ARMIPS)

    nds = NintendoDSRom(ROM.read_bytes())
    cfg = get_ppmdu_config_for_rom(nds)
    ov29 = bytearray(get_binary_from_rom(nds, cfg.bin_sections.overlay29))

    gen = (
        f"; measure {label}\n"
        f".definelabel ZMoveOv29CodeAddress, 0x{CAVE_OFF:X}\n"
        f".definelabel PriorExecuteMoveEffectCall, 0x0232E864\n"
        f"ZGaugeRamAddress equ 0x022B6A00\n"
        f".definelabel ZGauge, ZGaugeRamAddress\n"
    )

    wrapper = f"""
.nds
.arm
.include "common/offsetsUS.asm"
.include "common/effectsUS.asm"
.open "overlay_0029.bin", 0x{LOAD:X}
.org 0x{LOAD:X} + ZMoveOv29CodeAddress
{cave_body}
.close
"""

    with tempfile.TemporaryDirectory(prefix="zmove_measure_") as tmp:
        work = Path(tmp)
        (work / "common").mkdir()
        for f in (ASM / "common").glob("*"):
            (work / "common" / f.name).write_bytes(f.read_bytes())
        (work / "generated.inc").write_text(gen, encoding="utf-8")
        (work / "overlay_0029.bin").write_bytes(bytes(ov29))
        (work / "measure.asm").write_text(wrapper, encoding="utf-8")

        result = subprocess.run(
            [str(ARMIPS), "measure.asm"],
            cwd=work,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"armips failed ({label}):\n{result.stdout}\n{result.stderr}"
            )
        return (work / "overlay_0029.bin").read_bytes()


def _cave_used_bytes(ov29: bytes, start: int) -> int:
    """Bytes from start until last nonzero before CAVE_MAX_END."""
    last_nz = start - 1
    limit = min(len(ov29), CAVE_MAX_END)
    for i in range(start, limit):
        if ov29[i] != 0:
            last_nz = i
    if last_nz < start:
        return 0
    return ((last_nz + 1 - start) + 3) // 4 * 4


def diff_cave_sizes(full: bytes, core: bytes, start: int) -> tuple[int, int, int]:
    fu = _cave_used_bytes(full, start)
    cu = _cave_used_bytes(core, start)
    return fu, cu, fu - cu


def main() -> None:
    before, effects, after = split_ov29()
    # after include: trailing .pool / LoadEntityStatus / .close from ov29 tail
    core_body = before.split(".org ZMoveOv29CodeAddress", 1)[1] + after
    full_body = before.split(".org ZMoveOv29CodeAddress", 1)[1] + effects + after

    core_instr = count_instructions(before.split(".org ZMoveOv29CodeAddress", 1)[1])
    fx_instr = count_instructions(effects)
    full_instr = core_instr + fx_instr

    print("=== Static (line/instruction) estimate ===")
    print(f"  core (ZMoveOv29 cave part): ~{core_instr} instr, {len(before.split('.org ZMoveOv29CodeAddress',1)[1])} chars")
    print(f"  effects (ZMoveExecuteEffects): ~{fx_instr} instr, {len(effects)} chars")
    print(f"  ratio effects/total instr: {fx_instr/full_instr*100:.1f}%")

    if ARMIPS.is_file():
        print("\n=== armips assembled size @ 0x548E0 ===")
        full_bin = _assemble_bytes("full", full_body)
        core_bin = _assemble_bytes("core_only", core_body)
        full_size, core_size, saved = diff_cave_sizes(full_bin, core_bin, CAVE_OFF)
        print(f"  full cave:       {full_size} bytes (0x{full_size:X})")
        print(f"  without effects: {core_size} bytes (0x{core_size:X})")
        print(f"  saved:           {saved} bytes (0x{saved:X})")
        print(f"  manifest est 5120 -> core-only est ~{max(5120 - saved, core_size)}")


if __name__ == "__main__":
    main()
