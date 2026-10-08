; Struct doping helpers — Nonsave hook skeleton, no EV RAM/save sync.
; GetTeamMember = ground_monster: +1 level, +4 species, +0xA HP, +0xC..+0xF stats.

.org SpindaEvArm9CodeAddress

; In: r0=roster, r1=&out[6] (HP,Atk,SpA,Def,SpD,Spe).
; Save bytes are doping V. Copy them.
EvFillBoosts:
	push {r4, r5, r6, lr}
	mov r6, r0
	mov r5, r1
	mov r4, #0
	mov r0, #0
EvFillBoosts_Clear:
	strb r0, [r5, r4]
	add r4, r4, #1
	cmp r4, #6
	blt EvFillBoosts_Clear
	mov r0, r6
	bl GetTeamMember
	movs r4, r0
	beq EvFillBoosts_Done
	ldrb r0, [r4, #0xa]
	strb r0, [r5]
	ldrb r0, [r4, #0xc]
	strb r0, [r5, #1]
	ldrb r0, [r4, #0xd]
	strb r0, [r5, #2]
	ldrb r0, [r4, #0xe]
	strb r0, [r5, #3]
	ldrb r0, [r4, #0xf]
	strb r0, [r5, #4]
	ldrb r0, [r4, #0xb]
	strb r0, [r5, #5]
EvFillBoosts_Done:
	pop {r4, r5, r6, pc}

; r0 = roster. Add 1 to Spe V at ground +0xB.
EvAddSpeed:
	mov r1, #1
; r0 = roster, r1 = signed delta.
EvAddSpeedDelta:
	push {r2, r3, lr}
	mov r3, r1
	bl GetTeamMember
	cmp r0, #0
	beq EvAddSpeed_Done
	ldrb r2, [r0, #0xb]
	add r2, r2, r3
	cmp r2, #0
	movlt r2, #0
	cmp r2, #0xff
	movgt r2, #0xff
	strb r2, [r0, #0xb]
EvAddSpeed_Done:
	pop {r2, r3, pc}

EvClampBoostU8:
	cmp r0, #0
	movlt r0, #0
	cmp r0, #0xff
	movgt r0, #0xff
	bx lr

; Cafe UI: reverse now (safe), ExtraBits only reads EvDrinkBoostCache.
; In: r0 = bar state* (roster halfword @ +0xd4).
EvDrinkRefreshBoostCacheForState:
	push {r1, r2, lr}
	cmp r0, #0
	beq EvDrinkRefreshBoostCache_Zero
	ldr r0, [r0, #0xd4]
	lsl r0, r0, #0x10
	asr r0, r0, #0x10
	cmp r0, #0
	blt EvDrinkRefreshBoostCache_Zero
	ldr r1, =EV_TEAM_COUNT
	cmp r0, r1
	bge EvDrinkRefreshBoostCache_Zero
	ldr r1, =EvDrinkBoostCacheAddress
	bl EvFillBoosts
	b EvDrinkRefreshBoostCache_Done
EvDrinkRefreshBoostCache_Zero:
	ldr r1, =EvDrinkBoostCacheAddress
	mov r0, #0
	strb r0, [r1]
	strb r0, [r1, #1]
	strb r0, [r1, #2]
	strb r0, [r1, #3]
	strb r0, [r1, #4]
	strb r0, [r1, #5]
EvDrinkRefreshBoostCache_Done:
	pop {r1, r2, pc}

EvDrinkRefreshBoostCache:
	push {r0, lr}
	ldr r0, =SpindaCafeStatePtr
	ldr r0, [r0]
	bl EvDrinkRefreshBoostCacheForState
	pop {r0, pc}

.pool

SpindaEvSaveCodeEnd:
