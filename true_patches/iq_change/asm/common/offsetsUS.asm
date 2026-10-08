; US Explorers of Sky — iq_change vanilla symbols.

ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

.definelabel IqSkillIsEnabled,           0x02301F80
.definelabel BoostOffensiveStat,          0x0231399C
.definelabel BoostDefensiveStat,          0x02313B08
.definelabel FixedPointMul,               0x02001A54
.definelabel IqSkillFlagIsEnabled,       0x02347B80
.definelabel DungeonRandRange,            0x022EAA98
.definelabel HasLowHealth,               0x022FB610

.definelabel NonsleeperSleepImmunityBranch, 0x02311A7C
.definelabel NonsleeperSleepImmunitySkip,    0x02311AA0

; CalcDamage crit branch: ldr r2, =<fx64 multiplier> right before MultiplyFixedPoint64
; on the damage multiplier at sp+0xB8 (r0 already = sp+0xB8). r9 = defender.
.definelabel CalcDamageCritMulSniper,     0x0230CEC8
.definelabel CalcDamageCritMulNormal,     0x0230CEE0
; Literal-pool slots holding the fx64* those ldr's load (damage_formula may repoint normal).
.definelabel CalcDamageCritMulSniperPtr,  0x0230D074
.definelabel CalcDamageCritMulNormalPtr,  0x0230D078

.definelabel TryInflictBurnSuccess,       0x02312318
.definelabel TryInflictBurnEpilogue,      0x0231231C

.definelabel TryInflictPoisonSuccess,     0x0231291C
.definelabel TryInflictPoisonEpilogue,    0x02312920

.definelabel TryInflictBadPoisonSuccess,  0x02312BD8
.definelabel TryInflictBadPoisonEpilogue,  0x02312BDC

.definelabel TryInflictParalysisSuccess,  0x023147CC
.definelabel TryInflictParalysisEpilogue, 0x023147D0

.definelabel TryInflictConfusionSuccess,  0x023150F8
.definelabel TryInflictConfusionEpilogue, 0x023150FC

.definelabel TryInflictCringeSuccess,     0x02315258
.definelabel TryInflictCringeEpilogue,     0x0231525C

; Was wrongly 0x02311980 (wrapper "already asleep" msg). Real success is after
; the status-apply BL inside TryInflictSleep returns nonzero.
.definelabel TryInflictSleepSuccess,      0x02311B68
.definelabel TryInflictSleepEpilogue,     0x02311B78

; Restore site: old mistaken hook in the sleep wrapper message path.
.definelabel TryInflictSleepWrapperMsgLoad, 0x02311980

.definelabel TryInflictNightmareSuccess,   0x02311D4C
.definelabel TryInflictNightmareEpilogue,  0x02311D50

.definelabel TryInflictFrozenSuccess,      0x02312DCC
.definelabel TryInflictFrozenResume,       0x02312DD0

.definelabel TryInflictPetrifiedSuccess,   0x023135E4

; ApplyDamageAndEffects counter section: r5 = counter damage in quarters, r9 = defender.
; Physical: bl IqSkillIsEnabled(sb, Counter Basher) -> random full (+4) counter.
.definelabel CounterBasherPhysicalRoll,    0x02308888
; Physical: Counter Hitter (+1) roll, reached when Counter Basher is off.
.definelabel CounterHitterPhysicalRoll,    0x023088B0
; Special: cmp r0, #8 (Mirror Coat) -> +4.
.definelabel SpecialCounterStatusCheck,    0x023088E4
.definelabel SpecialCounterDone,           0x023088F8
.definelabel MirrorCoatCounterEffect,      0x022E40C0
; Pointer vanilla uses for the Counter Hitter roll chance (s16, out of 100).
.definelabel CounterHitterChancePtr,       0x022C4464

; AddExpSpecial (0x0230253C): bonus is applied only to the monster in r7.
.definelabel TeamMemberHasEnabledIqSkill, 0x022FB064
.definelabel EntityIsValid,               0x022F7364
.definelabel ExpHeldItemBoostActive,      0x023026CC
.definelabel TeamMemberHasExclusiveItemEffectActive, 0x0230F840
.definelabel DungeonPtr,                  0x02353538

.definelabel AddExpIqCheck,               0x02302590
.definelabel AddExpChestWonder,           0x023025C8
.definelabel AddExpChestMiracle,          0x02302600
.definelabel AddExpExclusiveBoost,        0x02302630
.definelabel AddExpExclusiveResume,       0x02302650

; Intimidator roll: ldr r1, [sp, #0x14] loads the 12% threshold. r0 is the 0..99 roll.
; sl is the monster that has Intimidator.
.definelabel IntimidatorRollLoad,        0x02322A04

IQ_STATUS_RESISTENCE equ 0x11
IQ_CRITICAL_DODGER   equ 0x40
IQ_COUNTER_BASHER    equ 0x31
IQ_EXP_ELITE         equ 0x1C
INTIMIDATOR_CHANCE   equ 20
EXCLUSIVE_EFF_EXP_BOOST equ 0x4F

STATUS_MIRROR_COAT       equ 0x08

STAT_STAGE_BOOST     equ 2
; 1.2 as fx64 with 16 fraction bits (stored as upper word, lower word)
CRIT_DODGER_MUL_FX64 equ 0x13333

OFFENSIVE_STAT_ATTACK    equ 0
OFFENSIVE_STAT_SP_ATTACK equ 1
DEFENSIVE_STAT_DEFENSE   equ 0
DEFENSIVE_STAT_SP_DEFENSE equ 1
