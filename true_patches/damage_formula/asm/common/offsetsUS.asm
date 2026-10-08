; US Explorers of Sky / Alpha — damage_formula
ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

; Mid-CalcDamage: after A/D finalized at [sp,#0x90]/[sp,#0x94], before ln base.
.definelabel CalcDamageBaseFormula,       0x0230C984
; Resume at Fx64 clamp (max 999 / min 1) then type/crit/random path.
.definelabel CalcDamageAfterBaseFormula,  0x0230CB78

.definelabel IntToFx64,                    0x02001C80
.definelabel SoftDiv,                     0x0208FEA4
.definelabel SomeDungeonFlagCheck,        0x022E08CC
.definelabel InitMove,                    0x020137B8
.definelabel DealDamageProjectile,        0x02332C4C
; ApplyBlastSeedEffect → CalcDamageFixedNoCategory call sites (thrown / eat-front).
.definelabel BlastSeedFixedCallThrown,    0x0231D004
.definelabel BlastSeedFixedCallFront,     0x0231D09C
; DAMAGE_MULTIPLIER_1_5 (fx64: upper word, lower word). Alpha sets it to 1.25. Read only by
; the normal crit multiplier and the Sunny-Fire / Rain-Water weather boost.
.definelabel DamageMultiplier1_5Lower,    0x02352848
; MATCHUP_SUPER_EFFECTIVE_MULTIPLIER in ov10. Fx32, 8 fraction bits (1.0 = 0x100).
; Patched by apply (0x166 ≈ 1.4 → 0x180 = 1.5), once per defending type.
.definelabel MatchupSuperEffectiveMult,   0x022C4818
