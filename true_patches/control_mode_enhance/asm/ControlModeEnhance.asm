; Full control mode. Start on any team member's turn toggles auto/manual.
; Select stays camera mode.
;
; Party entities are four fixed slots, stride 0xB8, slot 0 first. Alpha's scan
; only walks forward from whoever just acted, so a round that opens on a later
; slot never comes back to anyone in front of them. NextParty walks the four
; party slots and wraps, and stops when the next one is the round opener
; (CeRoundOrigin), so each living member acts once.
;
; A manual round starts on the current leader, then walks forward through the
; party slots and wraps, until it returns to that leader. Auto follows vanilla's
; ally batch and deferred movement phase before enemies. Manual to auto makes
; that pokemon the leader; the next round starts on them. At each turn the leader is
; controlled. Anyone else is controlled in manual and takes the ally turn in
; auto. A floor transition keeps the current living leader. CeLeader stays at cave+8
; for belly_union; the town assembly can choose a different leader after the run.
;
; A guest (team member_idx 0x55AA, 0x5AA5, or negative) always takes the AI
; turn, in either mode.

.open "overlay_0029.bin", ov_29

.org CmeRunLeaderTurnSite
	bl ControlModeEnhance_BeginRound

.org CmeLeaderMenuSite
	bl ControlModeEnhance_LeaderOrAi

.org CmeFloorInitSite
	b ControlModeEnhance_FloorClear

.org CmeDungeonStartSite
	bl ControlModeEnhance_DungeonStart
.org CmeSpawnTeamSite
	bl ControlModeEnhance_SpawnTeam

.org CmeDungeonEndSite
	bl ControlModeEnhance_DungeonEnd
.org CmeFaintSite
	b ControlModeEnhance_Faint
.org CmeRecruitCheckSite
	b ControlModeEnhance_RecruitCheck
.org CmeTryRecruitSite
	b ControlModeEnhance_TryRecruit

.close

.open "arm9.bin", 0x02000000
.org CmeLeaderSwitchFlagSite
	b ControlModeEnhance_ForceLeaderSwitch
.close

.open "overlay_0036.bin", ov_36

.org CmeToggleGateSite
	bl ControlModeEnhance_HomeToR4

.org CmeToggleMessageSite
	bl ControlModeEnhance_OnToggle

.org CmeTurnEndHomeSite
	bl ControlModeEnhance_HomeToR6

.org CmeAfterTurnHomeSite
	bl ControlModeEnhance_HomeToR1

.org CmeScanHomeSite
	bl ControlModeEnhance_HomeToR6

.org CmeScanStartSite
	bl ControlModeEnhance_ScanStart

.org CmeScanStaySite
	bl ControlModeEnhance_ScanStay

.org CmeScanStepSite
	bl ControlModeEnhance_NextParty

.org CmeScanGiveTurnSite
	bl ControlModeEnhance_GiveTurn

.org CmeScanEndSite
	bl ControlModeEnhance_ScanEnd

.org ov_36 + ControlModeEnhanceCodeAddress
.area 5120

.align 4
CeHome:
.word 0
; 1 = the next RunLeaderTurn starts a round, so the opener must act first.
CeRoundPending:
.word 0
; Cave+8. belly_union imports this address. Do not move it.
CeLeader:
.word 0
; Entity who opened this round. The party walk stops when it would reach them.
CeRoundOrigin:
.word 0
; Entity whose turn just ran. The walk continues after this entity.
CeLastAct:
.word 0
; Persistent roster indices, not entity addresses (entities change per floor).
CeEntryLeader:
.word -1
CeDeadMask:
.word 0
CeDeadHp:
.word 0, 0, 0, 0
; Four PP bytes per roster member. Zero PP is preserved as zero.
CeDeadPp:
.word 0, 0, 0, 0
; Stable guild member identity; unlike active roster / physical slot indices.
CeEntryMemberId:
.word -1
CeDeadMemberId:
.word -1, -1, -1, -1
.align 4

; Performance flag 7 normally unlocks Chimecho Assembly leader selection only
; after graduation. Always report it as enabled for the main game. The caller
; has already saved r4 and expects the ordinary function epilogue here.
ControlModeEnhance_ForceLeaderSwitch:
	bl GetGameMode
	cmp r0, #3
	moveq r0, #0
	movne r0, #1
	and r0, r0, #0xff
	pop {r4, pc}

; r0 = entity. Returns that entity when it is a live team member, else 0.
ControlModeEnhance_LeaderOk:
	push {r1, r2, lr}
	cmp r0, #0
	beq ControlModeEnhance_LeaderBad
	ldr r1, [r0]
	cmp r1, #1
	bne ControlModeEnhance_LeaderBad
	ldr r2, [r0, #0xb4]
	cmp r2, #0
	beq ControlModeEnhance_LeaderBad
	ldrb r1, [r2, #6]
	cmp r1, #0
	bne ControlModeEnhance_LeaderBad
	pop {r1, r2, pc}
ControlModeEnhance_LeaderBad:
	mov r0, #0
	pop {r1, r2, pc}

; Slot 0 entity. Not validated.
ControlModeEnhance_Slot0:
	ldr r0, =DungeonPtrAddr
	ldr r0, [r0]
	add r0, r0, #0x12000
	ldr r0, [r0, #0xb28]
	bx lr

; Returns the round opener in r0, or slot 0 when that entity is gone.
; The mode does not change this.
ControlModeEnhance_ComputeHome:
	push {r1, lr}
	ldr r1, =CeHome
	ldr r0, [r1]
	bl ControlModeEnhance_LeaderOk
	cmp r0, #0
	bne ControlModeEnhance_ComputeHomeDone
	bl ControlModeEnhance_Slot0
ControlModeEnhance_ComputeHomeDone:
	pop {r1, pc}

; The monster currently choosing an action.
ControlModeEnhance_CurrentActor:
	push {r1, lr}
	ldr r1, =LeaderPtrAddr
	ldr r0, [r1]
	cmp r0, #0
	beq ControlModeEnhance_CurrentActorSlot0
	ldr r1, [r0]
	cmp r1, #1
	bne ControlModeEnhance_CurrentActorSlot0
	ldr r1, [r0, #0xb4]
	cmp r1, #0
	beq ControlModeEnhance_CurrentActorSlot0
	pop {r1, pc}
ControlModeEnhance_CurrentActorSlot0:
	bl ControlModeEnhance_Slot0
	pop {r1, pc}

; Replaces "ldr r4, [r2, #0xb28]" (Start toggle gate).
ControlModeEnhance_HomeToR4:
	push {r0, r1, r2, r3, lr}
	bl ControlModeEnhance_CurrentActor
	mov r4, r0
	pop {r0, r1, r2, r3, lr}
	bx lr

; Replaces "ldr r6, [r6, #0xb28]" (end of a member's turn, start of the scan).
ControlModeEnhance_HomeToR6:
	push {r0, r1, r2, r3, lr}
	bl ControlModeEnhance_ComputeHome
	mov r6, r0
	pop {r0, r1, r2, r3, lr}
	bx lr

; Replaces "ldr r1, [r1, #0xb28]" (after the leader's turn).
ControlModeEnhance_HomeToR1:
	push {r0, r2, r3, lr}
	bl ControlModeEnhance_ComputeHome
	mov r1, r0
	pop {r0, r2, r3, lr}
	bx lr

; Replaces "mov r0, r4" before the control mode message. Manual to auto
; makes the pokemon who switched the designated leader. The round opener
; stays put, so the rest of the turn order is unchanged.
ControlModeEnhance_OnToggle:
	push {r0, r1, r2, lr}
	ldr r1, =CeManualFlag
	ldrb r1, [r1]
	cmp r1, #0
	bne ControlModeEnhance_OnToggleDone
	ldr r0, =LeaderPtrAddr
	ldr r0, [r0]
	bl ControlModeEnhance_SetLeader
ControlModeEnhance_OnToggleDone:
	pop {r0, r1, r2, lr}
	mov r0, r4
	bx lr

; Replaces "mov r7, r6" before the member scan. r6 stays the member that just
; acted. r8 becomes CeLeader when that entity is still the chosen leader, so
; the scan's end restores the leader flag onto that pokemon.
ControlModeEnhance_ScanStart:
	mov r7, r6
	push {r0, r1, lr}
	ldr r0, =CeLeader
	ldr r0, [r0]
	bl ControlModeEnhance_LeaderOk
	cmp r0, #0
	beq ControlModeEnhance_ScanStartDone
	mov r8, r0
ControlModeEnhance_ScanStartDone:
	pop {r0, r1, lr}
	bx lr

; Replaces "add r6, r6, #0xb8". Next living party member after r6, wrapping
; past slot 3. Reaching CeRoundOrigin ends the round (r4 = 16).
ControlModeEnhance_NextParty:
	push {r0, r1, r2, r3, r5, lr}
	ldr r5, =DungeonPtrAddr
	ldr r5, [r5]
	add r5, r5, #0x12000
	mov r3, #0
	mvn r2, #0
ControlModeEnhance_NextFind:
	cmp r3, #4
	bge ControlModeEnhance_NextFound
	add r0, r5, r3, lsl #2
	ldr r0, [r0, #0xb28]
	cmp r0, r6
	moveq r2, r3
	beq ControlModeEnhance_NextFound
	add r3, r3, #1
	b ControlModeEnhance_NextFind
ControlModeEnhance_NextFound:
	mov r3, #1
ControlModeEnhance_NextWalk:
	cmp r3, #4
	bgt ControlModeEnhance_NextDone
	add r0, r2, r3
	cmp r0, #4
	subge r0, r0, #4
	add r1, r5, r0, lsl #2
	ldr r1, [r1, #0xb28]
	ldr r0, =CeRoundOrigin
	ldr r0, [r0]
	cmp r0, #0
	beq ControlModeEnhance_NextNotOrigin
	cmp r1, r0
	beq ControlModeEnhance_NextDone
ControlModeEnhance_NextNotOrigin:
	cmp r1, #0
	beq ControlModeEnhance_NextSkip
	ldr r0, [r1]
	cmp r0, #1
	bne ControlModeEnhance_NextSkip
	ldr r0, [r1, #0xb4]
	cmp r0, #0
	beq ControlModeEnhance_NextSkip
	ldrb r0, [r0, #6]
	cmp r0, #0
	bne ControlModeEnhance_NextSkip
	mov r6, r1
	b ControlModeEnhance_NextReturn
ControlModeEnhance_NextSkip:
	add r3, r3, #1
	b ControlModeEnhance_NextWalk
ControlModeEnhance_NextDone:
	mov r4, #16
ControlModeEnhance_NextReturn:
	pop {r0, r1, r2, r3, r5, lr}
	bx lr

; Replaces "mov r6, r8" at the end of the member walk. The next RunLeaderTurn
; starts a new round on whoever is the leader then.
ControlModeEnhance_ScanEnd:
	mov r6, r8
	push {r0, r1, r2, lr}
	mov r0, #1
	ldr r1, =CeRoundPending
	str r0, [r1]
	pop {r0, r1, r2, lr}
	bx lr

; Replaces "mov r10, r0" at the start of RunLeaderTurn. A new round opens on
; the current leader and the lap wraps back to them. A turn already inside a
; lap keeps that lap's opener. The leader, and manual, get the menu. Anyone
; else takes the ally turn before the menu's camera and action display.
ControlModeEnhance_BeginRound:
	push {r0, r1, r2, r3, r4, r5, r6, r7, r8, lr}
	ldr r0, =CeRoundPending
	ldr r1, [r0]
	cmp r1, #0
	beq ControlModeEnhance_BeginRoundMid
	mov r1, #0
	str r1, [r0]
	ldr r0, =CeLeader
	ldr r0, [r0]
	bl ControlModeEnhance_LeaderOk
	cmp r0, #0
	bne ControlModeEnhance_BeginRoundHave
	ldr r0, =LeaderPtrAddr
	ldr r0, [r0]
	bl ControlModeEnhance_LeaderOk
	cmp r0, #0
	bne ControlModeEnhance_BeginRoundHave
	bl ControlModeEnhance_Slot0
ControlModeEnhance_BeginRoundHave:
	ldr r1, =CeHome
	str r0, [r1]
	ldr r1, =CeLeader
	str r0, [r1]
	ldr r1, =CeRoundOrigin
	str r0, [r1]
	mov r6, r0
	b ControlModeEnhance_BeginRoundActor
ControlModeEnhance_BeginRoundMid:
	ldr r0, =CeRoundOrigin
	ldr r1, [r0]
	cmp r1, #0
	bne ControlModeEnhance_BeginRoundMidActor
	ldr r1, =LeaderPtrAddr
	ldr r6, [r1]
	cmp r6, #0
	bne ControlModeEnhance_BeginRoundSetOrigin
	bl ControlModeEnhance_Slot0
	mov r6, r0
ControlModeEnhance_BeginRoundSetOrigin:
	ldr r0, =CeRoundOrigin
	str r6, [r0]
	ldr r0, =CeLeader
	ldr r0, [r0]
	bl ControlModeEnhance_LeaderOk
	cmp r0, #0
	bne ControlModeEnhance_BeginRoundActor
	ldr r0, =CeHome
	str r6, [r0]
	ldr r0, =CeLeader
	str r6, [r0]
	b ControlModeEnhance_BeginRoundActor
ControlModeEnhance_BeginRoundMidActor:
	ldr r6, =LeaderPtrAddr
	ldr r6, [r6]
	cmp r6, #0
	bne ControlModeEnhance_BeginRoundActor
	bl ControlModeEnhance_Slot0
	mov r6, r0
ControlModeEnhance_BeginRoundActor:
	ldr r0, =CeLastAct
	str r6, [r0]
	mov r0, r6
	bl ControlModeEnhance_ShouldPlayer
	cmp r0, #0
	beq ControlModeEnhance_BeginRoundAi
	ldr r5, =LeaderPtrAddr
	ldr r7, [r5]
	cmp r7, #0
	beq ControlModeEnhance_BeginRoundDone
	cmp r7, r6
	beq ControlModeEnhance_BeginRoundDone
	ldr r0, [r7]
	cmp r0, #1
	bne ControlModeEnhance_BeginRoundDone
	bl SwapLeader
	b ControlModeEnhance_BeginRoundDone
ControlModeEnhance_BeginRoundAi:
	mov r0, r6
	bl ControlModeEnhance_SpeedReady
	cmp r0, #0
	beq ControlModeEnhance_BeginRoundSkip
	mov r0, r6
	mov r1, #0
	bl ControlModeEnhance_GuestAi
	pop {r0, r1, r2, r3, r4, r5, r6, r7, r8, lr}
	pop {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
	mov r0, #1
	bx lr
ControlModeEnhance_BeginRoundSkip:
	pop {r0, r1, r2, r3, r4, r5, r6, r7, r8, lr}
	pop {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
	mov r0, #0
	bx lr
ControlModeEnhance_BeginRoundDone:
	pop {r0, r1, r2, r3, r4, r5, r6, r7, r8, lr}
	mov r10, r0
	bx lr

; r0 = entity. 1 when the speed table says this fractional tick is their action.
ControlModeEnhance_SpeedReady:
	push {r4, lr}
	mov r4, r0
	bl CalcSpeedStageWrapper
	ldr r1, =DungeonPtrAddr
	ldr r3, =SpeedTableAddr
	ldr r2, [r1]
	mov r1, #0x32
	add r2, r2, #0x700
	mla r1, r0, r1, r3
	ldrsh r2, [r2, #0x80]
	lsl r0, r2, #1
	bl SpeedStageGate
	pop {r4, lr}
	bx lr

; Slot init runs on floor entry. Drop entity pointers from the previous floor.
; Entered by b, so lr is still the caller's return. Replay the replaced push.
ControlModeEnhance_FloorClear:
	push {r0-r3, r12, lr}
	bl ControlModeEnhance_PrepareFloor
	ldr r0, =CeHome
	mov r1, #0
	str r1, [r0]
	str r1, [r0, #4]
	str r1, [r0, #8]
	str r1, [r0, #12]
	str r1, [r0, #16]
	pop {r0-r3, r12, lr}
	push {r4, r5, r6, r7, r8, lr}
	b CmeFloorInitResume

; r0 = entity. 1 when that monster's active-team member_idx is a guest.
ControlModeEnhance_IsGuest:
	push {r1, r2, lr}
	cmp r0, #0
	beq ControlModeEnhance_IsGuestNo
	ldr r1, [r0, #0xb4]
	cmp r1, #0
	beq ControlModeEnhance_IsGuestNo
	ldrsh r0, [r1, #0xc]
	bl GetActiveTeamMember
	cmp r0, #0
	beq ControlModeEnhance_IsGuestNo
	ldrsh r0, [r0, #8]
	bl IsGuestTeamMember
	pop {r1, r2, lr}
	bx lr
ControlModeEnhance_IsGuestNo:
	mov r0, #0
	pop {r1, r2, lr}
	bx lr

; Replaces "bl" into the leader menu. The speed check has already passed,
; and a normal tick has already run status regen. A player turn keeps the
; menu. An AI turn runs the ally action and returns from RunLeaderTurn.
ControlModeEnhance_LeaderOrAi:
	push {r0, r1, lr}
	mov r0, r9
	bl ControlModeEnhance_ShouldPlayer
	cmp r0, #0
	pop {r0, r1, lr}
	bne ControlModeEnhance_LeaderMenu
	mov r0, r9
	mov r1, #1
	bl ControlModeEnhance_GuestAi
	ldr r1, =DungeonPtrAddr
	ldr r1, [r1]
	mov r0, #0
	strb r0, [r1, #0x11]
	pop {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
	mov r0, #1
	bx lr
ControlModeEnhance_LeaderMenu:
	b LeaderMenuFn

; In auto, return to ExecuteRound's vanilla ally phase. Its deferred movement
; pass groups blocked followers by leader distance before retrying them. Doing
; retries immediately per member can make the rear member lose its move before
; the member in front has acted. Manual still uses the wrapping party scan.
ControlModeEnhance_ScanStay:
	push {r0, r1, lr}
	ldr r0, =CeManualFlag
	ldrb r0, [r0]
	cmp r0, #0
	pop {r0, r1, lr}
	bne ControlModeEnhance_ScanStayManual
	push {r0-r12, lr}
	ldr r0, =CeLeader
	ldr r0, [r0]
	bl ControlModeEnhance_LeaderOk
	cmp r0, #0
	blne ControlModeEnhance_SetLeader
	ldr r0, =CeRoundPending
	mov r1, #1
	str r1, [r0]
	pop {r0-r12, lr}
	; Replay Alpha's original auto return. Its frame is r0-r12 plus saved lr.
	pop {r0-r12, pc}
ControlModeEnhance_ScanStayManual:
	push {r0, lr}
	ldr r0, =DungeonPtrAddr
	ldr r0, [r0]
	add r0, r0, #0x1d8
	mvn r1, #0
	str r1, [r0]
	ldr r5, =LeaderPtrAddr
	ldr r7, [r5]
	ldr r0, =CeLastAct
	ldr r6, [r0]
	cmp r6, #0
	moveq r6, r7
	ldr r0, =CeLeader
	ldr r0, [r0]
	bl ControlModeEnhance_LeaderOk
	cmp r0, #0
	movne r8, r0
	moveq r8, r7
	pop {r0, lr}
	b CmeScanLoopSite

; r0 = entity. 1 when this turn is player-controlled.
; A guest is always the ally turn. The leader is controlled. Anyone else is
; controlled in manual and takes the ally turn in auto.
ControlModeEnhance_ShouldPlayer:
	push {r1, r4, lr}
	mov r4, r0
	bl ControlModeEnhance_IsGuest
	cmp r0, #0
	bne ControlModeEnhance_ShouldAi
	ldr r0, =CeLeader
	ldr r0, [r0]
	bl ControlModeEnhance_LeaderOk
	cmp r0, r4
	beq ControlModeEnhance_ShouldYes
	ldr r1, =CeManualFlag
	ldrb r1, [r1]
	cmp r1, #1
	bne ControlModeEnhance_ShouldAi
ControlModeEnhance_ShouldYes:
	mov r0, #1
	pop {r1, r4, lr}
	bx lr
ControlModeEnhance_ShouldAi:
	mov r0, #0
	pop {r1, r4, lr}
	bx lr

; r0 = entity. That pokemon becomes the leader the party follows. The round
; opener is not touched, so the turn already in progress keeps its order.
ControlModeEnhance_SetLeader:
	push {r4, r5, r6, r7, r8, lr}
	cmp r0, #0
	beq ControlModeEnhance_SetLeaderDone
	mov r4, r0
	ldr r1, =LeaderPtrAddr
	ldr r5, [r1]
	; Manual already made this actor the engine's temporary leader. Even if
	; LeaderPtrAddr matches, synchronize all entity AND persistent roster flags.
ControlModeEnhance_SetLeaderTransfer:
	ldr r8, =DungeonPtrAddr
	ldr r8, [r8]
	add r8, r8, #0x12000
	mov r3, #0
ControlModeEnhance_SetLeaderLoop:
	cmp r3, #4
	bge ControlModeEnhance_SetLeaderTeam
	add r0, r8, r3, lsl #2
	ldr r0, [r0, #0xb28]
	cmp r0, #0
	beq ControlModeEnhance_SetLeaderNext
	ldr r1, [r0, #0xb4]
	cmp r1, #0
	beq ControlModeEnhance_SetLeaderNext
	mov r2, #0
	cmp r0, r4
	moveq r2, #1
	strb r2, [r1, #7]
ControlModeEnhance_SetLeaderNext:
	add r3, r3, #1
	b ControlModeEnhance_SetLeaderLoop
ControlModeEnhance_SetLeaderTeam:
	ldr r8, [r4, #0xb4]
	ldrsh r7, [r8, #0xc]
	mov r6, #0
ControlModeEnhance_SetLeaderTeamLoop:
	cmp r6, #4
	bge ControlModeEnhance_SetLeaderAction
	mov r0, r6
	bl GetActiveTeamMember
	cmp r0, #0
	beq ControlModeEnhance_SetLeaderTeamNext
	ldrb r1, [r0]
	tst r1, #1
	beq ControlModeEnhance_SetLeaderTeamNext
	mov r1, #0
	cmp r6, r7
	moveq r1, #1
	strb r1, [r0, #1]
ControlModeEnhance_SetLeaderTeamNext:
	add r6, r6, #1
	b ControlModeEnhance_SetLeaderTeamLoop
ControlModeEnhance_SetLeaderAction:
	cmp r5, #0
	beq ControlModeEnhance_SetLeaderStore
	cmp r5, r4
	beq ControlModeEnhance_SetLeaderStore
	ldr r6, [r5, #0xb4]
	cmp r6, #0
	beq ControlModeEnhance_SetLeaderStore
	add r1, r6, #0x4a
	mov r3, #10
	mov r0, #0
ControlModeEnhance_SetLeaderZero:
	strh r0, [r1], #2
	subs r3, r3, #1
	bne ControlModeEnhance_SetLeaderZero
ControlModeEnhance_SetLeaderStore:
	ldr r0, =LeaderPtrAddr
	str r4, [r0]
	ldr r0, =CeLeader
	ldr r1, [r0]
	str r4, [r0]
	cmp r1, r4
	beq ControlModeEnhance_SetLeaderDone
	; Let the existing dungeon refresh path recompute its cached team view.
	ldr r0, =DungeonPtrAddr
	ldr r0, [r0]
	mov r1, #1
	strb r1, [r0, #0xE]
ControlModeEnhance_SetLeaderDone:
	pop {r4, r5, r6, r7, r8, lr}
	bx lr

; Replaces "bl SwapLeader" when the scan reaches the next member.
; Player turns still swap the leader in and open the menu. AI turns do not,
; and the walk continues with the same order.
ControlModeEnhance_GiveTurn:
	push {r0, r1, r2, r3, lr}
	mov r0, r6
	bl ControlModeEnhance_ShouldPlayer
	cmp r0, #0
	pop {r0, r1, r2, r3, lr}
	beq ControlModeEnhance_GuestAct
	b SwapLeader
ControlModeEnhance_GuestAct:
	push {r4, r5, r6, r7, r8, lr}
	mov r0, r6
	mov r1, #0
	bl ControlModeEnhance_GuestAi
	cmp r0, #0
	pop {r4, r5, r6, r7, r8, lr}
	bne CmeScanEndSite
	b CmeScanStepSite

; r0 = entity. r1 = 1 when RunLeaderTurn already ran status regen, so this
; skips that step and only performs the action. Returns 1 if the round
; must stop.
ControlModeEnhance_GuestAi:
	push {r4, r5, r6, r7, lr}
	mov r4, r0
	mov r7, r1
	ldr r6, [r4, #0xb4]
	cmp r6, #0
	beq ControlModeEnhance_GuestAiDone
	ldrb r0, [r6, #0x152]
	cmp r0, #0
	bne ControlModeEnhance_GuestAiDone
	ldrh r0, [r6]
	tst r0, #0x8000
	bne ControlModeEnhance_GuestAiDone
	tst r0, #0x4000
	beq ControlModeEnhance_GuestAiLive
	bic r0, r0, #0x4000
	strh r0, [r6]
	b ControlModeEnhance_GuestAiDone
ControlModeEnhance_GuestAiLive:
	ldr r1, =DungeonPtrAddr
	ldr r1, [r1]
	str r4, [r1, #0xc4]
	mov r0, r4
	bl GuestSetActorCam
	bl GuestRefreshLeader
	mov r1, #0
	strb r1, [r6, #0x14e]
	strb r1, [r6, #0x14f]
	cmp r7, #0
	bne ControlModeEnhance_GuestAiArmed
	mov r0, r4
	bl GuestAiDecide
ControlModeEnhance_GuestAiArmed:
	mov r0, r4
	bl GuestEntityValid
	cmp r0, #0
	beq ControlModeEnhance_GuestAiDone
	cmp r7, #0
	bne ControlModeEnhance_GuestAiArm
	mov r0, r4
	bl GuestAfterDecide
ControlModeEnhance_GuestAiArm:
	mov r0, r4
	mov r1, #1
	bl GuestArmAi
	mov r5, #0
ControlModeEnhance_GuestExec:
	cmp r5, #3
	bge ControlModeEnhance_GuestFollow
	mov r0, r4
	mov r1, #0
	bl GuestPreExecute
	bl GuestRoundAbort
	cmp r0, #0
	bne ControlModeEnhance_GuestAiAbort
	mov r0, r4
	bl GuestExecute
	cmp r0, #0
	beq ControlModeEnhance_GuestFollow
	mov r0, #0
	bl GuestTickWait
	bl GuestRoundAbort
	cmp r0, #0
	bne ControlModeEnhance_GuestAiAbort
	add r5, r5, #1
	b ControlModeEnhance_GuestExec
ControlModeEnhance_GuestFollow:
	ldr r1, [r4, #0xb4]
	cmp r1, #0
	beq ControlModeEnhance_GuestAiDone
	ldrb r0, [r1, #0x14e]
	cmp r0, #0
	beq ControlModeEnhance_GuestAiDone
	mov r0, #1
	strb r0, [r1, #0x14f]
	mov r0, #0
	strb r0, [r1, #0x14e]
	mov r0, r4
	mov r1, #1
	bl GuestPreExecute
	mov r0, r4
	bl GuestExecute
	bl GuestFollowupExtra
	mov r0, #0
	bl GuestTickWait
	mov r0, r4
	bl GuestEntityValid
	bl GuestRoundAbort
	cmp r0, #0
	bne ControlModeEnhance_GuestAiAbort
ControlModeEnhance_GuestAiDone:
	mov r0, #0
	pop {r4, r5, r6, r7, lr}
	bx lr
ControlModeEnhance_GuestAiAbort:
	mov r0, #1
	pop {r4, r5, r6, r7, lr}
	bx lr
	.include "Survival.asm"
	.pool

.endarea
.close
