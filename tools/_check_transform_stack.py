#!/usr/bin/env python3
"""Check transform effects and effect 86 + stackable compatibility."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

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

    def plain(i: int) -> str:
        return re.sub(r"\[.*?\]", "", strings.strings[block.begin + i]).strip()

    def show_item(item_id: int, label: str | None = None) -> None:
        e = item_p.item_list[item_id]
        eff = cd.get_item_effect_id(item_id)
        code = cd.get_effect_code(eff)
        print(f"=== {label or plain(item_id)} (ID {item_id}) ===")
        print(
            f"  category={e.category} effect={eff} "
            f"min={e.range_min} max={e.range_max}"
        )
        print(f"  bytecode ({len(code)}): {' '.join(f'{b:02X}' for b in code)}")

    print("VANILLA TRANSFORM / STACK EXAMPLES")
    print("=" * 60)
    for item_id, label in [
        (73, "Revival Seed"),
        (74, "Plain Seed"),
        (176, "TM (example)"),
        (175, "Used TM"),
        (70, "Oran Berry"),
        (17, "Pecha Berry"),
        (301, "Cleanse Orb"),
        (323, "would-be pack slot"),
    ]:
        if item_id < len(item_p.item_list):
            show_item(item_id, label)
            print()

    # Group items by identical effect bytecode
    effect_to_items: dict[int, list[int]] = defaultdict(list)
    for i in range(len(item_p.item_list)):
        effect_to_items[cd.get_item_effect_id(i)].append(i)

    print("\nUNIQUE EFFECT BYTECODES (count of items sharing)")
    print("=" * 60)
    bytecode_groups: dict[bytes, list[int]] = defaultdict(list)
    for eff_id in range(cd.nb_effects()):
        bytecode_groups[cd.get_effect_code(eff_id)].append(eff_id)

    # Find effects that look like transform (contain item id operands)
    print("\nEFFECTS WITH TRANSFORM-LIKE BYTECODE (first 16 bytes shown)")
    print("=" * 60)
    for eff_id in range(cd.nb_effects()):
        code = cd.get_effect_code(eff_id)
        if len(code) < 4:
            continue
        items = effect_to_items[eff_id][:5]
        names = [f"{i}:{plain(i)[:20]}" for i in items]
        print(f"effect {eff_id:3d} ({len(items)} items): {' '.join(f'{b:02X}' for b in code[:24])}")
        if eff_id in (cd.get_item_effect_id(73), cd.get_item_effect_id(176)):
            print(f"  ** transform candidate: {names}")

    revival_eff = cd.get_item_effect_id(73)
    tm_eff = cd.get_item_effect_id(176)
    orb_eff = cd.get_item_effect_id(301)
    print(f"\nRevival Seed effect ID: {revival_eff}")
    print(f"TM effect ID: {tm_eff}")
    print(f"Cleanse Orb effect ID: {orb_eff}")
    print(f"\nRevival bytecode: {' '.join(f'{b:02X}' for b in cd.get_effect_code(revival_eff))}")
    print(f"TM bytecode:       {' '.join(f'{b:02X}' for b in cd.get_effect_code(tm_eff))}")
    print(f"Orb bytecode:      {' '.join(f'{b:02X}' for b in cd.get_effect_code(orb_eff))}")

    print("\nSTACKABLE ITEMS (max_amount > 1) BY CATEGORY")
    print("=" * 60)
    by_cat: dict[int, list[tuple[int, str, int, int, int]]] = defaultdict(list)
    for i, e in enumerate(item_p.item_list):
        if e.range_max > 1:
            by_cat[e.category].append(
                (i, plain(i)[:28], cd.get_item_effect_id(i), e.range_min, e.range_max)
            )
    for cat in sorted(by_cat):
        rows = by_cat[cat][:15]
        print(f"\ncategory {cat} ({len(by_cat[cat])} stackable):")
        for row in rows:
            print(f"  {row[0]:4d} {row[1]:28s} eff={row[2]:3d} min={row[3]} max={row[4]}")

    print("\nCATEGORY 9 ORBS: min/max amounts")
    print("=" * 60)
    mins = Counter()
    maxs = Counter()
    for i, e in enumerate(item_p.item_list):
        if e.category == 9:
            mins[e.range_min] += 1
            maxs[e.range_max] += 1
    print("min_amount distribution:", dict(sorted(mins.items())))
    print("max_amount distribution:", dict(sorted(maxs.items())))

    print("\nITEMS SHARING EFFECT 86 (orbs)")
    print("=" * 60)
    eff86 = cd.get_item_effect_id(301)
    shared = [i for i in range(len(item_p.item_list)) if cd.get_item_effect_id(i) == eff86]
    print(f"effect id {eff86}, {len(shared)} items")
    sample = shared[:8]
    for i in sample:
        e = item_p.item_list[i]
        print(f"  {i:4d} {plain(i)[:30]:30s} min={e.range_min} max={e.range_max}")


if __name__ == "__main__":
    main()
