# balance_change: natural recovery (v13)

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
