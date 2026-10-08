"""List all GetPerformanceFlagWithChecks callers with r0 value setup."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
LOAD = 0x02000000


def bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def infer_r0(data: bytes, bl_off: int) -> str:
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    start = max(0, bl_off - 0x30)
    chunk = list(md.disasm(data[start : bl_off + 4], LOAD + start))
    r0 = "?"
    for ins in chunk:
        if ins.mnemonic == "mov" and ins.op_str.startswith("r0,"):
            r0 = ins.op_str.split("#")[-1].strip() if "#" in ins.op_str else ins.op_str
        if ins.mnemonic == "ldr" and ins.op_str.startswith("r0,"):
            r0 = f"pool({ins.op_str})"
    return r0


perf_off = 0x4CA94
callers = []
for off in range(0, len(ARM9) - 3, 4):
    w = struct.unpack_from("<I", ARM9, off)[0]
    if w >> 24 != 0xEB:
        continue
    if bl_target(LOAD + off, w) == LOAD + perf_off:
        callers.append(off)

print(f"callers {len(callers)}")
for c in sorted(callers):
    print(f"  0x{c:X}  r0={infer_r0(ARM9, c)}")
