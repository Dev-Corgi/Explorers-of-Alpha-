"""Resolve multiple Technician-like comparison sites."""
from __future__ import annotations

import struct
from pathlib import Path

ov = Path(r"C:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin").read_bytes()
arm = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
OV29_LOAD = 0x022DC240

out = []

def resolve_ldr_pc(file_off):
    """Resolve LDR Rt, [PC, #imm] at file_off."""
    instr = struct.unpack_from("<I", ov, file_off)[0]
    if (instr & 0x0F7F0000) != 0x051F0000 and (instr & 0x0FFF0000) != 0x059F0000:
        # generic: check E59Fxxxx
        if (instr & 0xFFFF0000) != 0xE59F0000:
            return None
    imm = instr & 0xFFF
    pc = file_off + 8
    pool_off = pc + imm
    if (instr & (1 << 23)) == 0:  # U bit - if clear, subtract
        # for E59F U=1 always add
        pass
    val = struct.unpack_from("<I", ov, pool_off)[0]
    return pool_off, val

def read_half_at_abs(abs_addr):
    for base, blob, name in [
        (OV29_LOAD, ov, "ov29"),
        (0x02000000, arm, "arm9"),
        (0x022C0000, None, "bss_guess"),
    ]:
        if name == "bss_guess":
            continue
        if base <= abs_addr < base + len(blob) - 1:
            return name, abs_addr - base, struct.unpack_from("<h", blob, abs_addr - base)[0]
    return None, None, None

# Site A: 0x41348 ldr
for label, ldr_off, cmp_desc in [
    ("site41348", 0x41348, "power vs thresh after mov#0x64"),
    ("site3415C", 0x3415C, "other"),
]:
    r = resolve_ldr_pc(ldr_off)
    out.append(f"{label} {cmp_desc}: {r}")
    if r:
        pool_off, val = r
        out.append(f"  points to {val:#x}")
        n, fo, h = read_half_at_abs(val)
        out.append(f"  deref halfword: {n} @{fo} = {h}")

# Search initialized data: find .word 4 in regions that look like constant tables
# near other known ability constants. Search for sequence matching vanilla chances.

# From pmdsky adjacent constants around TECHNICIAN:
# Look in arm9 for int16 4 that sits near int16 values matching known chances

# Scan arm9 for the pattern of documented data block
# BLAZE_KICK=10, ... TECHNICIAN=4
# Search for halfword 4 preceded within 0x40 bytes by halfword 10

hits = []
for off in range(0, len(arm) - 2, 2):
    if struct.unpack_from("<h", arm, off)[0] != 4:
        continue
    window = arm[max(0, off - 0x40) : off + 0x20]
    # look for 10 as int16 in window
    found10 = False
    for i in range(0, len(window) - 1, 2):
        if struct.unpack_from("<h", window, i)[0] == 10:
            found10 = True
            break
    if found10:
        hits.append(off)

out.append(f"arm9 halfword-4 near-10: {[hex(h) for h in hits[:30]]}")

# Same for ov29
hits2 = []
for off in range(0, len(ov) - 2, 2):
    if struct.unpack_from("<h", ov, off)[0] != 4:
        continue
    window = ov[max(0, off - 0x40) : off + 0x20]
    found10 = any(struct.unpack_from("<h", window, i)[0] == 10 for i in range(0, len(window) - 1, 2))
    if found10:
        hits2.append(off)
out.append(f"ov29 halfword-4 near-10: {[hex(h) for h in hits2[:30]]}")

# Read BSS init: check overlay 29 footer / y9
y9 = Path(r"C:\Working\SkyTemple\unpacked\y9.bin").read_bytes()
# each overlay entry is 32 bytes
# overlay 29 entry
ent = y9[29 * 32 : 30 * 32]
if len(ent) == 32:
    ov_id, ram, ramsize, bsssize = struct.unpack_from("<IIII", ent, 0)
    out.append(f"y9 ov29: id={ov_id} ram={ram:#x} size={ramsize:#x} bss={bsssize:#x}")
    static_init = struct.unpack_from("<I", ent, 16)[0]
    out.append(f"  static_init={static_init:#x} file_end would be ramsize")

# If BSS starts after compressed static: threshold lives in BSS and is inited by static ctor
# Search static init code for mov/str of value 4 to 0x22C46A0
target = 0x22C46A0
# Find references to this address in ov29
refs = []
for off in range(0, len(ov) - 3, 4):
    if struct.unpack_from("<I", ov, off)[0] == target:
        refs.append(off)
out.append(f"refs to 0x22C46A0 in ov29: {[hex(r) for r in refs]}")

# Also search nearby addresses for technician (vanilla was 0x22C455C)
for addr in range(0x22C4500, 0x22C4800, 4):
    refs = [off for off in range(0, len(ov) - 3, 4) if struct.unpack_from("<I", ov, off)[0] == addr]
    if refs:
        out.append(f"refs to {addr:#x}: {len(refs)} first={refs[0]:#x}")

Path(r"C:\Working\SkyTemple\tools\_tmp_tech_resolve2.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out))
