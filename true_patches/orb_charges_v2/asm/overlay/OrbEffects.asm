; Retargeted orb effects. r9 is the user while a move effect runs.
; Matched moves skip the loaded blob and join WazaEffectEpilogue.

OrbFx_Dispatch:
	ldr r0, =ORB_MOVE_PP
	cmp r6, r0
	beq OrbFx_PpSave
	ldr r0, =ORB_MOVE_POISON
	cmp r6, r0
	beq OrbFx_Poison
	ldr r0, =ORB_MOVE_REBOUND
	cmp r6, r0
	beq OrbFx_Rebound
	ldr r0, =ORB_MOVE_PROTECT
	cmp r6, r0
	beq OrbFx_Protect
	ldr r0, =ORB_MOVE_ATK
	cmp r6, r0
	beq OrbFx_DropAtk
	ldr r0, =ORB_MOVE_DEF
	cmp r6, r0
	beq OrbFx_DropDef
	ldr r0, =ORB_MOVE_POWER
	cmp r6, r0
	beq OrbFx_ArmPower
	ldr r0, =ORB_MOVE_DIET
	cmp r6, r0
	beq OrbFx_Diet
	b WazaEffectLoaded

OrbFx_Done:
	mov r10, #1
	b WazaEffectEpilogue

OrbFx_PpSave:
	ldr r0, =OrbFx_PpSaveFlag
	mov r1, #1
	strb r1, [r0]
	b OrbFx_Done

OrbFx_Diet:
	ldr r0, =OrbFx_DietFlag
	mov r1, #1
	strb r1, [r0]
	b OrbFx_Done

; The leader check at BuDrainGateSite. r0 = 0 skips the walk drain.
; Flag clear replays the vanilla leader byte.
OrbFx_DietDrainGate:
	ldr r0, =OrbFx_DietFlag
	ldrb r0, [r0]
	cmp r0, #0
	beq OrbFx_DietDrainGate_Leader
	mov r0, #0
	bx lr
OrbFx_DietDrainGate_Leader:
	ldrb r0, [r4, #7]
	bx lr

OrbFx_Rebound:
	mov r0, r9
	mov r1, r9
	mov r2, #REFLECT_COUNTER
	bl SetReflectStatus
	mov r0, r9
	mov r1, r9
	bl TryInflictMirrorCoatStatus
	b OrbFx_Done

OrbFx_ArmPower:
	push {r4, r5, lr}
	ldr r4, =OrbFx_PowerEnt
	mov r1, #ORB_POWER_SLOTS
	mov r5, #0
OrbFx_ArmPower_Find:
	cmp r5, #ORB_POWER_SLOTS
	bhs OrbFx_ArmPower_Store
	ldr r0, [r4, r5, lsl #2]
	cmp r0, r9
	moveq r1, r5
	beq OrbFx_ArmPower_Store
	cmp r0, #0
	moveq r1, r5
	add r5, r5, #1
	b OrbFx_ArmPower_Find
OrbFx_ArmPower_Store:
	cmp r1, #ORB_POWER_SLOTS
	moveq r1, #0
	str r9, [r4, r1, lsl #2]
	ldr r0, =OrbFx_PowerSt
	mov r2, #2
	strb r2, [r0, r1]
	pop {r4, r5, lr}
	b OrbFx_Done

OrbFx_Poison:
	push {r4-r8, r9, lr}
	mov r8, r9
	bl PopulateActiveMonsterPtrs
	ldr r5, =DungeonPtrAddr
	ldr r5, [r5]
	mov r7, #0
OrbFx_Poison_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs OrbFx_Poison_Leave
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq OrbFx_Poison_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq OrbFx_Poison_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	bl GetTreatmentBetweenMonsters
	cmp r0, #1
	bne OrbFx_Poison_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	bl TryInflictBadlyPoisonedStatus
	b OrbFx_Poison_Loop
OrbFx_Poison_Leave:
	pop {r4-r8, r9, lr}
	b OrbFx_Done

OrbFx_Protect:
	push {r4-r8, r9, lr}
	mov r8, r9
	mov r0, r8
	mov r1, r8
	bl TryInflictProtectStatus
	bl OrbFx_BeginRoom
OrbFx_Protect_Loop:
	bl OrbFx_NextMonster
	cmp r0, #0
	beq OrbFx_Protect_Leave
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne OrbFx_Protect_Loop
	bl OrbFx_SameRoom
	cmp r0, #0
	beq OrbFx_Protect_Loop
	mov r0, r8
	mov r1, r6
	bl TryInflictProtectStatus
	b OrbFx_Protect_Loop
OrbFx_Protect_Leave:
	pop {r4-r8, r9, lr}
	b OrbFx_Done

OrbFx_DropAtk:
	push {r4-r8, r9, lr}
	mov r8, r9
	bl OrbFx_BeginRoom
OrbFx_DropAtk_Loop:
	bl OrbFx_NextMonster
	cmp r0, #0
	beq OrbFx_DropAtk_Leave
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	bl GetTreatmentBetweenMonsters
	cmp r0, #1
	bne OrbFx_DropAtk_Loop
	bl OrbFx_SameRoom
	cmp r0, #0
	beq OrbFx_DropAtk_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	bl OrbFx_DropSix
	b OrbFx_DropAtk_Loop
OrbFx_DropAtk_Leave:
	pop {r4-r8, r9, lr}
	b OrbFx_Done

OrbFx_DropDef:
	push {r4-r8, r9, lr}
	mov r8, r9
	bl OrbFx_BeginRoom
OrbFx_DropDef_Loop:
	bl OrbFx_NextMonster
	cmp r0, #0
	beq OrbFx_DropDef_Leave
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	bl GetTreatmentBetweenMonsters
	cmp r0, #1
	bne OrbFx_DropDef_Loop
	bl OrbFx_SameRoom
	cmp r0, #0
	beq OrbFx_DropDef_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #1
	bl OrbFx_DropSix
	b OrbFx_DropDef_Loop
OrbFx_DropDef_Leave:
	pop {r4-r8, r9, lr}
	b OrbFx_Done

; r8 = user. r7 = scan index. r5 = dungeon.
OrbFx_BeginRoom:
	push {lr}
	bl PopulateActiveMonsterPtrs
	ldr r5, =DungeonPtrAddr
	ldr r5, [r5]
	mov r7, #0
	pop {pc}

; Next active monster into r6. r0 = 1 if one was found.
OrbFx_NextMonster:
	push {lr}
OrbFx_NextMonster_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs OrbFx_NextMonster_None
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq OrbFx_NextMonster_Loop
	cmp r6, r8
	beq OrbFx_NextMonster_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq OrbFx_NextMonster_Loop
	mov r0, #1
	pop {pc}
OrbFx_NextMonster_None:
	mov r0, #0
	pop {pc}

; r8 = user, r6 = other. r0 = 1 when the other is in the user's room.
OrbFx_SameRoom:
	push {r4, lr}
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	pop {r4, pc}

; r0 = user, r1 = target, r2 = 0 attack pair / 1 defense pair. Drop both by 6.
OrbFx_DropSix:
	push {r4, r5, r6, lr}
	mov r4, r0
	mov r5, r1
	mov r6, r2
	mov r0, #1
	mov r1, #1
	push {r0, r1}
	mov r0, r4
	mov r1, r5
	mov r2, #0
	mov r3, #6
	cmp r6, #0
	bleq LowerOffensiveStat
	blne LowerDefensiveStat
	add sp, sp, #8
	mov r0, #1
	mov r1, #1
	push {r0, r1}
	mov r0, r4
	mov r1, r5
	mov r2, #1
	mov r3, #6
	cmp r6, #0
	bleq LowerOffensiveStat
	blne LowerDefensiveStat
	add sp, sp, #8
	pop {r4, r5, r6, pc}

OrbFx_ShouldUsePp:
	ldr r1, =OrbFx_PpSaveFlag
	ldrb r1, [r1]
	cmp r1, #0
	beq OrbFx_ShouldUsePp_Vanilla
	ldr r2, [r0, #0xB4]
	cmp r2, #0
	beq OrbFx_ShouldUsePp_Vanilla
	ldrb r2, [r2, #6]
	cmp r2, #0
	bne OrbFx_ShouldUsePp_Vanilla
	mov r0, #1
	bx lr
OrbFx_ShouldUsePp_Vanilla:
	push {r3, r4, r5, r6, r7, lr}
	b ShouldUsePpBody

OrbFx_ResetFloor:
	push {r0-r3, lr}
	ldr r0, =OrbFx_PpSaveFlag
	mov r1, #0
	strb r1, [r0]
	ldr r0, =OrbFx_DietFlag
	strb r1, [r0]
	ldr r0, =OrbFx_PowerEnt
	ldr r2, =OrbFx_PowerSt
	mov r3, #0
OrbFx_ResetFloor_Clear:
	cmp r3, #ORB_POWER_SLOTS
	bhs OrbFx_ResetFloor_Replay
	str r1, [r0, r3, lsl #2]
	strb r1, [r2, r3]
	add r3, r3, #1
	b OrbFx_ResetFloor_Clear
OrbFx_ResetFloor_Replay:
	pop {r0-r3, lr}
	push {r4-r10, lr}
	b ResetFloorBody

OrbFx_EndTurn:
	push {r4, r5, lr}
	bl ActivateEndOfTurnEffects
	ldr r4, =OrbFx_PowerEnt
	ldr r5, =OrbFx_PowerSt
	mov r0, #0
OrbFx_EndTurn_Loop:
	cmp r0, #ORB_POWER_SLOTS
	bhs OrbFx_EndTurn_Done
	ldr r1, [r4, r0, lsl #2]
	cmp r1, r9
	bne OrbFx_EndTurn_Next
	ldrb r1, [r5, r0]
	cmp r1, #2
	moveq r1, #1
	beq OrbFx_EndTurn_Write
	cmp r1, #1
	moveq r1, #0
OrbFx_EndTurn_Write:
	strb r1, [r5, r0]
OrbFx_EndTurn_Next:
	add r0, r0, #1
	b OrbFx_EndTurn_Loop
OrbFx_EndTurn_Done:
	pop {r4, r5, lr}
	bx lr

; CalcDamage has already applied equipment. r10 = attacker, r3 = power.
OrbFx_StorePower:
	push {r0, r4, r5, lr}
	ldr r4, =OrbFx_PowerEnt
	ldr r5, =OrbFx_PowerSt
	mov r0, #0
OrbFx_StorePower_Loop:
	cmp r0, #ORB_POWER_SLOTS
	bhs OrbFx_StorePower_Keep
	ldr r1, [r4, r0, lsl #2]
	cmp r1, r10
	bne OrbFx_StorePower_Next
	ldrb r1, [r5, r0]
	cmp r1, #1
	bne OrbFx_StorePower_Keep
	add r3, r3, r3, lsl #1
	b OrbFx_StorePower_Keep
OrbFx_StorePower_Next:
	add r0, r0, #1
	b OrbFx_StorePower_Loop
OrbFx_StorePower_Keep:
	pop {r0, r4, r5, lr}
	str r3, [sp, #0x10]
	b CalcDamagePowerStoreResume

.align 4
OrbFx_PpSaveFlag:
	.byte 0
	.align 4
OrbFx_PowerEnt:
	.word 0, 0, 0, 0
OrbFx_PowerSt:
	.byte 0, 0, 0, 0
	.align 4

.pool
