; ExtraBits @ arm9 A3550 (Nonsave cave — do not relocate).

.org SpindaEvResetCaveAddress
; Caller 0x020119EC does `tst r1, #1` then GroundAddOffensiveStat(r8, r5).
; r1 must be the remaining mask; r5 is the gummi amount. Do not save r1
; or zero r5 — a leftover IQ-tier r1 plus GroundAdd's floor of 1 left Atk at 1.
EvGummiApplyExtraBits:
	push {r0, r2, r3, r4, r7, r8, lr}
	bl EvDrinkGetRoster
	movs r4, r0
	bmi EvGummiExtra_LoadMask
	bl EvDrinkRefreshBoostCache
	ldrh r1, [r6, #2]
	tst r1, #1
	beq EvGummiExtra_Bit1
	bic r1, r1, #1
	strh r1, [r6, #2]
	mov r3, #1
	bl EvDrinkCanBoost
	cmp r0, #0
	beq EvGummiExtra_Bit1
	mov r0, r8
	mov r1, #1
	bl GroundAddOffensiveStat
EvGummiExtra_Bit1:
	ldrh r1, [r6, #2]
	tst r1, #2
	beq EvGummiExtra_Bit2
	bic r1, r1, #2
	strh r1, [r6, #2]
	mov r3, #2
	bl EvDrinkCanBoost
	cmp r0, #0
	beq EvGummiExtra_Bit2
	add r0, r8, #1
	mov r1, #1
	bl GroundAddOffensiveStat
EvGummiExtra_Bit2:
	ldrh r1, [r6, #2]
	tst r1, #4
	beq EvGummiExtra_Bit3
	bic r1, r1, #4
	strh r1, [r6, #2]
	mov r3, #3
	bl EvDrinkCanBoost
	cmp r0, #0
	beq EvGummiExtra_Bit3
	mov r0, r7
	mov r1, #1
	bl GroundAddDefensiveStat
EvGummiExtra_Bit3:
	ldrh r1, [r6, #2]
	tst r1, #8
	beq EvGummiExtra_Bit4
	bic r1, r1, #8
	strh r1, [r6, #2]
	mov r3, #4
	bl EvDrinkCanBoost
	cmp r0, #0
	beq EvGummiExtra_Bit4
	add r0, r7, #1
	mov r1, #1
	bl GroundAddDefensiveStat
EvGummiExtra_Bit4:
	ldrh r1, [r6, #2]
	tst r1, #0x10
	beq EvGummiExtra_Bit5
	bic r1, r1, #0x10
	strh r1, [r6, #2]
	mov r3, #0
	bl EvDrinkCanBoost
	cmp r0, #0
	beq EvGummiExtra_Bit5
	sub r0, r8, #2
	mov r1, #1
	bl GroundAddOffensiveStat
EvGummiExtra_Bit5:
	ldrh r1, [r6, #2]
	tst r1, #0x40
	beq EvGummiExtra_BitReset
	bic r1, r1, #0x40
	strh r1, [r6, #2]
	mov r3, #5
	bl EvDrinkCanBoost
	cmp r0, #0
	beq EvGummiExtra_BitReset
	; Spe V is ground +0xB = Atk pointer r8 - 1. Byte add only.
	sub r0, r8, #1
	mov r1, #1
	bl GroundAddOffensiveStat
EvGummiExtra_BitReset:
	ldrh r1, [r6, #2]
	tst r1, #0x20
	beq EvGummiExtra_LoadMask
	bic r1, r1, #0x20
	strh r1, [r6, #2]
	bl EvDrinkDoReset
EvGummiExtra_LoadMask:
	ldrh r1, [r6, #2]
	pop {r0, r2, r3, r4, r7, r8, lr}
	bx lr

EvDrinkGetRoster:
	push {r1, lr}
	ldr r0, =SpindaCafeStatePtr
	ldr r0, [r0]
	cmp r0, #0
	mvneq r0, #0
	beq EvDrinkGetRoster_Done
	ldr r0, [r0, #0xd4]
	lsl r0, r0, #0x10
	asr r0, r0, #0x10
	cmp r0, #0
	mvnlt r0, #0
	blt EvDrinkGetRoster_Done
	ldr r1, =EV_TEAM_COUNT
	cmp r0, r1
	mvnge r0, #0
EvDrinkGetRoster_Done:
	pop {r1, pc}

; r0 = level -> r0 = floor(level / EV_LEVEL_DIVISOR)
EvFloorLevelDiv10:
	mov r1, #0
EvFloorLevelDiv10_Loop:
	cmp r0, #EV_LEVEL_DIVISOR
	blt EvFloorLevelDiv10_Done
	sub r0, r0, #EV_LEVEL_DIVISOR
	add r1, r1, #1
	b EvFloorLevelDiv10_Loop
EvFloorLevelDiv10_Done:
	mov r0, r1
	bx lr

; r0 = roster index -> r0 = level (0 if invalid)
EvGetMonLevelByRoster:
	push {r1, lr}
	bl GetTeamMember
	movs r1, r0
	moveq r0, #0
	beq EvGetMonLevelByRoster_Done
	ldrb r0, [r1, #1]
EvGetMonLevelByRoster_Done:
	pop {r1, pc}

; r0 = level -> r0 = floor(level/10) * EV_STAT_CAP_MULT
EvComputeStatCapFromLevel:
	push {lr}
	bl EvFloorLevelDiv10
	lsl r1, r0, #2
	add r0, r0, r1
	pop {pc}

; r0 = level -> r0 = floor(level/10) * EV_EARNED_CAP_MULT
EvComputeEarnedCapFromLevel:
	push {r1, lr}
	bl EvFloorLevelDiv10
	mov r1, r0
	lsl r0, r1, #3
	lsl r2, r1, #2
	add r0, r0, r2
	add r0, r0, r1
	pop {r1, pc}

EvDrinkCanBoost:
	push {r1, r2, r4, r5, r6, lr}
	mov r4, r3
	bl EvDrinkGetRoster
	movs r5, r0
	bmi EvDrinkCanBoost_No
	mov r0, r5
	bl EvGetMonLevelByRoster
	mov r6, r0
	mov r0, r6
	bl EvComputeEarnedCapFromLevel
	cmp r0, #0
	beq EvDrinkCanBoost_No
	mov r5, r0
	ldr r1, =EvDrinkBoostCacheAddress
	ldrb r0, [r1]
	ldrb r2, [r1, #1]
	add r0, r0, r2
	ldrb r2, [r1, #2]
	add r0, r0, r2
	ldrb r2, [r1, #3]
	add r0, r0, r2
	ldrb r2, [r1, #4]
	add r0, r0, r2
	ldrb r2, [r1, #5]
	add r0, r0, r2
	cmp r0, r5
	bge EvDrinkCanBoost_No
	mov r0, r6
	bl EvComputeStatCapFromLevel
	cmp r0, #0
	beq EvDrinkCanBoost_No
	mov r2, r0
	ldr r1, =EvDrinkBoostCacheAddress
	ldrb r0, [r1, r4]
	cmp r0, r2
	bge EvDrinkCanBoost_No
	mov r0, #1
	b EvDrinkCanBoost_Done
EvDrinkCanBoost_No:
	mov r0, #0
EvDrinkCanBoost_Done:
	pop {r1, r2, r4, r5, r6, pc}

; GroundAdd* floors at 1. Write the six V bytes to 0 directly.
EvDrinkDoReset:
	push {r0-r5, lr}
	bl EvDrinkGetRoster
	movs r4, r0
	bmi EvDrinkReset_Done
	bl GetTeamMember
	cmp r0, #0
	beq EvDrinkReset_Done
	mov r1, #0
	strb r1, [r0, #0xa]
	strb r1, [r0, #0xb]
	strb r1, [r0, #0xc]
	strb r1, [r0, #0xd]
	strb r1, [r0, #0xe]
	strb r1, [r0, #0xf]
	ldr r5, =EvDrinkBoostCacheAddress
	strb r1, [r5]
	strb r1, [r5, #1]
	strb r1, [r5, #2]
	strb r1, [r5, #3]
	strb r1, [r5, #4]
	strb r1, [r5, #5]
EvDrinkReset_Done:
	pop {r0-r5, lr}
	bx lr

.pool
