; Z-Move type secondary effects (ov36 cave) — all types except Normal.
; Included from ZMoveOv29.asm after WRAM + move hooks.

.include "common/effectsUS.asm"

; r0 = move data pointer -> r0 = 1 if the Z-Move shell (559) is the active move
ZMove_IsActiveJudgmentMove:
	push {r1, lr}
	cmp r0, #0
	moveq r0, #0
	beq ZMove_IsActiveJudgmentMoveDone
	ldr r1, =ZMovePendingFlag
	ldrb r1, [r1]
	cmp r1, #0
	moveq r0, #0
	beq ZMove_IsActiveJudgmentMoveDone
	ldrh r1, [r0, #MoveDataMoveIdOff]
	ldr r0, =Z_MOVE_SHELL_ID
	cmp r1, r0
	moveq r0, #1
	movne r0, #0
ZMove_IsActiveJudgmentMoveDone:
	pop {r1, pc}

; r0=user, r1=target struct (entity pointer array), r2=move data
ZMove_TryApplyTypeEffect:
	push {r4-r7, lr}
	mov r4, r0
	mov r5, r1
	mov r6, r2
	cmp r6, #0
	beq ZMove_TryApplyTypeEffectDone
	mov r0, r6
	bl ZMove_IsActiveJudgmentMove
	cmp r0, #0
	beq ZMove_TryApplyTypeEffectDone
	ldr r0, =ZMoveEffectApplied
	ldrb r1, [r0]
	cmp r1, #0
	bne ZMove_TryApplyTypeEffectDone
	mov r1, #1
	strb r1, [r0]
	ldr r0, =ZMoveActiveType
	ldrb r0, [r0]
	cmp r0, #TYPE_FIRE
	beq ZMove_EffectFire
	cmp r0, #TYPE_WATER
	beq ZMove_EffectWater
	cmp r0, #TYPE_GRASS
	beq ZMove_EffectGrass
	cmp r0, #TYPE_ELECTRIC
	beq ZMove_EffectElectric
	cmp r0, #TYPE_ICE
	beq ZMove_EffectIce
	cmp r0, #TYPE_FIGHTING
	beq ZMove_EffectFighting
	cmp r0, #TYPE_POISON
	beq ZMove_EffectPoison
	cmp r0, #TYPE_GROUND
	beq ZMove_EffectGround
	cmp r0, #TYPE_FLYING
	beq ZMove_EffectFlying
	cmp r0, #TYPE_PSYCHIC
	beq ZMove_EffectPsychic
	cmp r0, #TYPE_BUG
	beq ZMove_EffectBug
	cmp r0, #TYPE_ROCK
	beq ZMove_EffectRock
	cmp r0, #TYPE_GHOST
	beq ZMove_EffectGhost
	cmp r0, #TYPE_DRAGON
	beq ZMove_EffectDragon
	cmp r0, #TYPE_DARK
	beq ZMove_EffectDark
	cmp r0, #TYPE_STEEL
	beq ZMove_EffectSteel
	cmp r0, #TYPE_FAIRY
	beq ZMove_EffectFairy
ZMove_TryApplyTypeEffectDone:
	pop {r4-r7, pc}

; Load *dungeon into r5.
ZMove_GetDungeonPtrInR5:
	ldr r5, =DUNGEON_PTR
	ldr r5, [r5]
	bx lr

; r4=user, r9=callback (r0=user, r1=enemy) for each enemy in the user's room.
ZMove_IterEnemiesInUserRoom:
	push {r5-r9, lr}
	mov r8, r4
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_IterEnemiesInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_IterEnemiesInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_IterEnemiesInUserRoom_Loop
	cmp r6, r8
	beq ZMove_IterEnemiesInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_IterEnemiesInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	beq ZMove_IterEnemiesInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_IterEnemiesInUserRoom_Next
	mov r0, r8
	mov r1, r6
	blx r9
ZMove_IterEnemiesInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_IterEnemiesInUserRoom_Loop
ZMove_IterEnemiesInUserRoom_Done:
	pop {r5-r9, pc}

; r0=user, r1=target, r2=offensive stat id, r3=stages
ZMove_LowerOffensiveStatWithStackArgs:
	push {lr}
	sub sp, sp, #8
	mov r12, #1
	str r12, [sp]
	mov r12, #0
	str r12, [sp, #4]
	bl LowerOffensiveStat
	add sp, sp, #8
	pop {pc}

; r0=user, r1=target, r2=defensive stat id, r3=stages
ZMove_LowerDefensiveStatWithStackArgs:
	push {lr}
	sub sp, sp, #8
	mov r12, #1
	str r12, [sp]
	mov r12, #0
	str r12, [sp, #4]
	bl LowerDefensiveStat
	add sp, sp, #8
	pop {pc}

; r0=user, r1=enemy
ZMove_ApplyLowerSpeedToEnemy:
	push {r2-r4, lr}
	mov r4, r0
	mov r0, r4
	mov r2, #Z_MOVE_STAT_STAGES
	mov r3, #0
	bl LowerSpeed
	pop {r2-r4, pc}

; r0=user, r1=enemy
ZMove_ApplySleepToEnemy:
	push {r2-r4, lr}
	mov r4, r0
	mov r0, r4
	mov r2, #3
	mov r3, #0
	bl TryInflictSleepStatus
	pop {r2-r4, pc}

; r0=user, r1=enemy
ZMove_ApplyPausedToEnemy:
	push {r2-r4, lr}
	mov r4, r0
	sub sp, sp, #8
	mov r2, #0
	str r2, [sp]
	str r2, [sp, #4]
	mov r0, r4
	mov r3, #1
	bl TryInflictPausedStatus
	add sp, sp, #8
	pop {r2-r4, pc}

; r0=user, r1=enemy
ZMove_ApplyPetrifiedToEnemy:
	push {lr}
	mov r2, #0
	mov r3, #0
	bl TryInflictPetrifiedStatus
	pop {pc}

; r0=user, r1=enemy — Atk/SpA/Def/SpD -2
ZMove_ApplyBugStatDropToEnemy:
	push {r4, lr}
	mov r4, r0
	mov r0, r4
	mov r2, #OFFENSIVE_STAT_ATTACK
	mov r3, #Z_MOVE_STAT_STAGES
	bl ZMove_LowerOffensiveStatWithStackArgs
	mov r0, r4
	mov r2, #OFFENSIVE_STAT_SP_ATTACK
	mov r3, #Z_MOVE_STAT_STAGES
	bl ZMove_LowerOffensiveStatWithStackArgs
	mov r0, r4
	mov r2, #DEFENSIVE_STAT_DEFENSE
	mov r3, #Z_MOVE_STAT_STAGES
	bl ZMove_LowerDefensiveStatWithStackArgs
	mov r0, r4
	mov r2, #DEFENSIVE_STAT_SP_DEFENSE
	mov r3, #Z_MOVE_STAT_STAGES
	bl ZMove_LowerDefensiveStatWithStackArgs
	pop {r4, pc}

.pool

; Fire Z-Move: burn every enemy in the target struct, then set Sunlight once.
; r4=user, r5=target struct, r6=move
ZMove_EffectFire:
	cmp r5, #0
	beq ZMove_EffectFire_Weather
	mov r7, #0
ZMove_EffectFire_Loop:
	cmp r7, #0x41
	bhs ZMove_EffectFire_Weather
	ldr r1, [r5, r7, lsl #2]
	add r7, r7, #1
	cmp r1, #0
	beq ZMove_EffectFire_Loop
	mov r0, r4
	mov r2, #0
	mov r3, #0
	push {r4, r5, r6, r7, lr}
	bl TryInflictBurnStatus
	pop {r4, r5, r6, r7, lr}
	b ZMove_EffectFire_Loop
ZMove_EffectFire_Weather:
	mov r0, r4
	mov r1, #0
	mov r2, r6
	mov r3, #0
	bl DoMoveSunnyDay
	b ZMove_TryApplyTypeEffectDone

; Water Z-Move: slow every enemy in the user's room, then Rain once.
; r4=user, r6=move
ZMove_EffectWater:
	ldr r9, =ZMove_ApplyLowerSpeedToEnemy
	bl ZMove_IterEnemiesInUserRoom
	mov r0, r4
	mov r1, #0
	mov r2, r6
	mov r3, #0
	bl DoMoveRainDance
	b ZMove_TryApplyTypeEffectDone

; Heal every ally in the user's room to full HP.
; r4=user on entry.
ZMove_HealAlliesInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_HealAlliesInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_HealAlliesInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_HealAlliesInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_HealAlliesInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_HealAlliesInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_HealAlliesInUserRoom_Next
	mov r0, r8
	mov r1, r6
	ldr r2, =Z_MOVE_FULL_HEAL_HP
	bl TryRestoreHp
ZMove_HealAlliesInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_HealAlliesInUserRoom_Loop
ZMove_HealAlliesInUserRoom_Done:
	pop {r5-r8, pc}

; r0=user, r1=ally, r11=move data
ZMove_FightingBuffOneAlly:
	push {r4, r5, lr}
	mov r4, r0
	mov r5, r1
	mov r0, r4
	mov r1, r5
	bl TryInflictFocusEnergyStatus
	mov r0, r4
	mov r1, r5
	mov r2, r11
	mov r3, #0
	bl DoMoveSureShot
	mov r0, r4
	mov r1, r5
	mov r2, r11
	mov r3, #0
	bl DoMoveCounter
	pop {r4, r5, pc}

; Focus Energy + Sure Shot + Counter for the user and allies in the user's room.
; r4=user, r11=move on entry.
ZMove_FightingBuffTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	mov r1, r8
	bl ZMove_FightingBuffOneAlly
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_FightingBuffTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_FightingBuffTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_FightingBuffTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_FightingBuffTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_FightingBuffTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_FightingBuffTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_FightingBuffTeamInUserRoom_Next
	mov r0, r8
	mov r1, r6
	bl ZMove_FightingBuffOneAlly
ZMove_FightingBuffTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_FightingBuffTeamInUserRoom_Loop
ZMove_FightingBuffTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Apply Focus Energy to the user and every ally in the user's room.
; r4=user on entry from ZMove_EffectFighting.
ZMove_FocusEnergyTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	mov r1, r8
	bl TryInflictFocusEnergyStatus
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_FocusEnergyTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_FocusEnergyTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_FocusEnergyTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_FocusEnergyTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_FocusEnergyTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_FocusEnergyTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_FocusEnergyTeamInUserRoom_Next
	mov r0, r8
	mov r1, r6
	bl TryInflictFocusEnergyStatus
ZMove_FocusEnergyTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_FocusEnergyTeamInUserRoom_Loop
ZMove_FocusEnergyTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Boost target speed to the maximum stage count.
; r0=user, r1=target
ZMove_BoostMaxSpeed:
	push {r3, lr}
	mov r2, #0
	mov r3, #0
	str r3, [sp]
	mov r3, r2
	mov r2, #Z_MOVE_MAX_SPEED_STAGES
	bl BoostSpeed
	pop {r3, pc}

; Boost speed to max for the user and every ally in the user's room.
; r4=user on entry from ZMove_EffectFlying.
ZMove_MaxSpeedTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	mov r1, r8
	bl ZMove_BoostMaxSpeed
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_MaxSpeedTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_MaxSpeedTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_MaxSpeedTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_MaxSpeedTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_MaxSpeedTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_MaxSpeedTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_MaxSpeedTeamInUserRoom_Next
	mov r0, r8
	mov r1, r6
	bl ZMove_BoostMaxSpeed
ZMove_MaxSpeedTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_MaxSpeedTeamInUserRoom_Loop
ZMove_MaxSpeedTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Apply Protect to the user and every ally in the user's room.
; r4=user on entry from ZMove_EffectPsychic.
ZMove_ProtectTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	mov r1, r8
	bl TryInflictProtectStatus
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_ProtectTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_ProtectTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_ProtectTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_ProtectTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_ProtectTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_ProtectTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_ProtectTeamInUserRoom_Next
	mov r0, r8
	mov r1, r6
	bl TryInflictProtectStatus
ZMove_ProtectTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_ProtectTeamInUserRoom_Loop
ZMove_ProtectTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Cure negative status and apply Safeguard to one target.
; r0=user, r1=target
ZMove_HealStatusAndSafeguardTarget:
	push {r4, r5, lr}
	mov r4, r0
	mov r5, r1
	mov r0, r4
	mov r1, r5
	mov r2, #1
	mov r3, #0
	bl EndNegativeStatusConditionWrapper
	mov r0, r4
	mov r1, r5
	bl TryInflictSafeguardStatus
	pop {r4, r5, pc}

; Heal status + Safeguard for the user and every ally in the user's room.
; r4=user on entry from ZMove_EffectFairy.
ZMove_FairyTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	mov r1, r8
	bl ZMove_HealStatusAndSafeguardTarget
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_FairyTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_FairyTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_FairyTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_FairyTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_FairyTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_FairyTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_FairyTeamInUserRoom_Next
	mov r0, r8
	mov r1, r6
	bl ZMove_HealStatusAndSafeguardTarget
ZMove_FairyTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_FairyTeamInUserRoom_Loop
ZMove_FairyTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Boost Def and SpDef by Z_MOVE_STAT_STAGES on one target.
; r0=user, r1=target
ZMove_BoostDefensiveStats:
	push {r4, r5, lr}
	mov r4, r0
	mov r5, r1
	mov r0, r4
	mov r1, r5
	mov r2, #DEFENSIVE_STAT_DEFENSE
	mov r3, #Z_MOVE_STAT_STAGES
	bl BoostDefensiveStat
	mov r0, r4
	mov r1, r5
	mov r2, #DEFENSIVE_STAT_SP_DEFENSE
	mov r3, #Z_MOVE_STAT_STAGES
	bl BoostDefensiveStat
	pop {r4, r5, pc}

; +2 Def / +2 SpDef for the user and every ally in the user's room.
; r4=user on entry from ZMove_EffectRock.
ZMove_BoostDefTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	mov r1, r8
	bl ZMove_BoostDefensiveStats
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_BoostDefTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_BoostDefTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_BoostDefTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_BoostDefTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_BoostDefTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_BoostDefTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_BoostDefTeamInUserRoom_Next
	mov r0, r8
	mov r1, r6
	bl ZMove_BoostDefensiveStats
ZMove_BoostDefTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_BoostDefTeamInUserRoom_Loop
ZMove_BoostDefTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Boost Def and SpDef by Z_MOVE_STEEL_DEF_STAGES on one target.
; r0=user, r1=target
ZMove_BoostSteelDefStats:
	push {r4, r5, lr}
	mov r4, r0
	mov r5, r1
	mov r0, r4
	mov r1, r5
	mov r2, #DEFENSIVE_STAT_DEFENSE
	mov r3, #Z_MOVE_STEEL_DEF_STAGES
	bl BoostDefensiveStat
	mov r0, r4
	mov r1, r5
	mov r2, #DEFENSIVE_STAT_SP_DEFENSE
	mov r3, #Z_MOVE_STEEL_DEF_STAGES
	bl BoostDefensiveStat
	pop {r4, r5, pc}

; +3 Def / +3 SpDef for the user and every ally in the user's room.
; r4=user on entry from ZMove_EffectSteel.
ZMove_BoostSteelDefTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	mov r1, r8
	bl ZMove_BoostSteelDefStats
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_BoostSteelDefTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_BoostSteelDefTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_BoostSteelDefTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_BoostSteelDefTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_BoostSteelDefTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_BoostSteelDefTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_BoostSteelDefTeamInUserRoom_Next
	mov r0, r8
	mov r1, r6
	bl ZMove_BoostSteelDefStats
ZMove_BoostSteelDefTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_BoostSteelDefTeamInUserRoom_Loop
ZMove_BoostSteelDefTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Boost Atk and SpAtk by Z_MOVE_STAT_STAGES on one target.
; r0=user, r1=target
ZMove_BoostOffensiveStats:
	push {r4, r5, lr}
	mov r4, r0
	mov r5, r1
	mov r0, r4
	mov r1, r5
	mov r2, #OFFENSIVE_STAT_ATTACK
	mov r3, #Z_MOVE_STAT_STAGES
	bl BoostOffensiveStat
	mov r0, r4
	mov r1, r5
	mov r2, #OFFENSIVE_STAT_SP_ATTACK
	mov r3, #Z_MOVE_STAT_STAGES
	bl BoostOffensiveStat
	pop {r4, r5, pc}

; +2 Atk / +2 SpAtk for the user and every ally in the user's room.
; r4=user on entry from ZMove_EffectDark.
ZMove_BoostOffTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	mov r1, r8
	bl ZMove_BoostOffensiveStats
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_BoostOffTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_BoostOffTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_BoostOffTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_BoostOffTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_BoostOffTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_BoostOffTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_BoostOffTeamInUserRoom_Next
	mov r0, r8
	mov r1, r6
	bl ZMove_BoostOffensiveStats
ZMove_BoostOffTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_BoostOffTeamInUserRoom_Loop
ZMove_BoostOffTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Restore full PP on all move slots for the user and every ally in the user's room.
; r4=user on entry from ZMove_EffectDragon.
ZMove_RestorePpTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	bl RestorePpAllMovesSetFlags
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_RestorePpTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_RestorePpTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_RestorePpTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_RestorePpTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_RestorePpTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_RestorePpTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_RestorePpTeamInUserRoom_Next
	mov r0, r6
	bl RestorePpAllMovesSetFlags
ZMove_RestorePpTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_RestorePpTeamInUserRoom_Loop
ZMove_RestorePpTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Grass Z-Move: full heal allies in room, then Leech Seed on every hit enemy.
; r4=user, r5=target struct, r6=move
ZMove_EffectGrass:
	bl ZMove_HealAlliesInUserRoom
	cmp r5, #0
	beq ZMove_TryApplyTypeEffectDone
	mov r7, #0
ZMove_EffectGrass_Loop:
	cmp r7, #0x41
	bhs ZMove_TryApplyTypeEffectDone
	ldr r1, [r5, r7, lsl #2]
	add r7, r7, #1
	cmp r1, #0
	beq ZMove_EffectGrass_Loop
	mov r0, r4
	mov r2, #1
	mov r3, #0
	push {r4, r5, r6, r7, lr}
	bl TryInflictLeechSeedStatus
	pop {r4, r5, r6, r7, lr}
	b ZMove_EffectGrass_Loop

; Electric Z-Move: paralysis on every hit enemy.
; r4=user, r5=target struct, r6=move
ZMove_EffectElectric:
	cmp r5, #0
	beq ZMove_TryApplyTypeEffectDone
	mov r7, #0
ZMove_EffectElectric_Loop:
	cmp r7, #0x41
	bhs ZMove_TryApplyTypeEffectDone
	ldr r1, [r5, r7, lsl #2]
	add r7, r7, #1
	cmp r1, #0
	beq ZMove_EffectElectric_Loop
	mov r0, r4
	mov r2, #0
	mov r3, #0
	push {r4, r5, r6, r7, lr}
	bl TryInflictParalysisStatus
	pop {r4, r5, r6, r7, lr}
	b ZMove_EffectElectric_Loop

; Ice Z-Move: freeze every hit enemy, then set Hail once.
; r4=user, r5=target struct, r6=move
ZMove_EffectIce:
	cmp r5, #0
	beq ZMove_EffectIce_Weather
	mov r7, #0
ZMove_EffectIce_Loop:
	cmp r7, #0x41
	bhs ZMove_EffectIce_Weather
	ldr r1, [r5, r7, lsl #2]
	add r7, r7, #1
	cmp r1, #0
	beq ZMove_EffectIce_Loop
	mov r0, r4
	mov r2, #0
	mov r3, #0
	push {r4, r5, r6, r7, lr}
	bl TryInflictFrozenStatus
	pop {r4, r5, r6, r7, lr}
	b ZMove_EffectIce_Loop
ZMove_EffectIce_Weather:
	mov r0, r4
	mov r1, #0
	mov r2, r6
	mov r3, #0
	bl DoMoveHail
	b ZMove_TryApplyTypeEffectDone

; Fighting Z-Move: Paused on room enemies; Focus Energy + Sure Shot + Counter on allies.
; r4=user, r6=move
ZMove_EffectFighting:
	mov r11, r6
	ldr r9, =ZMove_ApplyPausedToEnemy
	bl ZMove_IterEnemiesInUserRoom
	bl ZMove_FightingBuffTeamInUserRoom
	b ZMove_TryApplyTypeEffectDone

; Poison Z-Move: badly poison + lower speed on every hit enemy.
; r4=user, r5=target struct, r6=move
ZMove_EffectPoison:
	push {r8}
	cmp r5, #0
	beq ZMove_EffectPoison_Done
	mov r7, #0
ZMove_EffectPoison_Loop:
	cmp r7, #0x41
	bhs ZMove_EffectPoison_Done
	ldr r1, [r5, r7, lsl #2]
	add r7, r7, #1
	cmp r1, #0
	beq ZMove_EffectPoison_Loop
	mov r8, r1
	mov r0, r4
	mov r1, r8
	mov r2, #0
	mov r3, #0
	push {r4, r5, r6, r7, lr}
	bl TryInflictBadlyPoisonedStatus
	mov r0, r4
	mov r1, r8
	mov r2, #Z_MOVE_STAT_STAGES
	mov r3, #0
	bl LowerSpeed
	pop {r4, r5, r6, r7, lr}
	b ZMove_EffectPoison_Loop
ZMove_EffectPoison_Done:
	pop {r8}
	b ZMove_TryApplyTypeEffectDone

; Ground Z-Move: Gravity on the floor, then petrify room enemies.
; r4=user, r6=move
ZMove_EffectGround:
	mov r0, r4
	mov r1, #0
	mov r2, r6
	mov r3, #0
	bl DoMoveGravity
	ldr r9, =ZMove_ApplyPetrifiedToEnemy
	bl ZMove_IterEnemiesInUserRoom
	b ZMove_TryApplyTypeEffectDone

; Flying Z-Move: max speed boost for user and every ally in the user's room.
; r4=user, r5=target struct (unused), r6=move
ZMove_EffectFlying:
	bl ZMove_MaxSpeedTeamInUserRoom
	b ZMove_TryApplyTypeEffectDone

; Psychic Z-Move: sleep every enemy in the user's room.
; r4=user
ZMove_EffectPsychic:
	ldr r9, =ZMove_ApplySleepToEnemy
	bl ZMove_IterEnemiesInUserRoom
	b ZMove_TryApplyTypeEffectDone

; Bug Z-Move: -2 Atk/SpA/Def/SpD on every enemy in the user's room.
; r4=user
ZMove_EffectBug:
	ldr r9, =ZMove_ApplyBugStatDropToEnemy
	bl ZMove_IterEnemiesInUserRoom
	b ZMove_TryApplyTypeEffectDone

; Rock Z-Move: +2 Def / +2 SpDef for team in room, then Sandstorm once.
; r4=user, r5=target struct (unused), r6=move
ZMove_EffectRock:
	bl ZMove_BoostDefTeamInUserRoom
	mov r0, r4
	mov r1, #0
	mov r2, r6
	mov r3, #0
	bl DoMoveSandstorm
	b ZMove_TryApplyTypeEffectDone

; Ghost Z-Move: confuse every hit enemy.
; r4=user, r5=target struct, r6=move
ZMove_EffectGhost:
	cmp r5, #0
	beq ZMove_TryApplyTypeEffectDone
	mov r7, #0
ZMove_EffectGhost_Loop:
	cmp r7, #0x41
	bhs ZMove_TryApplyTypeEffectDone
	ldr r1, [r5, r7, lsl #2]
	add r7, r7, #1
	cmp r1, #0
	beq ZMove_EffectGhost_Loop
	mov r0, r4
	mov r2, #0
	mov r3, #0
	push {r4, r5, r6, r7, lr}
	bl TryInflictConfusedStatus
	pop {r4, r5, r6, r7, lr}
	b ZMove_EffectGhost_Loop

; Dragon Z-Move: restore all move-slot PP for team in room.
; r4=user, r5=target struct (unused), r6=move
ZMove_EffectDragon:
	bl ZMove_RestorePpTeamInUserRoom
	b ZMove_TryApplyTypeEffectDone

; Dark Z-Move: +2 Atk / +2 SpAtk for team in room.
; r4=user, r5=target struct (unused), r6=move
ZMove_EffectDark:
	bl ZMove_BoostOffTeamInUserRoom
	b ZMove_TryApplyTypeEffectDone

; r0=user, r1=ally, r11=move
ZMove_SteelBuffOneAlly:
	push {r4, r5, lr}
	mov r4, r0
	mov r5, r1
	mov r0, r4
	mov r1, r5
	bl ZMove_BoostDefensiveStats
	mov r0, r4
	mov r1, r5
	mov r2, r11
	mov r3, #0
	bl DoMoveReflect
	mov r0, r4
	mov r1, r5
	mov r2, r11
	mov r3, #0
	bl DoMoveLightScreen
	pop {r4, r5, pc}

; Steel Z-Move: +2 Def/SpDef, Reflect, Light Screen for allies in the user's room.
; r4=user, r11=move on entry.
ZMove_SteelTeamInUserRoom:
	push {r5-r8, lr}
	mov r8, r4
	mov r0, r8
	mov r1, r8
	bl ZMove_SteelBuffOneAlly
	bl PopulateActiveMonsterPtrs
	bl ZMove_GetDungeonPtrInR5
	mov r7, #0
ZMove_SteelTeamInUserRoom_Loop:
	cmp r7, #ACTIVE_MONSTER_SLOT_COUNT
	bhs ZMove_SteelTeamInUserRoom_Done
	mov r0, r5
	add r0, r0, r7, lsl #2
	add r0, r0, #ACTIVE_MONSTER_ARRAY_BASE
	ldr r6, [r0, #ACTIVE_MONSTER_PTRS_OFF]
	add r7, r7, #1
	cmp r6, #0
	beq ZMove_SteelTeamInUserRoom_Loop
	cmp r6, r8
	beq ZMove_SteelTeamInUserRoom_Loop
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq ZMove_SteelTeamInUserRoom_Loop
	mov r0, r8
	mov r1, r6
	mov r2, #0
	mov r3, #0
	push {r6, r7, lr}
	bl GetTreatmentBetweenMonsters
	cmp r0, #0
	bne ZMove_SteelTeamInUserRoom_Next
	mov r0, r8
	bl GetEntityDropeyeFlag
	mov r2, r0
	mov r0, r8
	add r0, r0, #4
	mov r1, r6
	add r1, r1, #4
	bl IsPositionInSight
	cmp r0, #0
	beq ZMove_SteelTeamInUserRoom_Next
	mov r0, r8
	mov r1, r6
	bl ZMove_SteelBuffOneAlly
ZMove_SteelTeamInUserRoom_Next:
	pop {r6, r7, lr}
	b ZMove_SteelTeamInUserRoom_Loop
ZMove_SteelTeamInUserRoom_Done:
	pop {r5-r8, pc}

; Steel Z-Move: +2 Def / +2 SpDef, Reflect, Light Screen for team in room.
; r4=user, r6=move
ZMove_EffectSteel:
	mov r11, r6
	bl ZMove_SteelTeamInUserRoom
	b ZMove_TryApplyTypeEffectDone

; Fairy Z-Move: heal status + Safeguard for team in room.
; r4=user, r5=target struct (unused), r6=move
ZMove_EffectFairy:
	bl ZMove_FairyTeamInUserRoom
	b ZMove_TryApplyTypeEffectDone
