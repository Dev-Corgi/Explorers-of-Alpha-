#!/usr/bin/env python3
"""Survey move slots: learnset, hardcoded constants, binary refs, dummy stats."""

from __future__ import annotations

import struct
from collections import Counter
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom, read_u32

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)-patched.nds"

HARDCODED = {
    355: "REGULAR_ATTACK (0x163)",
    405: "PROJECTILE (0x195)",
    467: "JUDGMENT (0x1D3)",
    443: "PUNISHMENT (0x1BD)",
}


def main() -> None:
    with ROM.open("rb") as f:
        rom = NintendoDSRom(f.read())

    waza = FileType.WAZA_P.deserialize(rom.getFileByName("BALANCE/waza_p.bin"))
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))
    config = get_ppmdu_config_for_rom(rom)
    name_block = config.string_index_data.string_blocks["Move Names"]
    names = strings.strings[name_block.begin : name_block.end + 1]

    learnset_used: set[int] = set()
    for ls in waza.learnsets:
        for entry in ls.level_up_moves:
            learnset_used.add(int(entry.move_id))
        for mid in ls.tm_hm_moves:
            if mid:
                learnset_used.add(int(mid))
        for mid in ls.egg_moves:
            if mid:
                learnset_used.add(int(mid))

    table = loadOverlayTable(rom.arm9OverlayTable, lambda _id, _name: b"")
    regions: list[tuple[str, bytes]] = [("arm9", bytes(rom.arm9))]
    for ov_id in (10, 29, 30, 31):
        regions.append((f"ov{ov_id}", rom.files[table[ov_id].fileID]))

    hword_refs: Counter[int] = Counter()
    word_refs: Counter[int] = Counter()
    for _name, data in regions:
        for mid in range(len(waza.moves)):
            hword_refs[mid] += data.count(struct.pack("<H", mid))
            word_refs[mid] += data.count(struct.pack("<I", mid))

    # Read REGULAR_ATTACK constant from arm9
    reg_atk = read_u32(rom.arm9, 0x3021C)
    proj = read_u32(rom.arm9, 0x30E3C)

    print(f"Moves in waza_p: {len(waza.moves)}")
    print(f"Move name strings: {len(names)} (extra: {names[559:562]!r})")
    print(f"REGULAR_ATTACK constant in ROM: {reg_atk}")
    print(f"PROJECTILE constant in ROM: {proj}")
    print(f"In any learnset: {len(learnset_used)} ids")
    print(f"Not in learnset: {len(waza.moves) - len(learnset_used)} ids")
    print()

    rows: list[tuple[int, str, int, int, str]] = []
    for mid, move in enumerate(waza.moves):
        sr = move.settings_range
        flags: list[str] = []
        if mid not in learnset_used:
            flags.append("no-learnset")
        if mid in HARDCODED:
            flags.append(HARDCODED[mid])
        if sr.target == 15 or sr.range == 15:
            flags.append("invalid-range")
        if move.base_power == 0 and move.category == 2:
            flags.append("pow0-status")
        rows.append(
            (
                mid,
                names[mid] if mid < len(names) else "?",
                hword_refs[mid],
                word_refs[mid],
                ", ".join(flags) if flags else "learnset-only",
            )
        )

    no_ls = [r for r in rows if "no-learnset" in r[4]]
    print("=== Not in learnset (sorted by binary refs) ===")
    for mid, name, hw, wd, flags in sorted(no_ls, key=lambda r: (r[2] + r[3], r[0])):
        print(f"  {mid:3d} {name:18s}  hw={hw:4d} wd={wd:3d}  [{flags}]")

    print()
    print("=== Lowest total binary refs (all moves) ===")
    for mid, name, hw, wd, flags in sorted(rows, key=lambda r: (r[2] + r[3], r[0]))[:25]:
        print(f"  {mid:3d} {name:18s}  hw={hw:4d} wd={wd:3d}  [{flags}]")

    print()
    print("=== Invalid range 15/15 (typical unused table padding?) ===")
    invalid = [r for r in rows if "invalid-range" in r[4]]
    for mid, name, hw, wd, flags in invalid:
        print(f"  {mid:3d} {name:18s}  hw={hw:4d} wd={wd:3d}  [{flags}]")

    print()
    print("=== Move 0 (Nothing) ===")
    m0 = waza.moves[0]
    sr0 = m0.settings_range
    print(
        f"  pow={m0.base_power} type={m0.type} cat={m0.category} "
        f"tgt={sr0.target} rng={sr0.range} hw={hword_refs[0]} wd={word_refs[0]}"
    )


if __name__ == "__main__":
    main()
