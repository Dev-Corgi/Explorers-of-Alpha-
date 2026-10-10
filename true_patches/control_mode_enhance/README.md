# control_mode_enhance v19

Start on a regular member's manual turn selects that member as the auto leader.
Guests remain AI-controlled. `CeLeader` stays at cave+8 for `belly_union`; the
larger ov36 cave is allocated by the patch engine, never pinned in source.

## Auto following

Auto returns to ExecuteRound's vanilla ally phase, including its batched deferred
movement retries ordered by distance from the leader. The earlier per-member
immediate retry could run the rear follower before the intervening teammate had
moved, producing repeated blocked steps in narrow passages. Manual keeps the
wrapping party scan; auto movement uses vanilla ordering.

Selecting the auto leader synchronizes both entity leader flags and active-roster
leader flags. It does this even if manual control already made that entity the
engine's temporary leader. The old early return only updated `CeLeader` and left
the active-roster leader stale. A change to the designated leader marks the
existing dungeon refresh flag so the normal refresh path recomputes team state.
No terrain-traversal permissions or pathfinding algorithms are changed.

## Fainting and floors

- The current living leader remains selected across floors and dungeon exits.
  Start changes and active-roster reordering do not force a return to the
  dungeon-entry leader. The saved entry identity is retained only for death
  bookkeeping and diagnostics.
- After reviver handling fails, a regular member's faint can continue the run if
  another regular member lives. A fainted leader passes leadership to the next
  living regular member in roster order, wrapping to the start. Nonleader fainting
  keeps the designated living leader. Guests cannot inherit or keep a run alive.
- The fainted member's active roster slot and equipment remain reserved; its
  dungeon entity is removed. Guest deaths keep vanilla escort/story behavior.
- Members explicitly sent back to the guild use vanilla removal and are not
  reserved or revived on the next floor. The send-home action calls
  `HandleFaint` at `0x022F5ED8` with damage source `604` (`WENT_AWAY`), passed
  through `r9` at this module's hook. That source bypasses faint reservation.
  v20 also synchronizes the designated living leader before vanilla cleanup:
  a manual actor's temporary `monster+7` leader flag otherwise makes vanilla
  retain its active roster with flag 8 instead of clearing it. The departing
  member becomes a nonleader; if the designated leader itself departs, a living
  regular successor is selected. With no regular survivor, vanilla exit rules
  remain. Pending revival records for only that guild identity are cancelled.
- Before the next floor initializes, reserved members are revived at full HP
  (maximum HP including HP boost) and death-time PP, including zero PP. Normal
  vanilla floor/spawn processing follows. There is no PP-refill suppression or
  post-spawn PP overwrite. The current living leader is kept and synchronized
  to the newly spawned entity.
- Death-time HP/PP backups are allocated separately and keyed by guild member
  identity, so moving a successor into a dead member's former slot cannot
  overwrite that dead member's backup.
- RunDungeon's shared exit at `0x022E026C` preserves the current leader before
  final team export/free on clear, escape, and defeat. The exit path does not
  revive HP, refill PP, or change the result.
- When no living regular member remains, vanilla leader-loss handling runs even
  if living guests remain. It retains the normal dungeon failure behavior.

The performance flag that normally unlocks Chimecho Assembly leader selection at
graduation is forced on in the main game, so the player can select the desired
leader after returning to town.

`HandleFaint`'s entry belongs to `z_move_v2`. This module hooks its later body at
the first leader-loss check, after the existing faint cleanup, preserving the
Z-gauge hook and the original function's stack epilogue.

## Recruitment and message

While any regular member is reserved as fainted, a successful vanilla recruitment
check is rejected with a message. Checks that would already fail do not produce
the warning or alter recruitment RNG. Direct `TryRecruit` calls are guarded too.
After revival the guard is cleared and normal recruiting resumes.

`strings.yaml` reserves zero-based text_e index **19299**, which is empty in both
full_stack languages. `LogMessageById` uses **19300**. Spinda's menu begins at
text_e index 19300 (code 19301). Application requires the slot to be empty and
fails instead of overwriting another patch's text. English:

> You can't recruit while a teammate
> is fainted.

The matching English/Korean pair is stored at index 19299 in
`true_patches/korean/data/translations.json.gz`:

> 쓰러진 동료가 있어
> 새 동료를 영입할 수 없다.

## Verification

```powershell
.venv\Scripts\python.exe -B true_patches\control_mode_enhance\verify_survival.py
```

The check assembles temporary binary fixtures and executes the actual ARM
handlers in Unicorn with stubbed game services. It checks 12 leader/guest
permutations, reordered entity slots, multiple deaths, guest-only loss,
HP/PP restoration before vanilla processing, entry-leader identity, recruitment
results/arguments, message-slot conflicts, Korean encoding and the unchanged
Z-gauge hook. It also checks leader-flag synchronization and the auto/manual
scan return ABI, send-home hook bypass with intact death backups, and ordinary
battle fainting through the hook. Next-floor tests execute the vanilla active-roster cleanup for send-home
removal before running the real restoration/spawn wrappers. No ROM is written.
Full dungeon gameplay, in-game quicksave/resume,
and floor transitions still need an emulator integration test when a build is
requested.


The send-home regression also reproduces vanilla's temporary-leader retention
(`active flags 3 -> 11`) before applying the fix. Six ordinary send-home cases
and sixteen manual-actor cases execute actual roster cleanup and the next-floor
wrappers, with guild persistence, sprite/UI services, and spawning supplied by
the fixture. They retain unrelated death backups, the designated leader, and
normal battle-faint revival. Validation writes no ROM.


The send-home integration test also covers the Z-Move entry wrapper before
this module's hook. z_move_v2 v25 is required: older wrappers corrupt source
604 during native GetTeamMemberIndex, so even a nonleader is treated as a
battle faint. The fixture demonstrates reproduction without any leader change,
then verifies removal with the fixed wrapper and normal battle-faint revival.
