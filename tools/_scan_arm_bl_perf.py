"""Scan arm9 ARM-mode bl callers to GetPerformanceFlagWithChecks; find flag 55 reads."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
OUT = Path(r"C:\Working\SkyTemple\tools\_arm_bl_perf.txt")
LOAD = 0x02000000


def parse(name: str) -> tuple[int, int]:
    t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    m = re.search(rf"{name}\s*=\s*Symbol\((.*?)\)\n\n", t, re.S)
    nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(1))]
    return nums[0], nums[1]


def arm_bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def disasm_arm(data: bytes, off: int, size: int = 0x100) -> list[str]:
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    return [
        f"0x{ins.address-LOAD:06X}: {ins.mnemonic:7} {ins.op_str}"
        for ins in md.disasm(data[off : off + size], LOAD + off)
    ]


def has_mov_r0_55_before(data: bytes, bl_off: int, back: int = 0x20) -> bool:
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    start = max(0, bl_off - back)
    for ins in md.disasm(data[start : bl_off + 4], LOAD + start):
        if ins.mnemonic == "mov" and "#0x37" in ins.op_str and "r0" in ins.op_str:
            return True
    return False


def main() -> None:
    perf_off, perf_ram = parse("GetPerformanceFlagWithChecks")
    lines = [f"GetPerformanceFlagWithChecks off=0x{perf_off:X} ram=0x{perf_ram:X}"]
    lines.append("\n=== Function body ===")
    lines.extend(disasm_arm(ARM9, perf_off, 0x120))

    callers = []
    for off in range(0, len(ARM9) - 3, 4):
        w = struct.unpack_from("<I", ARM9, off)[0]
        if (w >> 24) != 0xEB:
            continue
        tgt = arm_bl_target(LOAD + off, w)
        if tgt == perf_ram:
            callers.append(off)

    lines.append(f"\n=== ARM bl callers: {len(callers)} ===")
    flag55 = [c for c in callers if has_mov_r0_55_before(ARM9, c)]
    lines.append(f"With mov r0,#55 before: {len(flag55)}")
    for c in flag55:
        lines.append(f"\n--- caller 0x{c:X} ---")
        lines.extend(disasm_arm(ARM9, c - 0x40, 0x90))

    # Also search mov r0,#55 anywhere followed by bl within 16 bytes
    lines.append("\n=== mov r0,#55 then bl (any target) ===")
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    insns = list(md.disasm(ARM9, LOAD))
    for i, ins in enumerate(insns):
        if ins.mnemonic != "mov" or "#0x37" not in ins.op_str or "r0" not in ins.op_str:
            continue
        off = ins.address - LOAD
        for ins2 in insns[i + 1 : i + 8]:
            if ins2.mnemonic == "bl":
                tgt = int(ins2.op_str.replace("#", ""), 0)
                lines.append(f"0x{off:X}: mov r0,#55 -> bl 0x{tgt:X} @ 0x{ins2.address-LOAD:X}")
                if tgt == perf_ram:
                    lines.append("  ** calls GetPerformanceFlagWithChecks **")
                    lines.extend("  " + x for x in disasm_arm(ARM9, off - 0x60, 0x120))
                break

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"callers={len(callers)} flag55={len(flag55)} wrote {OUT}")


if __name__ == "__main__":
    main()
