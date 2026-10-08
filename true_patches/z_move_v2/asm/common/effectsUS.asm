; US overlay29 / arm9 addresses for Z-Move type secondary effects.

.definelabel PopulateActiveMonsterPtrs,        0x022E2978
.definelabel EntityIsValid,                     0x022E1A1C
.definelabel GetTreatmentBetweenMonsters,       0x0230175C
.definelabel IsPositionInSight,                 0x022E91A4
.definelabel GetEntityDropeyeFlag,              0x02301F50
.definelabel DUNGEON_PTR,                       0x02353538

.definelabel GetMoveCritChance,                 0x02013B10
.definelabel GetMoveCritChanceBody,             0x02013B14

.definelabel GetTeamMember,                     0x020555A8
; RestorePpAllMovesSetFlags — defined in offsetsUS.asm (ForceRestore hook / PP effects)

.definelabel DoMoveSunnyDay,                     0x0232A220
.definelabel DoMoveRainDance,                   0x023260D0
.definelabel DoMoveHail,                        0x0232612C
.definelabel DoMoveSandstorm,                   0x023289F8
.definelabel DoMoveCharge,                       0x023282C8
.definelabel DoMoveHealStatus,                   0x02326188
.definelabel EndNegativeStatusConditionWrapper, 0x02305C28
.definelabel DoMoveSafeguard,                    0x02328528
.definelabel DoMoveGravity,                      0x0232D8FC
.definelabel DoMoveCounter,                      0x02326CB4
.definelabel DoMoveSureShot,                     0x023279AC
.definelabel DoMoveReflect,                      0x0232BF78
.definelabel DoMoveLightScreen,                 0x0232AD08
.definelabel DoMoveMagicCoat,                    0x0232B7C0

.definelabel TryInflictSleepStatus,              0x023118D8
.definelabel TryInflictPausedStatus,             0x0231206C
.definelabel TryInflictBurnStatus,              0x02312338
.definelabel TryInflictBadlyPoisonedStatus,      0x0231293C
.definelabel TryInflictFrozenStatus,            0x02312BF8
.definelabel TryInflictPetrifiedStatus,          0x0231346C
.definelabel TryInflictParalysisStatus,         0x02314544
.definelabel TryInflictConfusedStatus,          0x02314F38
.definelabel TryInflictWishStatus,               0x02318FAC
.definelabel TryInflictSafeguardStatus,          0x02318E70
.definelabel TryInflictLeechSeedStatus,          0x023157EC
.definelabel TryInflictFocusEnergyStatus,      0x02315D84
.definelabel TryInflictProtectStatus,           0x0231922C

.definelabel LowerOffensiveStat,                 0x023135FC
.definelabel LowerDefensiveStat,                 0x02313814
.definelabel BoostOffensiveStat,                 0x0231399C
.definelabel BoostDefensiveStat,                 0x02313B08
.definelabel BoostSpeed,                         0x02314810
.definelabel LowerSpeed,                         0x02314954
.definelabel TryRestoreHp,                       0x0231526C

OFFENSIVE_STAT_ATTACK         equ 0
OFFENSIVE_STAT_SP_ATTACK      equ 1
DEFENSIVE_STAT_DEFENSE        equ 0
DEFENSIVE_STAT_SP_DEFENSE     equ 1

Z_MOVE_FULL_HEAL_HP           equ 9999
Z_MOVE_MAX_SPEED_STAGES       equ 4
Z_MOVE_STAT_STAGES            equ 2
Z_MOVE_STEEL_DEF_STAGES       equ 3

ACTIVE_MONSTER_ARRAY_BASE     equ 0x12000
ACTIVE_MONSTER_PTRS_OFF       equ 0xB78
ACTIVE_MONSTER_SLOT_COUNT     equ 0x14
