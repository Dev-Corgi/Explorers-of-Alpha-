"""Patch selected Strong Enemy overlay10 HP fields to CalcStat(species, level).

Part of base_stats_speed (not spinda). Charmander-placeholder seats
(stats_entry 30 and fixed_room_id >= 200) stay on the ASM path in
BaseStats_FixedApply; this script leaves entry 30 alone.

Targets:
  - Same-species×3+ swarms from the Strong Enemy Same Species list, excluding
    Fixed Room 41 (Haunter) and Charmander L22 template (stats_entry 30).
  - Fixed Room 11 Strong Enemies except Wigglytuff.
  - Fixed Room 17 / 75 Strong Enemies except Regigigas.
  - Fixed Room 19 Strong Enemies except Darkrai.
  - Fixed Room 13 all Strong Enemies.
  - Fixed Room 51 Deoxys stats rows (entries 86-89): table HP = 500.

Boss Strong Enemies that share a floor with a same-species swarm but are not
themselves in that swarm are left alone. Shared-entry CalcStat HP conflicts
are deferred to balance_change (cartridge table append); in-table orphan
slots are never overwritten here.
"""

from __future__ import annotations

import re
import struct
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ndspy.rom import NintendoDSRom
from range_typed_integers import u8, u16
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import (
    get_binary_from_rom,
    get_ppmdu_config_for_rom,
    set_binary_in_rom,
)
from skytemple_files.dungeon_data.fixed_bin.model import EntityRule
from skytemple_files.hardcoded.fixed_floor import (
    HardcodedFixedFloorTables,
    MonsterSpawn,
    MonsterSpawnStats,
    MonsterSpawnType,
)

from true_patches.base_stats_speed.generate_tables import (
    GEN,
    N_PRIMARY,
    calc_stat_from_tables,
)

TAG_RE = re.compile(r"\[.*?\]")

# Same-species canvas UNIQUE_ROWS Fixed Room IDs, minus FR 41.
SAME_SPECIES_ROOMS = frozenset(
    {4, 9, 13, 28, 29, 32, 33, 34, 35, 37, 43, 67, 68, 69, 70, 73, 156, 158, 169}
)

# Extra fixed rooms: rewrite every Strong Enemy except named bosses.
EXTRA_ROOM_EXCLUDE: dict[int, frozenset[str]] = {
    11: frozenset({"Wigglytuff"}),
    13: frozenset(),
    17: frozenset({"Regigigas"}),
    19: frozenset({"Darkrai"}),
    75: frozenset({"Regigigas"}),
}

# Fixed Room 51 Deoxys Normal/Attack/Defense/Speed Strong Enemy table rows.
FR51_DEOXYS_STATS_ENTRIES = (86, 87, 88, 89)
FR51_DEOXYS_HP = 500

# In-table "orphan" slots (35/49/50/55/71) must not be overwritten for HP
# clones — several still have spawn-list owners (e.g. entry 35 = md 257), and
# the rest are reserved. Shared-entry CalcStat HP conflicts are deferred to
# balance_change, which appends independent rows on the expanded cartridge table.
CLONE_ENTRY_CANDIDATES: tuple[int, ...] = ()


def _plain(s: str) -> str:
    return TAG_RE.sub("", s).strip()


def _load_names(rom: NintendoDSRom, config) -> dict[int, str]:
    strings = FileType.STR.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"),
        string_encoding=config.string_encoding,
    )
    blocks = config.string_index_data.string_blocks
    base = blocks["Pokemon Names"].begin
    md = FileType.MD.deserialize(rom.getFileByName("BALANCE/monster.md"))
    primary_names: dict[int, str] = {}
    for i in range(min(600, len(md.entries))):
        primary_names[i] = (
            _plain(strings.strings[base + i])
            if (base + i) < len(strings.strings)
            else f"MD#{i}"
        )
    sprite_to_md: dict[int, int] = {}
    for i in range(1, min(600, len(md.entries))):
        spr = int(md.entries[i].sprite_index)
        sprite_to_md.setdefault(spr, i)
    names: dict[int, str] = {}
    for i, entry in enumerate(md.entries):
        if i < 600:
            names[i] = primary_names[i]
            continue
        resolved = None
        for key in ("md_index_base", "base_form_index"):
            b = int(getattr(entry, key))
            if 0 < b < 600 and primary_names.get(b):
                resolved = primary_names[b]
                break
        if not resolved:
            spr = int(entry.sprite_index)
            if spr in sprite_to_md:
                resolved = primary_names[sprite_to_md[spr]]
        names[i] = resolved or f"MD#{i}"
    return names


def _calc_hp(md_idx: int, level: int, primary: bytes, bases: bytes, rates: bytes) -> int:
    if md_idx * 2 + 2 > len(primary):
        raise ValueError(f"md_idx out of primary map: {md_idx}")
    pidx = struct.unpack_from("<H", primary, md_idx * 2)[0]
    if pidx >= N_PRIMARY:
        raise ValueError(f"primary index out of range for md {md_idx}: {pidx}")
    return calc_stat_from_tables(pidx, level, 0, 0, bases, rates)


def _floor_strong_placements(floor, entities, monsters) -> list[tuple[int, int, int]]:
    """Return (monster_spawn_id, md_idx, stats_entry) for Strong Enemy cells."""
    out: list[tuple[int, int, int]] = []
    for action in floor.actions:
        if not isinstance(action, EntityRule):
            continue
        eid = int(action.entity_rule_id)
        if not (0 <= eid < len(entities)):
            continue
        mid = int(entities[eid].monster_id)
        if not (0 <= mid < len(monsters)):
            continue
        spawn = monsters[mid]
        if spawn.enemy_settings != MonsterSpawnType.ENEMY_STRONG:
            continue
        out.append((mid, int(spawn.md_idx), int(spawn.stats_entry)))
    return out


def plan_strong_enemy_calcstat_hp(rom: NintendoDSRom) -> dict[str, Any]:
    """Collect (spawn, entry, md, level, new_hp) writes, cloning shared rows."""
    for name in ("primary.bin", "evo_rate.bin", "base_stats.bin"):
        if not (GEN / name).is_file():
            raise FileNotFoundError(f"missing CalcStat table {GEN / name}")
    primary = (GEN / "primary.bin").read_bytes()
    rates = (GEN / "evo_rate.bin").read_bytes()
    bases = (GEN / "base_stats.bin").read_bytes()

    config = get_ppmdu_config_for_rom(rom)
    ov29 = get_binary_from_rom(rom, config.bin_sections.overlay29)
    ov10 = get_binary_from_rom(rom, config.bin_sections.overlay10)
    monsters = HardcodedFixedFloorTables.get_monster_spawn_list(ov29, config)
    stat_rows = HardcodedFixedFloorTables.get_monster_spawn_stats_table(ov10, config)
    entities = HardcodedFixedFloorTables.get_entity_spawn_table(ov29, config)
    fixed = FileType.FIXED_BIN.deserialize(rom.getFileByName("BALANCE/fixed.bin"))
    names = _load_names(rom, config)

    # (spawn_id, md, name, entry, level, old_hp, new_hp, reason)
    targets: list[dict[str, Any]] = []
    seen_spawn_md: set[tuple[int, int]] = set()

    def add_target(fr: int, mid: int, md: int, entry: int, reason: str) -> None:
        key = (mid, md)
        if key in seen_spawn_md:
            return
        if entry == 30:
            return
        seen_spawn_md.add(key)
        st = stat_rows[entry]
        level = int(st.level)
        new_hp = _calc_hp(md, level, primary, bases, rates)
        targets.append(
            {
                "fixed_room": fr,
                "spawn_id": mid,
                "md_idx": md,
                "species": names.get(md, f"MD#{md}"),
                "entry": entry,
                "level": level,
                "old_hp": int(st.hp),
                "new_hp": new_hp,
                "reason": reason,
            }
        )

    for fr in sorted(SAME_SPECIES_ROOMS):
        if fr >= len(fixed.fixed_floors):
            continue
        placements = _floor_strong_placements(fixed.fixed_floors[fr], entities, monsters)
        by_md = Counter(md for _, md, _ in placements)
        for mid, md, entry in placements:
            if by_md[md] < 3:
                continue
            add_target(fr, mid, md, entry, "same_species")

    for fr, exclude in EXTRA_ROOM_EXCLUDE.items():
        if fr >= len(fixed.fixed_floors):
            continue
        placements = _floor_strong_placements(fixed.fixed_floors[fr], entities, monsters)
        for mid, md, entry in placements:
            name = names.get(md, f"MD#{md}")
            if name in exclude:
                continue
            add_target(fr, mid, md, entry, f"fixed_room_{fr}")

    # Desired HP per (entry, md). Detect shared-entry conflicts.
    by_entry: dict[int, dict[int, int]] = defaultdict(dict)
    for t in targets:
        by_entry[int(t["entry"])][int(t["md_idx"])] = int(t["new_hp"])

    clones: list[dict[str, Any]] = []
    spawn_retarget: dict[int, int] = {}  # spawn_id -> new entry
    deferred_clones: list[dict[str, Any]] = []
    # Never reuse in-table slots (including unused 55). Append happens later.
    free: list[int] = [
        e
        for e in CLONE_ENTRY_CANDIDATES
        if 0 <= e < len(stat_rows)
        and e not in {int(sp.stats_entry) for sp in monsters}
    ]

    for entry, md_hps in sorted(by_entry.items()):
        if len(md_hps) <= 1:
            continue
        # Keep the first md on the original entry; clone the rest when a free
        # in-table slot exists. Otherwise defer — balance_change appends.
        keep_md = sorted(md_hps.keys())[0]
        for md, hp in sorted(md_hps.items()):
            if md == keep_md:
                continue
            if not free:
                deferred_clones.append(
                    {
                        "from_entry": entry,
                        "md_idx": md,
                        "new_hp": hp,
                        "level": int(stat_rows[entry].level),
                    }
                )
                # Drop deferred md from HP targets so the shared row keeps keep_md HP.
                targets[:] = [
                    t
                    for t in targets
                    if not (int(t["entry"]) == entry and int(t["md_idx"]) == md)
                ]
                continue
            new_entry = free.pop(0)
            src = stat_rows[entry]
            clones.append(
                {
                    "from_entry": entry,
                    "to_entry": new_entry,
                    "md_idx": md,
                    "new_hp": hp,
                    "level": int(src.level),
                }
            )
            for t in targets:
                if int(t["entry"]) == entry and int(t["md_idx"]) == md:
                    t["entry"] = new_entry
                    t["cloned_from"] = entry
                    spawn_retarget[int(t["spawn_id"])] = new_entry

    # Final HP write per entry (after retarget). Must be unique.
    entry_hp: dict[int, int] = {}
    entry_meta: dict[int, dict[str, Any]] = {}
    for t in targets:
        entry = int(t["entry"])
        hp = int(t["new_hp"])
        if entry in entry_hp and entry_hp[entry] != hp:
            raise RuntimeError(
                f"entry {entry} still has conflicting HP {entry_hp[entry]} vs {hp}"
            )
        entry_hp[entry] = hp
        entry_meta[entry] = t

    return {
        "targets": targets,
        "clones": clones,
        "deferred_clones": deferred_clones,
        "spawn_retarget": spawn_retarget,
        "entry_hp": entry_hp,
        "entry_meta": entry_meta,
    }


def patch_strong_enemy_calcstat_hp_rom(rom: NintendoDSRom) -> dict[str, Any]:
    """Apply CalcStat HP writes (and clones) to overlay10 / ov29 spawn tables."""
    plan = plan_strong_enemy_calcstat_hp(rom)
    config = get_ppmdu_config_for_rom(rom)
    ov29 = bytearray(get_binary_from_rom(rom, config.bin_sections.overlay29))
    ov10 = bytearray(get_binary_from_rom(rom, config.bin_sections.overlay10))
    monsters = HardcodedFixedFloorTables.get_monster_spawn_list(ov29, config)
    stat_rows = HardcodedFixedFloorTables.get_monster_spawn_stats_table(ov10, config)

    for clone in plan["clones"]:
        src = stat_rows[int(clone["from_entry"])]
        dst = int(clone["to_entry"])
        stat_rows[dst] = MonsterSpawnStats(
            u16(int(src.level)),
            u16(int(clone["new_hp"])),
            u16(int(src.exp_yield)),
            u8(int(src.attack)),
            u8(int(src.special_attack)),
            u8(int(src.defense)),
            u8(int(src.special_defense)),
            u16(int(src.unkA)),
        )

    for spawn_id, new_entry in plan["spawn_retarget"].items():
        sp = monsters[int(spawn_id)]
        monsters[int(spawn_id)] = MonsterSpawn(
            sp.md_idx,
            u8(int(new_entry)),
            sp.enemy_settings,
        )

    hp_changed = 0
    for entry, hp in plan["entry_hp"].items():
        entry = int(entry)
        # Cloned rows already have new_hp; still set for clarity / non-clones.
        if int(stat_rows[entry].hp) != int(hp):
            stat_rows[entry].hp = u16(int(hp))
            hp_changed += 1
        else:
            # ensure typed write even if equal (clone path)
            stat_rows[entry].hp = u16(int(hp))

    # FR51 Deoxys: table HP only (entries 86/87/88/89).
    deoxys_writes: list[dict[str, Any]] = []
    for entry in FR51_DEOXYS_STATS_ENTRIES:
        old = int(stat_rows[entry].hp)
        if old != FR51_DEOXYS_HP:
            hp_changed += 1
        stat_rows[entry].hp = u16(FR51_DEOXYS_HP)
        deoxys_writes.append(
            {
                "entry": entry,
                "old_hp": old,
                "hp": FR51_DEOXYS_HP,
                "level": int(stat_rows[entry].level),
            }
        )

    HardcodedFixedFloorTables.set_monster_spawn_stats_table(ov10, stat_rows, config)
    HardcodedFixedFloorTables.set_monster_spawn_list(ov29, monsters, config)
    set_binary_in_rom(rom, config.bin_sections.overlay10, bytes(ov10))
    set_binary_in_rom(rom, config.bin_sections.overlay29, bytes(ov29))

    return {
        "hp_changed": hp_changed,
        "clone_count": len(plan["clones"]),
        "deferred_clone_count": len(plan.get("deferred_clones") or []),
        "target_count": len(plan["targets"]),
        "clones": plan["clones"],
        "deferred_clones": plan.get("deferred_clones") or [],
        "fr51_deoxys_hp": deoxys_writes,
        "writes": [
            {
                "entry": e,
                "hp": h,
                "species": plan["entry_meta"][e].get("species"),
                "level": plan["entry_meta"][e].get("level"),
                "old_hp": plan["entry_meta"][e].get("old_hp"),
            }
            for e, h in sorted(plan["entry_hp"].items())
        ],
    }
