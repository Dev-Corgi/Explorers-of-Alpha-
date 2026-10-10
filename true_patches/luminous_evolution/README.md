# luminous_evolution

Luminous Spring permits hero/partner evolution as soon as the graduation visit
opens the Spring. Normal level, IQ, move and evolution-item requirements still
apply. Ascend Stone Mark I/II requirements and scripted rewards are removed.
Alpha's direct Luxio/Luxray Stone requirements are restored to levels 15/30 in
both gender blocks. Old inventory Stones remain harmless relics.

The first visit preserves Teddiursa's evolution and the Spring introduction,
then opens the native evolution menu for the hero and partner only. Final forms,
unmet requirements and cancellation skip evolution. The warning about a space
distortion follows the menu regardless of whether either member evolved.
The scene uses both native `message_Menu(21)` and `message_Menu(22)`, including
the original appearance/actor result loop from `evolve.ssb`. Starting menu 21
alone does not wait for the controller to finish; the warning must wait until
menu 22 reports completion and the shop has closed its own windows. An empty
eligible list waits for the no-eligible notice to be acknowledged before closing.
Repeat warnings, bedroom recollections and the later mysterious-energy report
use matching English/Korean dialogue. The Gengar letter no longer promises a
Stone; its dialogue moves from Alpha's neutral constants into language strings
so the Korean translator can translate it.

The entry menu stays unchanged. After choosing a Pokemon, its state-14 submenu
shows optional `Evolve`, optional `Regression`, optional `Change Form`,
`Summary`, `Cancel`. Evolve is absent when no candidate meets the ordinary
requirements. Korean labels are `퇴화한다` and `폼변경`. Final forms remain
selectable for regression. Explicit form groups are Castform, Deoxys, Burmy,
Wormadam, Cherrim, Shaymin and Giratina. Form options have distinct localized
labels and use the native target selector, confirmation and appearance-change
sequence. Gender blocks are preserved where applicable. Form links/cycles do
not become regression targets. Sunshine Cherrim shares Cherubi as its previous
stage; Shedinja has an explicit Nincada regression relationship.

Every species change retains nickname, level, experience, moves, IQ, permanent
doping and the other saved record fields. Normal evolution updates the existing
two evolution-history level bytes; regression removes the latest history entry;
form changes preserve history. No evolution stat bonus is added. Existing
`base_stats_speed` summary and dungeon initialization calculate stats for the
new species from the retained doping values. The original Nincada-to-Ninjask
wrapper still creates Shedinja. Regression and form changes call the resident
species writer directly and cannot create Shedinja or increment evolution count.

## Placement and application

Apply after `base_stats_speed`/`spinda_ev_speed`, before `korean`; it is last in
`FULL_STACK_MODULES`. `patch_engine/apply_luminous_evolution.py` compiles the
runtime with `arm-none-eabi-gcc` and assembles hooks with armips. Code, tables and
scratch storage occupy an aligned, dynamically allocated extension of ov16.
Overlay metadata is updated, BSS/overlap checks are enforced, and no ov36 cave
or `team_push` reservation is used. ARM9 calls the shop-local eligibility helper
only from the Spring's mode-5 team-list path. The permanent record writer stays
resident in its original ARM9 function space.

Hook guards check the canonical Alpha instructions, complete record-writer
body, Stone requirements, script anchors and occupied message slots. Linker
state records the cave hash, hook words and writer hash for verification.
New `text_e` slots are 19700–19706 and 19710–19729; code passes index + 1.
Authored script indices are independent of `text_e` IDs. All authored text is
registered in `korean/data/translations.json.gz` with its exact edited English.

## Verification without building a ROM

Run from the repository root:

```powershell
.venv\Scripts\python.exe -B true_patches\luminous_evolution\verify.py
.venv\Scripts\python.exe -B true_patches\luminous_evolution\verify.py --integration
```

The first uses the canonical Alpha input. The second reads the existing English
full-stack output, verifying the installed module if already present or applying
it in memory otherwise. Neither writes an
NDS file or state file, or rebuilds the full stack. Temporary binaries and linker
files are outside the repository and are deleted after linking.

Checks execute the real ARM MD condition reader and evolution checker, the
compiled runtime, resident record writer, original Shedinja wrapper, native
target selector and native No/cancel dispatch. File, bag and graphical services
are supplied by the harness. Coverage includes Stone-free first/second
evolutions (including Shinx and its gender counterpart), ordinary requirements,
first-visit filtering/final forms, conditional menu rows, gender/branch
regression, localized form selection, record and doping preservation, Shedinja,
repeated changes, script branch relocation, story progress flags, reward removal
and Korean exact matching/tag safety. These are ARM execution and data checks,
not an emulator playthrough or a screen-layout certification.

The menu regression test enters through the native member-selection update,
not just direct calls to the replacement functions. It checks the unmodified
state-6 entry menu, conditional state-14 rows, native Summary/Cancel, actual
Regression/Change Form/Evolve dispatch, window-close delay, No/Yes confirmation
and the native conversion call site. The original state-6 and state-14 menus
look similar but use separate dispatchers; attaching member actions to state 6
would leave them appearing only after declining evolution and inert there.

First-visit checks also exercise the native no-eligible popup through actual
window closure, plus the script result loop for no change, repeated evolution
and appearance events. Level-63 Pikachu/Eevee fixtures demonstrate that ordinary
item conditions remain: without suitable items Pikachu can regress to Pichu,
while Eevee has no eligible action; a Thunderstone makes both eligible with
the Spring-unlock flag set and the late hero-evolution flag unset. No Ascend
Stone is needed, but levels alone do not replace their normal item conditions.

Full-stack building remains opt-in under the repository instructions. After a
requested rebuild, emulator QA should cover the first graduation scene, the
appearance-change sequence, saving/reloading and later story visits in EN/KO.
