#!/usr/bin/env python3
"""Deep trace for Cleanse Orb first-use bug."""
from __future__ import annotations

import struct
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.item_p.handler import ItemPHandler
import pmdsky_debug_py.na as na

ROM = (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges.nds"
)
L = 0x022DC240
ARM9 = 0x02000000

rom = NintendoDSRom(open(ROM, "rb").read())
ov = rom.loadArm9Overlays([29])[29].data
arm9 = rom.arm9
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def dump(data: bytes, base: int, addr: int, n: int = 0x80, label: str = "") -> None:
    if label:
        print(f"\n=== {label} @{addr:08X} ===")
    for ins in cs.disasm(data[addr - base : addr - base + n], addr):
        print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


init = 0x0200CE9C  # na InitItem US
dump(arm9, ARM9, init, 0x80, f"InitItem @{init:08X}")
dump(arm9, ARM9, 0x0200CF58, 0x30, "InitStandardItem")
dump(arm9, ARM9, 0x0200D81C, 0x50, "ClearItemSlot")
dump(arm9, ARM9, 0x0200F604, 0xA0, "RemoveEquivItemNoHole body")
dump(arm9, ARM9, 0x0200F55C, 0xA0, "RemoveEquivItemScan body")

# MaybeSkip + ItemEffectPostClear label
dump(ov, L, 0x023307A4, 0x40, "MaybeSkipItemEffectPostClear cave")
dump(ov, L, 0x0231B68C, 0x80, "0231B68C (ItemEffectPostClear label)")

# Trace from FB310 - what vanilla called before patch?
# Callers of functions that purge bag
for addr, label in [
    (0x023455A4, "023455A4 (F600 from PostClear BFS)"),
    (0x02345580, "02345580 region"),
    (0x02346A00, "02346A00 (346A44 func)"),
    (0x02322374, "UseItem"),
    (0x022FEBAC, "Action49 resolver"),
    (0x022FED54, "EnsureCanStand + TryWarp path"),
    (0x02321104, "2321104 type5 caller"),
    (0x02320D08, "TryWarp"),
    (0x022EC878, "InlineItemClear site"),
]:
    dump(ov, L, addr, 0x60, label)

cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/item_cd.bin"))
item_p = ItemPHandler.deserialize(rom.getFileByName("BALANCE/item_p.bin"))
for iid in [323, 301, 318]:
    it = item_p.item_list[iid]
    print(
        f"\nItem {iid}: cat={it.category} eff={cd.get_item_effect_id(iid)} "
        f"range={it.range_min}-{it.range_max}"
    )

# Cleanse effect bytecode
eff = cd.get_item_effect_id(323)
code = cd.get_effect_code(eff)
print(f"\nCleanse effect {eff}: {len(code)} bytes")
dump(code, 0x0231BE50, 0x0231BE50, min(len(code), 0x80), "Cleanse effect bytecode")

# Check struct item size references
print("\n=== struct item field refs in TryConsume (cave) ===")
dump(ov, L, 0x02330520, 0x60, "TryConsumeOrbChargeOv29")

# Disassemble ItemEffect path for entity held item vs bag
dump(ov, L, 0x022FB280, 0x100, "ItemEffect handler FB280")
