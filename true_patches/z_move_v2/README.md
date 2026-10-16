# z_move_v2: Selected move's damage category (v28)

Z-Moves now inherit the selected base move's physical/special category as well
as its type. Capture the category before replacing temporary slot 3, including
when the selected base move is itself in slot 3. Physical bases use Attack and
Defense; special bases use Special Attack and Special Defense. Status bases
retain the previous special-damage behavior.

The engine redirects overlay 29's calls to GetMoveCategory to a wrapper in the
allocated ov36 cave. This covers CalcDamage's stat selector and damage category
records, plus dungeon category checks such as screens and counters. The wrapper
only overrides move 559 while a Z-Move is pending; other moves and a shell queried
after cancellation/cleanup use the native category. ARM9's category function is
unchanged so it remains safe outside a dungeon. Re-application relocates existing
category calls when needed, and verification checks their destinations.

The command below now covers 144 member/slot/category/validation combinations,
all 22 native dungeon category calls, register preservation, and the native
damage stat selector. Balance-file category reads use fixtures. It also assembles
the complete module in memory to check its category export and cave bounds.
No full-stack build runs and no ROM is written. Module order and strings are
unchanged (LogMessageById continues to use the string index plus one).

## Selected member's Z-Move slot (v26)

The ov31 move submenu keeps the selected entity in r6 but the current leader's
status in r7. Saving r7 as ZMoveSelectedStatus made a partner Z-Move replace the
leader's fourth move while recording the partner as the pending restore owner.
Cleanup then copied the leader's backup into the partner and left move 559 in
the leader's moveset. Resolve the status from the selected entity at +0xB4 so
move typing, backup, temporary shell, action and restore use the same member.

```powershell
.venv\Scripts\python.exe -B true_patches\z_move_v2\verify_partner_slot.py
```

This test reads the canonical Alpha input ROM and assembles the actual selection,
setup and restore routines into a temporary fixture. It verifies the native
menu's leader-status register setup and runs native InitMove, GetTeamMemberIndex
and SetActionUseMovePlayer with Unicorn. UI append, type lookup, base PP lookup
and target validation use fixtures. It covers all four members, all four selected
move slots, validation success/failure, and cleanup's entity gate,
and reproduces the old leader-slot corruption. No ROM is written.

## HandleFaint argument preservation (v25)

The gauge wrapper runs GetTeamMemberIndex before replaying HandleFaint's
prologue. That native lookup overwrites r1-r3. The old wrapper preserved only
r4/LR, so source 604 (WENT_AWAY) became an entity address and the optional
context pointer in r2 became a roster index. The later control-mode source
filter therefore reserved a manually sent-home member as an ordinary faint.
This occurs without changing the selected leader.

Preserve r1-r4, r12 and LR around both gauge helpers, restore r0 to the victim,
and replay the original prologue unchanged. Gauge gains are unchanged.

```powershell
.venv\Scripts\python.exe -B true_patches\z_move_v2\verify_handle_faint.py
.venv\Scripts\python.exe -B true_patches\control_mode_enhance\verify_survival.py
```

The first test assembles the actual wrapper/gauge routine and executes native
GetTeamMemberIndex for 120 source/context/slot/gauge cases. It also reproduces
the old corruption. The second starts at the real send-home caller and follows
the entry hook/native argument capture, control-mode decision, native roster
cleanup and next-floor wrappers. UI, guild persistence and entity spawning use
fixtures. No ROM is written by these tests.
