.nds
.arm

.open "overlay_0029.bin", 0x022DC240

.org GetSubMenuStringId + 0x14
	b TmRead_CheckReadString

.org ExecuteMonsterActionEpilogueValidate1
	bl TmRead_EpilogueIsEntityValid

.org ExecuteMonsterActionEpilogueValidate2
	bl TmRead_EpilogueIsEntityValid

; Force-restore before learn-move UI / revive PP / bag TM teach.
.org LevelUp
	b TmRead_LevelUpForceRestore

.org RestorePpAllMovesSetFlags
	b TmRead_RestorePpForceRestore

.org TeachItemHandler
	b TmRead_TeachItemForceRestore

.org DungeonFree
	b TmRead_OnDungeonGroupEnd

.close

.open "overlay_0036.bin", 0x023A7080

.org TmReadOv29CodeAddress

; Overridden by generated.inc when room_charge v1 is in build.state (v3 keeps stubs).
TmRead_IsRoomChargeMoveStub:
	mov r0, #0
	bx lr

TmRead_GetRoomChargeStateStub:
	mov r0, #0
	bx lr

TmRead_PriorPostValidateRestoreNoOp:
	bx lr

.align 4

TmReadSelectedItemPtr:
.word 0

TmReadPendingFlag:
.byte 0

TmReadTwoTurnRead:
.byte 0
.align 4

TmReadPendingEntity:
.word 0

TmReadPendingItemPtr:
.word 0

TmReadSlotBackup:
.fill 8, 0

TmRead_CheckReadString:
	cmp r6, #ACTION_TM_READ
	beq TmRead_ReturnReadString
	mov r4, r1
	b GetSubMenuStringId_Continue

TmRead_ReturnReadString:
	ldr r0, =TmReadSelectedItemPtr
	ldr r0, [r0]
	bl TmRead_PickReadMenuStringId
	pop {r3, r4, r5, r6, r7, pc}

; r0 = item struct -> r0 = string index (+1 offset for game lookup)
TmRead_PickReadMenuStringId:
	push {r1-r5, lr}
	mov r4, r0
	cmp r4, #0
	beq TmRead_PickReadMenuStringIdDefault
	ldrh r0, [r4, #4]
	cmp r0, #0
	beq TmRead_PickReadMenuStringIdDefault
	bl TmRead_LookupMaxCharges
	cmp r0, #0
	beq TmRead_PickReadMenuStringIdDefault
	mov r5, r0
	ldrh r0, [r4, #2]
	and r0, r0, #0xFF
	sub r1, r5, r0
	cmp r1, #3
	ldreq r0, =STRING_ID_READ_MENU_3
	beq TmRead_PickReadMenuStringIdDone
	cmp r1, #2
	ldreq r0, =STRING_ID_READ_MENU_2
	beq TmRead_PickReadMenuStringIdDone
	cmp r1, #1
	ldreq r0, =STRING_ID_READ_MENU_LAST
	beq TmRead_PickReadMenuStringIdDone
TmRead_PickReadMenuStringIdDefault:
	ldr r0, =STRING_ID_READ_MENU_3
TmRead_PickReadMenuStringIdDone:
	pop {r1-r5, pc}

TmRead_TryAppendReadOption:
	push {r4, lr}
	mov r0, r8
	ldrh r0, [r0, #4]
	cmp r0, #0
	beq TmRead_TryAppendReadOption_Skip
	bl GetItemCategory
	cmp r0, #ITEM_CATEGORY_TM
	bne TmRead_TryAppendReadOption_Skip
	mov r0, r8
	bl TmRead_HasReadCharges
	cmp r0, #0
	beq TmRead_TryAppendReadOption_Skip
	mov r0, #ACTION_TM_READ
	mov r1, #1
	bl AddDungeonSubMenuOption
	ldr r1, =DungeonSubMenuCountPtr
	ldr r0, [r1]
	sub r0, r0, #1
	lsl r4, r0, #3
	ldr r1, =DungeonSubMenuStringIds
	mov r0, r8
	bl TmRead_PickReadMenuStringId
	strh r0, [r1, r4]
TmRead_TryAppendReadOption_Skip:
	pop {r4, pc}

; r10 = entity, r6 = status, slot 3 fixed -> r0 = 1 success, 0 fail
; Mirrors overlay29 move-menu Use @ 0x022F1C04 (ValidateMoveTarget + SetActionUseMovePlayer).
TmRead_CallMoveMenuUseSlot3:
	push {r4, r5, lr}
	mov r4, #3
	mov r5, #3
	bl CheckDungeonMoveValidateGate
	cmp r0, #0
	beq TmRead_CallMoveMenuUseSlot3_SetAction
	mov r0, r10
	add r1, r6, #StatusMoveSlotsBase
	add r1, r1, r5, lsl #3
	bl ValidateMoveTarget
	cmp r0, #0
	beq TmRead_CallMoveMenuUseSlot3_Fail
TmRead_CallMoveMenuUseSlot3_SetAction:
	mov r0, r10
	bl GetTeamMemberIndex
	mov r1, r0
	add r0, r6, #StatusActionField
	mov r2, r4
	bl SetActionUseMovePlayer
	mov r0, #1
	pop {r4, r5, pc}
TmRead_CallMoveMenuUseSlot3_Fail:
	mov r0, #0
	pop {r4, r5, pc}

; r10 = entity (sl) -> r0 = 1 on success, 0 on failure
TmRead_SetupReadAction:
	push {r4-r7, lr}
	ldr r0, [r10, #0xB4]
	mov r6, r0
	cmp r6, #0
	beq TmRead_SetupReadAction_Fail
	ldr r0, =TmReadSelectedItemPtr
	ldr r0, [r0]
	cmp r0, #0
	beq TmRead_SetupReadAction_Fail
	mov r4, r0
	ldrh r0, [r4, #4]
	cmp r0, #0
	beq TmRead_SetupReadAction_Fail
	mov r0, r4
	bl TmRead_HasReadCharges
	cmp r0, #0
	beq TmRead_SetupReadAction_Fail
	ldrh r0, [r4, #4]
	bl GetItemMoveId
	mov r5, r0
	cmp r5, #0
	beq TmRead_SetupReadAction_Fail
	mov r0, r5
	bl TmRead_IsTwoTurnMove
	cmp r0, #0
	bne TmRead_SetupReadAction_SetDeferredRestore
	mov r0, r5
	bl TmReadIsRoomChargeMove
TmRead_SetupReadAction_SetDeferredRestore:
	ldr r1, =TmReadTwoTurnRead
	strb r0, [r1]
	mov r7, #3
	mov r0, r6
	bl TmRead_BackupMoveSlot
	add r0, r6, #StatusMoveSlotsBase
	add r0, r0, r7, lsl #3
	mov r1, r5
	bl InitMove
	bl TmRead_CallMoveMenuUseSlot3
	cmp r0, #0
	beq TmRead_SetupReadAction_RestoreFail
	ldr r0, =TmReadPendingItemPtr
	str r4, [r0]
	ldr r0, =TmReadPendingEntity
	mov r1, r10
	str r1, [r0]
	mov r0, #1
	ldr r1, =TmReadPendingFlag
	strb r0, [r1]
	mov r0, #1
	pop {r4-r7, pc}
TmRead_SetupReadAction_RestoreFail:
	mov r0, #0
	ldr r1, =TmReadTwoTurnRead
	strb r0, [r1]
	mov r0, r6
	bl TmRead_RestoreMoveSlotFromBackup
TmRead_SetupReadAction_Fail:
	mov r0, #0
	pop {r4-r7, pc}

; r6 = status, slot in r7 -> copy 8-byte move slot to TmReadSlotBackup
TmRead_BackupMoveSlot:
	push {r0-r3, lr}
	add r0, r6, #StatusMoveSlotsBase
	add r0, r0, r7, lsl #3
	ldr r1, =TmReadSlotBackup
	ldmia r0, {r2, r3}
	stmia r1, {r2, r3}
	pop {r0-r3, pc}

; r0 = status -> restore slot 3 from TmReadSlotBackup
TmRead_RestoreMoveSlotFromBackup:
	push {r4-r7, lr}
	mov r6, r0
	mov r7, #3
	ldr r0, =TmReadSlotBackup
	add r1, r6, #StatusMoveSlotsBase
	add r1, r1, r7, lsl #3
	ldmia r0, {r2, r3}
	stmia r1, {r2, r3}
	pop {r4-r7, pc}

; r0 = item id -> r0 = max charges (0 if not in table)
TmRead_LookupMaxCharges:
	push {r1-r4, lr}
	mov r1, r0
	mov r2, #0
	mov r3, #TmChargeTableCount
	ldr r12, =TmChargeTableOv29Address
TmRead_LookupMaxChargesLoop:
	cmp r2, r3
	bge TmRead_LookupMaxChargesMiss
	lsl r0, r2, #2
	add r0, r12, r0
	ldrh r0, [r0]
	cmp r0, r1
	beq TmRead_LookupMaxChargesHit
	add r2, r2, #1
	b TmRead_LookupMaxChargesLoop
TmRead_LookupMaxChargesHit:
	lsl r0, r2, #2
	add r0, r12, r0
	ldrb r0, [r0, #2]
	b TmRead_LookupMaxChargesDone
TmRead_LookupMaxChargesMiss:
	mov r0, #0
TmRead_LookupMaxChargesDone:
	pop {r1-r4, pc}

; r0 = item struct ptr -> r0 = 1 if charges remain, else 0
TmRead_HasReadCharges:
	push {r4-r6, lr}
	mov r4, r0
	ldrh r0, [r4, #4]
	bl TmRead_LookupMaxCharges
	cmp r0, #0
	beq TmRead_HasReadChargesNo
	mov r5, r0
	ldrh r0, [r4, #2]
	and r0, r0, #0xFF
	cmp r0, r5
	movlo r0, #1
	movhs r0, #0
	pop {r4-r6, pc}
TmRead_HasReadChargesNo:
	mov r0, #0
	pop {r4-r6, pc}

; r0 = move id -> r0 = 1 if two-turn charge move, else 0
TmRead_IsTwoTurnMove:
	push {r1-r3, lr}
	mov r1, r0
	mov r2, #0
	ldr r3, =TWO_TURN_MOVES_AND_STATUSES
TmRead_IsTwoTurnMoveLoop:
	lsl r0, r2, #2
	add r0, r3, r0
	ldrh r0, [r0]
	cmp r0, #0
	beq TmRead_IsTwoTurnMoveNo
	cmp r0, r1
	beq TmRead_IsTwoTurnMoveYes
	add r2, r2, #1
	b TmRead_IsTwoTurnMoveLoop
TmRead_IsTwoTurnMoveYes:
	mov r0, #1
	b TmRead_IsTwoTurnMoveDone
TmRead_IsTwoTurnMoveNo:
	ldr r3, =TmReadRoomChargeTwoTurnExtTable
	cmp r3, #0
	beq TmRead_IsTwoTurnMoveDoneZero
	mov r2, #0
TmRead_IsTwoTurnMoveExtLoop:
	cmp r2, #100
	bhs TmRead_IsTwoTurnMoveDoneZero
	lsl r0, r2, #2
	add r0, r3, r0
	ldrh r0, [r0]
	cmp r0, #0
	beq TmRead_IsTwoTurnMoveDoneZero
	cmp r0, r1
	beq TmRead_IsTwoTurnMoveYes
	add r2, r2, #1
	b TmRead_IsTwoTurnMoveExtLoop
TmRead_IsTwoTurnMoveDoneZero:
	mov r0, #0
TmRead_IsTwoTurnMoveDone:
	pop {r1-r3, pc}

; Decrement via TmReadPendingItemPtr after a completed Read action.
TmRead_TryConsumeCharge:
	push {r4, lr}
	ldr r4, =TmReadPendingItemPtr
	ldr r4, [r4]
	cmp r4, #0
	beq TmRead_TryConsumeChargeClearPtr
	ldrh r0, [r4, #2]
	add r0, r0, #1
	strh r0, [r4, #2]
TmRead_TryConsumeChargeClearPtr:
	mov r0, #0
	ldr r1, =TmReadPendingItemPtr
	str r0, [r1]
	pop {r4, pc}

TmRead_TryRestoreSlot:
	push {r4-r8, lr}
	mov r8, r0
	ldr r4, =TmReadPendingFlag
	ldrb r0, [r4]
	cmp r0, #0
	beq TmRead_TryRestoreSlotDone
	ldr r5, =TmReadPendingEntity
	ldr r5, [r5]
	cmp r5, #0
	beq TmRead_TryRestoreSlotClear
	cmp r8, #0
	beq TmRead_TryRestoreSlotAfterEntityGate
	cmp r8, r5
	bne TmRead_TryRestoreSlotDone
TmRead_TryRestoreSlotAfterEntityGate:
	bl TmRead_LoadEntityStatus
	cmp r6, #0
	beq TmRead_TryRestoreSlotClear
	ldr r0, =TmReadTwoTurnRead
	ldrb r0, [r0]
	cmp r0, #0
	beq TmRead_TryRestoreSlotDoRestore
	mov r0, r5
	add r1, r6, #StatusMoveSlot3Off
	bl IsChargingTwoTurnMove
	cmp r0, #0
	bne TmRead_TryRestoreSlotDone
	mov r0, r5
	bl TmReadGetRoomChargeState
	cmp r0, #RoomChargePending
	beq TmRead_TryRestoreSlotDone
TmRead_TryRestoreSlotDoRestore:
	mov r7, #3
	ldr r0, =TmReadSlotBackup
	add r1, r6, #StatusMoveSlotsBase
	add r1, r1, r7, lsl #3
	ldmia r0, {r2, r3}
	stmia r1, {r2, r3}
	bl TmRead_TryConsumeCharge
TmRead_TryRestoreSlotClear:
	mov r0, #0
	strb r0, [r4]
	mov r0, #0
	ldr r1, =TmReadTwoTurnRead
	strb r0, [r1]
	mov r0, #0
	ldr r1, =TmReadPendingEntity
	str r0, [r1]
	mov r0, #0
	ldr r1, =TmReadPendingItemPtr
	str r0, [r1]
TmRead_TryRestoreSlotDone:
	pop {r4-r8, pc}

; Clear TwoTurn deferral (+ optional charge status), then TryRestore(r0=0).
; Used before moveset UI (LevelUp/TeachItem) and on revive (RestorePp).
TmRead_ForceRestorePending:
	push {r4, lr}
	ldr r4, =TmReadPendingEntity
	ldr r4, [r4]
	mov r0, #0
	ldr r1, =TmReadTwoTurnRead
	strb r0, [r1]
	cmp r4, #0
	beq TmRead_ForceRestorePending_DoRestore
	mov r0, r4
	bl ClearTwoTurnStatus
TmRead_ForceRestorePending_DoRestore:
	mov r0, #0
	bl TmRead_TryRestoreSlot
	pop {r4, pc}

TmRead_LevelUpForceRestore:
	push {r0-r3, lr}
	bl TmRead_ForceRestorePending
	pop {r0-r3, lr}
	push {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
	b LevelUpBody

TmRead_RestorePpForceRestore:
	push {r0-r3, lr}
	bl TmRead_ForceRestorePending
	pop {r0-r3, lr}
	push {r4, r5, r6, r7, r8, lr}
	b RestorePpAllMovesSetFlagsBody

TmRead_TeachItemForceRestore:
	push {r0-r3, lr}
	bl TmRead_ForceRestorePending
	pop {r0-r3, lr}
	push {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
	b TeachItemHandlerResume

; ExecuteMonsterActionEpilogue only (not global IsEntityValid). r0 = entity (sb).
TmRead_EpilogueIsEntityValid:
	push {r4, r5, lr}
	mov r4, r0
	bl ExecuteMonsterActionEpilogueCleanup2
	mov r5, r0
	ldr r0, =TmReadPendingFlag
	ldrb r0, [r0]
	cmp r0, #0
	beq TmRead_EpilogueSkipTmReadRestore
	cmp r5, #0
	beq TmRead_EpilogueForceOnInvalid
	mov r0, r4
	bl TmRead_TryRestoreSlot
	b TmRead_EpilogueSkipTmReadRestore
TmRead_EpilogueForceOnInvalid:
	; Entity failed Cleanup2 (faint path): still force-restore so revive is not stuck deferred.
	bl TmRead_ForceRestorePending
TmRead_EpilogueSkipTmReadRestore:
	mov r0, r4
TmRead_PostValidateRestoreBl:
	bl PriorPostValidateRestore
TmRead_EpilogueIsEntityValidDone:
	mov r0, r5
	pop {r4, r5, lr}
	bx lr

; ov31 submenu confirm: r0 = status+0x4A, r1 = action id, r7 = status, r10 = entity
TmRead_Ov31ConfirmHook:
	cmp r1, #ACTION_TM_READ
	beq TmRead_Ov31ConfirmHook_Read
	b SetActionGeneric
TmRead_Ov31ConfirmHook_Read:
	push {r4, lr}
	mov r4, r7
	bl TmRead_SetupReadAction
	cmp r0, #0
	beq TmRead_Ov31ConfirmHook_Fail
	pop {r4, pc}
TmRead_Ov31ConfirmHook_Fail:
	mov r0, r10
	ldr r1, =STRING_ID_NOTHING_HAPPENED
	bl LogMessageByIdWithPopupCheckUser
	add r0, r4, #StatusActionField
	mov r1, #1
	bl SetActionField
	pop {r4, pc}

TmRead_Ov31MenuHook:
	push {lr}
	ldr r1, =TmReadSelectedItemPtr
	str r8, [r1]
	bl TmRead_TryAppendReadOption
	bl SortSubMenu
	pop {lr}
	b TmReadMenuResume

TmRead_LoadEntityStatus:
	ldr r0, [r5]
	cmp r0, #0
	moveq r6, #0
	bxeq lr
	ldr r6, [r5, #0xB4]
	bx lr

; DungeonFree entry: DUNGEON_PTR_MASTER is still live (working copy may be 0).
TmRead_OnDungeonGroupEnd:
	push {r0-r3, lr}
	bl TmRead_IsDungeonGroupOutingEnd
	cmp r0, #0
	beq TmRead_OnDungeonGroupEndResume
	bl TmRead_RefillBag
TmRead_OnDungeonGroupEndResume:
	pop {r0-r3, lr}
	b TmRead_PriorDungeonFree

; r0=1: faint/escape/give-up, or clear of the last floor in the group.
TmRead_IsDungeonGroupOutingEnd:
	push {r4, r5, lr}
	ldr r4, =DungeonMasterPtr
	ldr r5, [r4, #4]
	cmp r5, #0
	ldreq r5, [r4]
	movs r4, r5
	beq TmRead_GroupEndNo
	add r0, r4, #0x2C000
	add r0, r0, #0xA00
	ldrh r0, [r0, #0x66]
	ldr r1, =DAMAGE_SOURCE_DUNGEON_CLEAR
	cmp r0, r1
	bne TmRead_GroupEndYes
	add r0, r4, #0x4A
	add r0, r0, #0x700
	add r1, r4, #0x48
	add r1, r1, #0x700
	bl DungeonFloorToGroupFloor
	ldrb r5, [r4, #DUNGEON_GROUP_FLOOR_OFF]
	ldrb r0, [r4, #DUNGEON_ID_FLOOR_OFF]
	bl GetNbFloorsDungeonGroup
	cmp r5, r0
	movge r0, #1
	movlt r0, #0
	pop {r4, r5, pc}
TmRead_GroupEndYes:
	mov r0, #1
	pop {r4, r5, pc}
TmRead_GroupEndNo:
	mov r0, #0
	pop {r4, r5, pc}

TmRead_RefillBag:
	push {r4, r5, r6, lr}
	ldr r4, =BagItemsPtr
	ldr r4, [r4]
	cmp r4, #0
	beq TmRead_RefillBagDone
	ldr r4, [r4, #BAG_ITEMS_OFF]
	cmp r4, #0
	beq TmRead_RefillBagDone
	mov r5, #BAG_SLOT_COUNT
	mov r6, #0
TmRead_RefillBagLoop:
	ldrb r0, [r4]
	tst r0, #1
	beq TmRead_RefillBagNext
	ldrh r0, [r4, #4]
	bl TmRead_LookupMaxCharges
	cmp r0, #0
	strneh r6, [r4, #2]
TmRead_RefillBagNext:
	add r4, r4, #BAG_ITEM_SIZE
	subs r5, r5, #1
	bne TmRead_RefillBagLoop
TmRead_RefillBagDone:
	pop {r4, r5, r6, pc}

.align 4
TmChargeTableOv29Address:
.include "generated/tm_charge_table_ov29.asm"

.pool

.close

.open "overlay_0031.bin", 0x02382820

.org TmReadMenuHook
	b TmRead_Ov31MenuHook

.org TmReadConfirmHook
	bl TmRead_Ov31ConfirmHook

.close
