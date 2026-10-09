.open "overlay_0029.bin", ov_29
.org BugFixHailRegenBonusSite
	nop
.org BugFixTraceAbilityReadSite
	b BugFix_Trace
.close

.open "overlay_0036.bin", ov_36
.org BugFixMirrorAttackSite
	b BugFix_MirrorAttack
.org BugFixMirrorDefenseSite
	b BugFix_MirrorDefense
.org BugFixMirrorHitChanceSite
	b BugFix_MirrorHitChance
.org BugFixGasSuppressionSite
	b BugFix_GasSuppression

.org ov_36 + BugFixCodeAddress

; Alpha's success branch still has the original r0-r3 saved on the stack.
; Restore actual pointers, then reverse the stat-change source and target.
BugFix_MirrorAttack:
	ldr r12, =MirrorAttackResume
	b BugFix_MirrorAD
BugFix_MirrorDefense:
	ldr r12, =MirrorDefenseResume
BugFix_MirrorAD:
	push {r12, lr}
	ldr r8, [sp, #12]             ; source = original defender (Mirror Armor)
	ldr r7, [sp, #8]              ; target = original attacker
	ldr r0, =AlphaStatChangeSource
	str r8, [r0]
	str r7, [r0, #4]             ; Defiant/Competitive use the reflected target
	mov r0, r8
	ldr r1, =MirrorArmorMessagePool
	ldr r1, [r1]
	bl LogMessageById
	pop {r12, lr}
	bx r12                      ; original pop r0-r3, then set reversed pointers

BugFix_MirrorHitChance:
	push {r12, lr}
	ldr r7, [sp, #12]            ; source = original defender
	ldr r6, [sp, #8]             ; target = original attacker; keep r8 amount
	ldr r0, =AlphaStatChangeSource
	str r7, [r0]
	str r6, [r0, #4]
	mov r0, r7
	ldr r1, =MirrorArmorMessagePool
	ldr r1, [r1]
	bl LogMessageById
	pop {r12, lr}
	b MirrorHitChanceResume

; r8 = recipient entity, r6 = recipient monster. Preserve the original
; two-slot choice (including secondary-slot preference when both are Trace).
BugFix_Trace:
	push {r0, r1, r2, r3, r12, lr}
	mov r0, r8
	mov r1, #TRACE
	bl AbilityIsActiveVeneer
	cmp r0, #0
	pop {r0, r1, r2, r3, r12, lr}
	beq BugFix_TraceSuppressed
	ldrb r0, [r6, #0x60]         ; displaced instruction
	b TraceAbilityReadContinue
BugFix_TraceSuppressed:
	mvn r4, #0
	b TraceSlotCheckContinue      ; skip Trace, still process Color Change

; Called from Alpha's AbilitySuppression after its Gastro Acid check.
; r4 = queried entity, r1 = queried ability. Do not use the floor-wide gas
; flag: examine live adjacent gas holders on either side each time instead.
BugFix_GasSuppression:
	push {r1, r2, r3, r4, r5, r6, r7, r8, lr}
	cmp r1, #NEUTRALIZING_GAS
	beq BugFix_GasAllow           ; avoid recursion; gas does not suppress gas
	mov r5, r4
	ldr r6, =DungeonPtr
	ldr r6, [r6]
	cmp r6, #0
	beq BugFix_GasAllow
	add r6, r6, #0x12000
	add r6, r6, #0xB00
	add r6, r6, #0x78            ; dungeon.all_monsters[20]
	mov r7, #20
BugFix_GasNext:
	ldr r8, [r6], #4
	cmp r8, #0
	beq BugFix_GasAdvance
	cmp r8, r5
	beq BugFix_GasAdvance         ; holder's other ability is not self-suppressed
	mov r0, r8
	bl IsMonster
	cmp r0, #0
	beq BugFix_GasAdvance
	ldr r0, [r8, #0xB4]
	cmp r0, #0
	beq BugFix_GasAdvance
	ldrsh r0, [r0, #0x10]
	cmp r0, #0
	ble BugFix_GasAdvance
	ldrsh r0, [r8, #4]
	ldrsh r1, [r5, #4]
	sub r0, r0, r1
	cmp r0, #1
	bgt BugFix_GasAdvance
	cmn r0, #1
	blt BugFix_GasAdvance
	ldrsh r0, [r8, #6]
	ldrsh r1, [r5, #6]
	sub r0, r0, r1
	cmp r0, #1
	bgt BugFix_GasAdvance
	cmn r0, #1
	blt BugFix_GasAdvance
	mov r0, r8
	mov r1, #NEUTRALIZING_GAS
	bl AbilityIsActiveVeneer      ; includes Gastro Acid / Ability Monitor
	cmp r0, #0
	bne BugFix_GasBlock
BugFix_GasAdvance:
	subs r7, r7, #1
	bne BugFix_GasNext
BugFix_GasAllow:
	mov r0, #1
	b BugFix_GasDone
BugFix_GasBlock:
	mov r0, #0
BugFix_GasDone:
	pop {r1, r2, r3, r4, r5, r6, r7, r8, lr}
	b AbilitySuppressionContinue

.pool
.if . > ov_36 + BugFixCodeAddress + 768
	.error "bug_fixes helpers exceed allocated cave"
.endif
.close
