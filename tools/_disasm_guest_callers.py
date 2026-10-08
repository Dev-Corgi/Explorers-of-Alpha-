"""Disassemble CheckTeamMemberIdx callers and search for level scaling nearby."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
OUT = Path(r"C:\Working\SkyTemple\tools\_guest_callers.txt")
LOAD = 0x02000000


def parse_syms() -> dict[str, int]:
    t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    out = {}
    for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
        if nums:
            out[m.group(1)] = nums[0]
    return out


def bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def disasm_fn(data: bytes, off: int, size: int = 0x300) -> list[str]:
    syms = parse_syms()
    rev = {v: k for k, v in syms.items()}
    # find function start (scan back for push {..lr})
    start = off
    for back in range(0, 0x200, 4):
        p = off - back
        if p < 0:
            break
        w = struct.unpack_from("<I", data, p)[0]
        if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):  # push includes lr
            start = p
            break
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    lines = [f"// function from 0x{start:X}, marker call @ 0x{off:X}"]
    for ins in md.disasm(data[start : start + size], LOAD + start):
        note = ""
        if ins.mnemonic == "bl":
            w = struct.unpack_from("<I", data, ins.address - LOAD)[0]
            tgt = bl_target(ins.address, w) - LOAD
            if tgt in rev:
                note = f"  ; {rev[tgt]}"
        mark = " <-- CheckTeamMemberIdx" if ins.address - LOAD == off else ""
        lines.append(f"0x{ins.address-LOAD:06X}: {ins.mnemonic:7} {ins.op_str}{mark}{note}")
        if ins.address - LOAD > off + 0x180:
            break
    return lines


def main() -> None:
    syms = parse_syms()
    chk = syms["CheckTeamMemberIdx"]
    callers = []
    for off in range(0, len(ARM9) - 3, 4):
        w = struct.unpack_from("<I", ARM9, off)[0]
        if w >> 24 != 0xEB:
            continue
        if bl_target(LOAD + off, w) == LOAD + chk:
            callers.append(off)

    lines = [f"CheckTeamMemberIdx callers: {callers}"]
    for c in callers:
        lines.append("")
        lines.extend(disasm_fn(ARM9, c))

    # Search for GetPerformanceFlagWithChecks callers in same functions
    perf = syms["GetPerformanceFlagWithChecks"]
    lines.append("\n\n=== Functions calling GetPerformanceFlagWithChecks ===")
    perf_callers = []
    for off in range(0, len(ARM9) - 3, 4):
        w = struct.unpack_from("<I", ARM9, off)[0]
        if w >> 24 != 0xEB:
            continue
        if bl_target(LOAD + off, w) == LOAD + perf:
            perf_callers.append(off)
    lines.append(f"count {len(perf_callers)}")
    for c in perf_callers:
        lines.append("")
        lines.extend(disasm_fn(ARM9, c, 0x200))

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
