# z_move_v2: HandleFaint argument preservation (v25)

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
