#!/usr/bin/env python3
"""Find last-target / multi-hit helpers near move effect dispatch."""
from __future__ import annotations

import struct
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom

rom = NintendoDSRom.fromFile(r"C:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
ov = rom.files[29]
base = 0x022DC240
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

# Find BLs to MoveEffectJump / waza from a likely target loop.
# Known: MOVE_EFFECT_JUMP = 0x023326CC area; effect stubs at 0x02330134
# Search for functions that call something then check a counter.

# Disasm around DoMoveRazorWind if it exists - move 100
# Search pool for status 3 razor wind handler references

# Find GetVisibility or target iteration: bl DealDamage after loop
# Look for ldrb with #1 cmp near "last" patterns in 0x232xxxx move wrappers

# Symbol from common knowledge: Some versions have
# 0x022EFA80 GetEntity on target list

# Search string-ish: find functions referencing both IsChargingTwoTurnMove and DealDamage
ischarge = 0x023245A4
hits = []
for off in range(0, len(ov) - 4, 4):
    w = struct.unpack_from("<I", ov, off)[0]
    if (w >> 24) != 0xEB:
        continue
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    dest = base + off + 8 + imm * 4
    if dest == ischarge:
        hits.append(base + off)

print("IsChargingTwoTurnMove callers:", len(hits))
for h in hits[:25]:
    print(f"  {h:#010x}")

# For each caller, see if ClearTwoTurnStatus follows within 0x80
clear = 0x02318D58
for h in hits:
    off = h - base
    window = ov[off : off + 0xC0]
    found_clear = False
    for i in range(0, len(window) - 4, 4):
        w = struct.unpack_from("<I", window, i)[0]
        if (w >> 24) != 0xEB:
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        dest = h + i + 8 + imm * 4
        if dest == clear:
            found_clear = True
            break
    if found_clear:
        print(f"caller+clear {h:#010x}")
        for ins in cs.disasm(ov[off - 0x10 : off + 0x80], h - 0x10):
            print(f"  {ins.address:08x}: {ins.mnemonic} {ins.op_str}")
        print()
