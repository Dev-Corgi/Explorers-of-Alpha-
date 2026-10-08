; US Explorers of Sky (true_patches z_move_v2)
.arm

arm9                      equ 0x02000000

.definelabel AddDungeonSubMenuOption,     0x022EB81C
.definelabel GetSubMenuStringId,          0x022EB2C8
.definelabel GetSubMenuStringId_Continue, 0x022EB2E0
.definelabel SortSubMenu,                 0x022EB9A0
.definelabel SetActionField,              0x022EB408
.definelabel SetActionUseMovePlayer,      0x022EBC98
.definelabel InitMove,                    0x020137B8
.definelabel GetTeamMemberIndex,          0x022E2A38
.definelabel GetLeader,                   0x022E9580
.definelabel GetMoveCategory,             0x020151C8
.definelabel ApplyDamage,                 0x02308FE0
.definelabel ApplyDamageBody,             0x02308FE4
.definelabel HandleFaint,                 0x022F7F30
.definelabel HandleFaintBody,             0x022F7F34
.definelabel DealDamageBody,              0x02332B24
.definelabel DealDamageAfterPrologue,     0x02332B28
.definelabel ValidateMoveTarget,          0x022F0C3C
.definelabel CheckDungeonMoveValidateGate, 0x0204AF20
.definelabel LogMessageByIdWithPopupCheckUser, 0x0234B2A4
.definelabel LogMessageByIdQuiet,               0x0234B31C
.definelabel LogMessageById,                    0x0234B714
.definelabel LogMessageWithPopupCheckUser,      0x0234B2E4
.definelabel MessageWaitAfterPopup,             0x022EA370
.definelabel GetStringFromFile,                 0x020258C4
.definelabel DrawTextInWindow,                  0x02026214
.definelabel PreprocessString,                 0x020223F0
.definelabel Snprintf,                          0x0208955C
.definelabel GetMoneyCarried,                   0x0200ECFC
.definelabel DungeonMenuBeforeMoneyHook,        0x023828F8
.definelabel FloorHudAfterUpdateHook,          0x022F0A98
.definelabel BottomHudAfterBellyHook,          0x0234F75C
.definelabel UseItemBeforeUsedMoveMessageHookSite,   0x02322608
.definelabel UseItemBeforeUsedMoveMessageHookSiteB,  0x02322670
.definelabel UseItemBeforeUsedMoveMessageHookSiteC,  0x023226A8
.definelabel GetMoveTypeForMonster,       0x0230227C
.definelabel GetMoveTypeForMonsterBody,   0x02302280
.definelabel GetMovePower,                0x0230231C
.definelabel GetMovePowerBody,            0x02302320
.definelabel IsRoomChargeMove,            0x0231C3D0
; IsRoomChargeMoveBody -> PriorIsRoomChargeMove in generated.inc (room_charge integration)
.definelabel CalcDamageJudgmentTypeHookSite, 0x0230BCA8
.definelabel CalcDamageAfterJudgmentTypeStore, 0x0230BCB0
.definelabel IsChargingTwoTurnMove,       0x023245A4
.definelabel GetRoomChargeState,          0x0231C47C
.definelabel ExecuteMonsterActionEpilogueCleanup2Return, 0x022FEDB8
.definelabel AllocTopScreenStatus,         0x022E7EC4
.definelabel RunDungeon,                   0x022DEF38
.definelabel DungeonFree,                  0x022DEAB0
.definelabel DungeonFreeBody,              0x022DEAB4
.definelabel GetDungeonResultMsg,          0x0200C4FC
.definelabel GetDungeonResultMsgCallSite,  0x0200C6F0
.definelabel GetCoroutineInfo,             0x022E7FB8
.definelabel GetCoroutineInfoBody,         0x022E7FBC
.definelabel DungeonEntryArm9SetupSite,    0x022DF280
.definelabel DungeonEntryArm9SetupTarget,  0x020585D8
.definelabel DungeonFloorToGroupFloor,     0x0204F64C
.definelabel GetNbFloorsDungeonGroup,      0x0204F5F8
.definelabel DungeonMasterPtr,             0x02353538
DUNGEON_ID_FLOOR_OFF                      equ 0x748
DUNGEON_GROUP_ID_OFF                      equ 0x74A
DUNGEON_GROUP_FLOOR_OFF                   equ 0x74B
DAMAGE_SOURCE_DUNGEON_CLEAR               equ 634
.definelabel ZMoveArm9GaugeCaveOldAf3e0,   0x020AF3E0
.definelabel ExecuteMoveEffect,             0x0232E864
.definelabel ExecuteMoveEffectHook1,        0x02322B50
.definelabel ExecuteMoveEffectHook2,        0x023238AC

.definelabel DungeonSubMenuCountPtr,       0x0237C918
.definelabel DungeonSubMenuStringIds,     0x0237C922
.definelabel MoveMenuSelectedSlotPtr,     0x0238A270

ACTION_Z_MOVE             equ 42
STRING_ID_Z_MOVE_TEXT     equ 19100
STRING_ID_Z_MOVE_MENU     equ 19101
STRING_ID_NOTHING_HAPPENED equ 3048
STRING_ID_MOVE_FAILED     equ 3021
STRING_ID_Z_POWER_MESSAGE_BASE equ 19102
STRING_ID_Z_GAUGE_HUD         equ 19120

JUDGMENT_MOVE_ID          equ 467
Z_MOVE_SHELL_ID           equ 559
Z_MOVE_POWER              equ 180
Z_MOVE_POWER_NORMAL       equ 360
Z_MOVE_TYPE_COUNT         equ 18

Z_GAUGE_MAX               equ 100
Z_GAUGE_GAIN_LEADER_ATTACK equ 1
Z_GAUGE_GAIN_LEADER_HIT    equ 1
Z_GAUGE_GAIN_ENEMY_FAINT   equ 2
MOVE_CATEGORY_STATUS      equ 2

StatusMoveSlotsBase       equ 0x124
StatusActionField         equ 0x4A
StatusMoveSlot3Off        equ 0x13C
MoveDataMoveIdOff         equ 4
AttackerPrimaryTypeOff    equ 0x5e
ZMoveTempMoveSlot         equ 3
RoomChargePending         equ 1

.definelabel TeachItemHandler,             0x0231DA80
.definelabel TeachItemHandlerResume,      0x0231DA84
.definelabel LevelUp,                      0x0230303C
.definelabel LevelUpBody,                  0x02303040
.definelabel RestorePpAllMovesSetFlags,    0x022F9A74
.definelabel RestorePpAllMovesSetFlagsBody, 0x022F9A78
.definelabel ClearTwoTurnStatus,           0x02318D58

.definelabel ZMoveMenuHook,               0x023859C0
.definelabel ZMoveMenuResume,             0x023859C4
.definelabel ZMoveMoveConfirmHook,        0x02385FC0

Z_MOVE_MESSAGE_WAIT_FRAMES  equ 10
Z_MOVE_MESSAGE_WAIT_PARAM   equ 63

; ZMoveOv29CodeAddress, ZMoveArm9GaugeCave, ZGauge, PriorExecuteMoveEffectCall -> generated.inc
.include "generated.inc"
