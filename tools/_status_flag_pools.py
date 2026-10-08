#!/usr/bin/env python3
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OV29 = 0x022DC240
van = (REPO / "unpacked/overlay/overlay_0029.bin").read_bytes()
CAVE_LO, CAVE_HI = 0x02351380, 0x02351400


def is_ldr_pc(word: int) -> bool:
    return (word & 0x0FEF0000) == 0x051F0000 or (word & 0x0F7F0000) == 0x059F0000


fn_lo, fn_hi = 0x022E3AB4, 0x022E3D90
print(f"Status icon flag builder @ [{fn_lo:#x}, {fn_hi:#x})")
print("ldr [pc] pools:\n")
for off in range(fn_lo - OV29, fn_hi - OV29, 4):
    addr = OV29 + off
    word = struct.unpack_from("<I", van, off)[0]
    if not is_ldr_pc(word):
        continue
    pool = addr + 8 + (word & 0xFFF)
    pval = struct.unpack_from("<I", van, pool - OV29)[0]
    rd = (word >> 12) & 0xF
    tags = []
    if CAVE_LO <= pval < CAVE_HI:
        tags.append("VALUE_IN_CAVE")
    if 0x02351000 <= pval < 0x02354000:
        tags.append("ov29_tail")
    print(f"  {addr:#010x} ldr r{rd} -> pool {pool:#010x} = {pval:#010x}  {' '.join(tags)}")

print("\nLiteral pool block @ 0x022E3D94 (all entries):")
for a in range(0x022E3D94, 0x022E3DD8, 4):
    w = struct.unpack_from("<I", van, a - OV29)[0]
    tag = " *** CAVE" if CAVE_LO <= w < CAVE_HI else ""
    print(f"  {a:#010x}: {w:#010x}{tag}")

print("\n8-byte entries at cave-related tail bases:")
for base in [0x023513B4, 0x023513F4, 0x0235130C]:
    print(f"  base {base:#010x}:")
    for i in range(6):
        a = base + i * 8
        if a - OV29 + 8 > len(van):
            break
        w1, w2 = struct.unpack_from("<II", van, a - OV29)
        print(f"    [{i}] {a:#010x}: {w1:#010x} {w2:#010x}")
