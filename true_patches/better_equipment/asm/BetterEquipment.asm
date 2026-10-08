; Held-item changes. Team-wide items use ItemIsActive.
; Lockon = Life Band, No-Aim = Lens, Bounce = Focus, Gold Ribbon = Bright Ribbon.
; Joy = PP, Whiff = Wish, Patsy = Expert Band, Curve = Z-Scarf, Racket = Rhythm.
; Munch Belt = Consistent Band.

; r0 = Z-gauge gain. Entered by a branch, so lr is still the caller.
; Doubles the gain when any party member holds the Z-Scarf, then replays
; ZMove_AddZGauge's push. The following branch is patched to
; ZMove_AddZGauge+4 when this module is applied on top of z_move_v2.
Eq_ScaleZGaugeGain:
	push {r0, r1, r2, r3, r4, lr}
	mov r4, r0
	ldr r0, =DungeonPtr
	ldr r0, [r0]
	cmp r0, #0
	beq Eq_ScaleDone
	mov r3, #0
Eq_ScaleLoop:
	cmp r3, #4
	bge Eq_ScaleDone
	add r1, r0, r3, lsl #2
	add r1, r1, #0x12000
	ldr r1, [r1, #0xb28]
	cmp r1, #0
	beq Eq_ScaleNext
	push {r0, r3}
	mov r0, r1
	bl EntityIsValid
	cmp r0, #0
	pop {r0, r3}
	beq Eq_ScaleNext
	add r1, r0, r3, lsl #2
	add r1, r1, #0x12000
	ldr r1, [r1, #0xb28]
	push {r0, r3}
	mov r0, r1
	mov r1, #ITEM_ROCKY
	bl HasHeldItem
	cmp r0, #0
	pop {r0, r3}
	beq Eq_ScaleNext
	lsl r4, r4, #1
	b Eq_ScaleDone
Eq_ScaleNext:
	add r3, r3, #1
	b Eq_ScaleLoop
Eq_ScaleDone:
	str r4, [sp]
	pop {r0, r1, r2, r3, r4, lr}
	push {r1, r2, lr}
Eq_ScaleZGaugeBack:
	b Eq_ScaleZGaugeBack

Eq_ItemIsActive:
	push {r4, r5, r6, r7, r8, lr}
	mov r4, r0
	mov r5, r1
	bl IsMonster
	cmp r0, #0
	beq Eq_ItemNo
	mov r0, r4
	mov r1, r5
	bl Eq_SelfHolds
	cmp r0, #0
	bne Eq_ItemYes
	mov r0, r5
	bl Eq_ItemIsTeamWide
	cmp r0, #0
	beq Eq_ItemNo
	ldr r0, [r4, #0xb4]
	cmp r0, #0
	beq Eq_ItemNo
	ldrb r0, [r0, #6]
	cmp r0, #0
	bne Eq_ItemNo
	ldr r0, =DungeonPtr
	ldr r6, [r0]
	cmp r6, #0
	beq Eq_ItemNo
	mov r7, #0
Eq_TeamLoop:
	cmp r7, #4
	bge Eq_ItemNo
	add r0, r6, r7, lsl #2
	add r0, r0, #0x12000
	ldr r8, [r0, #0xb28]
	cmp r8, #0
	beq Eq_TeamNext
	mov r0, r8
	bl EntityIsValid
	cmp r0, #0
	beq Eq_TeamNext
	mov r0, r8
	mov r1, r5
	bl Eq_SelfHolds
	cmp r0, #0
	bne Eq_ItemYes
Eq_TeamNext:
	add r7, r7, #1
	b Eq_TeamLoop
Eq_ItemYes:
	mov r0, #1
	pop {r4, r5, r6, r7, r8, pc}
Eq_ItemNo:
	mov r0, #0
	pop {r4, r5, r6, r7, r8, pc}

; r0 entity, r1 item. Klutz disables the holder's own item.
Eq_SelfHolds:
	push {r4, r5, r6, lr}
	mov r4, r0
	mov r5, r1
	bl IsMonster
	cmp r0, #0
	moveq r0, #0
	popeq {r4, r5, r6, pc}
	mov r0, r4
	mov r1, #KLUTZ_ABILITY
	bl AbilityIsActiveVeneer
	cmp r0, #0
	movne r0, #0
	popne {r4, r5, r6, pc}
	mov r0, r4
	mov r1, r5
	bl HasHeldItem
	pop {r4, r5, r6, pc}

; r0 item id.
Eq_ItemIsTeamWide:
	push {r4, lr}
	ldr r4, =Eq_TeamWideTable
Eq_TeamWideLoop:
	ldrb r1, [r4]
	cmp r1, #0
	beq Eq_TeamWideNo
	cmp r1, r0
	beq Eq_TeamWideYes
	add r4, r4, #1
	b Eq_TeamWideLoop
Eq_TeamWideYes:
	mov r0, #1
	pop {r4, pc}
Eq_TeamWideNo:
	mov r0, #0
	pop {r4, pc}

; Holding Ability Monitor (item 39) makes AbilityIsActive fail for that holder.
; Vanilla AbilityIsActive starts with IsMonster. HasHeldItem does not.
Eq_Ability:
	push {r0, r1, r2, r3, r4, lr}
	mov r4, r0
	bl IsMonster
	cmp r0, #0
	beq Eq_AbilityPass
	mov r0, r4
	mov r1, #ITEM_ABILITY
	bl HasHeldItem
	cmp r0, #0
	beq Eq_AbilityPass
	pop {r0, r1, r2, r3, r4, lr}
	mov r0, #0
	bx lr
Eq_AbilityPass:
	pop {r0, r1, r2, r3, r4, lr}
	push {r3, r4, r5, lr}
	b AbilityIsActiveBody

; Not-very-effective hits become neutral while Consistent Band is held.
; r0 attacker, r1 defender, r2 move. Return stays in r0.
Eq_Matchup:
	push {r0, r1, r2, r3, r4, lr}
	bl Eq_MatchupInvoke
	mov r4, r0
	ldr r0, [sp]
	mov r1, #ITEM_CONSISTENT
	bl Eq_ItemIsActive
	cmp r0, #0
	beq Eq_MatchupStore
	cmp r4, #MATCHUP_NOT_VERY
	moveq r4, #MATCHUP_NEUTRAL
Eq_MatchupStore:
	str r4, [sp]
	pop {r0, r1, r2, r3, r4, pc}
Eq_MatchupInvoke:
	push {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
	b GetTypeMatchupBody

; Life Band scales power x1.5 and drains HP. Expert Band scales
; super-effective power x1.5. Rhythm scales by the streak recorded at move start.
; Eight registers keep the saved power at [sp, #12] and the move id,
; which callers stored at [sp, #0xC], at [sp, #0x2C].
Eq_CalcDamage:
	push {r0, r1, r2, r3, r4, r5, r6, lr}
	mov r4, r0
	mov r1, #ITEM_LIFE
	bl Eq_ItemIsActive
	cmp r0, #0
	beq Eq_CalcExpert
	ldr r0, [sp, #12]
	cmp r0, #0
	beq Eq_CalcDrain
	mov r1, #15
	mul r0, r1, r0
	mov r1, #10
	bl SignedDivide
	cmp r0, #1
	movlt r0, #1
	str r0, [sp, #12]
Eq_CalcDrain:
	mov r0, r4
	bl Eq_DrainTenth
Eq_CalcExpert:
	mov r0, r4
	mov r1, #ITEM_EXPERT
	bl Eq_ItemIsActive
	cmp r0, #0
	beq Eq_CalcRhythm
	ldr r0, [sp]
	ldr r1, [sp, #4]
	ldr r2, [sp, #8]
	bl GetTypeMatchupBothTypes
	cmp r0, #MATCHUP_SUPER_EFFECTIVE
	bne Eq_CalcRhythm
	ldr r0, [sp, #12]
	cmp r0, #0
	beq Eq_CalcRhythm
	mov r1, #15
	mul r0, r1, r0
	mov r1, #10
	bl SignedDivide
	cmp r0, #1
	movlt r0, #1
	str r0, [sp, #12]
Eq_CalcRhythm:
	mov r0, r4
	mov r1, #ITEM_RHYTHM
	bl Eq_ItemIsActive
	cmp r0, #0
	beq Eq_CalcRestore
	ldrh r1, [sp, #0x2C]
	mov r0, r4
	bl Eq_RhythmMultiplier
	cmp r0, #4
	beq Eq_CalcRestore
	mov r5, r0
	ldr r0, [sp, #12]
	cmp r0, #0
	beq Eq_CalcRestore
	mul r0, r5, r0
	mov r1, #4
	bl SignedDivide
	cmp r0, #1
	movlt r0, #1
	str r0, [sp, #12]
Eq_CalcRestore:
	pop {r0, r1, r2, r3, r4, r5, r6, lr}
	push {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
	b CalcDamageBody

; r0 entity. Subtract max(1, maxHP/10) from current HP, floored at 1.
Eq_DrainTenth:
	push {r4, lr}
	mov r4, r0
	ldr r2, [r4, #0xb4]
	ldrsh r0, [r2, #0x12]
	ldrsh r1, [r2, #0x16]
	add r0, r0, r1
	ldr r1, =999
	cmp r0, r1
	movgt r0, r1
	cmp r0, #1
	movlt r0, #1
	mov r1, #10
	bl SignedDivide
	cmp r0, #1
	movlt r0, #1
	ldr r2, [r4, #0xb4]
	ldrsh r1, [r2, #0x10]
	sub r1, r1, r0
	cmp r1, #1
	movlt r1, #1
	strh r1, [r2, #0x10]
	mov r0, r4
	bl RefreshEntityAfterStatChange
	pop {r4, pc}

; Lens Scarf: accuracy stage +2, past the move rank cap. Preserve the flags.
Eq_Accuracy:
	mrs r12, cpsr
	push {r0, r1, r2, r3, r12, lr}
	ldrsh r9, [r9, #0x2c]
	mov r0, r7
	mov r1, #ITEM_LENS
	bl Eq_ItemIsActive
	cmp r0, #0
	addne r9, r9, #2
	pop {r0, r1, r2, r3, r12, lr}
	msr cpsr_f, r12
	b AccuracyStageContinue

; Bright Ribbon: evasion stage +2, past the move rank cap.
Eq_Evasion:
	push {r0, r1, r2, r3, r4, lr}
	ldrsh r10, [r5, #0x2e]
	mov r0, r6
	mov r1, #ITEM_BRIGHT
	bl Eq_ItemIsActive
	cmp r0, #0
	addne r10, r10, #2
	pop {r0, r1, r2, r3, r4, lr}
	b EvasionStageContinue

; Bands: the matching stage +2 while held. This is added on top of the
; stage already used for damage, including a stage that moves capped at +6.
; [sp, #0x18] is 0 for physical, [sp, #0x44] holds the attacker stage,
; r4 the defender stage. [sp, #0xF8] gates defender items as in vanilla.
Eq_BandStage:
	push {r0, r1, r2, r3, r12, lr}
	ldr r0, [sp, #0x30]
	cmp r0, #0
	moveq r1, #ITEM_POWER_BAND
	movne r1, #ITEM_SPECIAL_BAND
	mov r0, r10
	bl Eq_ItemIsActive
	cmp r0, #0
	beq Eq_BandDefender
	ldr r0, [sp, #0x5C]
	add r0, r0, #2
	str r0, [sp, #0x5C]
Eq_BandDefender:
	ldr r0, [sp, #0x110]
	cmp r0, #0
	beq Eq_BandDone
	ldr r0, [sp, #0x30]
	cmp r0, #0
	moveq r1, #ITEM_DEF_BAND
	movne r1, #ITEM_ZINC_BAND
	mov r0, r9
	bl Eq_ItemIsActive
	cmp r0, #0
	beq Eq_BandDone
	add r4, r4, #2
Eq_BandDone:
	pop {r0, r1, r2, r3, r12, lr}
	ldr r0, [sp, #0x44]
	b BandStageContinue

; Weather Band already branches on this result. Make the check team-wide.
Eq_Weather:
	push {r1, r2, r3, lr}
	mov r0, r4
	mov r1, #ITEM_WEATHER
	bl Eq_ItemIsActive
	pop {r1, r2, r3, lr}
	b WeatherBandContinue

Eq_Nightmare:
	push {r0, r1, r2, r3, r4, lr}
	mov r0, r1
	mov r1, #ITEM_INSOMNI
	bl Eq_ItemIsActive
	cmp r0, #0
	pop {r0, r1, r2, r3, r4, lr}
	bne Eq_StatusBlocked
	push {r3, r4, r5, r6, r7, r8, lr}
	b TryInflictNightmareBody

Eq_Napping:
	push {r0, r1, r2, r3, r4, lr}
	mov r0, r1
	mov r1, #ITEM_INSOMNI
	bl Eq_ItemIsActive
	cmp r0, #0
	pop {r0, r1, r2, r3, r4, lr}
	bne Eq_StatusBlocked
	push {r3, r4, r5, r6, r7, r8, lr}
	b TryInflictNappingBody

Eq_Yawning:
	push {r0, r1, r2, r3, r4, lr}
	mov r0, r1
	mov r1, #ITEM_INSOMNI
	bl Eq_ItemIsActive
	cmp r0, #0
	pop {r0, r1, r2, r3, r4, lr}
	bne Eq_StatusBlocked
	push {r3, r4, r5, r6, lr}
	b TryInflictYawningBody

Eq_StatusBlocked:
	mov r0, #0
	bx lr

; Twist Band also blocks Defense and Special Defense drops, team-wide.
Eq_DefDrop:
	push {r0, r1, r2, r3, r4, lr}
	mov r0, r7
	mov r1, #ITEM_TWIST
	bl Eq_ItemIsActive
	cmp r0, #0
	pop {r0, r1, r2, r3, r4, lr}
	bne Eq_DefAbort
	mov r5, r3
	b LowerDefensiveResume
Eq_DefAbort:
	mov r0, #0
	b LowerDefensiveAbort

; Focus Scarf: a super-effective matchup against the holder counts as neutral.
; r0 attacker, r1 defender, r2 defending-type index, r3 attack type.
Eq_FocusMatchup:
	push {r4, r5, r6, lr}
	mov r4, r1
	bl Eq_FocusMatchupInvoke
	mov r5, r0
	mov r0, r4
	mov r1, #ITEM_FOCUS
	bl Eq_ItemIsActive
	cmp r0, #0
	beq Eq_FocusMatchupOut
	cmp r5, #MATCHUP_SUPER_EFFECTIVE
	moveq r5, #MATCHUP_NEUTRAL
Eq_FocusMatchupOut:
	mov r0, r5
	pop {r4, r5, r6, pc}
Eq_FocusMatchupInvoke:
	push {r3, r4, r5, r6, r7, lr}
	b GetTypeMatchupResume

; Record the move, then the original prologue.
Eq_MoveBegin:
	push {r0, r1, r2, r3, r4, lr}
	ldr r4, [sp, #0x1C]
	ldr r2, =Eq_CurrentMove
	cmp r4, #0
	beq Eq_MoveClear
	ldrh r1, [r4, #4]
	strh r1, [r2]
	str r0, [r2, #4]
	bl Eq_RhythmObserve
	b Eq_MoveBeginOut
Eq_MoveClear:
	mov r1, #0
	strh r1, [r2]
	str r1, [r2, #4]
Eq_MoveBeginOut:
	pop {r0, r1, r2, r3, r4, lr}
	push {r4, r5, r6, r7, r8, r9, r10, lr}
	b MoveExecuteBody

; r0 entity, r1 move id. Status moves and any different move reset the streak.
Eq_RhythmObserve:
	push {r4, r5, r6, r7, r8, lr}
	mov r4, r0
	mov r5, r1
	mov r1, #ITEM_RHYTHM
	bl Eq_ItemIsActive
	cmp r0, #0
	popeq {r4, r5, r6, r7, r8, pc}
	mov r0, r5
	bl GetMoveCategory
	mov r6, r0
	ldr r7, =Eq_RhythmSlots
	mov r2, #0
	mov r3, #16
Eq_RhythmFind:
	cmp r2, #16
	bge Eq_RhythmAlloc
	ldr r0, [r7, r2, lsl #3]
	cmp r0, r4
	beq Eq_RhythmHit
	cmp r0, #0
	cmpeq r3, #16
	moveq r3, r2
	add r2, r2, #1
	b Eq_RhythmFind
Eq_RhythmAlloc:
	cmp r3, #16
	movge r3, #0
	mov r2, r3
	add r0, r7, r2, lsl #3
	mov r3, #0
	b Eq_RhythmWrite
Eq_RhythmHit:
	add r0, r7, r2, lsl #3
	ldrh r1, [r0, #4]
	ldrb r3, [r0, #6]
	cmp r6, #MOVE_CATEGORY_STATUS
	beq Eq_RhythmReset
	cmp r1, r5
	bne Eq_RhythmReset
	add r3, r3, #1
	cmp r3, #4
	movgt r3, #4
	b Eq_RhythmWrite
Eq_RhythmReset:
	mov r3, #0
Eq_RhythmWrite:
	str r4, [r0]
	strh r5, [r0, #4]
	strb r3, [r0, #6]
	pop {r4, r5, r6, r7, r8, pc}

; r0 entity, r1 move id. Returns 4 + streak (x1.25 per repeat, cap x2), or 4.
Eq_RhythmMultiplier:
	push {r4, r5, r6, lr}
	mov r4, r0
	mov r5, r1
	ldr r6, =Eq_RhythmSlots
	mov r3, #0
Eq_RhythmMulFind:
	cmp r3, #16
	bge Eq_RhythmMulNone
	ldr r0, [r6, r3, lsl #3]
	cmp r0, r4
	beq Eq_RhythmMulHit
	add r3, r3, #1
	b Eq_RhythmMulFind
Eq_RhythmMulHit:
	add r0, r6, r3, lsl #3
	ldrh r1, [r0, #4]
	cmp r1, r5
	bne Eq_RhythmMulNone
	ldrb r0, [r0, #6]
	add r0, r0, #4
	pop {r4, r5, r6, pc}
Eq_RhythmMulNone:
	mov r0, #4
	pop {r4, r5, r6, pc}

; Second +1 PP after Deep Breather's own restore. r5 is the team entity.
Eq_PpEntry:
	push {r0, r1, r2, r3, r4, lr}
	mov r0, r5
	cmp r0, #0
	beq Eq_PpSkip
	bl EntityIsValid
	cmp r0, #0
	beq Eq_PpSkip
	mov r0, r5
	mov r1, #ITEM_PP
	bl Eq_ItemIsActive
	cmp r0, #0
	beq Eq_PpSkip
	mov r0, r5
	bl Eq_RestoreRandomPp
Eq_PpSkip:
	pop {r0, r1, r2, r3, r4, lr}
	add r0, r6, #1
	b DeepBreatherStepNext

Eq_RestoreRandomPp:
	push {r4, r5, r6, r7, r8, lr}
	sub sp, sp, #8
	ldr r4, [r0, #0xb4]
	cmp r4, #0
	beq Eq_PpDone
	add r4, r4, #0x124
	mov r5, #0
	mov r6, #0
Eq_PpScan:
	cmp r6, #4
	bge Eq_PpPick
	ldrb r0, [r4, r6, lsl #3]
	tst r0, #1
	beq Eq_PpNext
	add r0, r4, r6, lsl #3
	bl GetMaxPp
	add r1, r4, r6, lsl #3
	ldrb r2, [r1, #6]
	cmp r2, r0
	bcs Eq_PpNext
	lsl r2, r5, #1
	strh r6, [sp, r2]
	add r5, r5, #1
Eq_PpNext:
	add r6, r6, #1
	b Eq_PpScan
Eq_PpPick:
	cmp r5, #0
	ble Eq_PpDone
	mov r0, r5
	bl DungeonRand
	lsl r0, r0, #16
	asr r0, r0, #15
	ldrsh r0, [sp, r0]
	add r1, r4, r0, lsl #3
	ldrb r0, [r1, #6]
	add r0, r0, #1
	strb r0, [r1, #6]
Eq_PpDone:
	add sp, sp, #8
	pop {r4, r5, r6, r7, r8, pc}

; Chain after the Z-Move ApplyDamage hook. Stack arguments stay put.
Eq_ApplyDamage:
	ldr r12, =Eq_InAfterHit
	ldrb r12, [r12]
	cmp r12, #0
	bne Eq_PriorApplyDamage
	ldr r12, =Eq_HitScratch
	str r0, [r12]
	str r1, [r12, #4]
	str r2, [r12, #8]
	str lr, [r12, #12]
	mov lr, #0
	str lr, [r12, #16]
	cmp r1, #0
	beq Eq_ApplyGo
	ldr r12, [r1, #0xb4]
	cmp r12, #0
	beq Eq_ApplyGo
	ldrsh r12, [r12, #0x10]
	ldr lr, =Eq_HitScratch
	str r12, [lr, #16]
Eq_ApplyGo:
	ldr lr, =Eq_ApplyReturn
	b Eq_PriorApplyDamage

Eq_ApplyReturn:
	ldr r12, =Eq_InAfterHit
	mov lr, #1
	strb lr, [r12]
	push {r0, r4, r5, r6, r7, r8, r9, lr}
	ldr r4, =Eq_HitScratch
	ldr r5, [r4]
	ldr r6, [r4, #4]
	ldr r7, [r4, #16]
	ldr r0, =Eq_CurrentUser
	ldr r0, [r0]
	cmp r0, r5
	bne Eq_AfterDone
	ldr r0, =Eq_CurrentMove
	ldrh r8, [r0]
	cmp r8, #0
	beq Eq_AfterDone
	mov r0, r5
	mov r1, #ITEM_WISH
	bl Eq_ItemIsActive
	cmp r0, #0
	beq Eq_AfterDone
	ldr r0, [r6, #0xb4]
	cmp r0, #0
	beq Eq_AfterDone
	ldrsh r1, [r0, #0x10]
	sub r0, r7, r1
	cmp r0, #0
	ble Eq_AfterDone
	mov r1, #8
	bl SignedDivide
	cmp r0, #0
	beq Eq_AfterDone
	mov r1, r0
	mov r0, r5
	bl Eq_Heal
Eq_AfterDone:
	pop {r0, r4, r5, r6, r7, r8, r9, lr}
	ldr r12, =Eq_InAfterHit
	mov lr, #0
	strb lr, [r12]
	ldr lr, =Eq_HitScratch
	ldr lr, [lr, #12]
	bx lr

; r0 entity, r1 amount. Cap at max HP.
Eq_Heal:
	push {r4, r5, r6, lr}
	mov r4, r0
	mov r5, r1
	ldr r2, [r4, #0xb4]
	cmp r2, #0
	beq Eq_HealDone
	ldrsh r0, [r2, #0x10]
	add r0, r0, r5
	ldrsh r1, [r2, #0x12]
	ldrsh r3, [r2, #0x16]
	add r1, r1, r3
	ldr r3, =999
	cmp r1, r3
	movgt r1, r3
	cmp r0, r1
	movgt r0, r1
	strh r0, [r2, #0x10]
	mov r0, r4
	bl RefreshEntityAfterStatChange
Eq_HealDone:
	pop {r4, r5, r6, pc}

.align 4
Eq_TeamWideTable:
	.byte ITEM_TWIST
	.byte ITEM_NO_STICK
	.byte ITEM_PERSIM
	.byte ITEM_PECHA
	.byte ITEM_INSOMNI
	.byte ITEM_SNEAK
	.byte ITEM_TRAP
	.byte ITEM_WEATHER
	.byte 0

.align 4
Eq_HitScratch:
	.fill 20, 0
Eq_InAfterHit:
	.byte 0
.align 4
Eq_CurrentMove:
	.dh 0
	.dh 0
Eq_CurrentUser:
	.word 0
Eq_RhythmSlots:
	.fill 128, 0

; Distribute Band. The six stat-rank functions start with push {r0-r3}.
; r0 = user, r1 = target, r2 = which stat, r3 = stages. Extra stack words,
; when the caller passed any, are forwarded unchanged.
; While the flag is set, the call applies only to r1.
Eq_DistLowerOff:
	ldr r12, =LowerOffensiveStatResume
	b Eq_DistCommon
Eq_DistLowerDef:
	ldr r12, =LowerDefensiveStatResume
	b Eq_DistCommon
Eq_DistBoostOff:
	ldr r12, =BoostOffensiveStatResume
	b Eq_DistCommon
Eq_DistBoostDef:
	ldr r12, =BoostDefensiveStatResume
	b Eq_DistCommon
Eq_DistBoostHit:
	ldr r12, =BoostHitChanceStatResume
	b Eq_DistCommon
Eq_DistLowerHit:
	ldr r12, =LowerHitChanceStatResume
	b Eq_DistCommon

Eq_DistCommon:
	push {r4}
	ldr r4, =Eq_DistFlag
	ldrb r4, [r4]
	cmp r4, #0
	pop {r4}
	bne Eq_DistGo
	b Eq_DistShare
Eq_DistGo:
	push {r0, r1, r2, r3}
	bx r12

Eq_DistShare:
	push {r4, r5, r6, r7, r8, r9, r10, lr}
	ldr r4, [sp, #0x20]
	ldr r5, [sp, #0x24]
	ldr r6, =Eq_DistStack
	str r4, [r6]
	str r5, [r6, #4]
	sub r4, r12, #4
	ldr r6, =Eq_DistFunc
	str r4, [r6]
	ldr r6, =Eq_DistSaved
	str r0, [r6]
	str r1, [r6, #4]
	str r2, [r6, #8]
	str r3, [r6, #12]
	mov r0, r1
	bl EntityIsValid
	cmp r0, #0
	beq Eq_DistShareOut
	ldr r4, =Eq_DistSaved
	ldr r0, [r4, #4]
	mov r1, #ITEM_DISTRIBUTE
	bl Eq_SelfHolds
	cmp r0, #0
	beq Eq_DistShareOut
	ldr r4, =Eq_DistSaved
	ldr r4, [r4, #4]
	ldrb r0, [r4, #0x25]
	cmp r0, #0xFF
	beq Eq_DistShareOut
	ldr r0, =DungeonPtr
	ldr r0, [r0]
	cmp r0, #0
	beq Eq_DistShareOut
	ldr r0, =Eq_DistSaved
	ldr r0, [r0, #4]
	bl Eq_DistCount
	cmp r0, #2
	bge Eq_DistShareOut
	ldr r0, =Eq_DistFlag
	mov r1, #1
	strb r1, [r0]
	mov r8, #0
Eq_DistLoop:
	cmp r8, #20
	bge Eq_DistLoopEnd
	ldr r0, =DungeonPtr
	ldr r0, [r0]
	add r0, r0, r8, lsl #2
	add r0, r0, #0x12000
	ldr r6, [r0, #0xB78]
	cmp r6, #0
	beq Eq_DistNext
	ldr r4, =Eq_DistSaved
	ldr r4, [r4, #4]
	cmp r6, r4
	beq Eq_DistNext
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq Eq_DistNext
	ldr r0, [r6, #0xB4]
	cmp r0, #0
	beq Eq_DistNext
	ldrsh r0, [r0, #0x10]
	cmp r0, #0
	ble Eq_DistNext
	ldr r4, =Eq_DistSaved
	ldr r4, [r4, #4]
	ldrb r0, [r4, #0x25]
	ldrb r1, [r6, #0x25]
	cmp r0, r1
	bne Eq_DistNext
	mov r0, r4
	mov r1, r6
	bl Eq_DistSameSide
	cmp r0, #0
	beq Eq_DistNext
	ldr r5, =Eq_DistSaved
	ldr r0, [r5]
	mov r1, r6
	ldr r2, [r5, #8]
	ldr r3, [r5, #12]
	ldr r4, =Eq_DistStack
	sub sp, sp, #8
	ldr r7, [r4]
	str r7, [sp]
	ldr r7, [r4, #4]
	str r7, [sp, #4]
	ldr r4, =Eq_DistFunc
	ldr r4, [r4]
	blx r4
	add sp, sp, #8
Eq_DistNext:
	add r8, r8, #1
	b Eq_DistLoop
Eq_DistLoopEnd:
	ldr r0, =Eq_DistFlag
	mov r1, #0
	strb r1, [r0]
Eq_DistShareOut:
	ldr r5, =Eq_DistSaved
	ldr r0, [r5]
	ldr r1, [r5, #4]
	ldr r2, [r5, #8]
	ldr r3, [r5, #12]
	ldr r12, =Eq_DistFunc
	ldr r12, [r12]
	add r12, r12, #4
	pop {r4, r5, r6, r7, r8, r9, r10, lr}
	b Eq_DistGo

; r0 = target. Counts allies on the target's side who hold the band.
Eq_DistCount:
	push {r3, r4, r5, r6, r7, r8, r9, lr}
	mov r4, r0
	ldr r0, =DungeonPtr
	ldr r0, [r0]
	cmp r0, #0
	moveq r0, #0
	beq Eq_DistCountOut
	mov r8, #0
	mov r7, #0
Eq_DistCountLoop:
	cmp r7, #20
	bge Eq_DistCountSum
	ldr r0, =DungeonPtr
	ldr r0, [r0]
	add r0, r0, r7, lsl #2
	add r0, r0, #0x12000
	ldr r6, [r0, #0xB78]
	cmp r6, #0
	beq Eq_DistCountNext
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq Eq_DistCountNext
	mov r0, r4
	mov r1, r6
	bl Eq_DistSameSide
	cmp r0, #0
	beq Eq_DistCountNext
	mov r0, r6
	mov r1, #ITEM_DISTRIBUTE
	bl Eq_SelfHolds
	cmp r0, #0
	beq Eq_DistCountNext
	add r8, r8, #1
Eq_DistCountNext:
	add r7, r7, #1
	b Eq_DistCountLoop
Eq_DistCountSum:
	mov r0, r8
Eq_DistCountOut:
	pop {r3, r4, r5, r6, r7, r8, r9, pc}

; r0 = reference, r1 = other. 1 when both are allies, or both are enemies.
; An allied guest counts with the team.
Eq_DistSameSide:
	push {r4, r5, r6, lr}
	ldr r4, [r0, #0xB4]
	ldr r5, [r1, #0xB4]
	cmp r4, #0
	cmpne r5, #0
	beq Eq_DistSideNo
	ldrb r0, [r4, #6]
	ldrb r2, [r4, #8]
	mov r3, #1
	cmp r0, #0
	moveq r3, #0
	cmp r2, #0
	movne r3, #0
	ldrb r0, [r5, #6]
	ldrb r2, [r5, #8]
	mov r4, #1
	cmp r0, #0
	moveq r4, #0
	cmp r2, #0
	movne r4, #0
	cmp r3, r4
	moveq r0, #1
	movne r0, #0
	pop {r4, r5, r6, pc}
Eq_DistSideNo:
	mov r0, #0
	pop {r4, r5, r6, pc}

.align 4
Eq_DistFlag:
	.byte 0
.align 4
Eq_DistFunc:
	.word 0
Eq_DistStack:
	.word 0
	.word 0
Eq_DistSaved:
	.word 0
	.word 0
	.word 0
	.word 0

.pool
