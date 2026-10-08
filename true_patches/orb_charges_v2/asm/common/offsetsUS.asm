; US Explorers of Sky (berryboost base)
arm9 equ 0x02000000
ov_29 equ 0x022DC240
ov_36 equ 0x023A7080
ov_31 equ 0x02382820
ov_11 equ 0x022DC240

.definelabel StrNCopy,                    0x0208975C
.definelabel GetItemCategory,             0x0200CAF0

.definelabel GetSubMenuStringId,          0x022EB2C8
.definelabel GetSubMenuStringId_Continue, 0x022EB2E0
.definelabel GetSubMenuStringId_ContinuePlus4, 0x022EB2E4
.definelabel GetSubMenuStringId_StairsBranch, 0x022EB2E8

.definelabel AddDungeonSubMenuOption,     0x022EB81C
.definelabel DungeonSubMenuCountPtr,       0x0237C918
.definelabel DungeonSubMenuStringIds,     0x0237C922

.definelabel ClearItemSlot,               0x0200D81C

.definelabel RemoveUsedItemClearPath,     0x022EB658
.definelabel RemoveUsedItemEpilogue,      0x022EB660

RemoveUsedItemSavedLrOffset equ 12

.definelabel BagOrbRemoveUsedItemReturn1, 0x022F53C4
.definelabel BagOrbRemoveUsedItemReturn2, 0x0231AC4C

.definelabel OrbUseMenuSaveItemSite,      0x02384C48
.definelabel OrbUseMenuSaveItemResume,    0x02384C4C
.definelabel OrbUseMenuAfterAddSite,      0x02384AE4
.definelabel OrbUseMenuAfterAddResume,    0x02384AE8
.definelabel OrbUseMenuAfterAddAltSite,   0x02384BF8
.definelabel OrbUseMenuAfterAddAltResume, 0x02384BFC

ACTION_USE_ORB              equ 0x31
; fp+7==0 orb bag path adds this action instead of GetItemAction (0x31).
ACTION_USE_ORB_MENU_ALT     equ 0x38

.definelabel DungeonEntryArm9SetupSite,    0x022DF280
.definelabel DungeonEntryArm9SetupTarget,  0x020585D8
.definelabel DungeonFree,                  0x022DEAB0
.definelabel DungeonFreeBody,              0x022DEAB4
.definelabel DungeonFloorToGroupFloor,     0x0204F64C
.definelabel GetNbFloorsDungeonGroup,      0x0204F5F8
DUNGEON_ID_FLOOR_OFF                      equ 0x748
DUNGEON_GROUP_ID_OFF                      equ 0x74A
DUNGEON_GROUP_FLOOR_OFF                   equ 0x74B
DAMAGE_SOURCE_DUNGEON_CLEAR               equ 634

; *(*BagItemsPtr + BAG_ITEMS_OFF) = bag item[BAG_SLOT_COUNT], 6 bytes each.
.definelabel BagItemsPtr,                 0x020AF6B8
BAG_ITEMS_OFF               equ 0x384
BAG_SLOT_COUNT              equ 50
BAG_ITEM_SIZE               equ 6

STRING_ID_USE_MENU_3        equ 19083
STRING_ID_USE_MENU_2        equ 19084
STRING_ID_USE_MENU_1        equ 19085

; Orb effect retargets. The move loader jumps to the loaded blob at
; WazaEffectLaunch; exclusive orb moves are intercepted there.
.definelabel ShouldUsePp,                 0x0231A7A0
.definelabel ShouldUsePpBody,             0x0231A7A4
.definelabel ResetFloor,                  0x02340B0C
.definelabel ResetFloorBody,              0x02340B10
.definelabel EndOfTurnCall,               0x022FED5C
.definelabel ActivateEndOfTurnEffects,    0x0230FC24
.definelabel WazaEffectLaunch,            0x0232F9A4
.definelabel WazaEffectLoaded,            0x02330134
.definelabel WazaEffectEpilogue,          0x023326CC
.definelabel CalcDamagePowerStore,        0x0230BBE0
.definelabel CalcDamagePowerStoreResume,  0x0230BBE4

; Walk-drain leader check. Replaced with a call that returns 0 while Diet is active.
.definelabel BuDrainGateSite,             0x0230FD0C

.definelabel PopulateActiveMonsterPtrs,   0x022E2978
.definelabel EntityIsValid,               0x022E1A1C
.definelabel GetTreatmentBetweenMonsters, 0x0230175C
.definelabel IsPositionInSight,           0x022E91A4
.definelabel GetEntityDropeyeFlag,        0x02301F50
.definelabel TryInflictBadlyPoisonedStatus, 0x0231293C
.definelabel TryInflictProtectStatus,     0x0231922C
.definelabel TryInflictMirrorCoatStatus,  0x023192DC
.definelabel SetReflectStatus,            0x02318D98
.definelabel LowerOffensiveStat,          0x023135FC
.definelabel LowerDefensiveStat,          0x02313814
.definelabel DungeonPtrAddr,              0x02353538

ACTIVE_MONSTER_ARRAY_BASE     equ 0x12000
ACTIVE_MONSTER_PTRS_OFF       equ 0xB78
ACTIVE_MONSTER_SLOT_COUNT     equ 20
REFLECT_COUNTER               equ 4
ORB_POWER_SLOTS               equ 4

ORB_MOVE_PP                   equ 388
ORB_MOVE_POISON               equ 393
ORB_MOVE_REBOUND              equ 365
ORB_MOVE_PROTECT              equ 384
ORB_MOVE_ATK                  equ 397
ORB_MOVE_DEF                  equ 395
ORB_MOVE_POWER                equ 383
ORB_MOVE_DIET                 equ 398

; OrbChargesOv29CodeAddress -> generated.inc

.include "generated.inc"
