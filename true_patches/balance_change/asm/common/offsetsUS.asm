; US Explorers of Sky — balance_change

arm9 equ 0x02000000
ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

.definelabel GetMonsterMovesEntrySite, 0x02303B18
.definelabel DungeonPtr,               0x02353538
.definelabel GetActiveTeamMember,      0x0205638C
.definelabel IsGuestTeamMember,        0x02056228
.definelabel ExpSharePercentageSite,   0x02097E34
.definelabel ExpShareUpgradeSite,      0x023A9378
.definelabel ExpShareToggleSite,       0x023A99A8

; arm9 rank-table readers. Replaced entirely; callers only need the level in r0.
.definelabel GetOutlawLevelSite,       0x0204F88C
.definelabel GetOutlawLeaderLevelSite, 0x0204F8A8
.definelabel GetOutlawMinionLevelSite, 0x0204F8C4

; GetOutlawSpawnData: strh r1, [r4, #4] stores the rank-table level.
.definelabel OutlawSpawnLevelSite,     0x022FE45C

; SpawnMonster, after max HP is stored at monster+0x12. OutlawHp overwrites
; that with 2 * CalcStat (or 2 * stored HP if CalcStat is not imported).
; The replaced word loads that half into r2 for the current-HP write at +0x10.
.definelabel OutlawHpSite,             0x022FD278

; dungeon_generation_info.fixed_room_id (dungeon + 0x40DA)
FIXED_ROOM_ID_HI equ 0x4000
FIXED_ROOM_ID_LO equ 0xDA
GENDER_ID_OFFSET equ 600
BOSS_ENTRY_SIZE equ 12

; Alpha ov36 difficulty helpers / patch sites
.definelabel GetDifficulty,                    0x023ACCF8
.definelabel EntityIsValid,                    0x022E95F4
.definelabel DiffRebalance_ApplyEnemyMultsSite, 0x023AA084
.definelabel DiffRebalance_A5MultSite,         0x023A9DC4
.definelabel DiffRebalance_VanillaLSSite,      0x023D91A4
.definelabel DiffRebalance_EHLSStoreSite,      0x023D926C
.definelabel DiffRebalance_ApplyEnemyMultsCont, 0x023AA0D8
.definelabel DiffRebalance_A5MultCont,         0x023A9DE4
.definelabel DiffRebalance_LSLoopCont,         0x023D9274

; Independent natural recovery multipliers and final denominator floor.
.definelabel RegenHealRibbonSite, 0x02311138
.definelabel RegenQuickHealerSite, 0x02311158
.definelabel RegenWishSite, 0x02311170
.definelabel RegenRainDishSite, 0x02311198
.definelabel RegenDrySkinSite, 0x023111C4
.definelabel RegenExclusiveSite, 0x02311214
.definelabel RegenMinimumCompareSite, 0x02311224
.definelabel RegenMinimumSetSite, 0x0231122C

.definelabel RegenStrongEnemyCheckSite, 0x02311120

; Alpha ability paths and unclaimed EoS body instructions.
.definelabel BalanceAbilitySpeedSite, 0x022FFEFC
.definelabel BalanceAbilityStabQuerySite, 0x0230B59C
.definelabel BalanceAbilityStabFactorSite, 0x0230B5A8
.definelabel BalanceAbilityDamageSite, 0x0230D03C
.definelabel BalanceAbilityMoveSite, 0x0232E864
.definelabel BalanceAbilityActionSite, 0x0232145C
.definelabel BalanceAbilityFaintSite, 0x022F7F34
.definelabel BalanceAbilityOldAdaptateSite, 0x023D4C0C
.definelabel BalanceAbilityOldAdaptateTypeSite, 0x023DAE04
.definelabel BalanceAbilityOldAdaptatePowerSite, 0x023D94A8
.definelabel BalanceAbilityOldSkySite, 0x023AF128
.definelabel BalanceAbilityOldSoundSite, 0x023B0338
.definelabel BalanceAbilityIsActive, 0x02301D78
.definelabel BalanceIsMonster, 0x02301A60
.definelabel BalanceMoveIsSound, 0x02013D5C
.definelabel BalanceMoveGetCategory, 0x020151C8
.definelabel BalanceSignedDivide, 0x0208FEA4
.definelabel BalanceBoostOffensiveStat, 0x0231399C
.definelabel BalanceAbility_OldAdaptateOff, 0x023D4C5C
.definelabel BalanceAbility_OldAdaptateTypeOff, 0x023DAE3C
.definelabel BalanceAbility_OldAdaptatePowerOff, 0x023D94BC
.definelabel BalanceAbility_OldSkyOff, 0x023AF148
.definelabel BalanceAbility_OldSoundOff, 0x023AF9E8
