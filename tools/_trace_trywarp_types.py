#!/usr/bin/env python3
"""Trace TryWarp paths by type (r2) and bag-menu item use."""

from pathlib import Path
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbdummies.nds"
)
L = 0x022DC240
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
rom = NintendoDSRom(ROM.read_bytes())
ov = rom.loadArm9Overlays([29])[29].data


def dump(addr, size, title):
    print(f"\n=== {title} ===")
    for ins in cs.disasm(ov[addr - L : addr - L + size], addr):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


def callers_of(target):
    out = []
    for base in range(L, L + len(ov), 4):
        off = base - L
        w = int.from_bytes(ov[off : off + 4], "little")
        if (w >> 24) & 0xFF != 0xEB:
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        if base + 8 + imm * 4 == target:
            out.append(base)
    return out


# Bag menu TryWarp r2=0 site
dump(0x0230FC80, 0x120, "230FC80 bag menu -> TryWarp r2=0")

# TryWarp type 0 entry (r7=0 -> 2320EC8)
dump(0x02320EC8, 0x80, "TryWarp type 0 path 2320EC8")
dump(0x02320E60, 0x60, "TryWarp jump table dispatch 2320E60")

# UseSingleUseItemWrapper caller context (22FEA0C)
dump(0x022FE980, 0x100, "22FE980 action dispatch incl UseSingleUseItemWrapper")

# 22F52F8 UseSingleUseItem start
dump(0x022F52F8, 0x120, "UseSingleUseItem 22F52F8")

# Who calls 230FC80 region - find function start
dump(0x0230FC00, 0x80, "230FC00 earlier context")

# ApplyItemEffect callers 22F53EC context
dump(0x022F5340, 0x100, "22F5340 ApplyItemEffect caller region")

# Search for bl 22f85f0 (item setup before effect) - ALL callers
target = 0x022F85F0
print("\n=== ALL bl 22F85F0 callers ===")
for base in range(L, L + len(ov), 4):
    off = base - L
    w = int.from_bytes(ov[off : off + 4], "little")
    if (w >> 24) & 0xFF != 0xEB:
        continue
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    if base + 8 + imm * 4 == target:
        print(f"  {base:08X}")
        for ins in cs.disasm(ov[base - L - 24 : base - L + 4], base - 24):
            print(f"    {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

# Search references to effect 86 loader / item script runner
for target2, name in [(0x0231B9A8, "ItemCdLoader"), (0x0231B68C, "ApplyItemEffect")]:
    print(f"\n=== branches (b) to {name} {target2:08X} ===")
    for base in range(L, L + len(ov), 4):
        off = base - L
        w = int.from_bytes(ov[off : off + 4], "little")
        if ((w >> 28) & 0xF) != 0xE:
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        if base + 8 + imm * 4 == target2:
            print(f"  b from {base:08X}")
