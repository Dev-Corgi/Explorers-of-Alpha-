; Exclude guest Pokémon from Level Scaling party-level math.
; Guest member_idx: 0x55AA, 0x5AA5, or negative (IsGuestTeamMember @ arm9).

.open "arm9.bin", arm9

.org LevelScaleArm9PerSlotGuestSite
	b LevelScaleGuestFix_Arm9PerSlot

.org LevelScaleArm9DungeonEntryAfterGetSite
	b LevelScaleGuestFix_Arm9DungeonEntry

.org LevelScaleArm9StatInitProcessSite
	b LevelScaleGuestFix_Arm9StatInit

.close

.open "overlay_0036.bin", ov_36

.org LevelScaleAlphaPartyMaxHook
	b LevelScaleGuestFix_AlphaPartyMax

.org LevelScaleAlphaPartyMaxSlotLimit
	cmp r1, #4

.org LevelScaleAlphaSpawnLdrbSite
	b LevelScaleGuestFix_AlphaSpawnSkip

.close

.open "overlay_0029.bin", ov_29

.org GetMonsterLevelCmpSite
	b LevelScaleGuestFix_KecleonLevelMatch

.close

.open "overlay_0036.bin", ov_36

.org ov_36 + LevelScaleGuestFixCodeAddress

; r0 = team_member*; returns r0 = 1 if guest.
LevelScaleGuestFix_IsGuestMember:
	push {lr}
	ldrsh r0, [r0, #8]
	bl IsGuestTeamMember
	pop {lr}
	bx lr

; r5 = slot index; early-out for guest slots (fixes slot-index vs member_idx bug).
LevelScaleGuestFix_Arm9PerSlot:
	mov r0, r5
	bl GetActiveTeamMember
	cmp r0, #0
	beq LevelScaleArm9PerSlotContinue
	push {lr}
	bl LevelScaleGuestFix_IsGuestMember
	cmp r0, #0
	pop {lr}
	popne {r3, r4, r5, pc}
	b LevelScaleArm9PerSlotContinue

; r0 = team_member* after GetActiveTeamMember in dungeon-entry loop.
LevelScaleGuestFix_Arm9DungeonEntry:
	push {r0, lr}
	bl LevelScaleGuestFix_IsGuestMember
	cmp r0, #0
	pop {r0, lr}
	bne LevelScaleArm9DungeonEntryNextSlot
	ldrb r1, [r0]
	b LevelScaleArm9DungeonEntryActiveCheck

; r8 = team_member* on active slot path in stat-init loop.
LevelScaleGuestFix_Arm9StatInit:
	mov r0, r8
	push {lr}
	bl LevelScaleGuestFix_IsGuestMember
	cmp r0, #0
	pop {lr}
	bne LevelScaleArm9StatInitSkipSlot
	strb r7, [sp, #6]
	b 0x0205783C

; r0 = team_member* in the Alpha party-max loop. Skip guests before [member+2]
; is compared into the running max (r3). r1 = slot, r3 = max so far.
LevelScaleGuestFix_AlphaPartyMax:
	push {r0, r1, lr}
	bl LevelScaleGuestFix_IsGuestMember
	cmp r0, #0
	pop {r0, r1, lr}
	bne LevelScaleAlphaPartyMaxNext
	ldrb r4, [r0]
	tst r4, #1
	beq LevelScaleAlphaPartyMaxNext
	b LevelScaleAlphaPartyMaxUseLevel

; r0 = monster id. EQ if Kecleon 383/384 or 983/984.
LevelScaleGuestFix_IsKecleon:
	push {r1}
	mov r1, #0x180
	cmp r0, r1
	sub r1, r1, #1
	cmpne r0, r1
	add r1, r1, #0x258
	cmpne r0, r1
	add r1, r1, #1
	cmpne r0, r1
	pop {r1}
	bx lr

; r5 = spawn entry+1 (high byte of packed level). ID at entry+6.
LevelScaleGuestFix_AlphaSpawnSkip:
	push {r0, r1, lr}
	ldrh r0, [r5, #5]
	bl LevelScaleGuestFix_IsKecleon
	pop {r0, r1, lr}
	beq LevelScaleAlphaSpawnNext
	ldrb r4, [r5]
	b LevelScaleAlphaSpawnAfterLdrb

; r5 = requested id, r0 = list-entry id. Any two Kecleon ids match.
LevelScaleGuestFix_KecleonLevelMatch:
	push {r0, r1, r2, lr}
	mov r2, r0
	mov r0, r5
	bl LevelScaleGuestFix_IsKecleon
	bne LevelScaleGuestFix_KecleonNotPair
	mov r0, r2
	bl LevelScaleGuestFix_IsKecleon
	bne LevelScaleGuestFix_KecleonNotPair
	pop {r0, r1, r2, lr}
	cmp r5, r5
	b GetMonsterLevelCmpContinue
LevelScaleGuestFix_KecleonNotPair:
	pop {r0, r1, r2, lr}
	cmp r5, r0
	b GetMonsterLevelCmpContinue

.close
