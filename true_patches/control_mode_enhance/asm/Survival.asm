; Regular members remain in the active roster when fainted. Their entity is
; removed normally, but neither their roster slot nor held item is discarded.
; Guests retain vanilla death/escort rules and can never keep the run alive.

ControlModeEnhance_DungeonStart:
	push {r0, r1}
	ldr r0, =CeEntryLeader
	mvn r1, #0
	str r1, [r0]
	ldr r0, =CeEntryMemberId
	str r1, [r0]
	ldr r0, =CeDeadMask
	mov r1, #0
	str r1, [r0]
	pop {r0, r1}
	b CmeFloorInitSite

ControlModeEnhance_PrepareFloor:
	push {r4-r7, lr}
	ldr r0, =CeDeadMask
	ldr r7, [r0]
	mov r4, #0
@@slot:
	mov r0, r4
	bl GetActiveTeamMember
	mov r5, r0
	cmp r5, #0
	beq @@next
	ldrb r0, [r5]
	tst r0, #1
	beq @@next
	ldrsh r0, [r5, #8]
	bl IsGuestTeamMember
	cmp r0, #0
	bne @@next
	; Backups follow guild identity, not a slot that may have been reordered.
	ldrsh r3, [r5, #8]
	ldr r2, =CeDeadMemberId
	mov r6, #0
@@backup:
	mov r0, #1
	tst r7, r0, lsl r6
	beq @@backup_next
	ldr r1, [r2, r6, lsl #2]
	cmp r1, r3
	beq @@restore
@@backup_next:
	add r6, r6, #1
	cmp r6, #4
	blt @@backup
	b @@next
@@restore:
	ldr r0, =CeDeadHp
	ldr r0, [r0, r6, lsl #2]
	strh r0, [r5, #0xE]
	; Restore the death-time PP in the active roster BEFORE vanilla floor
	; initialization/spawning. Subsequent vanilla PP processing is unchanged.
	ldr r1, =CeDeadPp
	add r1, r1, r6, lsl #2
	add r2, r5, #0x1C
	mov r3, #0
@@pp:
	ldrb r0, [r1, r3]
	strb r0, [r2, #6]
	add r2, r2, #8
	add r3, r3, #1
	cmp r3, #4
	blt @@pp
	ldrb r0, [r5]
	bic r0, r0, #8
	orr r0, r0, #3
	strb r0, [r5]
@@next:
	add r4, r4, #1
	cmp r4, #4
	blt @@slot
	ldr r0, =CeDeadMask
	mov r1, #0
	str r1, [r0]
@@done:
	pop {r4-r7, pc}

ControlModeEnhance_SpawnTeam:
	push {r4-r8, lr}
	bl SpawnTeam
	mov r8, r0
	; Keep the leader selected during the dungeon. SpawnTeam normally retains
	; that leader across a floor; synchronize our manual-mode state to the same
	; live entity without restoring the dungeon-entry leader.
	ldr r0, =LeaderPtrAddr
	ldr r4, [r0]
	mov r0, r4
	bl ControlModeEnhance_RegularAlive
	cmp r0, #0
	beq @@done
	mov r0, r4
	bl ControlModeEnhance_SetLeader
	ldr r0, =CeHome
	str r4, [r0]
	ldr r0, =CeRoundPending
	mov r1, #1
	str r1, [r0]
@@done:
	mov r0, r8
	pop {r4-r8, pc}

; Stable entry guild ID -> current active-roster index, or -1. Kept for
; diagnostics and death bookkeeping; dungeon exits no longer restore it.
ControlModeEnhance_ResolveEntry:
	push {r4-r6, lr}
	ldr r0, =CeEntryMemberId
	ldr r5, [r0]
	cmp r5, #0
	blt @@missing
	mov r4, #0
@@slot:
	mov r0, r4
	bl GetActiveTeamMember
	cmp r0, #0
	beq @@next
	ldrsh r1, [r0, #8]
	cmp r1, r5
	beq @@found
@@next:
	add r4, r4, #1
	cmp r4, #4
	blt @@slot
@@missing:
	mvn r0, #0
	b @@done
@@found:
	mov r0, r4
@@done:
	ldr r1, =CeEntryLeader
	str r0, [r1]
	pop {r4-r6, pc}

; All exits: preserve the current leader, clear only our death reservations, and
; preserve result, death HP, PP and items.
ControlModeEnhance_DungeonEnd:
	push {r0-r12, lr}
	mov r5, #0
@@slot:
	mov r0, r5
	bl GetActiveTeamMember
	cmp r0, #0
	beq @@next
	; Drop only our reservation marker; never turn a dead member into alive.
	mov r6, r0
	ldrsh r9, [r6, #8]
	ldr r0, =CeDeadMask
	ldr r7, [r0]
	ldr r3, =CeDeadMemberId
	mov r8, #0
@@record:
	mov r1, #1
	tst r7, r1, lsl r8
	beq @@record_next
	ldr r1, [r3, r8, lsl #2]
	cmp r1, r9
	bne @@record_next
	ldrb r1, [r6]
	bic r1, r1, #8
	strb r1, [r6]
	b @@next
@@record_next:
	add r8, r8, #1
	cmp r8, #4
	blt @@record
@@next:
	add r5, r5, #1
	cmp r5, #4
	blt @@slot
@@done:
	ldr r0, =CeDeadMask
	mov r1, #0
	str r1, [r0]
	pop {r0-r12, lr}
	b CmeDungeonEndOriginal

; r0 = entity -> bool, regardless of HP. Check the roster range BEFORE lookup.
ControlModeEnhance_IsRegular:
	push {r4, lr}
	mov r4, r0
	bl ControlModeEnhance_LeaderOk
	cmp r0, #0
	beq @@no
	ldr r1, [r4, #0xB4]
	ldrsh r0, [r1, #0xC]
	cmp r0, #4
	bhs @@no
	bl GetActiveTeamMember
	cmp r0, #0
	beq @@no
	ldrb r1, [r0]
	and r1, r1, #3
	cmp r1, #3
	bne @@no
	mov r0, r4
	bl ControlModeEnhance_IsGuest
	b @@result
@@no:
	mov r0, #0
	pop {r4, pc}
@@result:
	cmp r0, #0
	moveq r0, #1
	movne r0, #0
	pop {r4, pc}

ControlModeEnhance_RegularAlive:
	push {r4, lr}
	mov r4, r0
	bl ControlModeEnhance_IsRegular
	cmp r0, #0
	beq @@done
	ldr r1, [r4, #0xB4]
	ldrsh r0, [r1, #0x10]
	cmp r0, #0
	movgt r0, r4
	movle r0, #0
@@done:
	pop {r4, pc}

; r0 = persistent roster index -> living regular entity, or zero.
ControlModeEnhance_FindMember:
	push {r4-r6, lr}
	mov r4, r0
	ldr r0, =DungeonPtrAddr
	ldr r6, [r0]
	add r6, r6, #0x12000
	mov r5, #0
@@slot:
	add r0, r6, r5, lsl #2
	ldr r0, [r0, #0xB28]
	bl ControlModeEnhance_RegularAlive
	cmp r0, #0
	beq @@next
	ldr r1, [r0, #0xB4]
	ldrsh r1, [r1, #0xC]
	cmp r1, r4
	beq @@done
@@next:
	add r5, r5, #1
	cmp r5, #4
	blt @@slot
	mov r0, #0
@@done:
	pop {r4-r6, pc}

; Entered in HandleFaint with r10 = victim, r7 = monster, r9 = damage source.
; The send-home action also calls HandleFaint, with DAMAGE_SOURCE_WENT_AWAY
; (604). Let vanilla remove that member instead of reserving it for revival.
; Returning to the original epilogue retains its stack frame.
ControlModeEnhance_Faint:
	cmp r9, #604
	beq @@vanilla
	push {r0-r12, lr}
	mov r0, r10
	bl ControlModeEnhance_ReserveFaint
	cmp r0, #0
	pop {r0-r12, lr}
	bne CmeFaintReturn
@@vanilla:
	ldrb r0, [r7, #7]
	b CmeFaintResume

ControlModeEnhance_ReserveFaint:
	push {r4-r9, r12, lr}
	mov r4, r0
	bl ControlModeEnhance_IsRegular
	cmp r0, #0
	beq @@vanilla
	; The initial floor can enter through a vanilla spawn path that does not
	; reach our SpawnTeam wrapper.  If the entry identity is still unset,
	; capture the designated leader while that entity is still alive.  This is
	; the last reliable point before a leader faint removes its entity.
	ldr r0, =CeEntryMemberId
	ldr r1, [r0]
	cmp r1, #0
	bge @@entry_ready
	ldr r0, =CeHome
	ldr r0, [r0]
	bl ControlModeEnhance_RegularAlive
	cmp r0, #0
	beq @@entry_ready
	ldr r1, [r0, #0xB4]
	ldrsh r1, [r1, #0xC]
	ldr r2, =CeEntryMemberId
	str r1, [r2]
@@entry_ready:
	ldr r5, [r4, #0xB4]
	ldrsh r6, [r5, #0xC]
	mov r7, #1
@@find:
	add r0, r6, r7
	and r0, r0, #3
	bl ControlModeEnhance_FindMember
	cmp r0, #0
	bne @@survivor
	add r7, r7, #1
	cmp r7, #4
	blt @@find
	; Only guests (or nobody) remain. Ensure vanilla treats this as leader loss
	; even if manual control temporarily made a guest the engine's actor.
	mov r0, r4
	bl ControlModeEnhance_SetLeader
	b @@vanilla
@@survivor:
	mov r8, r0
	; A nonleader faint must not change the user's designated living leader.
	ldr r0, =CeLeader
	ldr r0, [r0]
	bl ControlModeEnhance_RegularAlive
	cmp r0, #0
	movne r8, r0
	mov r0, r6
	mov r1, r5
	bl UpdateTeamMember
	mov r0, r6
	bl GetActiveTeamMember
	ldrsh r9, [r0, #8]
	ldr r1, =CeDeadMask
	ldr r2, [r1]
	ldr r3, =CeDeadMemberId
	mov r1, #0
@@record:
	mov r12, #1
	tst r2, r12, lsl r1
	beq @@record_free
	add r1, r1, #1
	cmp r1, #4
	blt @@record
	; Four living-slot deaths cannot fill a fifth record while play continues.
	b @@vanilla
@@record_free:
	str r9, [r3, r1, lsl #2]
	mov r9, r1
	ldrb r1, [r0]
	orr r1, r1, #0xB
	strb r1, [r0]
	; Store actual maximum HP separately; team+0x10 also contains Speed V.
	ldrsh r0, [r5, #0x12]
	ldrsh r1, [r5, #0x16]
	add r0, r0, r1
	cmp r0, #1
	movlt r0, #1
	ldr r1, =0x7FFF
	cmp r0, r1
	movgt r0, r1
	ldr r1, =CeDeadHp
	str r0, [r1, r9, lsl #2]
	ldr r1, =CeDeadPp
	add r1, r1, r9, lsl #2
	add r2, r5, #0x124
	mov r3, #0
@@pp:
	ldrb r0, [r2, #6]
	strb r0, [r1, r3]
	add r2, r2, #8
	add r3, r3, #1
	cmp r3, #4
	blt @@pp
	ldr r0, =CeDeadMask
	ldr r1, [r0]
	mov r2, #1
	orr r1, r1, r2, lsl r9
	str r1, [r0]
	mov r0, r8
	bl ControlModeEnhance_SetLeader
	ldr r0, =CeHome
	ldr r1, [r0]
	cmp r1, r4
	streq r8, [r0]
	; Vanilla visual/entity cleanup, without releasing the active roster slot.
	mov r0, r4
	mov r1, #1
	bl DetachMonster
	ldr r0, [r5, #0xB0]
	bl FreeMonsterSprite
	mov r0, #0
	str r0, [r4]
	ldr r1, =DungeonPtrAddr
	ldr r1, [r1]
	mov r0, #1
	strb r0, [r1, #0xE]
	bl RefreshMonsterTiles
	bl RefreshDungeonView1
	bl RefreshDungeonView2
	mov r0, #1
	pop {r4-r9, r12, pc}

@@vanilla:
	mov r0, #0
	pop {r4-r9, r12, pc}

; Run the vanilla eligibility/chance checks first, then block successful offers.
; Thus the warning is not spammed for every enemy or changed recruitment RNG.
ControlModeEnhance_RecruitCheck:
	push {r4-r6, lr}
	mov r4, r0
	bl @@vanilla
	cmp r0, #0
	beq @@done
	ldr r1, =CeDeadMask
	ldr r1, [r1]
	cmp r1, #0
	beq @@done
	mov r0, r4
	bl ControlModeEnhance_RecruitBlocked
@@done:
	pop {r4-r6, pc}
@@vanilla:
	push {r3-r9, lr}
	b CmeRecruitCheckBody

; Also cover explicit TryRecruit callers that bypass RecruitCheck.
ControlModeEnhance_TryRecruit:
	ldr r12, =CeDeadMask
	ldr r12, [r12]
	cmp r12, #0
	bne ControlModeEnhance_RecruitBlocked
	push {r4-r11, lr}
	b CmeTryRecruitBody

ControlModeEnhance_RecruitBlocked:
	push {r4, lr}
	ldr r1, =CmeRecruitBlockedId
	mov r2, #0
	bl LogMessageById
	mov r0, #0
	pop {r4, pc}
