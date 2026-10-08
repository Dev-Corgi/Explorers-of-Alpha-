#!/usr/bin/env python3
"""Research stackable (cat 1) vs orb (cat 9) item handling in EoS US."""
from __future__ import annotations

import struct
from collections import defaultdict
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
import pmdsky_debug_py.na as na
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.item_p.handler import ItemPHandler

ROM = Path(
    r"c:\Working\SkyTemple\4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    r"-patched_orbs_roomcharge_nodarkness_berryboost.nds"
)
ARM9 = 0x02000000
OV29 = 0x022DC240


def arm_bl_target(pc: int, word: int) -> int | None:
    if (word & 0xFF000000) not in (0xEB000000, 0xEA000000):
        return None
    imm24 = word & 0xFFFFFF
    if imm24 & 0x800000:
        imm24 -= 1 << 24
    return (pc + 8 + (imm24 << 2)) & 0xFFFFFFFF


def find_bl(data: bytes, load: int, target: int) -> list[int]:
    return [
        load + off
        for off in range(0, len(data) - 4, 4)
        if arm_bl_target(load + off, struct.unpack_from("<I", data, off)[0]) == target
    ]


def dump(cs: Cs, data: bytes, base: int, addr: int, n: int = 0x100, label: str = "") -> None:
    if label:
        print(f"\n=== {label} @ 0x{addr:08X} ===")
    off = addr - base
    for ins in cs.disasm(data[off : off + n], addr):
        print(f"  0x{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    arm9 = rom.arm9
    table = loadOverlayTable(rom.arm9OverlayTable, lambda fid, _: rom.files[fid])
    ov29 = rom.files[table[29].fileID]
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    item_p = ItemPHandler.deserialize(rom.getFileByName("BALANCE/item_p.bin"))
    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/item_cd.bin"))

    # item_p samples
    print("=== item_p.bin category / range samples ===")
    for iid in [17, 70, 73, 176, 301, 318, 344]:
        if iid < len(item_p.item_list):
            e = item_p.item_list[iid]
            print(
                f"  ID {iid:3d}: cat={e.category:2d} min={e.range_min} max={e.range_max} "
                f"eff={cd.get_item_effect_id(iid)} action={e.action_name}"
            )

    cat9 = sum(1 for e in item_p.item_list if e.category == 9)
    cat1_stack = sum(1 for e in item_p.item_list if e.category == 1 and e.range_max > 1)
    print(f"\nOrbs (cat 9): {cat9}; cat-1 with max>1: {cat1_stack}")

    # Key ARM9 functions
    syms = {
        "InitItem": na.arm9.functions.InitItem.addresses[0] + ARM9,
        "ClearItemSlot": 0x0200D81C,
        "RemoveEquivItemNoHole": 0x0200F600,
        "RemoveEquivItemScan": 0x0200F558,
        "DecrementStackItem": 0x0200F694,
        "RemoveItemByIdAndStackNoHole": 0x0200F4D4,
        "AddItemToBag": 0x0200F884,
        "GetItemNameFormatted": 0x0200E884,
        "GetItemCategory": 0x0200E808,
        "IsItemThrowable?CAF0": 0x0200CAF0,
        "GetItemMax?CB70": 0x0200CB70,
        "IsMoney?CB10": 0x0200CB10,
        "GetMinMax?EA58": 0x0200EA58,
        "GenerateItem": na.overlay29.functions.GenerateItem.addresses[0] + OV29,
        "RemoveUsedItem": na.overlay29.functions.RemoveUsedItem.addresses[0] + OV29,
    }

    for name, addr in syms.items():
        region = "ov29" if addr >= OV29 else "arm9"
        data = ov29 if region == "ov29" else arm9
        base = OV29 if region == "ov29" else ARM9
        dump(cs, data, base, addr, 0x120, name)

    # BuildItemName - search for x3 formatting
    print("\n=== Scanning ARM9 for 'x3' / quantity suffix patterns near GetItemNameFormatted ===")
    for ins in cs.disasm(arm9[0x0200D000 - ARM9 : 0x0200D800 - ARM9], 0x0200D000):
        if "x3" in ins.op_str.lower() or ins.mnemonic == "bl" and ins.op_str.startswith("#0x200"):
            if 0x0200D280 <= ins.address <= 0x0200D600:
                print(f"  0x{ins.address:08X}: {ins.mnemonic} {ins.op_str}")

    dump(cs, arm9, ARM9, 0x0200D310, 0x200, "BuildItemName region @ D310")

    # Callers of DecrementStackItem, RemoveEquivItemNoHole
    print("\n=== BL callers (ARM9) ===")
    for tgt, name in [
        (0x0200F694, "DecrementStackItem"),
        (0x0200F600, "RemoveEquivItemNoHole"),
        (0x0200F558, "RemoveEquivItemScan"),
        (0x0200D81C, "ClearItemSlot"),
        (0x0200F884, "AddItemToBag"),
    ]:
        callers = find_bl(arm9, ARM9, tgt)
        print(f"  {name}: {len(callers)} callers -> {[f'0x{x:08X}' for x in callers[:12]]}")

    print("\n=== BL callers (ov29) for ClearItemSlot / RemoveEquiv / DecrementStack ===")
    for tgt, name in [
        (0x0200D81C, "ClearItemSlot"),
        (0x0200F600, "RemoveEquivItemNoHole"),
        (0x0200F558, "RemoveEquivItemScan"),
        (0x0200F694, "DecrementStackItem"),
    ]:
        callers = find_bl(ov29, OV29, tgt)
        print(f"  {name}: {len(callers)} ov29 callers")

    # GenerateItem category check
    gi = na.overlay29.functions.GenerateItem.addresses[0] + OV29
    dump(cs, ov29, OV29, gi, 0x80, "GenerateItem")

    # ITEM_CATEGORY_ACTIONS
    cat_off = na.overlay29.data.ITEM_CATEGORY_ACTIONS.addresses[0]
    raw = ov29[cat_off : cat_off + 32]
    print("\n=== ITEM_CATEGORY_ACTIONS (overlay29) ===")
    for i in range(16):
        act = struct.unpack_from("<H", raw, i * 2)[0]
        print(f"  category {i:2d} -> action {act}")

    # Check patched regions
    print("\n=== Patch footprint check (berry/orb caves) ===")
    for addr, label in [
        (0x02330100, "berry_boost cave"),
        (0x02330500, "orb_charges ov29 cave (approx)"),
    ]:
        off = addr - OV29
        chunk = ov29[off : off + 16]
        nz = any(b != 0 for b in chunk)
        print(f"  {label} @ 0x{addr:08X}: nonzero={nz} head={chunk.hex()}")


if __name__ == "__main__":
    main()
