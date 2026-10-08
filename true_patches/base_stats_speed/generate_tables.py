"""Build the phase-0 base stat and evolution-rate tables.

Main-series stats are the current default (and form) base stats, keyed by
national dex. Evolution rate is derived from monster.md pre-evolution links:

  no evolution            -> 1.0   (code 0)
  two-form line           -> 1.38 / 1.0 (code 2 / 0)
  three-or-more-form line -> 1.38 / 1.15 / 1.0 (code 2 / 1 / 0)

A pre-evolution cycle (Giratina's two forms point at each other) is not an
evolution line: those links are dropped and each form stays at 1.0.
"""

from __future__ import annotations

import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.str.handler import StrHandler

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
VANILLA = REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
FORMS_JSON = ROOT / "data" / "forms.json"
GEN = ROOT / "asm" / "generated"

N_PRIMARY = 600
N_ENTRIES = 1155
ENTRY = 68
PRIMARY_OFF = 0x400
RATE_OFF = PRIMARY_OFF + N_ENTRIES * 2
STATS_OFF = RATE_OFF + N_PRIMARY
SENTINEL_OFF = STATS_OFF + N_PRIMARY * 6
HIT_OFF = (SENTINEL_OFF + 4 + 3) & ~3
SPAWN_OFF = HIT_OFF + 0x80
COMBAT_OFF = SPAWN_OFF + 0x1C0
SPEED_OFF = COMBAT_OFF + 0x180
EVO_OFF = SPEED_OFF + 0x180
FIXED_OFF = EVO_OFF + 0x180
INIT_OFF = FIXED_OFF + 0x1A0
UI_OFF = INIT_OFF + 0xE0
CAVE_BYTES = 0x3000
HP_CAP = 32767

# ov29 / arm9 999 pools used as max-HP clamps (ldrsh/strh +0x10/+0x12/+0x16,
# or ground max_hp at +0xA). Loop/UI 999s are omitted.
OV29_HP_CAP_POOLS = (
    0x022E342C,
    0x022E3DD0,
    0x022EEEDC,
    0x022F5DAC,
    0x022F8FF0,
    0x022FB674,
    0x022FB838,
    0x022FB91C,
    0x022FD310,
    0x022FD9D0,
    0x02300814,
    0x023016A4,
    0x02301758,
    0x02302A30,
    0x02302BFC,
    0x02303274,
    0x023034C8,
    0x02309FD4,
    0x0230B7B8,
    0x0230BBA8,
    0x02310AB4,
    0x02311814,
    0x023152E0,
    0x023155F4,
    0x02318454,
    0x0231E8EC,
    0x02324020,
    0x02326400,
    0x02327644,
    0x02327E8C,
    0x02328008,
    0x02328070,
    0x023289F4,
    0x02329238,
    0x0232B364,
    0x0232B42C,
    0x0232C278,
    0x0232D734,
    0x0232DF30,
    0x0232E24C,
    0x0232E55C,
    0x02335F30,
)
ARM9_HP_CAP_POOLS = (
    0x020451A4,
    0x0205A058,
    0x020B662C,
)
# rsb rd, rn, #0x3E8 with rn=1 -> 997. Rewrite to #0x8000 -> 32767.
OV29_HP_CAP_RSB = (
    0x022E04FC,
    0x022FBE84,
    0x0234EE30,
)

# EoS / Alpha type ids. Fairy uses 18 in this ROM (Clefable, Sylveon).
TYPE_ID = {
    "Normal": 1,
    "Fire": 2,
    "Water": 3,
    "Grass": 4,
    "Electric": 5,
    "Ice": 6,
    "Fighting": 7,
    "Poison": 8,
    "Ground": 9,
    "Flying": 10,
    "Psychic": 11,
    "Bug": 12,
    "Rock": 13,
    "Ghost": 14,
    "Dragon": 15,
    "Dark": 16,
    "Steel": 17,
    "Fairy": 18,
}

# When several forms share a type, assign them in this order to the
# monster.md entries of that dex, lowest index first.
FORME_ORDER = [
    "",
    "Attack",
    "Defense",
    "Speed",
    "Origin",
    "Sky",
    "Sunny",
    "Rainy",
    "Snowy",
    "Plant",
    "Sandy",
    "Trash",
    "Alola",
    "Galar",
    "Hisui",
    "Paldea",
    "Primal",
]

# name -> rate code. Every monster.md entry with that name must match.
EXPECT_RATE = {
    "Bulbasaur": 2,
    "Ivysaur": 1,
    "Venusaur": 0,
    "Pichu": 2,
    "Pikachu": 1,
    "Raichu": 0,
    "Eevee": 2,
    "Vaporeon": 0,
    "Jolteon": 0,
    "Flareon": 0,
    "Tauros": 0,
    "Magikarp": 2,
    "Gyarados": 0,
    "Caterpie": 2,
    "Metapod": 1,
    "Butterfree": 0,
    "Wurmple": 2,
    "Silcoon": 1,
    "Cascoon": 1,
    "Beautifly": 0,
    "Dustox": 0,
    "Poliwag": 2,
    "Poliwhirl": 1,
    "Poliwrath": 0,
    "Politoed": 0,
    "Slowpoke": 2,
    "Slowbro": 0,
    "Slowking": 0,
    "Deoxys": 0,
    "Shaymin": 0,
    "Giratina": 0,
}


def _plain(raw: str) -> str:
    return re.sub(r"\[.*?\]", "", raw).strip()


def import_showdown(pokedex_ts: Path) -> None:
    text = pokedex_ts.read_text(encoding="utf-8")
    pat = re.compile(
        r'\n\t([a-z0-9]+): \{\n\t\tnum: (-?\d+),\n\t\tname: "([^"]+)",(.*?)\n\t\},',
        re.S,
    )
    forms = []
    for match in pat.finditer(text):
        num = int(match.group(2))
        body = match.group(4)
        stats_m = re.search(
            r"baseStats: \{ hp: (\d+), atk: (\d+), def: (\d+), spa: (\d+), spd: (\d+), spe: (\d+) \}",
            body,
        )
        types_m = re.search(r'types: \["([^"]+)"(?:, "([^"]+)")?\]', body)
        if num < 1 or not stats_m or not types_m:
            continue
        forme_m = re.search(r'forme: "([^"]+)"', body)
        type_ids = []
        for name in types_m.groups():
            if not name:
                continue
            type_ids.append(TYPE_ID.get(name, -1))
        stats = [int(x) for x in stats_m.groups()]
        forms.append(
            {
                "num": num,
                "forme": forme_m.group(1) if forme_m else "",
                "types": type_ids,
                "stats": stats,
            }
        )
    FORMS_JSON.parent.mkdir(parents=True, exist_ok=True)
    FORMS_JSON.write_text(json.dumps(forms, separators=(",", ":")), encoding="utf-8")
    print(f"forms {len(forms)} -> {FORMS_JSON}")


def _load_forms() -> dict[int, list[dict]]:
    rows = json.loads(FORMS_JSON.read_text(encoding="utf-8"))
    by_dex: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_dex[int(row["num"])].append(row)
    for dex, group in by_dex.items():
        group.sort(key=lambda row: FORME_ORDER.index(row["forme"]) if row["forme"] in FORME_ORDER else 100)
        by_dex[dex] = group
    return by_dex


def _entries(md: bytes) -> list[dict]:
    count = struct.unpack_from("<I", md, 4)[0]
    if count != N_ENTRIES:
        raise SystemExit(f"monster.md entries {count} != {N_ENTRIES}")
    rows = []
    for index in range(count):
        off = 8 + index * ENTRY
        dex = struct.unpack_from("<H", md, off + 4)[0]
        pre = struct.unpack_from("<H", md, off + 8)[0]
        base_form = struct.unpack_from("<H", md, off + 0x32)[0]
        rows.append(
            {
                "index": index,
                "dex": dex,
                "pre": pre,
                "base_form": base_form,
                "t1": md[off + 0x14],
                "t2": md[off + 0x15],
            }
        )
    return rows


def _type_set(t1: int, t2: int) -> frozenset[int]:
    out = {t1}
    if t2:
        out.add(t2)
    out.discard(0)
    return frozenset(out)


def _usable_form(form: dict) -> bool:
    forme = form["forme"]
    if forme.startswith("Mega") or forme.startswith("Gmax") or "Totem" in forme:
        return False
    return True


def _assign_stats(entries: list[dict], by_dex: dict[int, list[dict]]) -> tuple[bytearray, list[str]]:
    stats = bytearray(N_PRIMARY * 6)
    notes: list[str] = []
    used: dict[int, set[int]] = defaultdict(set)
    groups: dict[int, list[dict]] = defaultdict(list)
    for ent in entries[:N_PRIMARY]:
        groups[ent["dex"]].append(ent)
    for dex, group in groups.items():
        if dex == 0:
            continue
        forms = [form for form in (by_dex.get(dex) or []) if _usable_form(form)]
        if not forms:
            notes.append(f"no main-series stats for dex {dex} ({len(group)} entries)")
            continue
        base_index = next((i for i, form in enumerate(forms) if form["forme"] == ""), 0)
        for ent in group:
            want = _type_set(ent["t1"], ent["t2"])
            matches = [
                i
                for i, form in enumerate(forms)
                if i not in used[dex] and frozenset(t for t in form["types"] if t > 0) == want
            ]
            if matches:
                pick = matches[0]
            else:
                pick = base_index
                notes.append(f"md {ent['index']} dex {dex} type miss, used base")
            used[dex].add(pick)
            if forms[pick]["forme"]:
                notes.append(f"md {ent['index']} dex {dex} forme {forms[pick]['forme']}")
            blob = bytes(forms[pick]["stats"])
            if any(byte > 255 for byte in blob):
                raise SystemExit(f"stat > 255 at md {ent['index']}")
            stats[ent["index"] * 6 : ent["index"] * 6 + 6] = blob
    return stats, notes


def _evolution_rates(entries: list[dict]) -> bytearray:
    pre: dict[int, int] = {}
    for ent in entries[:N_PRIMARY]:
        parent = ent["pre"]
        if parent <= 0 or parent >= N_ENTRIES:
            pre[ent["index"]] = 0
            continue
        if parent >= N_PRIMARY:
            parent = entries[parent]["base_form"]
        if parent <= 0 or parent >= N_PRIMARY or parent == ent["index"]:
            pre[ent["index"]] = 0
        else:
            pre[ent["index"]] = parent

    for start in range(N_PRIMARY):
        seen: list[int] = []
        cur = start
        while cur and cur not in seen:
            seen.append(cur)
            cur = pre.get(cur, 0)
        if cur and cur in seen:
            for node in seen[seen.index(cur) :]:
                pre[node] = 0

    children: dict[int, list[int]] = defaultdict(list)
    for index, parent in pre.items():
        if parent:
            children[parent].append(index)

    def depth(index: int) -> int:
        seen: set[int] = set()
        steps = 0
        cur = index
        while pre.get(cur, 0) and pre[cur] not in seen:
            seen.add(cur)
            cur = pre[cur]
            steps += 1
            if steps > 8:
                break
        return steps

    def down(index: int, seen: set[int]) -> int:
        best = 0
        for child in children.get(index, []):
            if child in seen:
                continue
            best = max(best, 1 + down(child, seen | {child}))
        return best

    rates = bytearray(N_PRIMARY)
    for index in range(N_PRIMARY):
        if index == 0:
            continue
        stages = depth(index) + 1 + down(index, {index})
        slot = depth(index)
        if stages <= 1:
            rates[index] = 0
        elif stages == 2:
            rates[index] = 2 if slot == 0 else 0
        elif slot == 0:
            rates[index] = 2
        elif slot >= stages - 1:
            rates[index] = 0
        else:
            rates[index] = 1
    return rates


def _primary_table(entries: list[dict]) -> bytes:
    out = bytearray(N_ENTRIES * 2)
    for ent in entries:
        index = ent["index"]
        if index < N_PRIMARY:
            primary = index
        else:
            primary = ent["base_form"]
            if primary >= N_PRIMARY:
                primary = 0
        struct.pack_into("<H", out, index * 2, primary)
    return bytes(out)


def _check_rates(entries: list[dict], names: list[str], rates: bytes) -> None:
    by_name: dict[str, list[int]] = defaultdict(list)
    for ent in entries[:N_PRIMARY]:
        by_name[names[ent["index"]]].append(ent["index"])
    for name, code in EXPECT_RATE.items():
        indexes = by_name.get(name) or []
        if not indexes:
            raise SystemExit(f"missing species name {name}")
        bad = [i for i in indexes if rates[i] != code]
        if bad:
            raise SystemExit(f"{name} rate want {code} got {[(i, rates[i]) for i in bad]}")


def build(rom_path: Path = VANILLA) -> dict:
    if not FORMS_JSON.is_file():
        raise SystemExit(f"missing {FORMS_JSON}; run with --from-pokedex")
    rom = NintendoDSRom.fromFile(str(rom_path))
    md = rom.getFileByName("BALANCE/monster.md")
    entries = _entries(md)
    cfg = get_ppmdu_config_for_rom(rom)
    strings = StrHandler.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"), string_encoding=cfg.string_encoding
    )
    block = cfg.string_index_data.string_blocks["Pokemon Names"]
    names = [_plain(strings.strings[block.begin + i]) for i in range(N_PRIMARY)]
    stats, notes = _assign_stats(entries, _load_forms())
    rates = _evolution_rates(entries)
    _check_rates(entries, names, rates)
    primary = _primary_table(entries)
    if UI_OFF + 0x400 > CAVE_BYTES:
        raise SystemExit("summary UI does not fit in the cave")
    GEN.mkdir(parents=True, exist_ok=True)
    (GEN / "primary.bin").write_bytes(primary)
    (GEN / "evo_rate.bin").write_bytes(rates)
    (GEN / "base_stats.bin").write_bytes(stats)
    (GEN / "layout.inc").write_text(
        "\n".join(
            [
                "; Auto-generated by generate_tables.py",
                f".definelabel BaseStats_PrimaryOff, 0x{PRIMARY_OFF:X}",
                f".definelabel BaseStats_RateOff, 0x{RATE_OFF:X}",
                f".definelabel BaseStats_StatsOff, 0x{STATS_OFF:X}",
                f".definelabel BaseStats_SentinelOff, 0x{SENTINEL_OFF:X}",
                f".definelabel BaseStats_HitOff, 0x{HIT_OFF:X}",
                f".definelabel BaseStats_SpawnOff, 0x{SPAWN_OFF:X}",
                f".definelabel BaseStats_CombatOff, 0x{COMBAT_OFF:X}",
                f".definelabel BaseStats_SpeedOff, 0x{SPEED_OFF:X}",
                f".definelabel BaseStats_EvoOff, 0x{EVO_OFF:X}",
                f".definelabel BaseStats_FixedOff, 0x{FIXED_OFF:X}",
                f".definelabel BaseStats_InitOff, 0x{INIT_OFF:X}",
                f".definelabel BaseStats_UiOff, 0x{UI_OFF:X}",
                f".definelabel BaseStats_CaveBytes, 0x{CAVE_BYTES:X}",
                f".definelabel BaseStats_PrimaryCount, {N_ENTRIES}",
                f".definelabel BaseStats_SpeciesCount, {N_PRIMARY}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    counts = {0: 0, 1: 0, 2: 0}
    for code in rates:
        counts[code] = counts.get(code, 0) + 1
    summary = {
        "primary_off": PRIMARY_OFF,
        "rate_off": RATE_OFF,
        "stats_off": STATS_OFF,
        "sentinel_off": SENTINEL_OFF,
        "cave_bytes": CAVE_BYTES,
        "rate_counts": counts,
        "notes": notes,
    }
    (GEN / "hp_caps_ov29.inc").write_text(
        "\n".join(
            ["; ov29 MAX_HP_CAP / heal-HP 999 pools -> 32767"]
            + [f".org 0x{addr:08X}\n\t.word {HP_CAP}" for addr in OV29_HP_CAP_POOLS]
            + [""]
        ),
        encoding="utf-8",
    )
    (GEN / "hp_caps_arm9.inc").write_text(
        "\n".join(
            ["; arm9 HP 999 pools -> 32767"]
            + [f".org 0x{addr:08X}\n\t.word {HP_CAP}" for addr in ARM9_HP_CAP_POOLS]
            + [""]
        ),
        encoding="utf-8",
    )
    summary["hp_cap"] = HP_CAP
    summary["ov29_hp_cap_pools"] = [f"0x{a:08X}" for a in OV29_HP_CAP_POOLS]
    summary["arm9_hp_cap_pools"] = [f"0x{a:08X}" for a in ARM9_HP_CAP_POOLS]
    summary["ov29_hp_cap_rsb"] = [f"0x{a:08X}" for a in OV29_HP_CAP_RSB]
    (GEN / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        f"tables ok rates x1={counts[0]} x1.15={counts[1]} x1.38={counts[2]} notes={len(notes)}"
    )
    return summary


def patch_arm9_hp_caps(rom_path: Path) -> None:
    """Write 32767 over the arm9 HP-cap pools. ov29 pools are patched by armips."""
    from ndspy.rom import NintendoDSRom

    rom = NintendoDSRom.fromFile(str(rom_path))
    arm9 = bytearray(rom.arm9)
    for addr in ARM9_HP_CAP_POOLS:
        off = addr - 0x02000000
        old = struct.unpack_from("<I", arm9, off)[0]
        if old not in (999, HP_CAP):
            raise SystemExit(f"arm9 HP cap @ {addr:#x} is {old}, not 999/32767")
        struct.pack_into("<I", arm9, off, HP_CAP)
    rom.arm9 = bytes(arm9)
    rom.saveToFile(str(rom_path))


# NA EXCLUSIVE_ITEM_STAT_BOOST_DATA: 15 x (Atk, Def, SpA, SpD), then
# EXCLUSIVE_ITEM_EFFECT_DATA. We grow the boost table by 2 classes (8 B)
# into the gap before RECYCLE_SHOP and shift effect data forward.
EXCLUSIVE_STAT_BOOST_NA = 0x020980E8
EXCLUSIVE_EFFECT_DATA_NA = 0x02098124
EXCLUSIVE_EFFECT_COUNT = 956
EXCLUSIVE_TYPE_STAT_CLASSES = (1, 2, 3, 4)
# Pool sites that hold absolute pointers into these tables.
EXCLUSIVE_EFFECT_PTR_SITES = (0x02011164, 0x0201121C, 0x02011390)
EXCLUSIVE_EFFECT_INDEX_PTR_SITE = 0x02010F6C  # EFFECT_DATA + 1


def patch_exclusive_stat_boosts_rom(rom) -> dict:
    """Exclusive boost table: Silk/Dust nonzero→15; every 3→5.

    TYPE Silk/Dust use classes 1-4; each raised Atk/Def/SpA/SpD becomes 15.
    Every remaining 3 (Pokémon exclusives) becomes 5.

    Pokémon exclusives that shared classes 3-4 (Jewel of Life line, etc.)
    keep their old +10/+10 on new classes 15/16 after the table grows by two
    entries; effect-data pointers are shifted +8 to match.
    """
    from skytemple_files.data.item_s_p.handler import ItemSPHandler
    from skytemple_files.data.item_s_p.model import ItemSPExclusiveType

    arm9 = bytearray(rom.arm9)
    boost = EXCLUSIVE_STAT_BOOST_NA - 0x02000000
    effect = EXCLUSIVE_EFFECT_DATA_NA - 0x02000000
    before = bytes(arm9[boost : boost + 60])
    effect_bytes = bytes(arm9[effect : effect + EXCLUSIVE_EFFECT_COUNT * 2])

    # Grow table: 15 → 17 classes. Shift effect data +8.
    table = bytearray(arm9[boost : boost + 60])
    table.extend(bytes(8))
    # 3 → 5 on the original 15 classes.
    for i in range(60):
        if table[i] == 3:
            table[i] = 5
    # Preserve +10 patterns for Pokémon that shared Dust classes.
    table[15 * 4 : 16 * 4] = bytes([10, 0, 10, 0])
    table[16 * 4 : 17 * 4] = bytes([0, 10, 0, 10])
    # Silk / Dust classes → 15.
    for cls in EXCLUSIVE_TYPE_STAT_CLASSES:
        off = cls * 4
        for j in range(4):
            if table[off + j] != 0:
                table[off + j] = 15

    arm9[boost : boost + 68] = table
    new_effect = effect + 8
    arm9[new_effect : new_effect + len(effect_bytes)] = effect_bytes

    # Remap Pokémon exclusives off classes 3/4 onto 15/16.
    isp = ItemSPHandler.deserialize(rom.getFileByName("BALANCE/item_s_p.bin"))
    remapped = []
    for idx, entry in enumerate(isp.item_list):
        if entry.type.exclusive_to != ItemSPExclusiveType.MONSTER:
            continue
        cls_off = new_effect + idx * 2 + 1
        cls = arm9[cls_off]
        if cls == 3:
            arm9[cls_off] = 15
            remapped.append({"isp_index": idx, "was_class": 3, "now_class": 15})
        elif cls == 4:
            arm9[cls_off] = 16
            remapped.append({"isp_index": idx, "was_class": 4, "now_class": 16})

    # Pointers: effect base +8, index array (effect+1) +8.
    for site in EXCLUSIVE_EFFECT_PTR_SITES:
        off = site - 0x02000000
        old = struct.unpack_from("<I", arm9, off)[0]
        if old != EXCLUSIVE_EFFECT_DATA_NA:
            raise SystemExit(f"exclusive effect ptr @ {site:#x} is {old:#x}")
        struct.pack_into("<I", arm9, off, EXCLUSIVE_EFFECT_DATA_NA + 8)
    idx_off = EXCLUSIVE_EFFECT_INDEX_PTR_SITE - 0x02000000
    old_idx = struct.unpack_from("<I", arm9, idx_off)[0]
    if old_idx != EXCLUSIVE_EFFECT_DATA_NA + 1:
        raise SystemExit(f"exclusive index ptr unexpected {old_idx:#x}")
    struct.pack_into("<I", arm9, idx_off, EXCLUSIVE_EFFECT_DATA_NA + 9)

    after = bytes(arm9[boost : boost + 68])
    rom.arm9 = bytes(arm9)
    return {
        "changed": True,
        "classes": [list(after[i * 4 : i * 4 + 4]) for i in range(17)],
        "threes_to_five": sum(1 for a, b in zip(before, after) if a == 3 and b == 5),
        "type_class_bytes_to_15": sum(
            1
            for cls in EXCLUSIVE_TYPE_STAT_CLASSES
            for j in range(4)
            if before[cls * 4 + j] not in (0, 15) and after[cls * 4 + j] == 15
        ),
        "mon_remapped_to_keep_10": remapped,
        "effect_data_delta": 8,
    }


PERCENT = (100, 115, 138)
GUEST_LEVEL_OVERRIDES = {
    3: 15,
    5: 55,
    7: 70,
    8: 60,
    9: 62,
    10: 60,
    11: 60,
    12: 65,
    17: 15,
}
GUEST_LEVEL_OVERRIDE_POKE_ID = {
    7: 228,  # Dusknoir
}
SE_PC_LEVEL_OVERRIDES = {
    1: 20,  # Igglybuff
    6: 72,  # Dusknoir
    8: 70,  # Grovyle
    9: 24,  # Armaldo
}
SE_PC_LEVEL_OVERRIDE_POKE_ID = {
    1: 174,
    6: 228,
    8: 543,
    9: 376,
}
SNOVER_MD = (501, 1101)
DEEP_STAR_SNOVER_LEVEL = 12
DEEP_STAR_CAVE_NAME = "Deep Star Cave"
# Male 383, shiny male 384, female 983, shiny female 984.
# 983/984 are even-floor gender swaps and usually have no mappa row.
KECLEON_MD_INDEX = (383, 384, 983, 984)
KECLEON_LEVEL = 100
MAPPA_S = "BALANCE/mappa_s.bin"
# Alpha keeps BALANCE and UTILITY copies. t/y are Time/Darkness leftovers
# with their own Kecleon shop rows; SkyTemple can open any of these.
MAPPA_KECLEON_PATHS = (
    "BALANCE/mappa_s.bin",
    "BALANCE/mappa_t.bin",
    "BALANCE/mappa_y.bin",
    "UTILITY/mappa_s.bin",
    "UTILITY/mappa_t.bin",
    "UTILITY/mappa_y.bin",
)


def calc_stat_from_tables(
    primary: int, level: int, stat: int, doping: int, stats: bytes, rates: bytes
) -> int:
    base = stats[primary * 6 + stat]
    rate = rates[primary]
    effective = base + doping
    if effective < 0:
        effective = 0
    if effective > 32767:
        effective = 32767
    staged = (effective * PERCENT[rate]) // 100
    term = (staged * 2 * level) // 100
    result = term + level + 10 if stat == 0 else term + 5
    if result < 0:
        result = 0
    if result > 32767:
        result = 32767
    return result


def patch_guest_level_overrides_rom(rom: NintendoDSRom) -> list[dict]:
    """Write listed guest-table level fields only."""
    from range_typed_integers import u16
    from skytemple_files.common.util import (
        get_binary_from_rom,
        get_ppmdu_config_for_rom,
        set_binary_in_rom,
    )
    from skytemple_files.hardcoded.guest_pokemon import GuestPokemonList

    config = get_ppmdu_config_for_rom(rom)
    arm9 = bytearray(get_binary_from_rom(rom, config.bin_sections.arm9))
    guests = GuestPokemonList.read(bytes(arm9), config)
    edits: list[dict] = []
    for index, new_l in GUEST_LEVEL_OVERRIDES.items():
        if index < 0 or index >= len(guests):
            raise SystemExit(f"guest override id {index} out of range")
        guest = guests[index]
        if guest.is_null() or guest.poke_id <= 0:
            raise SystemExit(f"guest override id {index} is empty")
        want_md = GUEST_LEVEL_OVERRIDE_POKE_ID.get(index)
        if want_md is not None and int(guest.poke_id) != want_md:
            raise SystemExit(
                f"guest override id {index} poke_id {guest.poke_id}, want {want_md}"
            )
        old = int(guest.level)
        if old == new_l:
            edits.append(
                {"index": index, "poke_id": int(guest.poke_id), "old_level": old, "new_level": new_l}
            )
            continue
        guest.level = u16(new_l)
        edits.append(
            {"index": index, "poke_id": int(guest.poke_id), "old_level": old, "new_level": new_l}
        )
    if any(int(row["old_level"]) != int(row["new_level"]) for row in edits):
        GuestPokemonList.write(guests, arm9, config)
        set_binary_in_rom(rom, config.bin_sections.arm9, bytes(arm9))
    return edits


def patch_se_pc_level_overrides_rom(rom: NintendoDSRom) -> list[dict]:
    """Write listed special-episode PC table level fields only."""
    from range_typed_integers import u16
    from skytemple_files.common.util import (
        get_binary_from_rom,
        get_ppmdu_config_for_rom,
        set_binary_in_rom,
    )
    from skytemple_files.hardcoded.default_starters import HardcodedDefaultStarters

    config = get_ppmdu_config_for_rom(rom)
    arm9 = bytearray(get_binary_from_rom(rom, config.bin_sections.arm9))
    pcs = HardcodedDefaultStarters.get_special_episode_pcs(bytes(arm9), config)
    edits: list[dict] = []
    for index, new_l in SE_PC_LEVEL_OVERRIDES.items():
        if index < 0 or index >= len(pcs):
            raise SystemExit(f"SE PC override id {index} out of range")
        pc = pcs[index]
        want_md = SE_PC_LEVEL_OVERRIDE_POKE_ID.get(index)
        if want_md is not None and int(pc.poke_id) != want_md:
            raise SystemExit(
                f"SE PC override id {index} poke_id {pc.poke_id}, want {want_md}"
            )
        old = int(pc.level)
        if old != new_l:
            pc.level = u16(new_l)
        edits.append(
            {"index": index, "poke_id": int(pc.poke_id), "old_level": old, "new_level": new_l}
        )
    if any(int(row["old_level"]) != int(row["new_level"]) for row in edits):
        HardcodedDefaultStarters.set_special_episode_pcs(pcs, arm9, config)
        set_binary_in_rom(rom, config.bin_sections.arm9, bytes(arm9))
    return edits


def patch_guest_calcstat_rom(rom: NintendoDSRom) -> list[dict]:
    """Write CalcStat(V=0) into every guest table HP/Atk/SpA/Def/SpD/unk3(Spe)."""
    from skytemple_files.common.util import (
        get_binary_from_rom,
        get_ppmdu_config_for_rom,
        set_binary_in_rom,
    )
    from skytemple_files.hardcoded.guest_pokemon import GuestPokemonList

    primary = (GEN / "primary.bin").read_bytes()
    rates = (GEN / "evo_rate.bin").read_bytes()
    stats = (GEN / "base_stats.bin").read_bytes()
    config = get_ppmdu_config_for_rom(rom)
    arm9 = bytearray(get_binary_from_rom(rom, config.bin_sections.arm9))
    guests = GuestPokemonList.read(bytes(arm9), config)
    edits: list[dict] = []
    for i, g in enumerate(guests):
        if g.is_null() or g.poke_id <= 0 or g.level <= 0:
            continue
        md = int(g.poke_id)
        if md * 2 + 2 > len(primary):
            continue
        pidx = struct.unpack_from("<H", primary, md * 2)[0]
        if pidx >= N_PRIMARY:
            continue
        hp = calc_stat_from_tables(pidx, int(g.level), 0, 0, stats, rates)
        atk = calc_stat_from_tables(pidx, int(g.level), 1, 0, stats, rates)
        defense = calc_stat_from_tables(pidx, int(g.level), 2, 0, stats, rates)
        spa = calc_stat_from_tables(pidx, int(g.level), 3, 0, stats, rates)
        spd = calc_stat_from_tables(pidx, int(g.level), 4, 0, stats, rates)
        spe = min(calc_stat_from_tables(pidx, int(g.level), 5, 0, stats, rates), 255)
        atk = min(atk, 255)
        spa = min(spa, 255)
        defense = min(defense, 255)
        spd = min(spd, 255)
        was = [int(g.hp), int(g.atk), int(g.sp_atk), int(g.def_), int(g.sp_def), int(g.unk3)]
        now = [hp, atk, spa, defense, spd, spe]
        if was != now:
            g.hp = hp
            g.atk = atk
            g.sp_atk = spa
            g.def_ = defense
            g.sp_def = spd
            g.unk3 = spe
            edits.append({"index": i, "poke_id": md, "level": int(g.level), "was": was, "now": now})
    if edits:
        GuestPokemonList.write(guests, arm9, config)
        set_binary_in_rom(rom, config.bin_sections.arm9, bytes(arm9))
    return edits


def _combat_sum(pidx: int, level: int, stats: bytes, rates: bytes) -> int:
    total = 0
    for stat in (1, 2, 3, 4):
        total += min(calc_stat_from_tables(pidx, level, stat, 0, stats, rates), 255)
    return total


def _best_strong_level(
    pidx: int, target: int, orig: int, stats: bytes, rates: bytes
) -> int:
    best_l = 1
    best_diff = 10**9
    best_tie = 10**9
    for level in range(1, 101):
        got = _combat_sum(pidx, level, stats, rates)
        diff = abs(got - target)
        tie = abs(level - orig)
        if diff < best_diff or (diff == best_diff and tie < best_tie):
            best_l = level
            best_diff = diff
            best_tie = tie
    return best_l


def plan_strong_enemy_levels(rom: NintendoDSRom) -> list[dict]:
    """One overlay10 stats-row level per Strong Enemy stats_entry."""
    from skytemple_files.common.util import get_binary_from_rom, get_ppmdu_config_for_rom
    from skytemple_files.hardcoded.fixed_floor import (
        HardcodedFixedFloorTables,
        MonsterSpawnType,
    )

    primary = (GEN / "primary.bin").read_bytes()
    rates = (GEN / "evo_rate.bin").read_bytes()
    bases = (GEN / "base_stats.bin").read_bytes()
    config = get_ppmdu_config_for_rom(rom)
    ov29 = get_binary_from_rom(rom, config.bin_sections.overlay29)
    ov10 = get_binary_from_rom(rom, config.bin_sections.overlay10)
    monsters = HardcodedFixedFloorTables.get_monster_spawn_list(ov29, config)
    stat_rows = HardcodedFixedFloorTables.get_monster_spawn_stats_table(ov10, config)
    wanted: dict[int, list[int]] = defaultdict(list)
    old_level: dict[int, int] = {}
    for spawn in monsters:
        if spawn.enemy_settings != MonsterSpawnType.ENEMY_STRONG:
            continue
        md = int(spawn.md_idx)
        entry = int(spawn.stats_entry)
        if md * 2 + 2 > len(primary) or entry < 0 or entry >= len(stat_rows):
            continue
        pidx = struct.unpack_from("<H", primary, md * 2)[0]
        if pidx >= N_PRIMARY:
            continue
        st = stat_rows[entry]
        orig = int(st.level)
        target = (
            int(st.attack)
            + int(st.defense)
            + int(st.special_attack)
            + int(st.special_defense)
        )
        old_level[entry] = orig
        wanted[entry].append(_best_strong_level(pidx, target, orig, bases, rates))
    writes = []
    for entry, levels in sorted(wanted.items()):
        orig = old_level[entry]
        unique = sorted(set(levels))
        new_l = unique[0] if len(unique) == 1 else min(
            unique, key=lambda level: (abs(level - orig), level)
        )
        writes.append({"entry": entry, "old_level": orig, "new_level": new_l})
    return writes


def patch_strong_enemy_levels_rom(rom: NintendoDSRom) -> dict:
    """Overwrite Strong Enemy stats-table level fields with the matched L."""
    from range_typed_integers import u16
    from skytemple_files.common.util import (
        get_binary_from_rom,
        get_ppmdu_config_for_rom,
        set_binary_in_rom,
    )
    from skytemple_files.hardcoded.fixed_floor import HardcodedFixedFloorTables

    writes = plan_strong_enemy_levels(rom)
    config = get_ppmdu_config_for_rom(rom)
    ov10 = bytearray(get_binary_from_rom(rom, config.bin_sections.overlay10))
    stat_rows = HardcodedFixedFloorTables.get_monster_spawn_stats_table(ov10, config)
    changed = 0
    for row in writes:
        entry = int(row["entry"])
        new_l = int(row["new_level"])
        if int(stat_rows[entry].level) != new_l:
            stat_rows[entry].level = u16(new_l)
            changed += 1
    if changed:
        HardcodedFixedFloorTables.set_monster_spawn_stats_table(ov10, stat_rows, config)
        set_binary_in_rom(rom, config.bin_sections.overlay10, bytes(ov10))
    return {"writes": writes, "changed": changed}


def locate_deep_star_snover_entries(rom: NintendoDSRom) -> list[dict]:
    """Deep Star Cave 1F Strong Enemy Snover stats-table rows."""
    from skytemple_files.common.types.file_types import FileType
    from skytemple_files.common.util import get_binary_from_rom, get_ppmdu_config_for_rom
    from skytemple_files.dungeon_data.fixed_bin.model import EntityRule
    from skytemple_files.hardcoded.dungeons import HardcodedDungeons
    from skytemple_files.hardcoded.fixed_floor import (
        HardcodedFixedFloorTables,
        MonsterSpawnType,
    )

    config = get_ppmdu_config_for_rom(rom)
    arm9 = get_binary_from_rom(rom, config.bin_sections.arm9)
    ov29 = get_binary_from_rom(rom, config.bin_sections.overlay29)
    ov10 = get_binary_from_rom(rom, config.bin_sections.overlay10)
    defs = HardcodedDungeons.get_dungeon_list(arm9, config)
    names = config.dungeon_data.dungeons
    mappa = FileType.MAPPA_BIN.deserialize(rom.getFileByName("BALANCE/mappa_s.bin"))
    monsters = HardcodedFixedFloorTables.get_monster_spawn_list(ov29, config)
    stat_rows = HardcodedFixedFloorTables.get_monster_spawn_stats_table(ov10, config)
    entities = HardcodedFixedFloorTables.get_entity_spawn_table(ov29, config)
    fixed = FileType.FIXED_BIN.deserialize(rom.getFileByName("BALANCE/fixed.bin"))
    hits: list[dict] = []
    seen: set[int] = set()
    for dungeon_id, ddef in enumerate(defs):
        if names[dungeon_id].name != DEEP_STAR_CAVE_NAME:
            continue
        if int(ddef.number_floors) < 1:
            continue
        floor = mappa.floor_lists[int(ddef.mappa_index)][int(ddef.start_after)]
        ffid = int(floor.layout.fixed_floor_id)
        if ffid <= 0 or ffid >= len(fixed.fixed_floors):
            continue
        for action in fixed.fixed_floors[ffid].actions:
            if not isinstance(action, EntityRule):
                continue
            eid = int(action.entity_rule_id)
            if eid < 0 or eid >= len(entities):
                continue
            mid = int(entities[eid].monster_id)
            if mid < 0 or mid >= len(monsters):
                continue
            spawn = monsters[mid]
            if spawn.enemy_settings != MonsterSpawnType.ENEMY_STRONG:
                continue
            if int(spawn.md_idx) not in SNOVER_MD:
                continue
            entry = int(spawn.stats_entry)
            if entry < 0 or entry >= len(stat_rows) or entry in seen:
                continue
            seen.add(entry)
            hits.append(
                {
                    "dungeon": dungeon_id,
                    "ffid": ffid,
                    "entry": entry,
                    "md": int(spawn.md_idx),
                    "old_level": int(stat_rows[entry].level),
                }
            )
    return hits


def patch_deep_star_snover_level_rom(rom: NintendoDSRom) -> dict:
    """Overwrite Deep Star Cave 1F Strong Enemy Snover table level only."""
    from range_typed_integers import u16
    from skytemple_files.common.util import (
        get_binary_from_rom,
        get_ppmdu_config_for_rom,
        set_binary_in_rom,
    )
    from skytemple_files.hardcoded.fixed_floor import HardcodedFixedFloorTables

    hits = locate_deep_star_snover_entries(rom)
    if not hits:
        raise SystemExit("Deep Star Cave 1F Strong Enemy Snover missing")
    config = get_ppmdu_config_for_rom(rom)
    ov10 = bytearray(get_binary_from_rom(rom, config.bin_sections.overlay10))
    stat_rows = HardcodedFixedFloorTables.get_monster_spawn_stats_table(ov10, config)
    changed = 0
    writes = []
    for hit in hits:
        entry = int(hit["entry"])
        old = int(stat_rows[entry].level)
        if old != DEEP_STAR_SNOVER_LEVEL:
            stat_rows[entry].level = u16(DEEP_STAR_SNOVER_LEVEL)
            changed += 1
        writes.append(
            {
                "dungeon": int(hit["dungeon"]),
                "ffid": int(hit["ffid"]),
                "entry": entry,
                "md": int(hit["md"]),
                "old_level": old,
                "new_level": DEEP_STAR_SNOVER_LEVEL,
            }
        )
    if changed:
        HardcodedFixedFloorTables.set_monster_spawn_stats_table(ov10, stat_rows, config)
        set_binary_in_rom(rom, config.bin_sections.overlay10, bytes(ov10))
    return {"writes": writes, "changed": changed}


def _kecleon_monster_content_offsets(content: bytes, data_pointer: int) -> list[int]:
    """Content-relative starts of unique Kecleon spawn entries in unwrapped mappa."""
    from skytemple_files.common.util import read_u16, read_u32
    from skytemple_files.dungeon_data.mappa_bin._python_impl.model import (
        FLOOR_IDX_ENTRY_LEN,
        MappaBinReadContainer,
    )

    read = MappaBinReadContainer(content, data_pointer)
    empty = bytes(FLOOR_IDX_ENTRY_LEN)
    seen_lists: set[int] = set()
    offsets: list[int] = []
    for lut in range(read.dungeon_list_index_start, read.floor_layout_data_start, 4):
        pointer = read_u32(content, lut)
        if content[pointer : pointer + FLOOR_IDX_ENTRY_LEN] != empty:
            raise SystemExit("mappa floor list missing null floor")
        pointer += FLOOR_IDX_ENTRY_LEN
        while pointer <= read.dungeon_list_index_start - FLOOR_IDX_ENTRY_LEN:
            floor_data = content[pointer : pointer + FLOOR_IDX_ENTRY_LEN]
            if floor_data == empty:
                break
            monsters_idx = read_u16(content, pointer + 2)
            monster_ptr = read_u32(
                content, read.monster_spawn_list_index_start + 4 * monsters_idx
            )
            if monster_ptr not in seen_lists:
                seen_lists.add(monster_ptr)
                off = monster_ptr
                while True:
                    md = read_u16(content, off + 6)
                    if md == 0:
                        break
                    if md in KECLEON_MD_INDEX:
                        offsets.append(off)
                    off += 8
            pointer += FLOOR_IDX_ENTRY_LEN
    return offsets


def _count_kecleon_levels_in_file(data: bytes) -> dict[int, int]:
    from skytemple_files.common.util import read_u16
    from skytemple_files.container.sir0.handler import Sir0Handler
    from skytemple_files.dungeon_data.mappa_bin.protocol import LEVEL_MULTIPLIER

    sir0 = Sir0Handler.deserialize(data)
    levels: dict[int, int] = defaultdict(int)
    for off in _kecleon_monster_content_offsets(sir0.content, int(sir0.data_pointer)):
        stored = read_u16(sir0.content, off)
        levels[stored // LEVEL_MULTIPLIER] += 1
    return dict(sorted(levels.items()))


def count_kecleon_levels(rom: NintendoDSRom) -> dict:
    """Count SkyTemple Kecleon Level spawn entries in every Alpha mappa copy."""
    levels: dict[int, int] = defaultdict(int)
    per_file: dict[str, dict] = {}
    for path in MAPPA_KECLEON_PATHS:
        try:
            data = rom.getFileByName(path)
        except ValueError:
            continue
        file_levels = _count_kecleon_levels_in_file(data)
        per_file[path] = {
            "entries": sum(file_levels.values()),
            "levels": file_levels,
        }
        for level, count in file_levels.items():
            levels[level] += count
    return {
        "entries": sum(levels.values()),
        "levels": dict(sorted(levels.items())),
        "files": per_file,
    }


def patch_kecleon_levels_rom(rom: NintendoDSRom) -> dict:
    """Set every floor's SkyTemple Kecleon Level by rewriting only those u16s.

    FileType.MAPPA_BIN.serialize rebuilds SIR0 and drops Alpha layout. That
    shrinks mappa_s.bin and crashes on dungeon entry. BALANCE and UTILITY
    copies (s/t/y) are all written in place.
    """
    from range_typed_integers import u16
    from skytemple_files.common.util import read_u16, write_u16
    from skytemple_files.container.sir0 import HEADER_LEN
    from skytemple_files.container.sir0.handler import Sir0Handler
    from skytemple_files.dungeon_data.mappa_bin.protocol import LEVEL_MULTIPLIER

    want = KECLEON_LEVEL * LEVEL_MULTIPLIER
    changed = 0
    already = 0
    details: list[dict] = []
    for path in MAPPA_KECLEON_PATHS:
        try:
            raw = bytearray(rom.getFileByName(path))
        except ValueError:
            continue
        if raw[:4] != b"SIR0":
            raise SystemExit(f"{path} is not SIR0")
        sir0 = Sir0Handler.deserialize(bytes(raw))
        file_changed = 0
        file_already = 0
        for off in _kecleon_monster_content_offsets(
            sir0.content, int(sir0.data_pointer)
        ):
            file_off = HEADER_LEN + off
            old = read_u16(raw, file_off)
            if old == want:
                file_already += 1
                continue
            write_u16(raw, u16(want), file_off)
            file_changed += 1
        if file_changed:
            rom.setFileByName(path, bytes(raw))
        changed += file_changed
        already += file_already
        details.append(
            {
                "path": path,
                "changed": file_changed,
                "already": file_already,
                "entries": file_changed + file_already,
            }
        )
    if changed + already < 1:
        raise SystemExit("no Kecleon Level spawn entries")
    return {
        "files": details,
        "changed": changed,
        "already": already,
        "entries": changed + already,
        "new_level": KECLEON_LEVEL,
        "in_place": True,
    }


def main() -> None:
    if len(sys.argv) >= 3 and sys.argv[1] == "--from-pokedex":
        import_showdown(Path(sys.argv[2]))
        return
    rom = Path(sys.argv[1]) if len(sys.argv) >= 2 else VANILLA
    build(rom)


if __name__ == "__main__":
    main()
