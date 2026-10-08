"""Find all ARM mov r0,#55 sites and nearby context in arm9."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
OUT = Path(r"C:\Working\SkyTemple\tools\_mov55_sites.txt")
LOAD = 0x02000000


def parse_syms() -> dict[str, int]:
    t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    out = {}
    for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
        name = m.group(1)
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
        if nums:
            out[name] = nums[0]
    return out


def arm_bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def disasm(data: bytes, off: int, before=0x60, after=0x80) -> list[str]:
    start = max(0, off - before)
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    lines = []
    for ins in md.disasm(data[start : off + after], LOAD + start):
        mark = " <--" if ins.address - LOAD == off else ""
        tgt_note = ""
        if ins.mnemonic == "bl":
            w = struct.unpack_from("<I", data, ins.address - LOAD)[0]
            tgt = arm_bl_target(ins.address, w)
            sym = rev.get(tgt - LOAD, "")
            if sym:
                tgt_note = f"  ; {sym}"
        lines.append(f"0x{ins.address-LOAD:06X}: {ins.mnemonic:7} {ins.op_str}{mark}{tgt_note}")
    return lines


syms = parse_syms()
rev = {v: k for k, v in syms.items()}
lines = ["=== ARM mov r0,#55 sites ==="]
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
sites = []
for ins in md.disasm(ARM9, LOAD):
    if ins.mnemonic == "mov" and ins.op_str.strip() in ("r0, #0x37", "r0, #55"):
        sites.append(ins.address - LOAD)

lines.append(f"Count: {len(sites)}")
for off in sites:
    lines.append(f"\n=== 0x{off:X} ===")
    lines.extend(disasm(ARM9, off))

# also mov r1,#55, mov r2,#55 used as flag index
for reg in ["r0", "r1", "r2", "r4"]:
    hits = []
    for ins in md.disasm(ARM9, LOAD):
        if ins.mnemonic == "mov" and ins.op_str.strip() == f"{reg}, #0x37":
            hits.append(ins.address - LOAD)
    if hits:
        lines.append(f"\n=== mov {reg},#55: {len(hits)} sites ===")
        for off in hits[:10]:
            lines.append(f"  0x{off:X}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"mov r0,#55 sites: {len(sites)} -> {OUT}")
