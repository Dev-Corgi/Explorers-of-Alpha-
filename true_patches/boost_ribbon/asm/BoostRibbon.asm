; Bag Boost submenu. String code ids are the display id + 1.

BoostSavedItem:
	.word 0
BoostSavedGroup:
	.byte 0
	.align 4
BoostPendingUser:
	.word 0
BoostPendingTarget:
	.word 0

; id, group (1 Hp, 2 Atk, 3 Def, 4 SpA, 5 SpD). No-Aim Scope is Atk only.
; 14 Y-Ray Specs, 15 Gaggle Specs, 13 No-Slip Cap.
BoostItemGroups:
	.dh 14, 1
	.dh 34, 1
	.dh 17, 1
	.dh 53, 1
	.dh 32, 1
	.dh 23, 1
	.dh 16, 1
	.dh 39, 1
	.dh 38, 1
	.dh 30, 1
	.dh 47, 1
	.dh 15, 2
	.dh 26, 2
	.dh 51, 2
	.dh 20, 2
	.dh 22, 2
	.dh 19, 2
	.dh 24, 2
	.dh 48, 2
	.dh 13, 3
	.dh 37, 3
	.dh 21, 3
	.dh 27, 3
	.dh 25, 3
	.dh 29, 3
	.dh 52, 3
	.dh 28, 3
	.dh 40, 4
	.dh 46, 4
	.dh 50, 4
	.dh 36, 4
	.dh 31, 4
	.dh 49, 4
	.dh 41, 5
	.dh 45, 5
	.dh 42, 5
	.dh 44, 5
	.dh 35, 5
	.dh 18, 5
	.dh 33, 5
	.dh 0, 0

; r0 = item id. Returns group 1..5, or 0.
Boost_GroupForItem:
	push {r4, lr}
	ldr r1, =BoostItemGroups
Boost_GroupLoop:
	ldrh r2, [r1]
	cmp r2, #0
	moveq r0, #0
	popeq {r4, pc}
	cmp r0, r2
	ldrh r2, [r1, #2]
	add r1, r1, #4
	bne Boost_GroupLoop
	mov r0, r2
	pop {r4, pc}

; r6 = action id. Already inside GetSubMenuStringId's push.
Boost_CheckString:
	cmp r6, #ACTION_BOOST
	beq Boost_ReturnString
	b Boost_PriorSubMenu
Boost_ReturnString:
	ldr r0, =BoostSavedGroup
	ldrb r0, [r0]
	ldr r1, =BOOST_STRING_DISPLAY_BASE
	add r0, r1, r0
	pop {r3, r4, r5, r6, r7, pc}

; r8 = bag item. Chains into the TM Read menu hook, which sorts.
Boost_MenuHook:
	push {r4, lr}
	bl Boost_TryAppend
	pop {r4, lr}
	b Boost_PriorMenu

Boost_TryAppend:
	push {r4, r5, r6, lr}
	mov r0, r8
	ldrsh r0, [r0, #4]
	bl Boost_GroupForItem
	cmp r0, #0
	beq Boost_TryAppend_Skip
	mov r4, r0
	ldr r1, =BoostSavedGroup
	strb r4, [r1]
	ldr r1, =BoostSavedItem
	str r8, [r1]
	ldr r1, =DungeonSubMenuCountPtr
	ldr r5, [r1]
	mov r0, #ACTION_BOOST
	mov r1, #1
	bl AddDungeonSubMenuOption
	ldr r1, =DungeonSubMenuCountPtr
	ldr r0, [r1]
	cmp r0, r5
	beq Boost_TryAppend_Skip
	cmp r0, #0
	beq Boost_TryAppend_Skip
	sub r0, r0, #1
	lsl r0, r0, #3
	ldr r1, =DungeonSubMenuStringIds
	ldr r2, =BOOST_STRING_DISPLAY_BASE
	add r2, r2, r4
	strh r2, [r1, r0]
Boost_TryAppend_Skip:
	pop {r4, r5, r6, pc}

; ItemsMenu @ cmp r0,#0x12: Boost opens the same team target menu as Ingest.
; Returns with flags set for the vanilla beq.
Boost_TargetActionCmp:
	cmp r0, #ACTION_BOOST
	cmpne r0, #0x12
	bx lr

; ItemsMenu after the target menu: r7 = leader status, r10 = leader entity,
; [sp,#0x44] = chosen team slot. Records the target and leaves as a pass turn,
; so action 43 never reaches ExecuteMonsterAction. Messages logged while the
; bag menu is open leave an empty message window behind when it closes.
Boost_TargetSelected:
	ldrh r0, [r7, #StatusActionField]
	cmp r0, #ACTION_BOOST
	ldrne r1, [sp, #0x44]
	bne ItemsMenuTargetSelectedResume
	ldr r0, [sp, #0x44]
	ldr r1, =DungeonPtr
	ldr r1, [r1]
	add r1, r1, r0, lsl #2
	add r1, r1, #0x12000
	ldr r1, [r1, #0xb28]
	ldr r0, =BoostPendingUser
	str r10, [r0]
	str r1, [r0, #4]
	add r0, r7, #StatusActionField
	mov r1, #1
	bl SetActionField
	b ItemsMenuPlainExit

; ExecuteMonsterAction after the prologue, r9 = acting entity. The pending
; boost is consumed by the next action and applies only to the recorded user.
Boost_ExecHook:
	push {r0, r1, r2, r3, r12, lr}
	ldr r2, =BoostPendingUser
	ldr r0, [r2]
	cmp r0, #0
	beq Boost_ExecOut
	ldr r1, [r2, #4]
	mov r3, #0
	str r3, [r2]
	str r3, [r2, #4]
	cmp r0, r9
	bne Boost_ExecOut
	bl Boost_ApplyToTarget
Boost_ExecOut:
	pop {r0, r1, r2, r3, r12, lr}
	ldr r6, [r9, #0xb4]
	b ExecuteMonsterActionBoostResume

; r0 = user entity, r1 = target entity.
Boost_ApplyToTarget:
	push {r4, r5, r6, r7, r8, lr}
	mov r7, r0
	movs r6, r1
	beq Boost_Apply_Done
	ldr r0, =BoostSavedItem
	ldr r5, [r0]
	cmp r5, #0
	beq Boost_Apply_Done
	ldrb r0, [r5]
	tst r0, #1
	beq Boost_Apply_Done
	ldrsh r0, [r5, #4]
	bl Boost_GroupForItem
	cmp r0, #0
	beq Boost_Apply_Done
	mov r4, r0
	cmp r4, #1
	beq Boost_Apply_Hp
	cmp r4, #2
	ldreq r3, =ApplyProteinEffect
	beq Boost_Apply_Stat
	cmp r4, #3
	ldreq r3, =ApplyIronEffect
	beq Boost_Apply_Stat
	cmp r4, #4
	ldreq r3, =ApplyCalciumEffect
	beq Boost_Apply_Stat
	ldr r3, =ApplyZincEffect
Boost_Apply_Stat:
	mov r0, r7
	mov r1, r6
	mov r2, #BOOST_AMOUNT
	blx r3
	b Boost_Apply_Remove
Boost_Apply_Hp:
	sub sp, sp, #8
	mov r0, #0
	str r0, [sp]
	mov r0, r7
	mov r1, r6
	mov r2, #BOOST_AMOUNT
	mov r3, #BOOST_AMOUNT
	bl TryIncreaseHp
	add sp, sp, #8
Boost_Apply_Remove:
	mov r0, r5
	bl RemoveEquivItemScan
Boost_Apply_Done:
	pop {r4, r5, r6, r7, r8, pc}

.pool
