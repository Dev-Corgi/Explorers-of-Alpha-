; 7-entry table @ E380; B474 points here.
; HP / Atk / SpA / Def / SpD / Spe / Reset
; Patcher sits at +0x48 so the extra Spe row does not overlap it.

.org SpindaEvTeamSubmenuTable
SpindaEvTeamSubmenuItems:
	.halfword EV_STR_MENU_HP_CODE_BASE
	.halfword 0
	.word 1
	.halfword EV_STR_MENU_ATK_CODE_BASE
	.halfword 0
	.word 2
	.halfword EV_STR_MENU_SPA_CODE_BASE
	.halfword 0
	.word 3
	.halfword EV_STR_MENU_DEF_CODE_BASE
	.halfword 0
	.word 4
	.halfword EV_STR_MENU_SPD_CODE_BASE
	.halfword 0
	.word 5
	.halfword EV_STR_MENU_SPE_CODE_BASE
	.halfword 0
	.word 6
	.halfword EV_STR_MENU_RESET_CODE
	.halfword 0
	.word 7
	.halfword 0
	.halfword 0
	.word -1

.org SpindaEvTeamSubmenuTable + 0x48
EvDrinkPatchSubmenuLabels:
	push {r4-r7, lr}
	ldr r0, =SpindaEvTeamSubmenuTable
	ldr r4, =EvDrinkBoostCacheAddress
	ldr r7, =EvMenuStatCodeBase
	mov r5, #0
EvDrinkPatchSubmenuLabels_Loop:
	ldrb r2, [r4, r5]
	cmp r2, #EV_STR_MENU_MAX_V
	movgt r2, #EV_STR_MENU_MAX_V
	mov r6, r5
	lsl r6, r6, #1
	ldrh r3, [r7, r6]
	add r3, r3, r2
	strh r3, [r0]
	add r0, r0, #8
	add r5, r5, #1
	cmp r5, #6
	blt EvDrinkPatchSubmenuLabels_Loop
	ldr r3, =EV_STR_MENU_RESET_CODE
	strh r3, [r0]
	pop {r4-r7, pc}

EvDrinkStatSubmenuOpen:
	push {r0-r3, lr}
	mov r0, r8
	bl EvDrinkRefreshBoostCacheForState
	bl EvDrinkPatchSubmenuLabels
	ldr r0, =EvDrinkLastChoiceAddress
	ldrb r0, [r0]
	sub r0, r0, #1
	cmp r0, #5
	movhi r0, #0
	str r0, [sp, #0x14]
	pop {r0-r3, lr}
	b SpindaEvTeamSubmenuCreate

.pool
EvMenuStatCodeBase:
	.halfword EV_STR_MENU_HP_CODE_BASE
	.halfword EV_STR_MENU_ATK_CODE_BASE
	.halfword EV_STR_MENU_SPA_CODE_BASE
	.halfword EV_STR_MENU_DEF_CODE_BASE
	.halfword EV_STR_MENU_SPD_CODE_BASE
	.halfword EV_STR_MENU_SPE_CODE_BASE

; Cafe drink snapshots HP as a halfword at +0xA (Spe V lives in the high byte).
; Store HP/Spe as separate bytes so Spe drinks do not look like HP +256.
EvDrinkSnapHpSpe:
	push {r0, r1}
	ldrb r2, [r4, #0xa]
	ldrb r0, [r4, #0xb]
	ldr r1, =EvDrinkHpBeforeAddress
	strb r2, [r1]
	ldr r1, =EvDrinkSpeBeforeAddress
	strb r0, [r1]
	pop {r0, r1}
	bx lr

EvDrinkSnapHpAfter:
	ldrb r11, [r4, #0xa]
	bx lr

; r5 = drink text buffer, drink-fn sp is caller sp.
; Vanilla loop (r7=2..5) already prints Atk/SpA/Def/SpD via
; "[name]'s [stat] rose [digits]!". Append HP and Spe the same way.
EvDrinkAppendHpSpeMsgs:
	push {r1-r4, r6, r7, r8, lr}
	add r6, sp, #32
	add r7, r6, #0x100
	ldrsh r7, [r7, #0x78]
	ldr r8, =EV_STR_NAME_HP_CODE
	bl EvDrinkShowOneDelta
	ldr r0, =SpindaCafeStatePtr
	ldr r0, [r0]
	cmp r0, #0
	beq EvDrinkAppend_Done
	ldr r0, [r0, #0xd4]
	lsl r0, r0, #0x10
	asr r0, r0, #0x10
	cmp r0, #0
	blt EvDrinkAppend_Done
	ldr r1, =EV_TEAM_COUNT
	cmp r0, r1
	bge EvDrinkAppend_Done
	bl GetTeamMember
	cmp r0, #0
	beq EvDrinkAppend_Done
	ldrb r7, [r0, #0xb]
	ldr r1, =EvDrinkSpeBeforeAddress
	ldrb r1, [r1]
	sub r7, r7, r1
	ldr r8, =EV_STR_NAME_SPE_CODE
	bl EvDrinkShowOneDelta
EvDrinkAppend_Done:
	pop {r1-r4, r6, r7, r8, lr}
	add r0, sp, #0x128
	bx lr

; r5 = buf, r6 = drink-fn sp, r7 = signed delta, r8 = 1-based name id.
EvDrinkShowOneDelta:
	push {r0-r4, lr}
	cmp r7, #0
	beq EvDrinkShow_Done
	ldr r1, =EvDrinkRoseNewline
	mov r0, r5
	bl Strcat
	ldr r0, [r6, #0x10]
	mov r1, r8
	str r7, [r6, #0x14c]
	bl GetStringFromFileVeneer
	add r0, r5, #0x400
	mov r1, #0x100
	ldr r2, =EV_STR_ROSE_TEMPLATE_CODE
	mov r3, #0
	add r4, r6, #0x128
	str r4, [sp, #-4]!
	bl PreprocessStringFromId
	add sp, sp, #4
	mov r0, r5
	add r1, r5, #0x400
	bl Strcat
EvDrinkShow_Done:
	pop {r0-r4, pc}

.pool

.org SpindaEvTeamSubmenuMenuPtr
	.word SpindaEvTeamSubmenuTable

.org SpindaEvDrinkMenuOpenHook
	bl SpindaEvVanillaDrinkHelper

.org SpindaEvStatSubmenuOpenHook
	bl EvDrinkStatSubmenuOpen

.org SpindaEvDrinkSelectHook
	bl EvDrinkStatSelectHook

.org SpindaEvDrinkOutcomeHook
	bl ForceDrinkOutcomeNormal

.org EvDrinkSnapHpSpeHook
	bl EvDrinkSnapHpSpe

.org EvDrinkSnapHpAfterHook
	bl EvDrinkSnapHpAfter

.org EvDrinkAppendHpSpeMsgHook
	bl EvDrinkAppendHpSpeMsgs
