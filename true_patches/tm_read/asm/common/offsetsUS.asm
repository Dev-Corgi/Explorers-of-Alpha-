; US Explorers of Sky (true_patches tm_read)
.arm

.definelabel AddDungeonSubMenuOption,     0x022EB81C
.definelabel GetSubMenuStringId,          0x022EB2C8
.definelabel GetSubMenuStringId_Continue, 0x022EB2E0
.definelabel GetItemCategory,             0x0200CAF0
.definelabel GetItemMoveId,               0x0200EA80
.definelabel InitMove,                    0x020137B8
.definelabel SortSubMenu,                 0x022EB9A0
.definelabel GetTeamMemberIndex,          0x022E2A38
.definelabel SetActionUseMovePlayer,      0x022EBC98
.definelabel SetActionGeneric,            0x022EBBA8
.definelabel SetActionField,              0x022EB408
.definelabel ValidateMoveTarget,          0x022F0C3C
.definelabel CheckDungeonMoveValidateGate, 0x0204AF20
.definelabel MoveMenuUsePath,               0x022F1C04
.definelabel LogMessageByIdWithPopupCheckUser, 0x0234B2A4

.definelabel DungeonSubMenuCountPtr,       0x0237C918
.definelabel DungeonSubMenuStringIds,     0x0237C922

ACTION_TM_READ            equ 41
STRING_ID_READ_MENU_3       equ 19074
STRING_ID_READ_MENU_2       equ 19075
STRING_ID_READ_MENU_1       equ 19076
STRING_ID_READ_MENU_LAST    equ 19077
STRING_ID_NOTHING_HAPPENED equ 3048
ITEM_CATEGORY_TM          equ 5
TM_MAX_READ_CHARGES       equ 3

StatusMoveSlotsBase       equ 0x124
StatusActionField         equ 0x4A
StatusMoveSlot3Off        equ 0x13C
MoveDataMoveIdOff         equ 4
MoveSlotSize              equ 8
TmReadTempMoveSlot        equ 3

.definelabel ExecuteMoveAction,            0x022F5A40
.definelabel ExecuteMonsterActionEpilogue,         0x022FEBB4
.definelabel ExecuteMonsterActionEpilogueValidate1, 0x022FEBC0
.definelabel ExecuteMonsterActionEpilogueValidate2, 0x022FEBFC
.definelabel ExecuteMonsterActionEpilogueCleanup2, 0x022FED98
.definelabel ExecuteMonsterActionEpilogueCleanup2Return, 0x022FEDB8
.definelabel IsChargingTwoTurnMove,            0x023245A4
.definelabel ClearTwoTurnStatus,               0x02318D58
.definelabel TWO_TURN_MOVES_AND_STATUSES,      0x02352AAC
.definelabel LevelUp,                          0x0230303C
.definelabel LevelUpBody,                      0x02303040
.definelabel RestorePpAllMovesSetFlags,        0x022F9A74
.definelabel RestorePpAllMovesSetFlagsBody,    0x022F9A78
.definelabel TeachItemHandler,                 0x0231DA80
.definelabel TeachItemHandlerResume,           0x0231DA84
RoomChargePending               equ 1

.definelabel DungeonEntryArm9SetupSite,    0x022DF280
.definelabel DungeonEntryArm9SetupTarget,  0x020585D8
.definelabel DungeonFree,                  0x022DEAB0
.definelabel DungeonFreeBody,              0x022DEAB4
.definelabel DungeonFloorToGroupFloor,     0x0204F64C
.definelabel GetNbFloorsDungeonGroup,      0x0204F5F8
.definelabel DungeonMasterPtr,             0x02353538
DUNGEON_ID_FLOOR_OFF                      equ 0x748
DUNGEON_GROUP_ID_OFF                      equ 0x74A
DUNGEON_GROUP_FLOOR_OFF                   equ 0x74B
DAMAGE_SOURCE_DUNGEON_CLEAR               equ 634
; *(*BagItemsPtr + BAG_ITEMS_OFF) = bag item[BAG_SLOT_COUNT], 6 bytes each.
.definelabel BagItemsPtr,              0x020AF6B8
BAG_ITEMS_OFF             equ 0x384
BAG_SLOT_COUNT            equ 50
BAG_ITEM_SIZE             equ 6

; TmReadIsRoomChargeMove / TmReadGetRoomChargeState -> generated.inc
; v1 room_charge exports from build.state; v3 uses TWO_TURN + IsChargingTwoTurnMove (stubs OK).

.definelabel TmReadMenuHook,               0x02384C54
.definelabel TmReadMenuResume,             0x02384C58
.definelabel TmReadConfirmHook,            0x02384DFC
.definelabel TmReadConfirmResume,          0x02384E00

; TmReadOv29CodeAddress, TmChargeTableCount, PriorPostValidateRestore -> generated.inc
.include "generated.inc"
