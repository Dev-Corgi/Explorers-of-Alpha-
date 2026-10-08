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
