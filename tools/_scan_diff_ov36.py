"""Deep scan ov36 for difficulty-related logic (flags 55-59, multipliers)."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

OV36 = Path(r"c:\Working\SkyTemple\unpacked\overlay\overlay_0036.bin").read_bytes()
LOAD = 0x023A7080
OUT = Path(r"c:\Working\SkyTemple\tools\_scan_diff_ov36_out.txt")
PERF = 0x0204CA94


def bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def main() -> None:
    lines: list[str] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    # 1) All bl to GetPerformanceFlagWithChecks with context
    lines.append("=== ov36 bl GetPerformanceFlagWithChecks + 24 instr context ===")
    for off in range(0, len(OV36) - 3, 4):
        w = struct.unpack_from("<I", OV36, off)[0]
        if w >> 24 != 0xEB:
            continue
        if bl_target(LOAD + off, w) != PERF:
            continue
        start = max(0, off - 0x40)
        end = min(len(OV36), off + 0x30)
        lines.append(f"\n--- call @ 0x{LOAD + off:08X} ---")
        for ins in md.disasm(OV36[start:end], LOAD + start):
            mark = " <<" if ins.address == LOAD + off else ""
            lines.append(f"  {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}{mark}")

    # 2) Search for cmp rX, #1/#2/#3 after loading something that could be difficulty enum
    # Look for string-like comments: denser pattern — consecutive cmp with 0,1,2,3
    lines.append("\n=== mov r0,#55-59 anywhere in ov36 (ARM) + next 8 instr ===")
    for imm in (55, 56, 57, 58, 59):
        word = 0xE3A00000 | imm
        pat = struct.pack("<I", word)
        off = 0
        count = 0
        while True:
            i = OV36.find(pat, off)
            if i < 0:
                break
            if i % 4 == 0:
                count += 1
                if count <= 20:
                    lines.append(f"\n--- mov r0,#{imm} @ 0x{LOAD + i:08X} ---")
                    for ins in md.disasm(OV36[i : i + 0x30], LOAD + i):
                        lines.append(f"  {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")
            off = i + 1
        lines.append(f"(total mov r0,#{imm}: {count})")

    # 3) Also try mov Rx, #imm for other registers (r1-r3) with 55-59
    lines.append("\n=== mov r1/r2/r3,#55-59 then nearby bl ===")
    for reg in (1, 2, 3):
        for imm in (55, 56, 57, 58, 59):
            word = 0xE3A00000 | (reg << 12) | imm
            pat = struct.pack("<I", word)
            off = 0
            while True:
                i = OV36.find(pat, off)
                if i < 0:
                    break
                if i % 4 == 0:
                    lines.append(f"  mov r{reg},#{imm} @ 0x{LOAD + i:08X}")
                    for ins in list(md.disasm(OV36[i : i + 0x20], LOAD + i))[:6]:
                        lines.append(f"    {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")
                off = i + 1

    # 4) Search literal pools containing 55-59 near GetPerformance calls
    # Find words 55-59 in pools and see xrefs via ldr
    lines.append("\n=== literal pool values 55-59 and nearby ldr users (sample) ===")
    for imm in (55, 56, 57, 58, 59):
        pat = struct.pack("<I", imm)
        hits = 0
        off = 0
        while hits < 15:
            i = OV36.find(pat, off)
            if i < 0:
                break
            if i % 4 == 0:
                # check if previous words look like code or data
                hits += 1
                lines.append(f"  u32 {imm} @ off 0x{i:X} ram 0x{LOAD + i:08X}")
            off = i + 1

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
