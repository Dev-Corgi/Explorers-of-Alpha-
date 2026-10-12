# balance_change: natural recovery (v13)

## Ability names and effects (v15)

Workbook source: `포켓몬_특성_강화완성.xlsx`, E column (`불가사의`),
as supplied on 2026-10-12. F-column enhanced abilities are not applied here.
Ability IDs and species assignments stay unchanged.

English names are normalized in `patch_ability_names.py`, including descriptions
and messages in `MESSAGE/text_e.str`. Korean names and matching English/Korean
description pairs belong to `korean/data/translations.json.gz`. String counts
and indices remain unchanged; runtime message IDs still add one.

| Alpha ability | Official name | E-column effect |
| --- | --- | --- |
| Adaptate (24) | Adaptability | STAB x1.7; no Normal-to-secondary-type conversion |
| Sky Pact (142) | Gale Wings | Calculated Speed stage +2 at full HP; no Flying move repeats |
| Sound Waves (148) | Punk Rock | Sound move damage dealt x1.2, received x0.8 |
| Hubris (171) | Grim Neigh | Sp. Atk +1 after own attacking move defeats an enemy, once per action |
| Apex Aura (178) | Aura Break | Same-room Dark/Fairy Aura bonus becomes x0.8 damage, no stacking or Ground bonus |

The existing Adaptability ID 99 also uses STAB x1.7 so both IDs have the same
effect. Having both IDs does not apply the STAB multiplier twice. Grim Neigh
uses `UseMove` scope across repeated/linked move effects and restores nested
action context. Room checks inspect living monsters and use the existing
ability service, including suppression; hallways are not rooms.

Names with matching base functions: Royal Majesty -> Multiscale,
Healthy Body -> Clear Body, Solid Guard -> Filter, Marvel Veil -> Fur Coat,
Wonder Veil -> Ice Scales, Guiding Star -> Victory Star, Overload ->
Electromorphosis. Their effects are unchanged. Strong Jaws -> Strong Jaw
and Curious Medecine -> Curious Medicine correct English spelling.

Read-only validation (temporary assembly and in-memory ROM fixture):

```powershell
.venv\Scripts\python.exe -B true_patches\balance_change\verify_abilities.py
```

Checks actual ARM wrappers with engine services stubbed: HP boosts and Speed
clamping, both STAB IDs, sound attack/defense damage, room/type filtering,
suppression, non-stacking, kill source and multi-target/repeated action limits,
argument/stack preservation, stable indices, idempotence, Korean translation
matching, and runtime tags. It does not build a full stack or save a ROM.
Function signatures/layouts were cross-checked against
[pmdsky-debug](https://github.com/UsernameFodder/pmdsky-debug).

Heal Ribbon, Quick Healer, Wish recovery status, Rain Dish in rain, Dry Skin
in rain, and exclusive HP recovery effect 0x49 each independently halve the
current natural recovery denominator. Integer division rounds down. Apply
all active effects before clamping to 25..400. Heal Ribbon and Quick Healer
now stack instead of sharing one subtraction; multiple exclusive items with
one effect still enable that effect only once.

For a base denominator of 200: Heal Ribbon + Wish gives 50; adding Quick
Healer gives 25. Further bonuses cannot reduce it below 25. Existing base
regeneration and Fixed Room 6 scaling remain unchanged. Hail is not changed
here: the later bug_fixes module removes its old subtraction.

Validation (actual ARM recovery loop, helper calls stubbed):

```powershell
.venv\Scripts\python.exe -B true_patches\balance_change\verify_recovery.py --simulate
.venv\Scripts\python.exe -B true_patches\balance_change\verify_recovery.py
```

Simulation applies only the declared recovery instruction edits plus the
bug_fixes Hail NOP in memory to the baseline ROM. Default validation checks
both built full-stack ROMs, including the Hail NOP. Cases cover independent
and stacked effects, both ability slots, all relevant weather, odd division,
minimum clamping, and actual HP/accumulator updates. No ROM is saved by this
validator.

## Strong Enemy natural recovery (v14)

The existing monster behavior byte at +0xBC stores spawn behavior 6 for
Strong Enemy. At the original zero-regeneration-speed check, set the working
denominator to zero for that behavior and use the original recovery exit.
The natural recovery accumulator and HP stay unchanged, even with Wish,
Quick Healer, held/exclusive items, or rain abilities. Subsequent status
processing continues. Other behaviors, including Helping Ally (10), retain
v13 recovery. No new monster fields or persistent data are introduced.
