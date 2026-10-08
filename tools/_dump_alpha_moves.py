#!/usr/bin/env python3
"""Dump Alpha/PMD-only move data + range docs from ROM."""
from __future__ import annotations

import sys
from pathlib import Path

# Avoid Windows console encoding failures on accented strings.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.waza_p.handler import WazaPHandler
from skytemple_files.data.waza_p.protocol import (
    WazaMoveRangeCondition,
    WazaMoveRangeRange,
    WazaMoveRangeTarget,
)

ROM = Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds")
IDS = [55, 131, 168, 193, 331, 355, 360, 364, 366, 397, 405, 467, 557]


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    config = get_ppmdu_config_for_rom(rom)
    wp = WazaPHandler.deserialize(rom.getFileByName("BALANCE/waza_p.bin"))
    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/waza_cd.bin"))
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))
    blocks = config.string_index_data.string_blocks

    print("=== Move-related string blocks ===")
    for k, b in blocks.items():
        if "Move" in k or "Range" in k:
            print(f"  {k}: {b.begin}-{b.end}")

    name_b = blocks["Move Names"]
    names = strings.strings[name_b.begin : name_b.end + 1]

    descs = None
    for key in ("Move Descriptions", "Move Long Descriptions", "Move Short Descriptions"):
        if key in blocks:
            db = blocks[key]
            descs = strings.strings[db.begin : db.end + 1]
            print(f"Using descriptions from {key}")
            break

    RANGE = {e.value: e.print_name for e in WazaMoveRangeRange}
    TARGET = {e.value: e.print_name for e in WazaMoveRangeTarget}
    COND = {e.value: e.print_name for e in WazaMoveRangeCondition}

    print("\n=== WazaMoveRangeRange 0-5 ===")
    for i in range(6):
        print(f"  {i}: {RANGE[i]}")

    print("\n=== range_check_text base strings (10095+) ===")
    for i in range(10095, 10125):
        if i < len(strings.strings):
            print(f"  {i}: {strings.strings[i]!r}")

    # attrs of move for debugging
    sample = wp.moves[55]
    print("\n=== sample move attrs ===")
    print([a for a in dir(sample) if not a.startswith("_")])

    for mid in IDS:
        m = wp.moves[mid]
        name = names[mid] if mid < len(names) else "?"
        desc = descs[mid] if descs and mid < len(descs) else None
        rs = m.settings_range
        rsa = m.settings_range_ai
        try:
            eid = cd.get_item_effect_id(mid)
        except Exception as e:  # noqa: BLE001
            eid = f"err:{e}"
        print("=" * 60)
        print(f"ID {mid}: {name}")
        print(
            f"  power={m.base_power} pp={m.base_pp} accuracy={m.accuracy} "
            f"miss_acc={m.miss_accuracy} type={m.type} category={m.category} "
            f"crit={m.crit_chance}"
        )
        print(
            f"  range_check_text={m.range_check_text} message_id={m.message_id} "
            f"chained={m.number_chained_hits} ai_weight={m.ai_weight} "
            f"ai_cond1={m.ai_condition1_chance}"
        )
        print(
            f"  range: target={rs.target}({TARGET.get(rs.target)}) "
            f"range={rs.range}({RANGE.get(rs.range)}) "
            f"cond={rs.condition}({COND.get(rs.condition)})"
        )
        print(
            f"  ai_range: target={rsa.target}({TARGET.get(rsa.target)}) "
            f"range={rsa.range}({RANGE.get(rsa.range)}) "
            f"cond={rsa.condition}({COND.get(rsa.condition)})"
        )
        print(f"  effect_id={eid}")
        print(f"  desc={desc!r}")
        rct = m.range_check_text
        idx = 10095 + rct
        if idx < len(strings.strings):
            print(f"  range_text[{rct}->{idx}]={strings.strings[idx]!r}")
        # also try EU base mentioned in UI
        idx2 = 10097 + rct
        if idx2 < len(strings.strings) and idx2 != idx:
            print(f"  range_text_euish[{rct}->{idx2}]={strings.strings[idx2]!r}")


if __name__ == "__main__":
    main()
