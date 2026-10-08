# control_mode_enhance v14

Start on a regular member's manual turn selects that member as the auto leader.
Guests remain AI-controlled. `CeLeader` stays at cave+8 for `belly_union`; the
larger ov36 cave is allocated by the patch engine, never pinned in source.

## Fainting and floors

- The original leader is the regular member leading when the dungeon was entered,
  identified by active roster index. Start changes do not replace that identity.
- After reviver handling fails, a regular member's faint can continue the run if
  another regular member lives. A fainted leader passes leadership to the next
  living regular member in roster order, wrapping to the start. Nonleader fainting
  keeps the designated living leader. Guests cannot inherit or keep a run alive.
- The fainted member's active roster slot and equipment remain reserved; its
  dungeon entity is removed. Guest deaths keep vanilla escort/story behavior.
- Before the next floor initializes, reserved members are revived at full HP
  (maximum HP including HP boost) and death-time PP, including zero PP. Normal
  vanilla floor/spawn processing follows. There is no PP-refill suppression or
  post-spawn PP overwrite. The entry leader is selected in the active roster and
  rebound to the newly spawned entity on the new floor.
- When no living regular member remains, vanilla leader-loss handling runs even
  if living guests remain. It retains the normal dungeon failure behavior.

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
Z-gauge hook. No ROM is written. Full dungeon gameplay, in-game quicksave/resume,
and floor transitions still need an emulator integration test when a build is
requested.
