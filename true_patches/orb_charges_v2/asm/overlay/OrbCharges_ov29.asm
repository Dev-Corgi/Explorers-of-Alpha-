; Minimal patch: RemoveUsedItem ClearItemSlot hook only.
; [+2] low byte = use count; always ClearItemSlot (vanilla flow), restore slot if charges remain.
; No separate TryConsume call — inline logic avoids bl/caller side-effect crashes.

.org RemoveUsedItemClearPath
	b OrbCharges_RemoveUsedItemClearHook

.org GetSubMenuStringId_Continue
	b OrbCharges_CheckUseSubMenuString

.org OrbChargesOv29CodeAddress

.include "generated/orb_charge_table_ov29.asm"

; Replaces RemoveUsedItem @ 0x022EB658 mov r0,r5 / bl ClearItemSlot.
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

; r6 = submenu action -> maybe override Use string for charge-table orbs.
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

; r0 = item id -> r0 = max charges (0 if not in ov29 table)
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

; r0 = item struct -> r0 = string index (+1 offset for game lookup)
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

; Patch the last submenu row string id when Use was just appended.
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

; --- ov31 item submenu hooks (called from overlay 31 branch stubs) ---

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

.align 4
OrbSelectedItemPtr:
.word 0

.pool
