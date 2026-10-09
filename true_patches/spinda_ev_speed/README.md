# spinda_ev_speed

Spinda Cafe EV for the `base_stats_speed` stack. Save / team stat
bytes are doping V. Drink and outing vitamins share those bytes.
`CalcStat` reads them as `r3`.

Always apply after `base_stats_speed`. Do not apply with `spinda_ev`
or `spinda_ev_v2`.

## V layout

| Field | Meaning |
|-------|---------|
| ground `+0xA` / team `+0x10` | HP V |
| ground `+0xB` / team `+0x11` | Spe V |
| ground `+0xC..+0xF` / team `+0x12..+0x15` | Atk SpA Def SpD V |

`EvFillBoosts` copies those bytes. Drink labels show `HP(V)` … `Spe(V)`.

Caps stay `floor(level/10)*5` per stat and `floor(level/10)*13` total,
now including Spe.

Reset writes the six V bytes to 0 (GroundAdd helpers floor at 1).
HP/Spe drinks add their V bytes with `GroundAddOffensiveStat` on the
cafe pointers (`r8-2` / `r8-1`), same helper as Atk. Do not use
`GroundAddMaxHp` (signed 16-bit add, 999 cap) — Spe V sits in that high
byte, so Spe 5 (halfword 1280) became HP 231 / Spe 3. Stat submenu
select remaps rows to Drink and must keep cafe state `r8`.
HP and Spe drinks append the same cafe line as Atk/SpA/Def/SpD:
`[name]'s [stat] rose [delta]!` (delta can be negative).

## Exclusive items

Type Silk/Dust: each raised Atk/Def/SpA/SpD boost is **15** (table
classes 1–4). Pokémon exclusives: any boost of **3** becomes **5**.
Amounts still enter CalcStat as volatile `r3` only (save V unchanged);
`base_stats_speed` owns the table + CalcStat path. Apply this module
after `base_stats_speed`.

## Move-info Accuracy stars

`SetStringAccuracy` reads SkyTemple Accuracy (`waza +0x0B`), the same
byte `MoveHitCheck` uses. One full star per 10 Accuracy; any leftover
remainder is one half star (`[M:R1]`, same tag as power stars).

Examples: 45 → 4 full + half; 72 → 7 full + half; 125 → 12 full + half.

The vanilla threshold table (`>= 101` → Always Hit) is gone. A move
that is not a coded sure-hit shows stars instead of Always Hit. A
numeric Accuracy, including 125, is always stars.

Z-Move (waza 559) still always hits. After `base_stats_speed` the
rank/Spe formula can make a 100 Accuracy move miss; this module
appends on `MoveHitRankApply` so 559 skips that roll. Protect, Whiffer,
and the other `MoveHitCheck` exits still apply.

Floor Gravity (Gravity Orb or the Gravity move) multiplies Accuracy
by 5/3 on that roll, same as the main series: hit when
`roll < floor(Accuracy × 5/3 × rank × (atkSpe/defSpe)^0.25)`.
Integer floor. Z-Move still skips the roll. The Accuracy>100 sure-hit
exit already ran, so a 90 that becomes 150 still goes through rank/Spe.

## Save schema v1

RAM V remains permanent + temporary doping for CalcStat. Temporary doping
is recorded separately for all 555 guild roster IDs, not active slots or
leader identity. Dungeon vitamins, gummis and HP boosts record the actual
clamped delta, including nested Wonder Gummi calls. Returning a member to
the guild keeps its temporary record until the outing ends. Recruitment
uses a vacant guild record (temporary V = 0). Release/sorting in town occurs
after group-end cleanup, when all temporary records are zero.

DungeonFree clears temporary V only on group completion, escape, defeat
or give-up. Intermediate floors and group segments do not reset it.
All guild records and all three active rosters are reconciled by member ID.
There is no initial-floor snapshot, save-time peel, or RAM restore afterward.

The stock 0xB65C-byte main save and its checksum stay unchanged in size.
Reserved header bytes +0x35..+0x37 contain `EV`, version 1. A separately
checksummed 3908-byte tail starts at slot +0xB700: magic `EVS1`, main checksum,
version/count, full permanent Speed for 555 guild + 4 maze records, then
six temporary bytes per guild member. Main + tail end at +0xC644, before
the next slot at +0xC800. Main slots begin at backup pages 0 and 200;
quicksave starts at page 400. One device write writes each main/tail pair.
A damaged/mismatched tail fails that slot and permits the stock backup path.
Unknown extension versions are rejected, never treated as an old save.

Stock monster serialization uses a stack copy containing permanent doping.
Its 10-bit HP width is retained, with Speed in that word cleared; the tail
preserves all 8 Speed bits. Saving never temporarily alters the live team.
The tail is loaded before monster decoding and applied afterward, before
normal active-member initialization. Quicksave writes its dungeon payload
and then NoteSaveBase, so both payloads retain the same outing doping.

Unmarked saves require an explicit choice: original Alpha zeros +0xA..+0xF
for every guild/maze monster and the corresponding active copies; existing
Alpha+ keeps the saved permanent doping. Level, experience, moves, IQ and
recruitment data are unchanged. The town updater coroutine asks once; an
old dungeon quicksave that skips it asks before the first playable leader
turn. An unresolved choice cannot be saved. Previously truncated Speed
bits and old RAM-only temporary snapshots cannot be recovered.

The schema leaves Alpha's 0xFF update mark and script VAR_VERSION intact.
Runtime state resides in dynamically allocated ARM9 cave RAM, outside
Alpha's item cache and independent of dungeon heap lifetimes. The build
requires arm-none-eabi-gcc (or ARM_GCC); it links at the allocated cave,
then emits the binary and labels only in a temporary directory.

Verification (no fullstack build or ROM output):

```powershell
.venv\Scripts\python.exe -B true_patches\spinda_ev_speed\verify_save.py
```

This executes the ARM codec in Unicorn with device I/O stubbed, checking
Speed boundaries, nested item gains, slot/leader changes, sent-home group
cleanup, legacy policies, corruption/backup and script jump relocation.
Actual dialogue and complete dungeon gameplay still require an emulator
integration check on a user-requested ROM build.

## Apply

```
python true_patches/spinda_ev_speed/apply.py
```

`FULL_STACK_MODULES` places this after `base_stats_speed`.

Strong Enemy table work (Charmander-placeholder seats, Same Species /
listed-FR CalcStat HP, FR51 Deoxys HP) lives in `base_stats_speed`, which
this stack always includes.
