; Dungeon item stat gains are kept for the outing, then removed when the
; dungeon-group outing ends (DungeonFree). Escape / give-up / faint always
; restore; a clear restores only on the last floor of the group. Spinda Drink
; boosts and level-up gains stay.
; Dungeon mode reads and writes the active team_member (GetActiveTeamMember:
; +2 level, +8 roster, +0xC species, +0xE cur HP, +0x10 max HP, +0x12..+0x15
; Atk SpA Def SpD). The roster ground_monster is only synced from it by some
; ground menus, so both copies are trimmed.
; This cave must stay outside Alpha's GetItemIdFromList cache (0x0209F904-
; 0x020A0AD4); the game rewrites that range at runtime.

.org SpindaEvDungeonStatCave

DungeonStat_OnFloorMember:
	push {r0-r4, lr}
	ldr r4, =DungeonStatSnapAddress
	ldrb r0, [r4]
	cmp r0, #0
	bne DungeonStat_OnFloorMember_Resume
	bl DungeonStat_SnapshotParty
	cmp r0, #0
	beq DungeonStat_OnFloorMember_Resume
	mov r0, #1
	strb r0, [r4]
DungeonStat_OnFloorMember_Resume:
	pop {r0-r4, lr}
	push {r3-r10, lr}
	b InitTeamMemberBody

; Returns 1 if at least one active party member was stored.
; Entry i (active slot i) is 12 bytes: s16 roster, s16 species, u8 level, pad,
; s16 max HP, then Atk SpA Def SpD.
DungeonStat_SnapshotParty:
	push {r4-r8, lr}
	ldr r5, =DungeonStatSnapAddress
	mov r4, #0
	mov r8, #0
DungeonStat_SnapLoop:
	add r7, r5, #4
	add r1, r4, r4, lsl #1
	add r7, r7, r1, lsl #2
	mov r0, r4
	bl GetActiveTeamMember
	cmp r0, #0
	beq DungeonStat_SnapEmpty
	ldrb r1, [r0]
	tst r1, #1
	beq DungeonStat_SnapEmpty
	ldrsh r6, [r0, #8]
	cmp r6, #0
	blt DungeonStat_SnapEmpty
	ldr r1, =EV_TEAM_COUNT
	cmp r6, r1
	bge DungeonStat_SnapEmpty
	strh r6, [r7]
	ldrsh r1, [r0, #0xc]
	strh r1, [r7, #2]
	ldrb r1, [r0, #2]
	strb r1, [r7, #4]
	ldrh r1, [r0, #0x10]
	strh r1, [r7, #6]
	ldrh r1, [r0, #0x12]
	strh r1, [r7, #8]
	ldrh r1, [r0, #0x14]
	strh r1, [r7, #10]
	mov r8, #1
	b DungeonStat_SnapNext
DungeonStat_SnapEmpty:
	mvn r0, #0
	strh r0, [r7]
DungeonStat_SnapNext:
	add r4, r4, #1
	cmp r4, #4
	blt DungeonStat_SnapLoop
	mov r0, r8
	pop {r4-r8, pc}

; DungeonFree entry: DUNGEON_PTR_MASTER is still live (working copy may be 0).
DungeonStat_OnDungeonGroupEnd:
	push {r0-r3, lr}
	bl DungeonStat_IsDungeonGroupOutingEnd
	cmp r0, #0
	beq DungeonStat_OnDungeonGroupEndResume
	bl DungeonStat_RestoreParty
DungeonStat_OnDungeonGroupEndResume:
	pop {r0-r3, lr}
	b SpindaEv_PriorDungeonFree

; r0=1: faint/escape/give-up, or clear of the last floor in the group.
DungeonStat_IsDungeonGroupOutingEnd:
	push {r4, r5, lr}
	ldr r4, =DungeonMasterPtr
	ldr r5, [r4, #4]
	cmp r5, #0
	ldreq r5, [r4]
	movs r4, r5
	beq DungeonStat_GroupEndNo
	add r0, r4, #0x2C000
	add r0, r0, #0xA00
	ldrh r0, [r0, #0x66]
	ldr r1, =DAMAGE_SOURCE_DUNGEON_CLEAR
	cmp r0, r1
	bne DungeonStat_GroupEndYes
	add r0, r4, #0x4A
	add r0, r0, #0x700
	add r1, r4, #0x48
	add r1, r1, #0x700
	bl DungeonFloorToGroupFloor
	ldrb r5, [r4, #DUNGEON_GROUP_FLOOR_OFF]
	ldrb r0, [r4, #DUNGEON_ID_FLOOR_OFF]
	bl GetNbFloorsDungeonGroup
	cmp r5, r0
	movge r0, #1
	movlt r0, #0
	pop {r4, r5, pc}
DungeonStat_GroupEndYes:
	mov r0, #1
	pop {r4, r5, pc}
DungeonStat_GroupEndNo:
	mov r0, #0
	pop {r4, r5, pc}

; r0 = snap/peel buffer; r1 = 1 clears buffer.valid after apply.
DungeonStat_RestoreParty:
	ldr r0, =DungeonStatSnapAddress
	mov r1, #1
DungeonStat_ApplyBuffer:
	push {r4-r10, lr}
	mov r4, r0
	ldrb r0, [r4]
	cmp r0, #0
	beq DungeonStat_ApplyDone
	cmp r1, #0
	movne r0, #0
	strneb r0, [r4]
	mov r5, #0
DungeonStat_ApplyLoop:
	add r6, r4, #4
	add r0, r5, r5, lsl #1
	add r6, r6, r0, lsl #2
	ldrsh r7, [r6]
	cmp r7, #0
	blt DungeonStat_ApplyNext
	ldrsh r9, [r6, #2]
	cmp r9, #0
	ble DungeonStat_ApplyNext
	mov r0, r5
	bl GetActiveTeamMember
	movs r8, r0
	beq DungeonStat_ApplyGround
	ldrb r1, [r8]
	tst r1, #1
	beq DungeonStat_ApplyGround
	ldrsh r1, [r8, #8]
	cmp r1, r7
	bne DungeonStat_ApplyGround
	ldrsh r1, [r8, #0xc]
	cmp r1, r9
	bne DungeonStat_ApplyGround
	add r0, r8, #0x10
	mov r2, r6
	bl DungeonStat_TrimStats
DungeonStat_ApplyGround:
	mov r0, r7
	bl GetTeamMember
	movs r8, r0
	beq DungeonStat_ApplyNext
	ldrb r1, [r8]
	cmp r1, #0
	beq DungeonStat_ApplyNext
	ldrsh r1, [r8, #4]
	cmp r1, r9
	bne DungeonStat_ApplyNext
	add r0, r8, #0xa
	mov r2, r6
	bl DungeonStat_TrimStats
DungeonStat_ApplyNext:
	add r5, r5, #1
	cmp r5, #4
	blt DungeonStat_ApplyLoop
DungeonStat_ApplyDone:
	pop {r4-r10, pc}

; r0 = &HP V halfword (Atk SpA Def SpD follow at +2..+5).
; r2 = snapshot entry. Write snapshot V back; no level-up add.
DungeonStat_TrimStats:
	push {r4, r6, lr}
	mov r4, r0
	mov r6, r2
	ldrh r0, [r6, #6]
	strh r0, [r4]
	ldrh r0, [r6, #8]
	strh r0, [r4, #2]
	ldrh r0, [r6, #10]
	strh r0, [r4, #4]
	pop {r4, r6, pc}

; Mid-dungeon / any NoteSave: write snap V into the team so the save does
; not keep outing vitamins. Peel live V into DungeonStatPeelAddress, then
; Unpeel after GetMonsterInfoForSave returns. No-op if snap.valid == 0.
DungeonStat_SaveMonstersClean:
	push {r4, r5, r6, lr}
	mov r4, r0
	mov r5, r1
	bl DungeonStat_PeelForSave
	mov r0, r4
	mov r1, r5
	bl DungeonStat_SaveMonstersOrig
	mov r6, r0
	bl DungeonStat_UnpeelAfterSave
	mov r0, r6
	pop {r4, r5, r6, pc}

; Original prologue (replaced by the hook) + body.
DungeonStat_SaveMonstersOrig:
	push {r4, r5, r6, r7, r8, lr}
	b GetMonsterInfoForSaveBody

; Copy live V into peel, then apply snap V (keep snap.valid).
DungeonStat_PeelForSave:
	push {r4-r10, lr}
	ldr r4, =DungeonStatSnapAddress
	ldrb r0, [r4]
	cmp r0, #0
	beq DungeonStat_PeelDone
	ldr r5, =DungeonStatPeelAddress
	mov r0, #1
	strb r0, [r5]
	mov r8, #0
DungeonStat_PeelLoop:
	add r6, r4, #4
	add r0, r8, r8, lsl #1
	add r6, r6, r0, lsl #2
	add r7, r5, #4
	add r7, r7, r0, lsl #2
	ldrsh r9, [r6]
	cmp r9, #0
	mvnlt r0, #0
	strlth r0, [r7]
	blt DungeonStat_PeelNext
	ldrsh r10, [r6, #2]
	cmp r10, #0
	mvnle r0, #0
	strleh r0, [r7]
	ble DungeonStat_PeelNext
	strh r9, [r7]
	strh r10, [r7, #2]
	ldrb r0, [r6, #4]
	strb r0, [r7, #4]
	mov r0, r8
	bl GetActiveTeamMember
	movs r1, r0
	beq DungeonStat_PeelFromGround
	ldrb r0, [r1]
	tst r0, #1
	beq DungeonStat_PeelFromGround
	ldrsh r0, [r1, #8]
	cmp r0, r9
	bne DungeonStat_PeelFromGround
	ldrsh r0, [r1, #0xc]
	cmp r0, r10
	bne DungeonStat_PeelFromGround
	ldrh r0, [r1, #0x10]
	strh r0, [r7, #6]
	ldrh r0, [r1, #0x12]
	strh r0, [r7, #8]
	ldrh r0, [r1, #0x14]
	strh r0, [r7, #10]
	b DungeonStat_PeelNext
DungeonStat_PeelFromGround:
	mov r0, r9
	bl GetTeamMember
	movs r1, r0
	beq DungeonStat_PeelNext
	ldrb r0, [r1]
	cmp r0, #0
	beq DungeonStat_PeelNext
	ldrsh r0, [r1, #4]
	cmp r0, r10
	bne DungeonStat_PeelNext
	ldrh r0, [r1, #0xa]
	strh r0, [r7, #6]
	ldrh r0, [r1, #0xc]
	strh r0, [r7, #8]
	ldrh r0, [r1, #0xe]
	strh r0, [r7, #10]
DungeonStat_PeelNext:
	add r8, r8, #1
	cmp r8, #4
	blt DungeonStat_PeelLoop
	mov r0, r4
	mov r1, #0
	bl DungeonStat_ApplyBuffer
DungeonStat_PeelDone:
	pop {r4-r10, pc}

; Restore peeled V after the save bitstream is filled.
DungeonStat_UnpeelAfterSave:
	ldr r0, =DungeonStatPeelAddress
	mov r1, #1
	b DungeonStat_ApplyBuffer

.pool

.if . > SpindaEvDungeonStatCave + 0x400
	.error "dungeon stat code overlaps snap buffer"
.endif

; +0 u8 valid
; +4, 4 entries of 12 bytes (see DungeonStat_SnapshotParty).
.org SpindaEvDungeonStatCave + 0x400
DungeonStatSnapAddress:
	.fill 52, 0

; Live V peeled for the duration of GetMonsterInfoForSave (same layout).
.org SpindaEvDungeonStatCave + 0x434
DungeonStatPeelAddress:
	.fill 52, 0

; Summary roster, drink stat, last choice, HP/Spe before, drink boost cache.
; EvDrinkMaskAndInc clears the drink stat after each drink; the last choice byte stays.
.org SpindaEvDungeonStatCave + 0x480
	.fill 16, 0

.org GetMonsterInfoForSave
	b DungeonStat_SaveMonstersClean
