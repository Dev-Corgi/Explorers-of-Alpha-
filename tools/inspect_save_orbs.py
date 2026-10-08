#!/usr/bin/env python3
"""Inspect orb slots in an EoS .sav (storage + bag item structs)."""

from __future__ import annotations

import re
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def plain(s: str) -> str:
    return re.sub(r"\[.*?\]", "", s).strip()


def load_orb_names(rom_path: Path) -> dict[int, str]:
    from ndspy.rom import NintendoDSRom
    from skytemple_files.common.util import get_ppmdu_config_for_rom
    from skytemple_files.data.item_p.handler import ItemPHandler
    from skytemple_files.data.str.handler import StrHandler

    rom = NintendoDSRom(rom_path.read_bytes())
    item_p = ItemPHandler.deserialize(rom.getFileByName("BALANCE/item_p.bin"))
    config = get_ppmdu_config_for_rom(rom)
    block = config.string_index_data.string_blocks["Item Names"]
    strings = StrHandler.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"), string_encoding=config.string_encoding
    )
    out: dict[int, str] = {}
    for item_id, entry in enumerate(item_p.item_list):
        if entry.category == 9:
            out[item_id] = plain(strings.strings[block.begin + item_id])
    return out


def parse_item_struct(data: bytes, off: int) -> tuple[int, int, int] | None:
    """Return (item_id, quantity_u16, use_low_byte) for 6-byte struct item."""
    if off + 6 > len(data):
        return None
    b0, b1, q, iid = struct.unpack_from("<BBHh", data, off)
    return iid, q, q & 0xFF


def scan_struct_items(data: bytes, orb_names: dict[int, str]) -> list[tuple[int, int, int, int]]:
    """Find 6-byte item structs whose id@+4 is category-9 orb."""
    hits: list[tuple[int, int, int, int]] = []
    seen: set[tuple[int, int]] = set()
    for off in range(0, len(data) - 5):
        parsed = parse_item_struct(data, off)
        if parsed is None:
            continue
        iid, q, use = parsed
        if iid not in orb_names:
            continue
        key = (off, iid)
        if key in seen:
            continue
        seen.add(key)
        hits.append((off, iid, q, use))
    return hits


def main() -> None:
    sav = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "savefile" / (
        "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)-patched2.sav"
    )
    rom = ROOT / (
        "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
        "-patched_orbs_roomcharge_nodarkness_berryboost.nds"
    )

    if not sav.is_file():
        raise SystemExit(f"save not found: {sav}")
    data = sav.read_bytes()
    print(f"Save: {sav.name}")
    print(f"Size: {len(data)} bytes")
    if len(data) == 0:
        raise SystemExit("Save file is empty — copy a real .sav from DeSmuME/your emulator.")

    orb_names = load_orb_names(rom)
    hits = scan_struct_items(data, orb_names)
    if not hits:
        print("No 6-byte orb item structs found (storage may use id-only slots in this save).")
        return

    by_name: dict[str, list[tuple[int, int, int, int]]] = {}
    for h in hits:
        by_name.setdefault(orb_names[h[1]], []).append(h)

    print(f"\nFound {len(hits)} orb struct slot(s):\n")
    print(f"{'Name':<18} {'ID':>4} {'[+2]':>6} {'use':>4} {'offset':>8}")
    print("-" * 46)
    for name in sorted(by_name):
        for off, iid, q, use in by_name[name]:
            print(f"{name:<18} {iid:4d} {q:6d} {use:4d} 0x{off:06X}")

    print("\nDuplicate offsets summary:")
    c = Counter(orb_names[h[1]] for h in hits)
    for name, n in sorted(c.items()):
        print(f"  {name}: {n} hit(s)")


if __name__ == "__main__":
    main()
