; iq_change — Status-Resistence + Critical Dodger rework (US ov29 hooks + ov36 cave).

.open "overlay_0029.bin", ov_29

.org NonsleeperSleepImmunityBranch
	b NonsleeperSleepImmunitySkip

; Critical Dodger: defender takes crits at 1.2x instead of the crit multiplier.
.org CalcDamageCritMulSniper
	bl IqChange_CritMulSniper

.org CalcDamageCritMulNormal
	bl IqChange_CritMulNormal

.org TryInflictBurnSuccess
	bl IqChange_PostBurnSuccess

.org TryInflictPoisonSuccess
	bl IqChange_PostPoisonSuccess

.org TryInflictBadPoisonSuccess
	bl IqChange_PostBadPoisonSuccess

.org TryInflictParalysisSuccess
	bl IqChange_PostParalysisSuccess

.org TryInflictConfusionSuccess
	bl IqChange_PostConfusionSuccess

.org TryInflictCringeSuccess
	bl IqChange_PostCringeSuccess

; Undo prior wrong hook (wrapper already-asleep msg @ 0x02311980).
.org TryInflictSleepWrapperMsgLoad
	ldr r2, [pc, #0x50]

; Real success: after status-apply BL, r0!=0 means sleep landed.
.org TryInflictSleepSuccess
	b IqChange_PostSleepSuccess

.org TryInflictNightmareSuccess
	bl IqChange_PostNightmareSuccess

.org TryInflictFrozenSuccess
	bl IqChange_PostFrozenSuccess

.org TryInflictPetrifiedSuccess
	bl IqChange_PostPetrifiedSuccess

; Counter Basher: no physical full counter; 1/4 special counter at Counter Hitter's chance.
.org CounterBasherPhysicalRoll
	b CounterHitterPhysicalRoll

.org SpecialCounterStatusCheck
	b IqChange_SpecialCounter

; Party-wide exp bonuses. r7 = the monster receiving exp.
.org AddExpIqCheck
	bl IqChange_PartyExpIq

.org AddExpChestWonder
	bl IqChange_PartyExpChest

.org AddExpChestMiracle
	bl IqChange_PartyExpChest

.org AddExpExclusiveBoost
	b IqChange_PartyExpExclusive

; Intimidator: same close-range checks, but only at low HP, and 20% instead of 12%.
.org IntimidatorRollLoad
	bl IqChange_IntimidatorChance

.close

.open "overlay_0036.bin", ov_36

.org ov_36 + IqChangeCodeAddress

; Return r2 = crit multiplier (fx64*). r0/r1 preserved; r9 = defender.
IqChange_CritMulSniper:
	ldr r2, =CalcDamageCritMulSniperPtr
	b IqChange_CritMulDodger
IqChange_CritMulNormal:
	ldr r2, =CalcDamageCritMulNormalPtr
IqChange_CritMulDodger:
	ldr r2, [r2]
	push {r0-r2, lr}
	mov r0, r9
	mov r1, #IQ_CRITICAL_DODGER
	bl IqSkillIsEnabled
	cmp r0, #0
	ldrne r0, =IqChange_CritDodgerMul
	strne r0, [sp, #8]
	pop {r0-r2, pc}
	.pool
IqChange_CritDodgerMul:
	.word 0, CRIT_DODGER_MUL_FX64

IqChange_OnBadStatusInflicted:
	push {r4, r5, r6, r7, lr}
	mov r4, r0
	mov r5, r1
	mov r0, r5
	mov r1, #IQ_STATUS_RESISTENCE
	bl IqSkillIsEnabled
	cmp r0, #0
	beq IqChange_OnBadStatusInflicted_Done
	mov r0, #4
	bl DungeonRandRange
	cmp r0, #0
	beq IqChange_OnBadStatusInflicted_Atk
	cmp r0, #1
	beq IqChange_OnBadStatusInflicted_Spa
	cmp r0, #2
	beq IqChange_OnBadStatusInflicted_Def
	b IqChange_OnBadStatusInflicted_Spd

IqChange_OnBadStatusInflicted_Atk:
	mov r0, r4
	mov r1, r5
	mov r2, #OFFENSIVE_STAT_ATTACK
	mov r3, #STAT_STAGE_BOOST
	bl BoostOffensiveStat
	b IqChange_OnBadStatusInflicted_Done

IqChange_OnBadStatusInflicted_Spa:
	mov r0, r4
	mov r1, r5
	mov r2, #OFFENSIVE_STAT_SP_ATTACK
	mov r3, #STAT_STAGE_BOOST
	bl BoostOffensiveStat
	b IqChange_OnBadStatusInflicted_Done

IqChange_OnBadStatusInflicted_Def:
	mov r0, r4
	mov r1, r5
	mov r2, #DEFENSIVE_STAT_DEFENSE
	mov r3, #STAT_STAGE_BOOST
	bl BoostDefensiveStat
	b IqChange_OnBadStatusInflicted_Done

IqChange_OnBadStatusInflicted_Spd:
	mov r0, r4
	mov r1, r5
	mov r2, #DEFENSIVE_STAT_SP_DEFENSE
	mov r3, #STAT_STAGE_BOOST
	bl BoostDefensiveStat

IqChange_OnBadStatusInflicted_Done:
	pop {r4, r5, r6, r7, pc}

; Special-hit branch of the counter section: r0 = defender reflect status,
; r9 = defender, r5 = counter quarters. r0-r3 are dead at SpecialCounterDone.
IqChange_SpecialCounter:
	cmp r0, #STATUS_MIRROR_COAT
	bne IqChange_SpecialCounter_Basher
	mov r0, r9
	bl MirrorCoatCounterEffect
	add r5, r5, #4
IqChange_SpecialCounter_Basher:
	mov r0, r9
	mov r1, #IQ_COUNTER_BASHER
	bl IqSkillIsEnabled
	cmp r0, #0
	beq SpecialCounterDone
	mov r0, #100
	bl DungeonRandRange
	ldr r1, =CounterHitterChancePtr
	lsl r0, r0, #0x10
	ldrsh r1, [r1]
	cmp r1, r0, asr #16
	addgt r5, r5, #1
	b SpecialCounterDone
	.pool

IqChange_PostBurnSuccess:
	push {lr}
	mov r0, r5
	mov r1, r4
	bl IqChange_OnBadStatusInflicted
	pop {lr}
	mov r0, #1
	b TryInflictBurnEpilogue

IqChange_PostPoisonSuccess:
	push {lr}
	mov r0, r10
	mov r1, r9
	bl IqChange_OnBadStatusInflicted
	pop {lr}
	mov r0, #1
	b TryInflictPoisonEpilogue

IqChange_PostBadPoisonSuccess:
	push {lr}
	mov r0, r10
	mov r1, r9
	bl IqChange_OnBadStatusInflicted
	pop {lr}
	mov r0, #1
	b TryInflictBadPoisonEpilogue

IqChange_PostParalysisSuccess:
	push {lr}
	mov r0, r10
	mov r1, r9
	bl IqChange_OnBadStatusInflicted
	pop {lr}
	mov r0, #1
	b TryInflictParalysisEpilogue

IqChange_PostConfusionSuccess:
	push {lr}
	mov r0, r7
	mov r1, r6
	bl IqChange_OnBadStatusInflicted
	pop {lr}
	mov r0, #1
	b TryInflictConfusionEpilogue

IqChange_PostCringeSuccess:
	push {lr}
	mov r0, r5
	mov r1, r4
	bl IqChange_OnBadStatusInflicted
	pop {lr}
	mov r0, #1
	b TryInflictCringeEpilogue

; TryInflictSleep @ success: r8=user, r7=target, r0=apply result (nonzero=ok).
IqChange_PostSleepSuccess:
	push {r0, lr}
	cmp r0, #0
	beq IqChange_PostSleepSuccess_Resume
	mov r0, r8
	mov r1, r7
	bl IqChange_OnBadStatusInflicted
IqChange_PostSleepSuccess_Resume:
	pop {r0, lr}
	cmp r0, #0
	movne r0, #1
	moveq r0, #0
	and r0, r0, #0xff
	b TryInflictSleepEpilogue

IqChange_PostNightmareSuccess:
	push {lr}
	mov r0, r7
	mov r1, r6
	bl IqChange_OnBadStatusInflicted
	pop {lr}
	add sp, sp, #4
	b TryInflictNightmareEpilogue

IqChange_PostFrozenSuccess:
	push {lr}
	mov r0, r7
	mov r1, r6
	bl IqChange_OnBadStatusInflicted
	pop {lr}
	mov r0, r7
	b TryInflictFrozenResume

IqChange_PostPetrifiedSuccess:
	push {lr}
	mov r0, r6
	mov r1, r5
	bl IqChange_OnBadStatusInflicted
	pop {lr}
	pop {r3, r4, r5, r6, r7, r8, r9, pc}

; r0 = recipient, r1 = IQ id. Team members share the skill; others keep their own.
IqChange_PartyExpIq:
	push {r0, r1, lr}
	ldr r2, [r0, #0xb4]
	ldrb r2, [r2, #6]
	cmp r2, #0
	pop {r0, r1, lr}
	bne IqSkillIsEnabled
	mov r0, r1
	b TeamMemberHasEnabledIqSkill

; r0 = recipient, r1 = held item id. Team members share the chest; others keep their own.
IqChange_PartyExpChest:
	push {r0, r1, lr}
	ldr r2, [r0, #0xb4]
	ldrb r2, [r2, #6]
	cmp r2, #0
	pop {r0, r1, lr}
	bne ExpHeldItemBoostActive
	b IqChange_PartyHasHeldItem

; r1 = item id. True if any of the 4 dungeon party slots holds it (Klutz still blocks that slot).
IqChange_PartyHasHeldItem:
	push {r4, r5, r6, lr}
	mov r4, r1
	mov r5, #0
IqChange_PartyHasHeldItem_Loop:
	cmp r5, #4
	bge IqChange_PartyHasHeldItem_No
	ldr r0, =DungeonPtr
	ldr r0, [r0]
	add r0, r0, #0x328
	add r0, r0, #0x12800
	ldr r6, [r0, r5, lsl #2]
	mov r0, r6
	bl EntityIsValid
	cmp r0, #0
	beq IqChange_PartyHasHeldItem_Next
	mov r0, r6
	mov r1, r4
	bl ExpHeldItemBoostActive
	cmp r0, #0
	bne IqChange_PartyHasHeldItem_Yes
IqChange_PartyHasHeldItem_Next:
	add r5, r5, #1
	b IqChange_PartyHasHeldItem_Loop
IqChange_PartyHasHeldItem_Yes:
	mov r0, #1
	pop {r4, r5, r6, pc}
IqChange_PartyHasHeldItem_No:
	mov r0, #0
	pop {r4, r5, r6, pc}
	.pool

; Replaces the per-recipient exclusive-item check. Non-team recipients get no boost.
IqChange_PartyExpExclusive:
	push {lr}
	ldr r0, [r7, #0xb4]
	ldrb r0, [r0, #6]
	cmp r0, #0
	movne r0, #0
	bne IqChange_PartyExpExclusive_Done
	mov r0, #EXCLUSIVE_EFF_EXP_BOOST
	bl TeamMemberHasExclusiveItemEffectActive
IqChange_PartyExpExclusive_Done:
	pop {lr}
	b AddExpExclusiveResume

; r0 = roll 0..99, returned unchanged. r1 = chance, or 0 when not at low HP.
; r10 = the monster with Intimidator.
IqChange_IntimidatorChance:
	push {r0, lr}
	mov r0, r10
	bl HasLowHealth
	cmp r0, #0
	mov r1, #0
	movne r1, #INTIMIDATOR_CHANCE
	pop {r0, pc}

.close
