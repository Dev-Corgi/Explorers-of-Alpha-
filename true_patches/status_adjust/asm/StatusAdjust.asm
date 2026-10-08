; status_adjust — ov29 hook sites + ov36 cave.

.open "overlay_0029.bin", ov_29

.org CounterStatusDurationAddSite
	b StatusAdjust_CounterForceDuration

.org ProtectStatusDurationAddSite
	b StatusAdjust_ProtectForceDuration

.org MirrorCoatStatusDurationAddSite
	b StatusAdjust_MirrorCoatForceDuration

.org EndureStatusDurationAddSite
	b StatusAdjust_EndureForceDuration

; Z flag from the preceding tst #0x10 decides; lr is live at both sites, so no bl.
.org SpitePpZeroSite
	bne StatusAdjust_SpitePpReduce

.org GrudgePpZeroSite
	bne StatusAdjust_GrudgePpReduce

; Skip Alpha's ov36 exclusive trampoline (can miss the mul). Go straight to it.
.org ReflectStatusBranch
	beq ReflectDamageMulEntry

.org LightScreenStatusBranch
	beq LightScreenDamageMulEntry

; r0 is the damage fx64 pointer and must be kept. r2 becomes the 1/3 factor.
.org ReflectDamageMulLoad
	bl StatusAdjust_ScreenThird

.org LightScreenDamageMulLoad
	bl StatusAdjust_ScreenThird

; Stat stage limits: 10 +- 6 (STAT_STAGE_MIN..STAT_STAGE_MAX).
.org StatStageLowerOffensiveFloor
	bl StatusAdjust_StageFloor
.org StatStageLowerDefensiveFloor
	bl StatusAdjust_StageFloor
.org StatStageBoostOffensiveCeil
	bl StatusAdjust_StageCeil
.org StatStageBoostOffensiveCeilNop
	nop
.org StatStageBoostDefensiveCeil
	bl StatusAdjust_StageCeil
.org StatStageBoostDefensiveCeilNop
	nop

.org StatStageBoostHitChanceMaxCheck
	cmp r0, #STAT_STAGE_MAX
.org StatStageBoostHitChanceClampCmp
	cmp r0, #STAT_STAGE_MAX
.org StatStageBoostHitChanceClampMov
	movgt r0, #STAT_STAGE_MAX
.org StatStageLowerHitChanceMinCheck
	cmp r0, #STAT_STAGE_MIN
.org StatStageLowerHitChanceClampCmp
	cmp r0, #STAT_STAGE_MIN
.org StatStageLowerHitChanceClampMov
	movlt r0, #STAT_STAGE_MIN
.org StatStageMaxOffensiveAtk
	rsb r3, r3, #STAT_STAGE_MAX
.org StatStageMaxOffensiveSpa
	rsb r3, r3, #STAT_STAGE_MAX
.org StatStageAiSpAtkWeight
	cmp r0, #STAT_STAGE_MAX
.org StatStageRandomPick1
	cmp r1, #STAT_STAGE_MAX
.org StatStageRandomPick2
	cmp r1, #STAT_STAGE_MAX
.org StatStageRandomPick3
	cmp r1, #STAT_STAGE_MAX
.org StatStageRandomPick4
	cmp r1, #STAT_STAGE_MAX
.org StatStageCheckSelf01
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf02
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf03
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf04
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf05
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf06
	cmpgt r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf07
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf08
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf09
	cmpgt r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf10
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf11
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckSelf12
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckSelf13
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckSelf14
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckSelf15
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckSelf16
	cmpge r0, #STAT_STAGE_MAX
.org StatStageCheckSelf17
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckSelf18
	cmplt r0, #STAT_STAGE_MAX
.org StatStageCheckSelf19
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckSelf20
	cmplt r0, #STAT_STAGE_MAX
.org StatStageCheckSelf21
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckSelf22
	cmpge r0, #STAT_STAGE_MAX
.org StatStageCheckSelf23
	cmpge r0, #STAT_STAGE_MAX
.org StatStageCheckSelf24
	cmpge r0, #STAT_STAGE_MAX
.org StatStageCheckSelf25
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckSelf26
	cmpge r0, #STAT_STAGE_MAX
.org StatStageCheckSelf27
	cmpge r0, #STAT_STAGE_MAX
.org StatStageCheckSelf28
	cmpge r0, #STAT_STAGE_MAX
.org StatStageCheckSelf29
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckSelf30
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckTarget01
	cmp r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckTarget02
	cmpgt r0, #(STAT_STAGE_MAX - 1)
.org StatStageCheckTarget03
	cmp r0, #STAT_STAGE_MAX
.org StatStageCheckTarget04
	cmpge r0, #STAT_STAGE_MAX
.org StatStageCheckTarget05
	cmp r0, #(STAT_STAGE_MIN + 1)
.org StatStageCheckTarget06
	cmp r0, #(STAT_STAGE_MIN + 1)
.org StatStageCheckTarget07
	cmp r0, #(STAT_STAGE_MIN + 1)
.org StatStageCheckTarget08
	cmp r0, #(STAT_STAGE_MIN + 1)
.org StatStageCheckTarget09
	cmp r0, #(STAT_STAGE_MIN + 1)
.org StatStageCheckTarget10
	cmplt r0, #(STAT_STAGE_MIN + 1)
.org StatStageCheckTarget11
	cmp r0, #(STAT_STAGE_MIN + 1)
.org StatStageCheckTarget12
	cmp r0, #(STAT_STAGE_MIN + 1)
.org StatStageCheckTarget13
	cmp r0, #STAT_STAGE_MIN

.close

.open "overlay_0036.bin", ov_36

.org ov_36 + StatusAdjustCodeAddress

; Counter ticks at the start of the holder's own turn and ends at 0 (vanilla stores duration+1).
; 1 = rest of this round only; the next-turn-start tick clears it.
; Shared path also covers Mini Counter (0xA) and Metal Burst (0xF).
StatusAdjust_CounterForceDuration:
	mov r0, #1
	b CounterStatusDurationAddResume

StatusAdjust_ProtectForceDuration:
	mov r3, #1
	b ProtectStatusDurationAddResume

StatusAdjust_MirrorCoatForceDuration:
	mov r1, #1
	b MirrorCoatStatusDurationAddResume

StatusAdjust_EndureForceDuration:
	mov r1, #1
	b EndureStatusDurationAddResume

; r8 = move slot. r2 is reloaded at the loop head.
StatusAdjust_SpitePpReduce:
	ldrb r2, [r8, #MoveSlotPpOff]
	lsr r2, r2, #1
	strb r2, [r8, #MoveSlotPpOff]
	b SpitePpZeroResume

; lr = move slot. r2 is reloaded at the loop head.
StatusAdjust_GrudgePpReduce:
	ldrb r2, [lr, #MoveSlotPpOff]
	lsr r2, r2, #1
	strb r2, [lr, #MoveSlotPpOff]
	b GrudgePpZeroResume

; fx64 as CalcDamage reads it: first word high half, second word Q16.16 magnitude.
StatusAdjust_ScreenThird:
	ldr r2, =StatusAdjust_FxOneThird
	bx lr

; r0 = current stage, r4 = current - stages. A stage already below the floor stays put.
; The caller compares r4 with r0 next, so flags are free.
StatusAdjust_StageFloor:
	cmp r4, #STAT_STAGE_MIN
	bxge lr
	cmp r0, #STAT_STAGE_MIN
	movge r4, #STAT_STAGE_MIN
	movlt r4, r0
	bx lr

; r0 = current stage, r4 = current + stages. A stage already above the cap stays put.
StatusAdjust_StageCeil:
	cmp r4, #STAT_STAGE_MAX
	bxle lr
	cmp r0, #STAT_STAGE_MAX
	movle r4, #STAT_STAGE_MAX
	movgt r4, r0
	bx lr

.align 4
StatusAdjust_FxOneThird:
	.word 0
	.word SCREEN_DAMAGE_ONE_THIRD
	.pool

.close
