"""Split shared Strong Enemy stats rows and match levels via CalcStat.

Stores the expanded table in a reserved overlay36 cave that is loaded into RAM.
Overlay10 ends immediately before overlay29 and cannot be extended. Redirects ApplyFixedRoomStats' table
literal and Alpha's entry-30 absolute addresses to the new table.

For each listed species group that shared a stats_entry: keep one species on
the original row, clone the row for the others, retarget ov29 spawns, then
set each row's level so CalcStat Atk+Def+SpA+SpD matches the table combat
sum (HP and Spe excluded). Keep-row HP bytes are left unchanged; newly
appended clone rows get CalcStat HP for their species at the matched level.

Entries 35 and 55 are restored to vanilla Alpha bytes and never left holding
split-group species (spinda used to park Regidrago/Registeel there).
"""

from __future__ import annotations

import struct
from collections import defaultdict
from typing import Any

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import (
    create_file_in_rom,
    get_binary_from_rom,
    get_ppmdu_config_for_rom,
)
from range_typed_integers import u8
from skytemple_files.hardcoded.fixed_floor import (
    HardcodedFixedFloorTables,
    MonsterSpawn,
    MonsterSpawnType,
)

from true_patches.base_stats_speed.generate_tables import (
    GEN,
    N_PRIMARY,
    _best_strong_level,
    calc_stat_from_tables,
)
from patch_engine.overlay_caves import get_rom_binary, write_rom_binary
from patch_engine.cave_gap import file_offset_after_cave
from patch_engine.cave_reservations import FileRange, reserved_file_ranges
from patch_engine.ov36_layout import (
    allocate_ov36_cave, OV36_CAVE_CHAIN_FILE, OV36_CAVE_HOLE_END_FILE,
)
from patch_engine.state import AppliedModule, BuildState, CaveAllocation

STATS_TABLE_RAM = 0x022C5938
STATS_LITERAL_RAM = 0x022FBF04  # ov29: ldr pool for ApplyFixedRoomStats
ENTRY_SIZE = 12
ENTRY_30_RAM = STATS_TABLE_RAM + 30 * ENTRY_SIZE  # 0x022C5AA0
OV29_LOAD = 0x022DC240
OV36_LOAD = 0x023A7080
N_PRIMARY_ROWS = 99
ENTRY_30_LITERAL_SITES = (0x023A9F90, 0x023D7FAC, 0x023D854C)

# Species that must not share a Strong Enemy stats_entry with each other.
SPLIT_GROUPS: tuple[frozenset[int], ...] = (
    frozenset({549, 1130}),  # Darkrai · Cresselia
    frozenset({7, 537}),  # Squirtle · Arceus
    frozenset({381, 421}),  # Marshadow · Deoxys (Speed)
    frozenset({110, 139, 169}),  # Weezing · Omastar · Crobat
    frozenset({151, 535, 1017}),  # Mew · Shaymin · Jirachi
    frozenset({330, 411}),  # Sableye · Registeel
    frozenset({538, 539}),  # Regieleki · Regidrago
)

# Prefer these mds to keep the original stats_entry when splitting a group.
KEEP_PREFERRED = frozenset({549, 7, 421, 110, 151, 330, 538})

# Vanilla Alpha overlay10 stats rows — restore after migrating split species off.
# Entry 35 is owned by md 257 in the spawn list; 55 is unused but reserved.
VANILLA_RESTORE_ENTRIES: dict[int, bytes] = {
    35: bytes.fromhex("50008a02000073733c3c0000"),
    55: bytes.fromhex("6400e7030000d2e6b4b40000"),
}

# base_stats_speed defers distinct CalcStat HP for these when they share a
# keep-row; append clones therefore need a species HP write. Other split
# clones keep the table HP from the shared row.
CALCSTAT_HP_CLONE_MDS = frozenset({411, 539})  # Registeel · Regidrago


def _primary_index(md_idx: int, primary: bytes) -> int:
    if md_idx * 2 + 2 > len(primary):
        raise ValueError(f"md_idx out of range: {md_idx}")
    return struct.unpack_from("<H", primary, md_idx * 2)[0]


def _row_combat_sum(row: bytes) -> int:
    return row[6] + row[8] + row[7] + row[9]  # atk, def, spa, spd


def _set_level(row: bytearray, level: int) -> None:
    struct.pack_into("<H", row, 0, level & 0xFFFF)


def _get_level(row: bytes) -> int:
    return struct.unpack_from("<H", row, 0)[0]


def _set_hp(row: bytearray, hp: int) -> None:
    struct.pack_into("<H", row, 2, hp & 0xFFFF)


def _clone_spawn_to_append(
    rows: list[bytearray],
    monsters: list,
    spawn_i: int,
    src_entry: int,
    md: int,
    clones: list[dict[str, Any]],
    reason: str,
) -> int:
    new_entry = len(rows)
    if new_entry > 255:
        raise RuntimeError("stats_entry u8 exhausted")
    rows.append(bytearray(rows[src_entry]))
    monsters[spawn_i] = MonsterSpawn(
        monsters[spawn_i].md_idx,
        u8(new_entry),
        monsters[spawn_i].enemy_settings,
    )
    clones.append(
        {
            "md": md,
            "from_entry": src_entry,
            "to_entry": new_entry,
            "spawn": spawn_i,
            "reason": reason,
        }
    )
    return new_entry


def patch_se_entry_split_and_levels(
    rom: NintendoDSRom, *, state: BuildState | None, record: AppliedModule,
) -> dict[str, Any]:
    for name in ("primary.bin", "base_stats.bin", "evo_rate.bin"):
        if not (GEN / name).is_file():
            raise FileNotFoundError(f"missing CalcStat table {GEN / name}")
    primary = (GEN / "primary.bin").read_bytes()
    bases = (GEN / "base_stats.bin").read_bytes()
    rates = (GEN / "evo_rate.bin").read_bytes()

    config = get_ppmdu_config_for_rom(rom)
    ov10 = bytearray(get_binary_from_rom(rom, config.bin_sections.overlay10))
    ov29 = bytearray(get_rom_binary(rom, "ov29"))
    ov36 = bytearray(get_rom_binary(rom, "ov36"))
    old_lit = struct.unpack_from("<I", ov29, STATS_LITERAL_RAM - OV29_LOAD)[0]
    if old_lit != STATS_TABLE_RAM:
        raise RuntimeError(
            f"SE table already relocated to {old_lit:#x}; rebuild the stack from the Alpha base ROM"
        )

    stat_rows = HardcodedFixedFloorTables.get_monster_spawn_stats_table(ov10, config)
    monsters = list(HardcodedFixedFloorTables.get_monster_spawn_list(ov29, config))

    # Working copy of every row as 12 raw bytes (starts at 99).
    rows: list[bytearray] = [bytearray(st.to_bytes()) for st in stat_rows]
    if len(rows) != N_PRIMARY_ROWS:
        raise RuntimeError(f"expected {N_PRIMARY_ROWS} stats rows, got {len(rows)}")

    target_mds = set().union(*SPLIT_GROUPS)
    clones: list[dict[str, Any]] = []
    hp_writes: list[dict[str, Any]] = []

    for group in SPLIT_GROUPS:
        # Map entry -> {md: spawn_id} for Strong Enemy spawns in this group.
        while True:
            by_entry: dict[int, dict[int, int]] = defaultdict(dict)
            for spawn_i, sp in enumerate(monsters):
                if sp.enemy_settings != MonsterSpawnType.ENEMY_STRONG:
                    continue
                md = int(sp.md_idx)
                if md not in group:
                    continue
                entry = int(sp.stats_entry)
                by_entry[entry][md] = spawn_i
            shared = [(e, mds) for e, mds in by_entry.items() if len(mds) > 1]
            if not shared:
                break
            entry, mds = shared[0]
            keep_md = next(
                (m for m in sorted(mds.keys()) if m in KEEP_PREFERRED),
                sorted(mds.keys())[0],
            )
            for md in sorted(mds.keys()):
                if md == keep_md:
                    continue
                spawn_i = mds[md]
                new_entry = _clone_spawn_to_append(
                    rows, monsters, spawn_i, entry, md, clones, "shared_split"
                )
                clones[-1]["keep_md"] = keep_md
                _ = new_entry

    # Migrate split-group species off reserved vanilla slots onto append indices.
    for spawn_i, sp in enumerate(monsters):
        if sp.enemy_settings != MonsterSpawnType.ENEMY_STRONG:
            continue
        md = int(sp.md_idx)
        if md not in target_mds:
            continue
        entry = int(sp.stats_entry)
        if entry not in VANILLA_RESTORE_ENTRIES:
            continue
        _clone_spawn_to_append(
            rows, monsters, spawn_i, entry, md, clones, "vacate_restore"
        )

    # Restore reserved rows to vanilla Alpha (independent of who was parked there).
    restored: list[dict[str, Any]] = []
    for entry, vanilla in sorted(VANILLA_RESTORE_ENTRIES.items()):
        old = bytes(rows[entry])
        rows[entry] = bytearray(vanilla)
        restored.append(
            {
                "entry": entry,
                "old": old.hex(),
                "restored": vanilla.hex(),
                "changed": old != vanilla,
            }
        )

    # Level-match every row used by a target SE spawn.
    level_writes: list[dict[str, Any]] = []
    touched_entries: dict[int, int] = {}  # entry -> md (one representative)
    for spawn_i, sp in enumerate(monsters):
        if sp.enemy_settings != MonsterSpawnType.ENEMY_STRONG:
            continue
        md = int(sp.md_idx)
        if md not in target_mds:
            continue
        touched_entries[int(sp.stats_entry)] = md
    for entry, md in sorted(touched_entries.items()):
        pidx = _primary_index(md, primary)
        if pidx >= N_PRIMARY:
            continue
        row = rows[entry]
        target = _row_combat_sum(row)
        old_l = _get_level(row)
        new_l = _best_strong_level(pidx, target, old_l, bases, rates)
        if new_l != old_l:
            _set_level(row, new_l)
        level_writes.append(
            {
                "entry": entry,
                "md": md,
                "old_level": old_l,
                "new_level": new_l,
                "combat_sum": target,
            }
        )

    # Registeel/Regidrago clones inherited keep-row CalcStat HP; fix species HP.
    # Other append clones keep the shared table HP by design.
    for entry, md in sorted(touched_entries.items()):
        if md not in CALCSTAT_HP_CLONE_MDS:
            continue
        pidx = _primary_index(md, primary)
        if pidx >= N_PRIMARY:
            continue
        row = rows[entry]
        level = _get_level(row)
        new_hp = calc_stat_from_tables(pidx, level, 0, 0, bases, rates)
        old_hp = struct.unpack_from("<H", row, 2)[0]
        if new_hp != old_hp:
            _set_hp(row, new_hp)
        hp_writes.append(
            {
                "entry": entry,
                "md": md,
                "level": level,
                "old_hp": old_hp,
                "new_hp": new_hp,
            }
        )

    # The table must have a resident RAM allocation. Overlay10's BSS ends
    # exactly where overlay29 begins, so appending a file cannot provide one.
    table_blob = b"".join(bytes(r) for r in rows)
    reserved = reserved_file_ranges(state, "ov36", exclude_module=record.id)
    reserved.extend(
        FileRange(c.file_offset, file_offset_after_cave(c.file_offset, c.size))
        for c in record.caves if c.overlay == "ov36"
    )
    preferred = max(
        (r.end for r in reserved if OV36_CAVE_CHAIN_FILE <= r.start < OV36_CAVE_HOLE_END_FILE),
        default=OV36_CAVE_CHAIN_FILE,
    )
    slot, ov36 = allocate_ov36_cave(
        ov36, OV36_LOAD, len(table_blob),
        preferred_file_offset=preferred, reserved_file_offsets=reserved,
    )
    new_off, new_va = slot.file_offset, slot.load_address
    ov36[new_off:new_off + len(table_blob)] = table_blob
    record.caves.append(CaveAllocation("ov36", new_off, slot.size, new_va))

    # Redirect ApplyFixedRoomStats table base.
    lit_off = STATS_LITERAL_RAM - OV29_LOAD
    struct.pack_into("<I", ov29, lit_off, new_va)

    # Alpha Charmander rewrite hardcodes entry-30 absolute address.
    new_e30 = new_va + 30 * ENTRY_SIZE
    old_e30 = struct.pack("<I", ENTRY_30_RAM)
    new_e30_b = struct.pack("<I", new_e30)
    e30_patched = 0
    idx = 0
    while True:
        j = ov36.find(old_e30, idx)
        if j < 0:
            break
        ov36[j : j + 4] = new_e30_b
        e30_patched += 1
        idx = j + 4

    HardcodedFixedFloorTables.set_monster_spawn_list(ov29, monsters, config)
    write_rom_binary(rom, config, "ov29", bytes(ov29))
    write_rom_binary(rom, config, "ov36", bytes(ov36))

    # Mirror table as a named cartridge file for inspection / future loaders.
    try:
        create_file_in_rom(rom, "BALANCE/fr_mst.bin", table_blob)
        mirror = "BALANCE/fr_mst.bin"
    except Exception:
        try:
            rom.setFileByName("BALANCE/fr_mst.bin", table_blob)
            mirror = "BALANCE/fr_mst.bin"
        except Exception as exc:
            mirror = f"unavailable: {exc}"

    return {
        "se_entry_split": {
            "n_rows": len(rows),
            "storage_overlay": "ov36",
            "table_bytes": len(table_blob),
            "new_table_va": f"0x{new_va:X}",
            "new_table_file_off": f"0x{new_off:X}",
            "old_literal": f"0x{old_lit:X}",
            "e30_patched": e30_patched,
            "clones": clones,
            "level_writes": level_writes,
            "hp_writes": hp_writes,
            "restored_entries": restored,
            "mirror_file": mirror,
        }
    }


def verify_se_table_storage(rom: NintendoDSRom, record: AppliedModule) -> None:
    """Check the actual runtime bytes and reservation, not just the mirror file."""
    info = next((d["se_entry_split"] for d in record.data if "se_entry_split" in d), None)
    if info is None or info.get("storage_overlay") != "ov36":
        raise AssertionError("balance_change: SE table lacks a resident ov36 allocation")
    table = bytes(rom.getFileByName("BALANCE/fr_mst.bin"))
    overlays = rom.loadArm9Overlays()
    address = int(info["new_table_va"], 16)
    offset = address - overlays[36].ramAddress
    cave = next((c for c in record.caves if c.overlay == "ov36"
                 and c.load_address == address and c.file_offset == offset), None)
    if cave is None or cave.size < len(table):
        raise AssertionError("balance_change: SE table reservation missing or too small")
    if not (OV36_CAVE_CHAIN_FILE <= offset < offset + len(table) <= OV36_CAVE_HOLE_END_FILE):
        raise AssertionError("balance_change: SE table outside safe ov36 hole")
    if offset + len(table) > overlays[36].ramSize:
        raise AssertionError("balance_change: SE table is not in the loaded image")
    if len(table) != info["n_rows"] * ENTRY_SIZE or len(table) != info["table_bytes"]:
        raise AssertionError("balance_change: SE table size differs from build metadata")
    if bytes(overlays[36].data[offset:offset + len(table)]) != table:
        raise AssertionError("balance_change: resident SE table differs from cartridge mirror")
    literal = struct.unpack_from("<I", overlays[29].data, STATS_LITERAL_RAM - OV29_LOAD)[0]
    if literal != address:
        raise AssertionError("balance_change: ApplyFixedRoomStats points outside its SE table")
    for site in ENTRY_30_LITERAL_SITES:
        value = struct.unpack_from("<I", overlays[36].data, site - OV36_LOAD)[0]
        if value != address + 30 * ENTRY_SIZE:
            raise AssertionError(f"balance_change: entry30 pointer @ {site:#x} is stale")
    if len(overlays[10].data) != overlays[10].ramSize:
        raise AssertionError("balance_change: overlay10 file grew beyond its loaded image")
    if overlays[10].ramAddress + overlays[10].ramSize + overlays[10].bssSize > overlays[29].ramAddress:
        raise AssertionError("balance_change: overlay10 overlaps overlay29")
    for other in record.caves:
        if other is cave or other.overlay != "ov36":
            continue
        if offset < other.file_offset + other.size and other.file_offset < offset + len(table):
            raise AssertionError("balance_change: SE table overlaps its code cave")
