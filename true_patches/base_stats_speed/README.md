# base_stats_speed

Main-series base stats, evolution-line multipliers, and Speed on the
hit check. Combat and the team summary Stats tab read `CalcStat` instead
of the monster uint8 cache.

## Formula

Integer floor everywhere. No design cap; saturate only to int16 `0..32767`.

```
effective_base = base_stat + doping
staged_base    = floor(effective_base * percent / 100)
HP             = floor(staged_base * 2 * level / 100) + level + 10
other          = floor(staged_base * 2 * level / 100) + 5
```

Doping is added to the species base, then the multiplier and the level
formula run. It is not added at the end.

Save / team fields hold doping V, not the final stat:

| Field | V |
|-------|---|
| team `+0x10` / ground `+0xA` low byte | HP V |
| team `+0x11` / ground `+0x0B` | Spe V |
| team `+0x12..+0x15` / ground `+0xC..+0xF` / dungeon `+0x1A..+0x1D` | Atk SpA Def SpD V |

`CalcStat` r3 is that V, plus any exclusive-item amount for the
stat when the caller has a monster or summary boost cache. Exclusive
boosts are volatile doping only — they are never written into the save
V bytes. CalcDamage no longer adds exclusive offense/defense flats after
CalcStat; those bytes from monster `+0x224` / `+0x226` are already in r3.
Dungeon exclusive HP effects bake into CalcStat after ApplyExclusive and
come out of `+0x16` so other max-HP flats stay. Ground summary exclusive
HP uses the same r3 path instead of `max = current + excl`.
Dungeon `+0x12` is the real max HP from `CalcStat(HP, HP V [+ excl])`.
Wild spawn writes V=0. Level-up and evolution keep V. `InitTeamMember`
copies the four V bytes and writes CalcStat HP.

Exclusive boost table (`EXCLUSIVE_ITEM_STAT_BOOST_DATA`): type Silk/Dust
classes (1–4) set every nonzero Atk/Def/SpA/SpD boost to **15**. Every
remaining **3** in the table becomes **5** (Pokémon exclusives). Gems and
Globes are unchanged (effect-only, class 0).

This module always applies with `spinda_ev_speed` (not `spinda_ev_v2`).

`percent` is 100 / 115 / 138 from the evolution-line rate:

| Line | Unevolved | Middle | Final |
|------|-----------|--------|-------|
| No evolution (single form) | ×1.0 | — | — |
| Two forms | ×1.38 | — | ×1.0 |
| Three forms | ×1.38 | ×1.15 | ×1.0 |

Branching (Eevee, Slowpoke, Wurmple) uses the longest path through that
species. A pre-evolution cycle (Giratina's two forms) is not an evolution:
those links are dropped and both stay ×1.0.

Strong Enemy HP is the Pokémon Stats table value by default. Helping Ally
HP is this CalcStat result with no extra multiply. Charmander-placeholder
Strong Enemies (stats_entry 30 and `fixed_room_id >= 200`) set party-max
level and rewrite HP to `CalcStat×1.25` after `ApplyFixedRoomStats`; that
Alpha seat condition keeps them distinct from normal Strong Enemies.
In FR **200, 202, 206, 211, 214, 215, 217, 218, 219, 220, 221, 250**,
these entry-30 seats instead use `min(100, party-max + 5)` and
`CalcStat(species, that level, HP, V=0) × 2`. Party-max excludes guests.
This runs after fixed-room stat application, independently of dungeon level
scaling. Both current and maximum HP receive the result (cap 32767).
Other rooms retain party-max and HP ×1.25; other stats entries are unchanged.
Run `verify_fixed_scaling.py` to assemble a temporary fixture and check all
256 room IDs, level boundaries, guest exclusion, HP caps and register preservation.
Same Species ×3+ swarms (except FR41 / entry 30) and FR11/13/17/19/75
(except listed bosses) rewrite overlay10 table HP to
`CalcStat(species, table level)` after the level remap; FR51 Deoxys
entries 86–89 get table HP 500. Shared-entry HP conflicts defer to
`balance_change` append clones. Strong Enemy table levels are rewritten so
`CalcStat(L) Atk+Def+SpA+SpD` matches the table combat-stat sum.
Guest table levels 3/5/7-12/17 become 15/55/70/60/62/60/60/65/15, then
CalcStat rewrites those rows. Special-episode PC levels 1/6/8/9 become
20/72/70/24 (Igglybuff / Dusknoir / Grovyle / Armaldo). Deep Star Cave 1F Strong Enemy Snover
table level is 12 after the remap. Every floor's SkyTemple Kecleon
Level spawn entry in `BALANCE` and `UTILITY` `mappa_s.bin` / `mappa_t.bin`
/ `mappa_y.bin` is 100 (383/384/983/984).
`level_scaling_guest_fix` leaves those four IDs out of the Alpha spawn
rewrite and folds them in `GetMonsterLevelToSpawn`.

## Apply order

`FULL_STACK_MODULES` places this module after `better_equipment` and
before `balance_change`.

| Module | Relation |
|--------|----------|
| `better_equipment` | Apply first. Lens Scarf / Bright Ribbon / band stages patch the loads before this module's hit and damage hooks. |
| `damage_formula` | Different site in `CalcDamage`. This module writes A/D; that module uses the later base formula. |
| `spinda_ev_speed` | Apply after this module. Drink/temp V writers and snapshot restore. Do not apply `spinda_ev_v2` on the same ROM. |
| `balance_change` | Apply after. Outlaw / house HP ×2 runs on the HP this module wrote. That module still caps the doubled HP at 999. |

Unit apply:

```
python true_patches/base_stats_speed/apply.py
```

Writes `Export Rom/Unit_Test/Explorers of Alpha_Vanilla+base_stats_speed.nds`.

Do not put `korean` or `korean_assemble` in `FULL_STACK_MODULES`. Rebuild
the English or Korean full stack only when asked.

Hit check: one roll of SkyTemple **Accuracy** (`waza +0x0B`).
`floor(Accuracy × rank × (atkSpe/defSpe)^0.25)`.
The second `MoveHitCheck` (Miss Accuracy) returns hit.
Main-series moves use Gen 9 Accuracy (`true` → 125). Listed ROM-only
moves use `data/rom_accuracy_overrides.json`. The rest stay.

## What is hooked

- `MoveHitCheck` entry: one Accuracy roll
- Move hit rank, then × `(atkSpe/defSpe)^0.25`
- Normal spawn and level-up writers
- `CalcDamage` A/D and Download's Def vs SpD
- Dungeon `EvolveMonster`
- Fixed-room Strong Enemy (6) and Helping Ally (`0xA`)
- Team summary Stats tab: arm9 `0x0205A628` / `0x0205AE6C` and ov29
  `0x022F8A18` branch into the ov36 cave (`BaseStats_UiOff`), which calls the
  same `CalcStat` (no V suffix on the stats page) and writes Spe V into
  summary `+0x3D`. DrawWindowText ids are table index + 1. The arm9 file tail
  (from `0xDCD3C`) is inside the static BSS `0x020B3380`–`0x022BCA80` and is
  cleared at boot, so no code lives there.
- New-game / recruit / species-refresh write V=0 (HP/Spe halfword and the four uint8s)
- Guests start at V=0 and use `CalcStat` like the hero and partner. `level_scaling_guest_fix` keeps their table level out of the party-max rewrite so CalcStat is not run at the party's level. GuestMonsterToGroundMonster restores dest+0x14 so the learned-move bitset write does not clear the valid flag.
- Dungeon level-up stat lines: CalcStat(new) − CalcStat(saved old level), plus Spe. Spe digits overwrite the `[string:1]` tag in the format buffer (that tag copies 16-bit units, so ASCII itoa drew leftover bytes).
- Dungeon→team sync keeps the V halfword; it no longer copies real max HP onto team `+0x10`
- Dungeon `TryRecruit` stores 0 into team `+0x10` instead of summary max HP (HP|Spe V)
- Life Seed / Sitrus max-HP boost adds to HP V and rewrites dungeon `+0x12` from CalcStat
- Ground level-up keeps V (no vanilla m_level add)

## Left as-is

- Explorer Maze (`0xB`–`0xE`) saved records
- Alpha dungeon-wide tables for Zero Isle East / Realm of Perfection
- Ground Luminous Spring species change (ov36 is unloaded; next dungeon write refreshes)
- Top-screen LV/HP sprites, dungeon X-menu (HP only)
- Dungeon 3-digit number printers `0x0233C830`, `0x0233C9CC`
- `better_equipment` / `balance_change` / `damage_formula` leftover 999s
- Wonder Gummi / vitamin writers that still touch the uint8 cache
