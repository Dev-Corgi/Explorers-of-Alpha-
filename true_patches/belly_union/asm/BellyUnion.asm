; One belly for the whole team.
;
; Walk drain used to run on every member that looked like the leader. In manual
; control that is every actor, so a shared belly would fall once per member.
; The drain now runs only when the real leader walks. In manual state that is
; CeLeader (the leader stored for manual mode), not the round opener. Allies' held items that
; the drain formula already checks are summed into that single step.
; TryIncreaseBelly / TryDecreaseBelly, hunger seed, and belly refills copy the
; changed value onto every team member.

.open "overlay_0029.bin", ov_29

.org BuDrainGateSite
	bl BellyUnion_ShouldDrain

.org BuTightScaleSite
	b BellyUnion_TightScale

.org BuAfterBellySite
	bl BellyUnion_AfterBelly

.org BuDecreaseSite
	b BellyUnion_Decrease

.org BuIncreaseSite
	b BellyUnion_Increase

.org BuTeamInitSite
	bl BellyUnion_AfterTeamInit

.org BuMonsterInitSite
	bl BellyUnion_AfterMonsterInit

.org BuSubInitSite
	bl BellyUnion_AfterSubInit

.org BuHungerSite
	bl BellyUnion_AfterHunger

.org BuFillASite
	bl BellyUnion_AfterFillR4

.org BuFillBSite
	bl BellyUnion_AfterFillR4

.org BuFillCSite
	bl BellyUnion_AfterFillR4

.org BuMoveFillSite
	bl BellyUnion_AfterMoveFill

.org BuMoveWriteSite
	bl BellyUnion_AfterMoveWrite

.org BuMoveSetSite
	bl BellyUnion_AfterMoveSet

.org ItemIsActive_09
	b BellyUnion_ItemIsActive

.close

.open "overlay_0036.bin", ov_36

.org BuSkipDrainSite
	b BellyUnion_SkipDrain

.org ov_36 + BellyUnionCodeAddress

; r5 is the actor. Return r0 = 1 when this walk should drain the shared belly.
; Diet Orb sets OrbFx_DietFlag. Address 0 means that module is absent.
BellyUnion_ShouldDrain:
	push {r1, lr}
	ldr r1, =OrbFx_DietFlag
	cmp r1, #0
	beq BellyUnion_ShouldDrain_Actor
	ldrb r1, [r1]
	cmp r1, #0
	beq BellyUnion_ShouldDrain_Actor
	mov r0, #0
	pop {r1, pc}
BellyUnion_ShouldDrain_Actor:
	bl BellyUnion_DrainActor
	cmp r0, r5
	moveq r0, #1
	movne r0, #0
	pop {r1, pc}

; Alpha re-enters the drain for every manual-mode actor. Always leave instead.
BellyUnion_SkipDrain:
	b BuSkipDrainTarget

; Tight Belt subtracts 10 from the drain index per holder. r0 is the count.
BellyUnion_TightScale:
	mov r2, r0, lsl #3
	add r2, r2, r0, lsl #1
	b BuTightContinue

; The drain writes the actor, then every path joins here. Mirror the leader.
BellyUnion_AfterBelly:
	push {r0-r3, lr}
	bl BellyUnion_DrainActor
	push {r0}
	bl BellyUnion_Broadcast
	pop {r0}
	bl BellyUnion_SyncFamished
	pop {r0-r3, lr}
	mov r0, r5
	bx lr

BellyUnion_Decrease:
	ldr r12, =BuDecLr
	str lr, [r12]
	ldr r12, =BuDecTarget
	str r1, [r12]
	ldr lr, =BellyUnion_DecreaseDone
	push {r3, r4, r5, r6, r7, r8, lr}
	b TryDecreaseBody

BellyUnion_DecreaseDone:
	push {r0-r3, lr}
	ldr r0, =BuDecTarget
	ldr r0, [r0]
	bl BellyUnion_Broadcast
	pop {r0-r3, lr}
	ldr r12, =BuDecLr
	ldr pc, [r12]

BellyUnion_Increase:
	ldr r12, =BuIncLr
	str lr, [r12]
	ldr r12, =BuIncTarget
	str r1, [r12]
	ldr lr, =BellyUnion_IncreaseDone
	push {r4-r11, lr}
	b TryIncreaseBody

BellyUnion_IncreaseDone:
	push {r0-r3, lr}
	ldr r0, =BuIncTarget
	ldr r0, [r0]
	bl BellyUnion_Broadcast
	pop {r0-r3, lr}
	ldr r12, =BuIncLr
	ldr pc, [r12]

; Called with the same r0 SubInitMonster expects. r6 is the entity.
BellyUnion_AfterSubInit:
	push {r4, r6, lr}
	mov r4, r6
	bl SubInitMonster
	mov r0, r4
	bl BellyUnion_Adopt
	pop {r4, r6, pc}

BellyUnion_AfterTeamInit:
	strh r1, [r3, #0x4c]
	push {r0-r3, lr}
	mov r0, r7
	bl BellyUnion_Adopt
	pop {r0-r3, pc}

; cmp r5, #0 just ran; the next ldrhne still needs those flags.
BellyUnion_AfterMonsterInit:
	strh r1, [r0, #0x4c]
	push {r0-r3, r12, lr}
	mrs r12, cpsr
	mov r0, r4
	bl BellyUnion_EntityFromMonster
	bl BellyUnion_Adopt
	msr cpsr_f, r12
	pop {r0-r3, r12, pc}

BellyUnion_AfterHunger:
	strh r4, [r3, #0x48]
	push {r0-r3, lr}
	mov r0, r5
	bl BellyUnion_Broadcast
	pop {r0-r3, pc}

BellyUnion_AfterFillR4:
	strh r1, [r0, #0x48]
	push {r0-r3, lr}
	mov r0, r4
	bl BellyUnion_EntityFromMonster
	bl BellyUnion_Broadcast
	pop {r0-r3, pc}

BellyUnion_AfterMoveFill:
	strh r2, [r1, #0x48]
	push {r0-r3, lr}
	mov r0, r4
	bl BellyUnion_Broadcast
	pop {r0-r3, pc}

BellyUnion_AfterMoveWrite:
	strh r2, [r1, #0x48]
	push {r0-r3, lr}
	mov r0, r10
	bl BellyUnion_EntityFromMonster
	bl BellyUnion_Broadcast
	pop {r0-r3, pc}

BellyUnion_AfterMoveSet:
	strh r1, [r0, #0x48]
	push {r0-r3, lr}
	mov r0, r5
	bl BellyUnion_EntityFromMonster
	bl BellyUnion_Broadcast
	pop {r0-r3, pc}

; r0 entity, r1 item. Inside the walk drain, return how many team members have it.
BellyUnion_ItemIsActive:
	push {r4-r8, lr}
	mov r4, r0
	mov r5, r1
	mov r0, lr
	bl BellyUnion_IsDrainCaller
	cmp r0, #0
	beq BellyUnion_ItemOne
	mov r6, #0
	mov r7, #0
	ldr r8, =DungeonPtrAddr
	ldr r8, [r8]
	cmp r8, #0
	beq BellyUnion_ItemDone
BellyUnion_ItemLoop:
	cmp r7, #4
	bge BellyUnion_ItemDone
	add r0, r8, r7, lsl #2
	add r0, r0, #0x12000
	ldr r0, [r0, #0xb28]
	cmp r0, #0
	beq BellyUnion_ItemNext
	bl BellyUnion_IsTeam
	cmp r0, #0
	beq BellyUnion_ItemNext
	add r0, r8, r7, lsl #2
	add r0, r0, #0x12000
	ldr r0, [r0, #0xb28]
	mov r1, r5
	bl PriorItemIsActive
	add r6, r6, r0
BellyUnion_ItemNext:
	add r7, r7, #1
	b BellyUnion_ItemLoop
BellyUnion_ItemDone:
	mov r0, r6
	pop {r4-r8, pc}
BellyUnion_ItemOne:
	mov r0, r4
	mov r1, r5
	bl PriorItemIsActive
	pop {r4-r8, pc}

; r0 = return address. 1 if that call is part of the walk-drain formula.
BellyUnion_IsDrainCaller:
	push {r1, r2, lr}
	ldr r1, =BuDrainRets
BellyUnion_RetLoop:
	ldr r2, [r1], #4
	cmp r2, #0
	beq BellyUnion_RetNo
	cmp r2, r0
	bne BellyUnion_RetLoop
	mov r0, #1
	pop {r1, r2, pc}
BellyUnion_RetNo:
	mov r0, #0
	pop {r1, r2, pc}

; Entity whose walk drains, and whose belly is the shared value.
; Manual state: CeLeader. Otherwise the flagged leader.
BellyUnion_DrainActor:
	push {r1-r3, lr}
	ldr r1, =CeManualFlag
	ldrb r1, [r1]
	cmp r1, #1
	bne BellyUnion_DrainFlag
	ldr r1, =CeLeader
	cmp r1, #0
	beq BellyUnion_DrainFlag
	ldr r0, [r1]
	mov r2, r0
	bl BellyUnion_IsTeam
	cmp r0, #0
	beq BellyUnion_DrainFlag
	mov r0, r2
	pop {r1-r3, pc}
BellyUnion_DrainFlag:
	ldr r1, =LeaderPtrAddr
	ldr r0, [r1]
	mov r2, r0
	bl BellyUnion_IsTeam
	cmp r0, #0
	beq BellyUnion_DrainScan
	ldr r1, [r2, #0xb4]
	ldrb r1, [r1, #7]
	cmp r1, #0
	beq BellyUnion_DrainScan
	mov r0, r2
	pop {r1-r3, pc}
BellyUnion_DrainScan:
	ldr r1, =DungeonPtrAddr
	ldr r1, [r1]
	cmp r1, #0
	beq BellyUnion_DrainNone
	mov r3, #0
BellyUnion_DrainScanLoop:
	cmp r3, #4
	bge BellyUnion_DrainNone
	add r0, r1, r3, lsl #2
	add r0, r0, #0x12000
	ldr r2, [r0, #0xb28]
	cmp r2, #0
	beq BellyUnion_DrainScanNext
	mov r0, r2
	bl BellyUnion_IsTeam
	cmp r0, #0
	beq BellyUnion_DrainScanNext
	ldr r0, [r2, #0xb4]
	ldrb r0, [r0, #7]
	cmp r0, #0
	beq BellyUnion_DrainScanNext
	mov r0, r2
	pop {r1-r3, pc}
BellyUnion_DrainScanNext:
	add r3, r3, #1
	b BellyUnion_DrainScanLoop
BellyUnion_DrainNone:
	mov r0, #0
	pop {r1-r3, pc}

; r0 = entity. If it is a team member, make its belly match the shared value.
; When it is the shared holder, copy that value out to the rest of the party.
BellyUnion_Adopt:
	push {r4, lr}
	mov r4, r0
	bl BellyUnion_IsTeam
	cmp r0, #0
	beq BellyUnion_AdoptOut
	bl BellyUnion_DrainActor
	cmp r0, #0
	beq BellyUnion_AdoptOut
	cmp r0, r4
	bne BellyUnion_AdoptOne
	bl BellyUnion_Broadcast
	b BellyUnion_AdoptOut
BellyUnion_AdoptOne:
	mov r1, r4
	bl BellyUnion_CopyOne
BellyUnion_AdoptOut:
	pop {r4, pc}

; r0 = source entity. Copy its four belly halfwords onto every team member.
BellyUnion_Broadcast:
	push {r4-r7, lr}
	mov r4, r0
	bl BellyUnion_IsTeam
	cmp r0, #0
	beq BellyUnion_BroadcastOut
	ldr r5, =DungeonPtrAddr
	ldr r5, [r5]
	cmp r5, #0
	beq BellyUnion_BroadcastOut
	mov r6, #0
BellyUnion_BroadcastLoop:
	cmp r6, #4
	bge BellyUnion_BroadcastOut
	add r0, r5, r6, lsl #2
	add r0, r0, #0x12000
	ldr r7, [r0, #0xb28]
	cmp r7, #0
	beq BellyUnion_BroadcastNext
	mov r0, r7
	bl BellyUnion_IsTeam
	cmp r0, #0
	beq BellyUnion_BroadcastNext
	mov r0, r4
	mov r1, r7
	bl BellyUnion_CopyOne
BellyUnion_BroadcastNext:
	add r6, r6, #1
	b BellyUnion_BroadcastLoop
BellyUnion_BroadcastOut:
	pop {r4-r7, pc}

; r0 = source entity. Copy famished (monster+0x150) onto the team.
; The walk drain updates that flag only on the actor who drained.
BellyUnion_SyncFamished:
	push {r4-r7, lr}
	cmp r0, #0
	beq BellyUnion_FamishOut
	ldr r4, [r0, #0xb4]
	cmp r4, #0
	beq BellyUnion_FamishOut
	ldrb r4, [r4, #0x150]
	ldr r5, =DungeonPtrAddr
	ldr r5, [r5]
	cmp r5, #0
	beq BellyUnion_FamishOut
	mov r6, #0
BellyUnion_FamishLoop:
	cmp r6, #4
	bge BellyUnion_FamishOut
	add r0, r5, r6, lsl #2
	add r0, r0, #0x12000
	ldr r7, [r0, #0xb28]
	cmp r7, #0
	beq BellyUnion_FamishNext
	mov r0, r7
	bl BellyUnion_IsTeam
	cmp r0, #0
	beq BellyUnion_FamishNext
	ldr r0, [r7, #0xb4]
	cmp r0, #0
	beq BellyUnion_FamishNext
	strb r4, [r0, #0x150]
BellyUnion_FamishNext:
	add r6, r6, #1
	b BellyUnion_FamishLoop
BellyUnion_FamishOut:
	pop {r4-r7, pc}

; r0 = source entity, r1 = dest entity.
BellyUnion_CopyOne:
	push {r2-r4, lr}
	cmp r0, #0
	beq BellyUnion_CopyOut
	cmp r1, #0
	beq BellyUnion_CopyOut
	cmp r0, r1
	beq BellyUnion_CopyOut
	ldr r2, [r0, #0xb4]
	ldr r3, [r1, #0xb4]
	cmp r2, #0
	beq BellyUnion_CopyOut
	cmp r3, #0
	beq BellyUnion_CopyOut
	add r2, r2, #0x100
	add r3, r3, #0x100
	ldrh r4, [r2, #0x46]
	strh r4, [r3, #0x46]
	ldrh r4, [r2, #0x48]
	strh r4, [r3, #0x48]
	ldrh r4, [r2, #0x4a]
	strh r4, [r3, #0x4a]
	ldrh r4, [r2, #0x4c]
	strh r4, [r3, #0x4c]
BellyUnion_CopyOut:
	pop {r2-r4, pc}

; r0 = monster pointer. Return the team slot entity that owns it, or 0.
BellyUnion_EntityFromMonster:
	push {r4-r7, lr}
	mov r4, r0
	ldr r5, =DungeonPtrAddr
	ldr r5, [r5]
	cmp r5, #0
	beq BellyUnion_EntityNone
	mov r6, #0
BellyUnion_EntityLoop:
	cmp r6, #4
	bge BellyUnion_EntityNone
	add r0, r5, r6, lsl #2
	add r0, r0, #0x12000
	ldr r7, [r0, #0xb28]
	cmp r7, #0
	beq BellyUnion_EntityNext
	ldr r0, [r7, #0xb4]
	cmp r0, r4
	beq BellyUnion_EntityFound
BellyUnion_EntityNext:
	add r6, r6, #1
	b BellyUnion_EntityLoop
BellyUnion_EntityFound:
	mov r0, r7
	pop {r4-r7, pc}
BellyUnion_EntityNone:
	mov r0, #0
	pop {r4-r7, pc}

; r0 = entity. 1 when it is a living team member.
BellyUnion_IsTeam:
	push {r1, r2, lr}
	mov r1, r0
	bl EntityIsValid
	cmp r0, #0
	beq BellyUnion_IsTeamNo
	mov r0, r1
	ldr r2, [r0]
	cmp r2, #1
	bne BellyUnion_IsTeamNo
	ldr r2, [r0, #0xb4]
	cmp r2, #0
	beq BellyUnion_IsTeamNo
	ldrb r2, [r2, #6]
	cmp r2, #0
	movne r0, #0
	moveq r0, #1
	pop {r1, r2, pc}
BellyUnion_IsTeamNo:
	mov r0, #0
	pop {r1, r2, pc}

.align 4
BuDecLr:
	.word 0
BuDecTarget:
	.word 0
BuIncLr:
	.word 0
BuIncTarget:
	.word 0
BuDrainRets:
	.word BuRetTight
	.word BuRetStamina
	.word BuRetDiet
	.word BuRetHeal
	.word BuRetMunch
	.word BuRetItem18
	.word BuRetItem21
	.word BuRetAlpha1
	.word BuRetAlpha2
	.word BuRetAlpha3
	.word BuRetAlpha4
	.word BuRetAlpha5
	.word 0

.pool

.close
