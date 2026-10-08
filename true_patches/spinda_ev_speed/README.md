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

## Snapshot

First-floor snapshot stores those V bytes. DungeonFree restore (group
outing end: escape / give-up / faint, or last group-floor clear) writes
the snapshot back with no m_level add. Outing protein / ribbon /
Wonder Gummi / Life Seed on those bytes drop off; Drink V stays.

Mid-outing saves (`GetMonsterInfoForSave`): live V is peeled aside, the
snapshot V is what goes into the save stream, then live V is restored in
RAM. Outing vitamins stay for the current session but do not pollute the
save. The snapshot itself is still RAM-only (lost on quit).

## Apply

```
python true_patches/spinda_ev_speed/apply.py
```

`FULL_STACK_MODULES` places this after `base_stats_speed`.

Strong Enemy table work (Charmander-placeholder seats, Same Species /
listed-FR CalcStat HP, FR51 Deoxys HP) lives in `base_stats_speed`, which
this stack always includes.
