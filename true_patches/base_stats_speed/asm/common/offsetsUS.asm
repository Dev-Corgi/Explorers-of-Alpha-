; Explorers of Alpha US.

ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

SoftDiv equ 0x0208FEA4
Strcat equ 0x020897AC

; MoveHitCheck entry. First call uses Accuracy; the second call returns hit.
MoveHitCheck equ 0x02323C48
MoveHitCheckBody equ 0x02323C4C
; MoveHitCheck rank multiply. r9/r10 are already the accuracy/evasion stages.
MoveHitRankSite equ 0x02323F94
MoveHitEpilogue equ 0x02324008

; Vanilla m_level sum after Alpha's dungeon 0x64 / 0xA5 early-out.
SpawnHpResume equ 0x022FE30C
SpawnAtkResume equ 0x022FE368
SpawnDefResume equ 0x022FE3D0

; LevelUpBody: write the new stats. Level is already stored (Alpha 0x02097DC0).
LevelUpStatApply equ 0x02303160
LevelUpAfterStats equ 0x02303258
LevelUpRefresh equ 0x023021F0
LevelUpIqCheck equ 0x02318D58
LevelUpTryLearn equ 0x023034E0
LevelUpSaveOldLevel equ 0x0230308C
LevelUpDeltasExp equ 0x02302B3C
LevelUpDeltasExpContinue equ 0x02302B98
LevelUpDeltasJoy equ 0x0230297C
LevelUpDeltasJoyContinue equ 0x023029E8
LevelUpSpeDigit equ 0x02302F24
SetStringDigit equ 0x0234B09C
SetMessageLogString equ 0x0234B0B4

; CalcDamage: after stages are clamped. Exclusive offense/defense flats
; used to run at 0x0230C2F0; those amounts now enter CalcStat as r3.
; Resume at 0x0230C338 (band / later path).
CalcDamageStatLoad equ 0x0230C26C
CalcDamageAfterStats equ 0x0230C338
CalcDamageDownloadLoad equ 0x0230BDFC
CalcDamageDownloadCmp equ 0x0230BE04
Fx32Mul equ 0x02001A54
OffensiveStageTable equ 0x022C4D98
DefensiveStageTable equ 0x022C4DEC

; ApplyExclusiveItemStatBoosts epilogue: r4=monster move list, r7=monster.
ApplyExclusiveEpilogue equ 0x023482A8
ExclusiveEffectCheck equ 0x023482B0
ExclusiveEffectBitCheck equ 0x02010FA4
ExclusiveHpAmount equ 0x020A1878

; Ground summary: after exclusive boosts are on the stack, before
; max = current + exclusive HP.
SummaryHpExclusiveAdd equ 0x0205AF90
SummaryHpExclusiveContinue equ 0x0205AFA0

; EvolveMonster: species and InitMonster already ran. Write CalcStat next.
EvolveAfterInitSite equ 0x02303CF4
EvolveAfterInitContinue equ 0x02303CF8

; After SpawnMonster in GenerateFixedRoom. r9 is the spawn type:
; 6 = Strong Enemy, 0xA = Helping Ally. Those two then copy the 12-byte
; Pokémon Stats table onto the monster at ApplyFixedRoomStats.
FixedRoomAfterSpawn equ 0x023438A4
FixedRoomAfterSpawnContinue equ 0x023438BC
ApplyFixedRoomStats equ 0x022FBE58

; dungeon_generation_info.fixed_room_id (dungeon + 0x40DA)
FIXED_ROOM_ID_HI equ 0x4000
FIXED_ROOM_ID_LO equ 0xDA

; rsb rd, #1, #0x3E8  -> 997. Phase 7 rewrites to #0x8000 (32767).
HpCapImmRevive equ 0x022E04FC
HpCapImmFixed equ 0x022FBE84
HpCapImmGuest equ 0x0234EE30

ov_arm9 equ 0x02000000
DungeonPtr equ 0x02353538
GetActiveTeamMember equ 0x0205638C
IsGuestTeamMember equ 0x02056228
SprintfTagged equ 0x020235B8
DrawWindowText equ 0x02026214
SummaryStatsAtkLoad equ 0x0205A628
SummaryStatsAtkContinue equ 0x0205A7D0
InitTeamMemberHpCopy equ 0x022FD50C
InitTeamMemberAfterHp equ 0x022FD514
SummaryHpFill equ 0x0205AE6C
SummaryHpFillContinue equ 0x0205AE74
DungeonSummaryLevel equ 0x022F8A18
DungeonSummaryLevelContinue equ 0x022F8A20
GroundInitV equ 0x02052D20
GroundInitVContinue equ 0x02052D68
GuestInitV equ 0x02052E74
GuestInitVContinue equ 0x02052E9C
InitMentryHpStore equ 0x020532D0
InitMentryHpStoreContinue equ 0x020532D4
GroundRefreshV equ 0x02052F10
GroundRefreshVContinue equ 0x02052F58
RecruitInitV equ 0x02055BB8
RecruitInitVContinue equ 0x02055C00
RecruitHpOverwrite equ 0x02048B00
GroundLevelUpV equ 0x02054720
GroundLevelUpVContinue equ 0x02054758
TeamSyncMaxHp equ 0x022FE068
TryRecruitHpVStore equ 0x0230E1B0
TryIncreaseHpBoost equ 0x023153C4
TryIncreaseHpBoostResume equ 0x023153C8
TryIncreaseHpAfterBoost equ 0x023153E4
