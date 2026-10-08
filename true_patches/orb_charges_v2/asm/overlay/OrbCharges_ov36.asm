.org OrbChargesOv29CodeAddress

; Cave+0. belly_union reads this byte. Do not move it.
OrbFx_DietFlag:
	.byte 0, 0, 0, 0

.include "generated/orb_charge_table_ov29.asm"

OrbCharges_RemoveUsedItemClearHook:
	ldr r1, [sp, #RemoveUsedItemSavedLrOffset]
	adr r0, OrbCharges_BagOrbCallerWords
	ldmia r0, {r2, r3}
	cmp r1, r2
	beq OrbCharges_ClearHookBagOrb
	cmp r1, r3
	beq OrbCharges_ClearHookBagOrb
	b OrbCharges_RemoveUsedItemVanilla

OrbCharges_ClearHookBagOrb:
	push {r4-r9, lr}
	mov r8, r5
	ldrb r0, [r8, #1]
	cmp r0, #0
	bne OrbCharges_ClearHookDestroyPop
	ldrh r4, [r8, #4]
	cmp r4, #0
	beq OrbCharges_ClearHookDestroyPop
	mov r6, #0
	mov r7, #OrbChargeTableCount
	adr r12, OrbChargeTableOv29
OrbCharges_ClearHookLookupLoop:
	cmp r6, r7
	bge OrbCharges_ClearHookDestroyPop
	lsl r0, r6, #2
	add r0, r12, r0
	ldrh r0, [r0]
	cmp r0, r4
	beq OrbCharges_ClearHookLookupHit
	add r6, r6, #1
	b OrbCharges_ClearHookLookupLoop
OrbCharges_ClearHookLookupHit:
	lsl r0, r6, #2
	add r0, r12, r0
	ldrb r9, [r0, #2]
	ldrb r2, [r8, #2]
	cmp r2, r9
	bge OrbCharges_ClearHookDestroyPop
	add r2, r2, #1
	strb r2, [r8, #2]
	sub sp, sp, #8
	ldrh r0, [r8]
	strh r0, [sp]
	ldrh r0, [r8, #2]
	strh r0, [sp, #2]
	ldrh r0, [r8, #4]
	strh r0, [sp, #4]
	mov r0, r8
	bl ClearItemSlot
	cmp r2, r9
	bge OrbCharges_ClearHookSkipRestore
	ldrh r0, [sp]
	strh r0, [r8]
	ldrh r0, [sp, #2]
	strh r0, [r8, #2]
	ldrh r0, [sp, #4]
	strh r0, [r8, #4]
OrbCharges_ClearHookSkipRestore:
	add sp, sp, #8
	pop {r4-r9, lr}
	b RemoveUsedItemEpilogue

OrbCharges_ClearHookDestroyPop:
	pop {r4-r9, lr}
OrbCharges_RemoveUsedItemVanilla:
	mov r0, r5
	bl ClearItemSlot
	b RemoveUsedItemEpilogue

OrbCharges_CheckUseSubMenuString:
	cmp r6, #ACTION_USE_ORB
	beq OrbCharges_CheckUseSubMenuStringPick
	cmp r6, #ACTION_USE_ORB_MENU_ALT
	bne OrbCharges_CheckUseSubMenuStringVanilla
OrbCharges_CheckUseSubMenuStringPick:
	ldr r0, =OrbSelectedItemPtr
	ldr r0, [r0]
	cmp r0, #0
	beq OrbCharges_CheckUseSubMenuStringVanilla
	bl OrbCharges_PickUseMenuStringId
	pop {r3, r4, r5, r6, r7, pc}

OrbCharges_CheckUseSubMenuStringVanilla:
	cmp r6, #0x26
	bne GetSubMenuStringId_ContinuePlus4
	b GetSubMenuStringId_StairsBranch

OrbChargeLookupOv29Table:
	push {r1-r4, lr}
	mov r1, r0
	mov r2, #0
	mov r3, #OrbChargeTableCount
	adr r12, OrbChargeTableOv29
OrbChargeLookupOv29Loop:
	cmp r2, r3
	bge OrbChargeLookupOv29Miss
	lsl r0, r2, #2
	add r0, r12, r0
	ldrh r0, [r0]
	cmp r0, r1
	beq OrbChargeLookupOv29Hit
	add r2, r2, #1
	b OrbChargeLookupOv29Loop
OrbChargeLookupOv29Hit:
	lsl r0, r2, #2
	add r0, r12, r0
	ldrb r0, [r0, #2]
	b OrbChargeLookupOv29Done
OrbChargeLookupOv29Miss:
	mov r0, #0
OrbChargeLookupOv29Done:
	pop {r1-r4, pc}

OrbCharges_PickUseMenuStringId:
	push {r1-r5, lr}
	mov r4, r0
	cmp r4, #0
	beq OrbCharges_PickUseMenuStringIdDefault
	ldrh r0, [r4, #4]
	cmp r0, #0
	beq OrbCharges_PickUseMenuStringIdDefault
	bl OrbChargeLookupOv29Table
	cmp r0, #0
	beq OrbCharges_PickUseMenuStringIdDefault
	mov r5, r0
	ldrh r0, [r4, #2]
	and r0, r0, #0xFF
	sub r1, r5, r0
	cmp r1, #3
	ldreq r0, =STRING_ID_USE_MENU_3
	beq OrbCharges_PickUseMenuStringIdDone
	cmp r1, #2
	ldreq r0, =STRING_ID_USE_MENU_2
	beq OrbCharges_PickUseMenuStringIdDone
	cmp r1, #1
	ldreq r0, =STRING_ID_USE_MENU_1
	beq OrbCharges_PickUseMenuStringIdDone
OrbCharges_PickUseMenuStringIdDefault:
	ldr r0, =STRING_ID_USE_MENU_1
OrbCharges_PickUseMenuStringIdDone:
	pop {r1-r5, pc}

OrbCharges_TryPatchLastSubMenuUseString:
	push {r1-r4, lr}
	mov r4, r0
	ldrh r0, [r4, #4]
	cmp r0, #0
	beq OrbCharges_TryPatchLastSubMenuUseStringDone
	bl OrbChargeLookupOv29Table
	cmp r0, #0
	beq OrbCharges_TryPatchLastSubMenuUseStringDone
	mov r5, r0
	ldrh r0, [r4, #2]
	and r0, r0, #0xFF
	cmp r0, r5
	bhs OrbCharges_TryPatchLastSubMenuUseStringDone
	ldr r1, =DungeonSubMenuCountPtr
	ldr r0, [r1]
	sub r0, r0, #1
	lsl r3, r0, #3
	ldr r1, =DungeonSubMenuStringIds
	mov r0, r4
	bl OrbCharges_PickUseMenuStringId
	strh r0, [r1, r3]
OrbCharges_TryPatchLastSubMenuUseStringDone:
	pop {r1-r4, pc}

OrbCharges_BagOrbCallerWords:
	.word BagOrbRemoveUsedItemReturn1
	.word BagOrbRemoveUsedItemReturn2

OrbCharges_SaveItemBeforeFill:
	ldr r1, =OrbSelectedItemPtr
	str r8, [r1]
	ldrsh r1, [r8, #4]
	b OrbUseMenuSaveItemResume

OrbCharges_AfterAddSubMenuOption:
	push {r0-r4, lr}
	cmp r4, #ACTION_USE_ORB
	beq OrbCharges_AfterAddSubMenuOptionPatch
	cmp r4, #ACTION_USE_ORB_MENU_ALT
	bne OrbCharges_AfterAddSubMenuOptionDone
OrbCharges_AfterAddSubMenuOptionPatch:
	mov r0, r8
	bl OrbCharges_TryPatchLastSubMenuUseString
OrbCharges_AfterAddSubMenuOptionDone:
	pop {r0-r4, lr}
	ldrb r0, [r8]
	b OrbUseMenuAfterAddResume

OrbCharges_AfterAddSubMenuOptionAlt:
	push {r0-r4, lr}
	mov r0, r8
	bl OrbCharges_TryPatchLastSubMenuUseString
	pop {r0-r4, lr}
	cmp r4, #0
	b OrbUseMenuAfterAddAltResume

; DungeonFree entry: DUNGEON_PTR_MASTER is still live (working copy may be 0).
OrbCharges_OnDungeonGroupEnd:
	push {r0-r3, lr}
	bl OrbCharges_IsDungeonGroupOutingEnd
	cmp r0, #0
	beq OrbCharges_OnDungeonGroupEndResume
	bl OrbCharges_RefillBag
OrbCharges_OnDungeonGroupEndResume:
	pop {r0-r3, lr}
	push {r3, lr}
	b DungeonFreeBody

; r0=1: faint/escape/give-up, or clear of the last floor in the group.
OrbCharges_IsDungeonGroupOutingEnd:
	push {r4, r5, lr}
	ldr r4, =DungeonPtrAddr
	ldr r5, [r4, #4]
	cmp r5, #0
	ldreq r5, [r4]
	movs r4, r5
	beq OrbCharges_GroupEndNo
	add r0, r4, #0x2C000
	add r0, r0, #0xA00
	ldrh r0, [r0, #0x66]
	ldr r1, =DAMAGE_SOURCE_DUNGEON_CLEAR
	cmp r0, r1
	bne OrbCharges_GroupEndYes
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
OrbCharges_GroupEndYes:
	mov r0, #1
	pop {r4, r5, pc}
OrbCharges_GroupEndNo:
	mov r0, #0
	pop {r4, r5, pc}

OrbCharges_RefillBag:
	push {r4, r5, r6, lr}
	ldr r4, =BagItemsPtr
	ldr r4, [r4]
	cmp r4, #0
	beq OrbCharges_RefillBagDone
	ldr r4, [r4, #BAG_ITEMS_OFF]
	cmp r4, #0
	beq OrbCharges_RefillBagDone
	mov r5, #BAG_SLOT_COUNT
	mov r6, #0
OrbCharges_RefillBagLoop:
	ldrb r0, [r4]
	tst r0, #1
	beq OrbCharges_RefillBagNext
	ldrh r0, [r4, #4]
	bl OrbChargeLookupOv29Table
	cmp r0, #0
	strneb r6, [r4, #2]
OrbCharges_RefillBagNext:
	add r4, r4, #BAG_ITEM_SIZE
	subs r5, r5, #1
	bne OrbCharges_RefillBagLoop
OrbCharges_RefillBagDone:
	pop {r4, r5, r6, pc}

.align 4
OrbSelectedItemPtr:
.word 0

.pool

.include "overlay/OrbEffects.asm"
