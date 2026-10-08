#!/usr/bin/env python3
"""Deep-dive effect 86 and transform/stack behavior."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.item_p.handler import ItemPHandler
from skytemple_files.data.str.handler import StrHandler

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost.nds"
)
ITEM_EFFECT_BASE = 0x0231BE50
L = 0x022DC240


def plain(strings, block, i: int) -> str:
    return re.sub(r"\[.*?\]", "", strings.strings[block.begin + i]).strip()


def disasm(code: bytes, base: int) -> None:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in cs.disasm(code, base):
        print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/item_cd.bin"))
    item_p = ItemPHandler.deserialize(rom.getFileByName("BALANCE/item_p.bin"))
    config = get_ppmdu_config_for_rom(rom)
    block = config.string_index_data.string_blocks["Item Names"]
    strings = StrHandler.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"),
        string_encoding=config.string_encoding,
    )
    ov = rom.loadArm9Overlays([29])[29].data

    eff86 = cd.get_item_effect_id(301)
    code = cd.get_effect_code(eff86)
    print(f"Effect {eff86} size={len(code)}")
    print("Disassembly (as loaded at 0x0231BE50):")
    disasm(code, ITEM_EFFECT_BASE)

    # Parse literal pool at end
    print("\nLiteral pool tail:")
    tail = code[-16:]
    for off in range(0, 16, 4):
        val = struct.unpack_from("<I", tail, off)[0]
        print(f"  +{len(code)-16+off:02X}: 0x{val:08X}")

    ptr = struct.unpack_from("<I", code, len(code) - 16)[0]
    val2 = struct.unpack_from("<I", code, len(code) - 12)[0]
    val3 = struct.unpack_from("<I", code, len(code) - 8)[0]
    print(f"\nResolved pool pointer 0x{ptr:08X}:")
    if ptr - L < len(ov):
        chunk = ov[ptr - L : ptr - L + 32]
        print("  overlay bytes:", " ".join(f"{b:02X}" for b in chunk))
        for ins in Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(chunk, ptr):
            print(f"    {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

    print("\nitem_p fields for transform-related items:")
    ids = [73, 74, 175, 176, 301, 323, 70, 17, 128, 129]
    for i in ids:
        if i >= len(item_p.item_list):
            continue
        e = item_p.item_list[i]
        print(
            f"  {i:4d} {plain(strings, block, i)[:24]:24s} "
            f"cat={e.category:2d} eff={cd.get_item_effect_id(i):3d} "
            f"item_id={e.item_id:4d} move_id={e.move_id:4d} "
            f"range={e.range_min}-{e.range_max}"
        )

    print("\nAll effect-86 items (first 30):")
    shared = [i for i in range(min(len(item_p.item_list), cd.nb_items())) if cd.get_item_effect_id(i) == eff86]
    print(f"  total={len(shared)}")
    for i in shared[:30]:
        e = item_p.item_list[i]
        print(
            f"  {i:4d} {plain(strings, block, i)[:26]:26s} "
            f"cat={e.category} item_id={e.item_id} move_id={e.move_id} "
            f"range={e.range_min}-{e.range_max}"
        )

    print("\nStackable items with effect 86:")
    for i in shared:
        e = item_p.item_list[i]
        if e.range_max > 1:
            print(
                f"  {i:4d} {plain(strings, block, i)[:26]:26s} "
                f"range={e.range_min}-{e.range_max}"
            )

    print("\nStackable category-9 orbs? (range_max>1):")
    for i, e in enumerate(item_p.item_list):
        if e.category == 9 and e.range_max > 1:
            print(f"  {i} {plain(strings, block, i)} range={e.range_min}-{e.range_max}")

    print("\nExamples of stackable consumables (range_max>1):")
    count = 0
    for i, e in enumerate(item_p.item_list):
        if e.range_max > 1 and cd.get_item_effect_id(i) != 0:
            print(
                f"  {i:4d} {plain(strings, block, i)[:26]:26s} "
                f"cat={e.category} eff={cd.get_item_effect_id(i):3d} "
                f"range={e.range_min}-{e.range_max}"
            )
            count += 1
            if count >= 25:
                break

    # Effect 14 = plain seed
    eff14 = cd.get_item_effect_id(74)
    code14 = cd.get_effect_code(eff14)
    print(f"\nEffect {eff14} (Plain Seed) size={len(code14)}:")
    disasm(code14, ITEM_EFFECT_BASE)

    # Hunt unique small transform-like effects
    print("\nSmall effects (<=32b) used by multiple items - possible simple transforms:")
    from collections import defaultdict

    groups: dict[bytes, list[int]] = defaultdict(list)
    for eff in range(cd.nb_effects()):
        groups[cd.get_effect_code(eff)].append(eff)
    for code_b, eff_ids in sorted(groups.items(), key=lambda x: len(x[1]), reverse=True):
        if len(code_b) > 32 or len(eff_ids) < 2:
            continue
        sample_items = []
        for eff in eff_ids[:1]:
            sample_items.extend(cd.get_all_of(eff)[:3])
        names = [f"{i}:{plain(strings, block, i)[:16]}" for i in sample_items]
        print(f"  effects {eff_ids} ({len(code_b)}b): {' '.join(f'{b:02X}' for b in code_b)}")
        print(f"    items: {names}")


if __name__ == "__main__":
    main()
