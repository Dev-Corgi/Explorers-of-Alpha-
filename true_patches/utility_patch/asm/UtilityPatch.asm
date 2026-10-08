; Stop B-run when a visible enemy stands two tiles ahead of the leader.

.open "overlay_0029.bin", ov_29

.org ShouldLeaderKeepRunningOkSite
	b UtilityPatch_KeepRunning

.close

.open "overlay_0036.bin", ov_36

.org ov_36 + UtilityPatchCodeAddress

; r4 = leader, r7 = facing, r10 = x, r9 = y. Returns r0 keep-running flag
; and continues at the vanilla epilogue.
UtilityPatch_KeepRunning:
	push {r1, r2, r3, r4, r5, lr}
	ldr r1, =DIRECTIONS_XY
	lsl r2, r7, #2
	ldrsh r3, [r1, r2]
	add r1, r1, #2
	ldrsh r2, [r1, r2]
	lsl r3, r3, #1
	lsl r2, r2, #1
	add r0, r10, r3
	add r1, r9, r2
	bl GetTile
	ldr r1, [r0, #TILE_MONSTER_OFF]
	cmp r1, #0
	beq UtilityPatch_Keep
	ldr r0, [r1]
	cmp r0, #ENTITY_MONSTER
	bne UtilityPatch_Keep
	ldr r2, [r1, #MONSTER_INFO_OFF]
	cmp r2, #0
	beq UtilityPatch_Keep
	ldrb r0, [r2, #IS_NOT_TEAM_MEMBER_OFF]
	cmp r0, #0
	beq UtilityPatch_Keep
	mov r0, r4
	bl CanSeeTarget
	cmp r0, #0
	beq UtilityPatch_Keep
	mov r0, #0
	b UtilityPatch_Done
UtilityPatch_Keep:
	mov r0, #1
UtilityPatch_Done:
	pop {r1, r2, r3, r4, r5, lr}
	b ShouldLeaderKeepRunningEpilogue

	.pool

.close
