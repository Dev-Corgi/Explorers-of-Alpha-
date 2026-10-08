; Summary roster capture, drink hooks, and stats-page layout passthrough.
; FromMonster: bl trampoline after vanilla push (member_index chain).
; Stats page prints CalcStat only; (Vn) suffixes are not drawn.

.org SpindaEvSaveCodeEnd

STAT_BONUS_HP  equ 0
STAT_BONUS_ATK equ 1
STAT_BONUS_SPA equ 2
STAT_BONUS_DEF equ 3
STAT_BONUS_SPD equ 4

PREPROCESS_VALUE0_OFF equ 0x24
DRAW_FRAME equ 0x108
DRAW_VAL_OFF equ 0x10
DRAW_STR_OFF equ 0x40
DRAW_PAD_OFF equ 0x100

; r1 = team_member*; +8 = member_index.
SummarySaveTeamMemberHook:
	push {r0, r2, lr}
	ldrsh r0, [r1, #8]
	ldr r2, =SummaryRosterIndexAddress
	str r0, [r2]
	pop {r0, r2, lr}
	mov r8, r1
	bx lr

; After vanilla FromMonster push: replaces `mov r6, r1`.
; entity→monster(+0xb4)→team_index(+0xc)→GetActiveTeamMember→[+8].
; OOR / guest → 0xFFFFFFFF.
SummarySaveFromMonsterHook:
	push {r0-r3, r4, lr}
	ldr r0, [r1, #0xb4]
	cmp r0, #0
	beq SummarySaveFromMonster_Clear
	ldrsh r0, [r0, #0xc]
	cmp r0, #0
	blt SummarySaveFromMonster_Clear
	cmp r0, #4
	bge SummarySaveFromMonster_Clear
	bl GetActiveTeamMember
	cmp r0, #0
	beq SummarySaveFromMonster_Clear
	ldrsh r0, [r0, #8]
	ldr r1, =EV_TEAM_COUNT
	cmp r0, r1
	bhs SummarySaveFromMonster_Clear
	ldr r1, =SummaryRosterIndexAddress
	str r0, [r1]
	b SummarySaveFromMonster_Done
SummarySaveFromMonster_Clear:
	ldr r1, =SummaryRosterIndexAddress
	mov r0, #0
	mvn r0, r0
	str r0, [r1]
SummarySaveFromMonster_Done:
	pop {r0-r3, r4, lr}
	mov r6, r1
	bx lr

; ov19 inner17: r0 = menu action. Actions 1..7 → store 0..6, cache boosts, remap to Drink (4).
; Must preserve r8 (cafe state*). Vanilla was a single `mov r4, r0`.
EvDrinkStatSelectHook:
	cmp r0, #1
	blt EvDrinkStatSelect_Keep
	cmp r0, #7
	bgt EvDrinkStatSelect_Keep
	push {r1, r2, r3, r8, lr}
	sub r1, r0, #1
	ldr r2, =EvDrinkSelectedStatAddress
	strb r1, [r2]
	ldr r2, =EvDrinkLastChoiceAddress
	strb r0, [r2]
	bl EvDrinkRefreshBoostCache
	pop {r1, r2, r3, r8, lr}
	mov r0, #4
EvDrinkStatSelect_Keep:
	mov r4, r0
	bx lr

; ov19 @ B204: was `str r5, [r4, #0xfc]`.
; Force Miracle outcomes (1, 2, 6) → 0 so gummi/EV path runs.
; Keep 3 (special), 4 (recruit), 5 (secret exploration spot).
ForceDrinkOutcomeNormal:
	cmp r5, #1
	beq ForceDrinkOutcome_ToNormal
	cmp r5, #2
	beq ForceDrinkOutcome_ToNormal
	cmp r5, #6
	bne ForceDrinkOutcome_Store
ForceDrinkOutcome_ToNormal:
	mov r5, #0
ForceDrinkOutcome_Store:
	str r5, [r4, #0xfc]
	bx lr

; From 20119B4: set gummi mask from Selected, clear Selected; then b APPLY.
; Mask: 0→0x10 HP, 1→1 Atk, 2→2 SpA, 3→4 Def, 4→8 SpD, 5→0x40 Spe, 6→0x20 Reset.
EvDrinkMaskAndInc:
	push {r0-r8, lr}
	ldr r1, =EvDrinkSelectedStatAddress
	ldrb r4, [r1]
	mov r0, #1
	cmp r4, #0
	moveq r0, #0x10
	cmp r4, #2
	moveq r0, #2
	cmp r4, #3
	moveq r0, #4
	cmp r4, #4
	moveq r0, #8
	cmp r4, #5
	moveq r0, #0x40
	cmp r4, #6
	moveq r0, #0x20
	strh r0, [r6, #2]
	mov r0, #0xFF
	strb r0, [r1]
	pop {r0-r8, lr}
	bx lr

.pool

; Stats page shows CalcStat only. Suffix hooks stay so apply/chain is unchanged.
SummaryAfterLayHp:
SummaryAfterLayAtkBoost:
SummaryAfterLaySpaBoost:
SummaryAfterLaySpaNorm:
SummaryAfterLayAtkNorm:
SummaryAfterLayDef:
SummaryAfterLaySpd:
	b SummaryLayoutCall

; Record Wonder Gummi (type 0xFF) then run the original prologue.
WonderGummi_Entry:
	push {r4, lr}
	cmp r2, #WONDER_GUMMI_TYPE
	moveq r4, #1
	movne r4, #0
	ldr r12, =WonderGummiPending
	strb r4, [r12]
	pop {r4, lr}
	push {r3-r11, lr}
	b ApplyGummiBoostsAfterPrologue

WonderGummiPending:
	.byte 0
	.align 4

; Wonder Gummi exit was in the dungeon-stat cave; kept here with Entry so
; both live in the arm9 code cave (dungeon-stat needs room for peel/snap).
WonderGummi_Exit:
	ldr r4, =WonderGummiPending
	ldrb r0, [r4]
	mov r1, #0
	strb r1, [r4]
	cmp r0, #0
	beq WonderGummi_Epilogue
	ldr r4, =ApplyProteinEffect
	mov r5, #4
WonderGummi_StatLoop:
	mov r0, r10
	mov r1, r9
	mov r2, #WONDER_GUMMI_ALL_STAT
	blx r4
	add r4, r4, #WONDER_GUMMI_STAT_FN_STRIDE
	subs r5, r5, #1
	bne WonderGummi_StatLoop
	ldr r2, [r9, #0xb4]
	ldrsh r0, [r2, #0xc]
	cmp r0, #0
	blt WonderGummi_HpBar
	cmp r0, #4
	bge WonderGummi_HpBar
	bl GetActiveTeamMember
	cmp r0, #0
	beq WonderGummi_HpBar
	ldrb r1, [r0, #0x10]
	add r1, r1, #WONDER_GUMMI_ALL_STAT
	cmp r1, #0xff
	movgt r1, #0xff
	strb r1, [r0, #0x10]
WonderGummi_HpBar:
	ldr r2, [r9, #0xb4]
	ldrsh r3, [r2, #0x12]
	ldrsh r1, [r2, #0x16]
	add r0, r3, #WONDER_GUMMI_ALL_STAT
	add r12, r0, r1
	ldr r4, =WONDER_GUMMI_HP_CAP
	cmp r12, r4
	subgt r0, r4, r1
	cmp r0, r3
	movlt r0, r3
	sub r12, r0, r3
	strh r0, [r2, #0x12]
	add r1, r0, r1
	cmp r1, r4
	movgt r1, r4
	ldrsh r0, [r2, #0x10]
	add r0, r0, r12
	cmp r0, r1
	movgt r0, r1
	strh r0, [r2, #0x10]
	mov r0, r9
	bl RefreshEntityAfterStatChange
WonderGummi_Epilogue:
	add sp, sp, #8
	pop {r3-r11, pc}

; After Protect / Whiffer / accuracy>100 exits. r11 is the move*.
; Z-Move shell 559 skips the rank/Spe roll and returns hit.
; Floor Gravity (Orb / move) multiplies Accuracy by 5/3 before that roll.
SpindaEv_ZMoveNeverMiss:
	ldrh r0, [r11, #MoveDataMoveIdOff]
	ldr r1, =Z_MOVE_SHELL_ID
	cmp r0, r1
	moveq r0, #1
	beq MoveHitEpilogue
	bl GravityIsActive
	cmp r0, #0
	beq SpindaEv_PriorMoveHitRank
	mov r0, #5
	mul r0, r8, r0
	mov r1, #3
	bl S32DivF
	mov r8, r0
	b SpindaEv_PriorMoveHitRank

.pool

.org CreateMonsterSummarySaveHook
	bl SummarySaveTeamMemberHook

.org SummarySuffixHookHp
	bl SummaryAfterLayHp
.org SummarySuffixHookAtkBoost
	bl SummaryAfterLayAtkBoost
.org SummarySuffixHookSpaBoost
	bl SummaryAfterLaySpaBoost
.org SummarySuffixHookSpaNorm
	bl SummaryAfterLaySpaNorm
.org SummarySuffixHookAtkNorm
	bl SummaryAfterLayAtkNorm
.org SummarySuffixHookDef
	bl SummaryAfterLayDef
.org SummarySuffixHookSpd
	bl SummaryAfterLaySpd
