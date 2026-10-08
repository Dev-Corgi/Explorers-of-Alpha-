"""Check the cave bytes, spawn/level-up hooks, and print CalcStat samples."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

from true_patches.base_stats_speed.generate_tables import (
    ROOT,
    ARM9_HP_CAP_POOLS,
    COMBAT_OFF,
    GEN,
    HIT_OFF,
    HP_CAP,
    N_ENTRIES,
    N_PRIMARY,
    OV29_HP_CAP_POOLS,
    OV29_HP_CAP_RSB,
    PRIMARY_OFF,
    RATE_OFF,
    SENTINEL_OFF,
    SPAWN_OFF,
    SPEED_OFF,
    EVO_OFF,
    FIXED_OFF,
    INIT_OFF,
    STATS_OFF,
    UI_OFF,
    build,
)
from patch_engine.state import load_state

PERCENT = (100, 115, 138)
SAMPLES = (
    ("Bulbasaur", 0, 50, 0, "HP"),
    ("Pikachu", 0, 50, 0, "HP"),
    ("Pikachu", 0, 50, 10, "HP doping 10"),
    ("Eevee", 0, 20, 0, "HP"),
    ("Tauros", 0, 100, 0, "HP"),
    ("Raichu", 1, 100, 0, "Atk"),
    ("Magikarp", 5, 5, 0, "Spe"),
    ("Venusaur", 2, 100, 0, "Def"),
)


def isqrt(n: int) -> int:
    if n < 2:
        return n
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def rank_parts(acc_stage: int, eva_stage: int) -> tuple[int, int]:
    stage = acc_stage - eva_stage
    if stage >= 0:
        return stage + 3, 3
    return 3, 3 - stage


def rank_threshold(move_acc: int, acc_stage: int, eva_stage: int) -> int:
    num, den = rank_parts(acc_stage, eva_stage)
    return (move_acc * num) // den


def hit_threshold(
    move_acc: int, acc_stage: int, eva_stage: int, atk_spe: int, def_spe: int
) -> int:
    num, den = rank_parts(acc_stage, eva_stage)
    if atk_spe < 1:
        atk_spe = 1
    if def_spe < 1:
        def_spe = 1
    ratio = (atk_spe << 16) // def_spe
    if ratio < 1:
        ratio = 1
    fr = isqrt(isqrt(ratio))
    return (move_acc * num * fr) // (den * 16)


def calc(base: int, doping: int, rate: int, level: int, stat: int) -> int:
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


def verify(rom_path: Path, state_path: Path) -> None:
    state = load_state(state_path)
    mod = state.get_module("base_stats_speed")
    if mod is None or not mod.caves:
        raise SystemExit("base_stats_speed cave missing from state")
    cave = mod.caves[0]
    rom = NintendoDSRom(rom_path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov = rom.files[table[36].fileID]
    blob = bytes(ov[cave.file_offset : cave.file_offset + cave.size])
    primary = (GEN / "primary.bin").read_bytes()
    rates = (GEN / "evo_rate.bin").read_bytes()
    stats = (GEN / "base_stats.bin").read_bytes()
    if blob[PRIMARY_OFF : PRIMARY_OFF + len(primary)] != primary:
        raise SystemExit("primary table mismatch")
    if blob[RATE_OFF : RATE_OFF + len(rates)] != rates:
        raise SystemExit("evo rate table mismatch")
    if blob[STATS_OFF : STATS_OFF + len(stats)] != stats:
        raise SystemExit("base stat table mismatch")
    sentinel = struct.unpack_from("<I", blob, SENTINEL_OFF)[0]
    if sentinel != 0xB5A7E001:
        raise SystemExit(f"sentinel {sentinel:#x}")
    if blob[0:4] == b"\x00\x00\x00\x00":
        raise SystemExit("cave code empty")
    female_bulbasaur = struct.unpack_from("<H", primary, 601 * 2)[0]
    if female_bulbasaur != 1:
        raise SystemExit(f"gender map 601 -> {female_bulbasaur}")
    if blob[HIT_OFF : HIT_OFF + 4] == b"\x00\x00\x00\x00":
        raise SystemExit("hit-rank code empty")
    if blob[SPAWN_OFF : SPAWN_OFF + 4] == b"\x00\x00\x00\x00":
        raise SystemExit("spawn/level-up code empty")
    if blob[COMBAT_OFF : COMBAT_OFF + 4] == b"\x00\x00\x00\x00":
        raise SystemExit("combat code empty")
    if blob[SPEED_OFF : SPEED_OFF + 4] == b"\x00\x00\x00\x00":
        raise SystemExit("speed hit-rank code empty")
    if blob[EVO_OFF : EVO_OFF + 4] == b"\x00\x00\x00\x00":
        raise SystemExit("evolution code empty")
    if blob[FIXED_OFF : FIXED_OFF + 4] == b"\x00\x00\x00\x00":
        raise SystemExit("fixed-room Strong/Ally code empty")
    if blob[INIT_OFF : INIT_OFF + 4] == b"\x00\x00\x00\x00":
        raise SystemExit("InitTeamMember V helper empty")

    table29 = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = rom.files[table29[29].fileID]
    load29 = 0x022DC240
    spawn_sites = (
        ("SpawnHp", 0x022FE30C),
        ("SpawnAtk", 0x022FE368),
        ("SpawnDef", 0x022FE3D0),
        ("LevelUpStats", 0x02303160),
        ("LevelUpDeltasExp", 0x02302B3C),
        ("LevelUpDeltasJoy", 0x0230297C),
        ("CalcDamageAD", 0x0230C26C),
        ("CalcDamageDownload", 0x0230BDFC),
        ("EvolveMonster", 0x02303CF4),
        ("FixedRoomApply", 0x023438A4),
        ("InitTeamMemberHp", 0x022FD50C),
        ("TryIncreaseHpBoost", 0x023153C4),
        ("MoveHitOnce", 0x02323C48),
        ("MoveHitRank", 0x02323F94),
    )
    print("hooks")
    for name, site in spawn_sites:
        word = struct.unpack_from("<I", ov29, site - load29)[0]
        if (word >> 24) != 0xEA:
            raise SystemExit(f"{name} @ {site:#x} is {word:#010x}, not b")
        imm = word & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x01000000
        dest = site + 8 + (imm << 2)
        print(f"  {name} {site:#x} -> {dest:#x}")

    print("hp-cap")
    for addr in OV29_HP_CAP_POOLS:
        word = struct.unpack_from("<I", ov29, addr - load29)[0]
        if word != HP_CAP:
            raise SystemExit(f"ov29 HP cap @ {addr:#x} is {word}, not {HP_CAP}")
    print(f"  ov29 pools {len(OV29_HP_CAP_POOLS)} -> {HP_CAP}")
    arm9 = bytes(rom.arm9)
    for addr in ARM9_HP_CAP_POOLS:
        word = struct.unpack_from("<I", arm9, addr - 0x02000000)[0]
        if word != HP_CAP:
            raise SystemExit(f"arm9 HP cap @ {addr:#x} is {word}, not {HP_CAP}")
    print(f"  arm9 pools {len(ARM9_HP_CAP_POOLS)} -> {HP_CAP}")
    for addr in OV29_HP_CAP_RSB:
        word = struct.unpack_from("<I", ov29, addr - load29)[0]
        # rsb rd, rn, #0x8000
        if (word & 0x0FE00000) != 0x02600000:
            raise SystemExit(f"HP rsb @ {addr:#x} is {word:#010x}, not rsb imm")
        rot = (word >> 8) & 0xF
        imm8 = word & 0xFF
        # ARM expand: imm8 rotated right by 2*rot
        value = (imm8 >> (2 * rot) | (imm8 << (32 - 2 * rot))) & 0xFFFFFFFF if rot else imm8
        if value != 0x8000:
            raise SystemExit(f"HP rsb @ {addr:#x} imm {value:#x}, want 0x8000")
    print(f"  ov29 rsb {len(OV29_HP_CAP_RSB)} -> #0x8000")

    print("summary ui (ov36)")
    ui_sites = (
        ("SummaryStats", arm9, 0x02000000, 0x0205A628),
        ("SummaryHpFill", arm9, 0x02000000, 0x0205AE6C),
        ("DungeonSummaryLevel", ov29, load29, 0x022F8A18),
        ("GroundInitV", arm9, 0x02000000, 0x02052D20),
        ("GuestInitV", arm9, 0x02000000, 0x02052E74),
        ("InitMentryHpStore", arm9, 0x02000000, 0x020532D0),
        ("GroundRefreshV", arm9, 0x02000000, 0x02052F10),
        ("RecruitInitV", arm9, 0x02000000, 0x02055BB8),
        ("LevelUpSaveOld", ov29, load29, 0x0230308C),
        ("LevelUpSpeDigit", ov29, load29, 0x02302F24),
    )
    for name, data, load, site in ui_sites:
        word = struct.unpack_from("<I", data, site - load)[0]
        if (word >> 24) not in (0xEA, 0xEB):
            raise SystemExit(f"{name} @ {site:#x} is {word:#010x}, not b/bl")
        imm = word & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x01000000
        dest = site + 8 + (imm << 2)
        rel = dest - cave.load_address
        if not UI_OFF <= rel < cave.size:
            raise SystemExit(f"{name} -> {dest:#x} outside the ov36 UI block")
        if blob[rel : rel + 4] == b"\x00\x00\x00\x00":
            raise SystemExit(f"{name} target {dest:#x} is empty")
        print(f"  {name} {site:#x} -> {dest:#x}")
    nop = 0xE1A00000
    word = struct.unpack_from("<I", arm9, 0x02048B00 - 0x02000000)[0]
    if word != nop:
        raise SystemExit(f"RecruitHpOverwrite is {word:#010x}, not nop")
    word = struct.unpack_from("<I", ov29, 0x022FE068 - load29)[0]
    if word != nop:
        raise SystemExit(f"TeamSyncMaxHp is {word:#010x}, not nop")
    word = struct.unpack_from("<I", ov29, 0x0230E1B0 - load29)[0]
    if word != 0xE3A01000:  # mov r1, #0
        raise SystemExit(f"TryRecruitHpVStore is {word:#010x}, not mov r1,#0")
    word = struct.unpack_from("<I", arm9, 0x02054720 - 0x02000000)[0]
    if (word >> 24) != 0xEA:
        raise SystemExit(f"GroundLevelUpV is {word:#010x}, not b")
    print("  recruit HP overwrite nop, team max-HP sync nop, TryRecruit HP V=0, ground level-up skips V")

    from skytemple_files.common.util import get_ppmdu_config_for_rom
    from skytemple_files.data.str.handler import StrHandler

    cfg = get_ppmdu_config_for_rom(rom)
    strings = StrHandler.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"), string_encoding=cfg.string_encoding
    )
    hp_str = strings.strings[2387]
    if "[value:0:4]" not in hp_str or "[value:1:4]" not in hp_str:
        raise SystemExit(f"HP string width missing: {hp_str!r}")
    if "[CLUM_SET:96]" in hp_str:
        raise SystemExit(f"HP string still uses the overflowing column: {hp_str!r}")
    spe_str = strings.strings[19140]
    if "Spe:" not in spe_str or "[value:0" not in spe_str:
        raise SystemExit(f"Spe string missing: {spe_str!r}")
    atk_lbl = strings.strings[2388]
    spa_lbl = strings.strings[2389]
    if "Atk:" not in atk_lbl or "Def:" not in atk_lbl:
        raise SystemExit(f"Atk/Def labels missing: {atk_lbl!r}")
    if "SpA:" not in spa_lbl or "SpD:" not in spa_lbl:
        raise SystemExit(f"SpA/SpD labels missing: {spa_lbl!r}")
    if "Atk:" in spa_lbl:
        raise SystemExit(f"SpA/SpD string still has Atk: {spa_lbl!r}")
    print("  summary strings HP 4-digit + Spe + Atk/Def/SpA/SpD")
    lvl_str = strings.strings[3863]
    if "[digits_c:5]" in lvl_str:
        raise SystemExit(f"level-up Spe still uses digits_c:5: {lvl_str!r}")
    if "[string:1]" not in lvl_str:
        raise SystemExit(f"level-up Spe missing string:1: {lvl_str!r}")
    print("  level-up Spe uses string:1")

    from skytemple_files.common.util import read_u32
    from skytemple_files.container.sir0.handler import Sir0Handler
    from skytemple_files.data.waza_p._model import MOVE_ENTRY_BYTELEN
    from skytemple_files.data.waza_p.handler import WazaPHandler
    import skytemple_files.data.waza_p._model as waza_p_model

    raw = rom.getFileByName("BALANCE/waza_p.bin")
    sir0 = Sir0Handler.deserialize(raw)
    span = read_u32(sir0.content, sir0.data_pointer + 4) - read_u32(
        sir0.content, sir0.data_pointer
    )
    count, rem = divmod(span, MOVE_ENTRY_BYTELEN)
    if count < 1 or rem >= 16:
        raise SystemExit(f"waza move table is not aligned: span={span}")
    waza_p_model.MOVE_COUNT = count
    waza = WazaPHandler.deserialize(raw)
    gen9 = {
        int(k): int(v)
        for k, v in json.loads((ROOT / "data" / "gen9_accuracies_by_move_id.json").read_text(encoding="utf-8")).items()
    }
    leftover = json.loads((ROOT / "data" / "rom_only_accuracies.json").read_text(encoding="utf-8"))
    overrides = {
        int(k): int(v)
        for k, v in json.loads((ROOT / "data" / "rom_accuracy_overrides.json").read_text(encoding="utf-8")).items()
    }
    gen9.update(overrides)
    for mid, want in gen9.items():
        got = int(waza.moves[mid].accuracy)
        if got != want:
            raise SystemExit(f"move {mid} Accuracy {got}, want {want}")
    for row in leftover:
        mid = int(row["id"])
        want = int(row["accuracy"])
        got = int(waza.moves[mid].accuracy)
        if got != want:
            raise SystemExit(f"ROM-only move {mid} Accuracy {got}, want leftover {want}")
    print(f"  waza Accuracy {len(gen9)} leftover {len(leftover)}")

    from skytemple_files.hardcoded.guest_pokemon import GuestPokemonList
    from true_patches.base_stats_speed.generate_tables import calc_stat_from_tables

    guests = GuestPokemonList.read(arm9, cfg)
    print("guest CalcStat")
    guest_checked = 0
    for i, g in enumerate(guests):
        if g.is_null() or g.poke_id <= 0 or g.level <= 0:
            continue
        md = int(g.poke_id)
        if md * 2 + 2 > len(primary):
            continue
        pidx = struct.unpack_from("<H", primary, md * 2)[0]
        want_hp = calc_stat_from_tables(pidx, int(g.level), 0, 0, stats, rates)
        want_atk = min(calc_stat_from_tables(pidx, int(g.level), 1, 0, stats, rates), 255)
        want_def = min(calc_stat_from_tables(pidx, int(g.level), 2, 0, stats, rates), 255)
        want_spa = min(calc_stat_from_tables(pidx, int(g.level), 3, 0, stats, rates), 255)
        want_spd = min(calc_stat_from_tables(pidx, int(g.level), 4, 0, stats, rates), 255)
        want_spe = min(calc_stat_from_tables(pidx, int(g.level), 5, 0, stats, rates), 255)
        got = [int(g.hp), int(g.atk), int(g.sp_atk), int(g.def_), int(g.sp_def), int(g.unk3)]
        want = [want_hp, want_atk, want_spa, want_def, want_spd, want_spe]
        if got != want:
            raise SystemExit(f"guest {i} poke {md} lv {g.level}: {got} != {want}")
        guest_checked += 1
        if i == 3 and md == 501:
            print(f"  Snover guest[{i}] L{g.level} HP {want_hp} Atk {want_atk} Def {want_def} SpA {want_spa} SpD {want_spd} Spe {want_spe}")
    if guest_checked < 1:
        raise SystemExit("guest table empty")
    print(f"  {guest_checked} guest entries match CalcStat")

    from skytemple_files.hardcoded.default_starters import HardcodedDefaultStarters
    from true_patches.base_stats_speed.generate_tables import (
        DEEP_STAR_SNOVER_LEVEL,
        GUEST_LEVEL_OVERRIDES,
        GUEST_LEVEL_OVERRIDE_POKE_ID,
        KECLEON_LEVEL,
        SE_PC_LEVEL_OVERRIDES,
        SE_PC_LEVEL_OVERRIDE_POKE_ID,
        count_kecleon_levels,
        locate_deep_star_snover_entries,
        plan_strong_enemy_levels,
    )

    print("guest level overrides")
    for index, want in GUEST_LEVEL_OVERRIDES.items():
        got = int(guests[index].level)
        if got != want:
            raise SystemExit(f"guest {index} level {got}, want {want}")
        want_md = GUEST_LEVEL_OVERRIDE_POKE_ID.get(index)
        if want_md is not None and int(guests[index].poke_id) != want_md:
            raise SystemExit(
                f"guest {index} poke_id {guests[index].poke_id}, want {want_md}"
            )
        print(f"  guest[{index}] L{got}")

    print("SE PC level overrides")
    pcs = HardcodedDefaultStarters.get_special_episode_pcs(arm9, cfg)
    for index, want in SE_PC_LEVEL_OVERRIDES.items():
        pc = pcs[index]
        got = int(pc.level)
        if got != want:
            raise SystemExit(f"SE PC {index} level {got}, want {want}")
        want_md = SE_PC_LEVEL_OVERRIDE_POKE_ID.get(index)
        if want_md is not None and int(pc.poke_id) != want_md:
            raise SystemExit(f"SE PC {index} poke_id {pc.poke_id}, want {want_md}")
        print(f"  SE PC[{index}] poke {int(pc.poke_id)} L{got}")

    print("strong enemy levels")
    strong_writes = plan_strong_enemy_levels(rom)
    if not strong_writes:
        raise SystemExit("no Strong Enemy remaps to check")
    snover_hits = locate_deep_star_snover_entries(rom)
    if not snover_hits:
        raise SystemExit("Deep Star Cave 1F Strong Enemy Snover missing")
    snover_entries = {int(hit["entry"]) for hit in snover_hits}
    leftover = [
        row
        for row in strong_writes
        if row["old_level"] != row["new_level"] and int(row["entry"]) not in snover_entries
    ]
    if leftover:
        raise SystemExit(f"Strong Enemy levels not applied: {leftover[:3]}")
    for hit in snover_hits:
        got = int(hit["old_level"])
        if got != DEEP_STAR_SNOVER_LEVEL:
            raise SystemExit(
                f"Deep Star Cave 1F Snover entry {hit['entry']} level {got}, want {DEEP_STAR_SNOVER_LEVEL}"
            )
        print(f"  Deep Star Cave 1F Snover entry {hit['entry']} L{got}")
    print(f"  {len(strong_writes)} Strong Enemy stats rows already at matched L")

    print("kecleon levels")
    kecleon = count_kecleon_levels(rom)
    leftover = {
        level: count
        for level, count in kecleon["levels"].items()
        if int(level) != KECLEON_LEVEL
    }
    if kecleon["entries"] < 1:
        raise SystemExit("no Kecleon Level spawn entries")
    if leftover:
        raise SystemExit(f"Kecleon Level not 100: {leftover}")
    files = kecleon.get("files") or {}
    if len(files) < 1:
        raise SystemExit("no mappa files counted for Kecleon Level")
    for path, info in files.items():
        file_leftover = {
            level: count
            for level, count in info["levels"].items()
            if int(level) != KECLEON_LEVEL
        }
        if file_leftover:
            raise SystemExit(f"{path} Kecleon Level not 100: {file_leftover}")
        print(f"  {path}: {info['entries']} L{KECLEON_LEVEL}")
    print(f"  {kecleon['entries']} Kecleon spawn entries L{KECLEON_LEVEL}")

    block = cfg.string_index_data.string_blocks["Pokemon Names"]
    names = [strings.strings[block.begin + i] for i in range(N_PRIMARY)]
    expected = {
        (95, 10, 10): 95,
        (60, 12, 10): 100,
        (90, 10, 12): 54,
        (80, 12, 12): 80,
        (100, 10, 16): 33,
    }
    print("rank")
    for (move_acc, acc_stage, eva_stage), want in expected.items():
        got = rank_threshold(move_acc, acc_stage, eva_stage)
        if got != want:
            raise SystemExit(
                f"rank {move_acc} stages {acc_stage},{eva_stage}: {got} != {want}"
            )
        print(f"  acc={move_acc} stages {acc_stage - 10:+d}/{eva_stage - 10:+d} -> {got}")

    speed_cases = (
        (95, 10, 10, 100, 100, 95),
        (95, 10, 10, 200, 100, 112),
        (95, 10, 10, 50, 100, 77),
        (60, 12, 10, 100, 100, 100),
        (90, 10, 12, 100, 100, 54),
    )
    print("speed")
    for move_acc, acc_stage, eva_stage, atk_spe, def_spe, want in speed_cases:
        got = hit_threshold(move_acc, acc_stage, eva_stage, atk_spe, def_spe)
        if got != want:
            raise SystemExit(
                f"speed acc={move_acc} spe {atk_spe}/{def_spe}: {got} != {want}"
            )
        print(
            f"  acc={move_acc} stages {acc_stage - 10:+d}/{eva_stage - 10:+d} "
            f"spe {atk_spe}/{def_spe} -> {got}"
        )

    print("strong-hp")
    print("  Strong Enemy uses the table HP; Helping Ally uses CalcStat")

    print("samples")
    for name, stat, level, doping, label in SAMPLES:
        indexes = [i for i, mon in enumerate(names) if mon == name]
        if not indexes:
            raise SystemExit(f"sample species missing: {name}")
        index = indexes[0]
        base = stats[index * 6 + stat]
        rate = rates[index]
        value = calc(base, doping, rate, level, stat)
        print(
            f"  {name} md={index} {label} L{level} base={base} rate={rate} -> {value}"
        )
    summary = json.loads((GEN / "summary.json").read_text(encoding="utf-8"))
    counts = summary["rate_counts"]
    print(
        f"rates x1={counts['0']} x1.15={counts['1']} x1.38={counts['2']} "
        f"entries={N_ENTRIES}"
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    out = root / "PatchTesting" / "Export Rom" / "Unit_Test" / "Explorers of Alpha_Vanilla+base_stats_speed.nds"
    build()
    verify(out, out.with_suffix(".state.json"))
