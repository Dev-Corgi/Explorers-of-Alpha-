"""Resolve Technician threshold pointer from Alpha OV29 site 0x3413C."""
from __future__ import annotations

import struct
from pathlib import Path

ov = Path(r"C:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin").read_bytes()
# OV29 load address from damage_formula offsets
OV29_LOAD = 0x022DC240

site = 0x3415C
# LDR r0, [PC, #0x700] at site; PC = site+8
pc = site + 8
imm = 0x700
pool_addr_file = pc + imm
pool_val = struct.unpack_from("<I", ov, pool_addr_file)[0]
out = [
    f"pool file off={pool_addr_file:#x} value={pool_val:#x}",
    f"as ov29 abs={(OV29_LOAD + pool_addr_file):#x}",
]

# If pool_val is absolute address in OV29 or ARM9 or ITCM
candidates = []
if OV29_LOAD <= pool_val < OV29_LOAD + len(ov):
    file_off = pool_val - OV29_LOAD
    thr = struct.unpack_from("<h", ov, file_off)[0]
    candidates.append(("ov29", file_off, thr))
# ARM9 at 0x02000000
arm = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
if 0x02000000 <= pool_val < 0x02000000 + len(arm):
    file_off = pool_val - 0x02000000
    thr = struct.unpack_from("<h", arm, file_off)[0]
    candidates.append(("arm9", file_off, thr))
# Also try BSS region 0x22Cxxxx from vanilla symbol 0x22C455C
# In Alpha, overlay data might be at different place - search memory map
# Read nearby instructions fully for clarity
for i in range(0x3413C, 0x341D0, 4):
    w = struct.unpack_from("<I", ov, i)[0]
    out.append(f"{i:06X}: {w:08X}")

out.append(f"candidates: {candidates}")

# Broader: search for ldrsh of a halfword that equals 4 in writable/data sections
# Find all absolute pointers in ov29 that point to a halfword 4 in arm9/ov29
hits = []
for off in range(0, len(ov) - 4, 4):
    val = struct.unpack_from("<I", ov, off)[0]
    for base, blob, name in [
        (OV29_LOAD, ov, "ov29"),
        (0x02000000, arm, "arm9"),
    ]:
        if base <= val < base + len(blob) - 2:
            fo = val - base
            # aligned halfword
            if fo % 2 == 0:
                h = struct.unpack_from("<h", blob, fo)[0]
                if h == 4:
                    hits.append((off, name, fo, h))
out.append(f"pointers-to-halfword-4 count={len(hits)}")
for h in hits[:40]:
    out.append(f"  ptr_at_ov {h[0]:#x} -> {h[1]}@{h[2]:#x} = {h[3]}")

# Also check if threshold was raised (8, 40, 60, 70) for Gen9
for thr_want in [4, 5, 7, 8, 40, 50, 60, 70]:
    c = 0
    for off in range(0, len(ov) - 4, 4):
        val = struct.unpack_from("<I", ov, off)[0]
        for base, blob, name in [(OV29_LOAD, ov, "ov29"), (0x02000000, arm, "arm9")]:
            if base <= val < base + len(blob) - 2 and (val - base) % 2 == 0:
                if struct.unpack_from("<h", blob, val - base)[0] == thr_want:
                    c += 1
    out.append(f"ptrs to halfword {thr_want}: {c}")

# Dump what 0x3415C actually compares - maybe r6 is power from GetMovePower
# Look at bl targets
def bl_target(addr, instr):
    # BL: EBxxxxxx, offset = sign_extend(imm24)<<2
    imm24 = instr & 0xFFFFFF
    if imm24 & 0x800000:
        imm24 -= 0x1000000
    return addr + 8 + (imm24 << 2)

for addr in [0x34140, 0x34154, 0x34174]:
    instr = struct.unpack_from("<I", ov, addr)[0]
    if (instr & 0x0F000000) == 0x0B000000:
        tgt = bl_target(addr, instr)
        out.append(f"BL at {addr:#x} -> {tgt:#x} file={(tgt-OV29_LOAD) if OV29_LOAD<=tgt<OV29_LOAD+len(ov) else 'outside'}")

Path(r"C:\Working\SkyTemple\tools\_tmp_tech_resolve.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out[:60]))
