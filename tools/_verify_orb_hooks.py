#!/usr/bin/env python3
"""Verify all orb pack hook sites in output ROM."""

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

HOOKS = {
    "Action49_AfterItemId": 0x0231AA20,
    "TryWarp_PreItemEffect": 0x02321010,
    "UseSingleUseItem_PreApply": 0x022F53EC,
    "RunItemEffect_CheckId": 0x023223E0,
    "ItemCdLoader": 0x0231B9A8,
    "ItemEffectClearSlot1": 0x022FB2F0,
}

rom = NintendoDSRom(ROM.read_bytes())
ov = rom.loadArm9Overlays([29])[29].data

print("Hook verification:")
for name, addr in HOOKS.items():
    ins = list(cs.disasm(ov[addr - L : addr - L + 4], addr))[0]
    print(f"  {name} @{addr:08X}: {ins.mnemonic} {ins.op_str}")

print("\nAction49 hook target:")
w = int.from_bytes(ov[0x0231AA20 - L : 0x0231AA24 - L], "little")
imm = w & 0xFFFFFF
if imm & 0x800000:
    imm -= 0x1000000
dest = 0x0231AA20 + 8 + imm * 4
print(f"  branches to {dest:08X}")
for ins in cs.disasm(ov[dest - L : dest - L + 32], dest):
    print(f"    {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
