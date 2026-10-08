#!/usr/bin/env python3
"""Catalog item_cd effects; find transform-like patterns."""
from __future__ import annotations

import re
import struct
from collections import defaultdict
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
BASE = 0x0231BE50


def plain(strings, block, i: int) -> str:
    return re.sub(r"\[.*?\]", "", strings.strings[block.begin + i]).strip()


def pool_words(code: bytes) -> list[int]:
    out = []
    for off in range(max(0, len(code) - 64), len(code), 4):
        if off + 4 <= len(code):
            out.append(struct.unpack_from("<I", code, off)[0])
    return out


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
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    by_size: dict[int, list[int]] = defaultdict(list)
    for eff in range(cd.nb_effects()):
        by_size[len(cd.get_effect_code(eff))].append(eff)

    print("Effect sizes (count):")
    for size in sorted(by_size):
        print(f"  {size:3d} bytes: {len(by_size[size])} effects")

    interesting = [73, 74, 85, 175, 176, 187, 70, 301, 7, 8, 128]
    print("\nSelected items:")
    for i in interesting:
        eff = cd.get_item_effect_id(i)
        code = cd.get_effect_code(eff)
        print(f"\n{i:4d} {plain(strings, block, i)[:28]:28s} effect={eff} len={len(code)}")
        print("  hex:", " ".join(f"{b:02X}" for b in code))
        print("  pool:", " ".join(f"0x{w:08X}" for w in pool_words(code)))
        for ins in cs.disasm(code, BASE):
            print(f"    {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

    print("\nUnique small effects (len<=32), all items using them:")
    seen_code: dict[bytes, int] = {}
    for eff in range(cd.nb_effects()):
        code = bytes(cd.get_effect_code(eff))
        if len(code) > 32:
            continue
        if code not in seen_code:
            seen_code[code] = eff
            items = cd.get_all_of(eff)[:6]
            names = [f"{x}:{plain(strings, block, x)[:18]}" for x in items]
            print(f"  effect {eff:3d} ({len(code):2d}b): {' '.join(f'{b:02X}' for b in code)}")
            print(f"    items: {names}")

    # stack-like held items using effect 86
    print("\nHeld items (cat 4/8) with effect 86 and range_max>1:")
    for i, e in enumerate(item_p.item_list):
        if e.category in (4, 8) and e.range_max > 1 and cd.get_item_effect_id(i) == 86:
            print(
                f"  {i:4d} {plain(strings, block, i)[:24]:24s} "
                f"range={e.range_min}-{e.range_max}"
            )


if __name__ == "__main__":
    main()
