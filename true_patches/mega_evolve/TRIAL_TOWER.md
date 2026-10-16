# Trial Tower / 시련의 탑

Part of `mega_evolve` version 18, phase 6. No separate module or xdelta.

The input Alpha ROM uses all 180 ordinary dungeon definitions. Trial Tower uses
unused dungeon ID 234, a new mappa group appended at application time, and the
empty fixed-room slots 230–239. Installation rejects occupied slots or differing
BALANCE/UTILITY source banks. Native loaders use UTILITY; both banks are updated.
Zero Isle South (102), its original floors, and original rooms 21/77 stay intact.
All 99 floors and restrictions are copied; only the ten boss-floor references
change. The copied final floor remains the end of the dungeon.

The Spring controller unlocks the dungeon after a successful stage-1 Mega or
existing Primal/Origin awakening conversion. Menu entry, cancellation, failed
conversion, ordinary evolution, regression and Shiny conversion do not unlock it.
The normal saved dungeon-open/present/world-map bits hold the unlock. Previously
completed conversions cannot be inferred from a roster that may have regressed;
an older save unlocks on its next successful Spring Mega conversion.

Room slots 230–238 clone room 21; 239 clones room 77. All retain the native
exit-on-enemy-defeat property. Native enemy-objective processing waits for all
enemies in the room before requesting the next floor; floor 99 ends the run.
The original room-77 Palkia (551) and Dialga (552) seats stay as their existing
Alpha species. Only Darkrai (549) becomes Giratina (529).

`data/trial_tower.json` defines nine bosses, nine levels, and all eleven movesets.
Nine-way Fisher–Yates sampling uses the dungeon RNG. The permutation is shared by
sprite preloading and spawning, survives floor changes, and is stored in unused
MEK4 sidecar bytes 4888–4900 under its existing checksum. Loading rejects duplicate
or out-of-range entries. DungeonFree resets it. A fresh run draws a fresh order.

Species and level are chosen before SpawnMonster, so appearance, abilities and
initialization use the chosen species. After the existing Strong Enemy stats
application and V cleanup, only the specified level, current/max HP, IQ and moves
are assigned. Combat stats continue using the existing CalcStat implementation.
HP is CalcStat(species, level, HP, V=0) ×4 at floors 10–90 or ×2 at floor 99.
IQ is 999, the native Gummi cap; native UpdateIqSkills applies that species' skills.
Native InitMove initializes all four moves and their PP/AI flags. Slot 193 is
original Zap Cannon, named Tesla Cannon in Alpha; that existing slot is used.

The resident dungeon-query/name/menu helpers use a separately allocated ov36
cave, avoiding the dungeon heap dispatcher in ground mode. Original IDs retain
their native getter paths, including dojo definitions. Dungeon ID 234 is appended
only to the main departure list after unlock. Its map marker copies Zero Isle
South's location. The four unused dungeon-name slots alias new string index 19780
(message ID 19781) at the common string-file reader, covering direct copies and
StringFromId. Placeholder indices are not overwritten. Its exact English/Korean
pair is in `korean/data/translations.json.gz`.

Version 17 fixes the departure-menu owner pointer. The original instruction at
0x022FFE08 reads its literal from PC+8+0x58 (0x022FFE68), whose value is
0x02324D1C. Version 16 mistakenly used the preceding selector literal, 0x0238A080,
and also supplied it to the native epilogue. That could break the entire list
even while Trial Tower was locked. Installation now decodes the original load;
the constructor's actual allocation size also bounds the appended status row.
The unlock timing and existing saved open bits do not change.

Version 18 connects selection to the native Zero Isle South warning and
confirmation route. Cloning restriction data does not extend the hardcoded
special-dungeon checks at 0x0204F424/0x0204F4F8 or the warning selector at
0x022DDACC. Resident hooks add Trial Tower to those checks and map only the
warning selector to source ID 102 (SSB Case 26). Dungeon progress/open checks,
the selected ID, DUNGEON_SELECT/ENTER/ENTER_INDEX and dungeon_init retain ID 234.
The existing four warning messages and Yes/No choices are reused without
editing scripts or strings. Confirmation continues through the native entry
transition; cancellation follows the existing script exit.

Read-only verification (no full-stack build, ROM or save output):

```powershell
.venv/Scripts/python.exe -B -X utf8 -m true_patches.mega_evolve.verify_trial_tower
```

The fixture clones the base ROM in memory and verifies data and hook guards.
Compiled ARM checks cover all 81 boss/level combinations, HP, moves, IQ, sprite
selection, saved permutations, the complete phase-6 payload's linking/relocations
and RAM budget, original dungeon queries, name aliases, native victory objectives,
the original departure constructor through its real epilogue (including v16
failure reproduction), selection through native SSB Case dispatch, the ROM's
warning/Yes/No script routes, native entry with the selected ID preserved,
Trial Tower's own open/progress checks, and Spring success/exclusion cases.
The full payload compile uses the last completed Korean full-stack ROM as a
read-only fixture, so an interrupted English rebuild cannot supply partial data.
Engine file services,
CalcStat inputs, random numbers and selected UI services are modeled where noted
in the harness; this does not replace a playable emulator run after a requested
full-stack build.
