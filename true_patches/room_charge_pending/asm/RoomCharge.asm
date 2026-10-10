; Room-wide attacks (legacy + skip effect on charge) — cave in ov36, hooks in ov29.
; - Custom flags in status info (0x173 pending, 0x174 move slot)
; - Turn 1: BeginRoomChargeTurn only; ExecuteMoveEffect skipped (no DealDamage / no miss IQ)
; - Turn 2: ExecuteMonsterAction forces the stored move; full room damage; PP -1
; Requires ExtraSpace-resident ov36 (Alpha).
;
; Diff from room_charge: charge turn does not run ExecuteMoveEffect (avoids 0-damage = miss).

.nds
.arm
.include "common/offsetsUS.asm"
.include "generated.inc"

.open "overlay_0036.bin", ov_36

.org ov_36 + RoomChargeCodeFileOff

.align 4
RoomChargeMoveBitmapData:
	.byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ; 0-79
	.byte 0x04, 0x00, 0x20, 0x00, 0x43, 0x00, 0x08, 0x00, 0x60, 0x00 ; 80-159 (+Uproar, Earthquake)
	.byte 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x40, 0x40 ; 160-239
	.byte 0x00, 0x00, 0x01, 0x40, 0x40, 0x00, 0x00, 0x01, 0x00, 0x00 ; 240-319 (+Magnitude)
	.byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x00 ; 320-399
	; 400-479: cleared 435 Spacial Rend, 467 Judgement
	.byte 0x00, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x10, 0x00, 0x00 ; 400-479
	; 480-559: cleared 494 Roar of Time
	.byte 0x10, 0x00, 0x00, 0x00, 0x00, 0x0A, 0x00, 0x04, 0x00, 0x04 ; 480-559

.align 4

IsRoomChargeMove:
	push {r1-r3}
	mov r1, r0
	lsr r2, r1, #3
	ldr r0, =RoomChargeMoveBitmapData
	ldrb r0, [r0, r2]
	and r1, r1, #7
	mov r3, #1
	lsl r3, r3, r1
	tst r0, r3
	movne r0, #1
	moveq r0, #0
	pop {r1-r3}
	bx lr

; r4 = move data pointer
IsRoomChargeMovePtr:
	push {lr}
	cmp r4, #0
	moveq r0, #0
	beq IsRoomChargeMovePtrDone
	ldrh r0, [r4, #MoveDataMoveIdOff]
	bl IsRoomChargeMove
IsRoomChargeMovePtrDone:
	pop {pc}

; r0 = entity, r1 = move data pointer -> r0 = slot 0-3 or -1
FindMoveSlotIndex:
	push {r1-r5}
	mov r5, r0
	mov r4, r1
	mov r0, #0xFFFFFFFF
	cmp r4, #0
	beq FindMoveSlotIndexDone
	cmp r5, #0
	beq FindMoveSlotIndexDone
	ldr r1, [r5, #StatusInfoBaseOff]
	cmp r1, #0
	beq FindMoveSlotIndexDone
	mov r2, #0
	add r3, r1, #StatusMoveSlotsBase
FindMoveSlotIndexLoop:
	cmp r2, #4
	bge FindMoveSlotIndexDone
	add r12, r3, r2, lsl #3
	cmp r12, r4
	moveq r0, r2
	beq FindMoveSlotIndexDone
	add r2, r2, #1
	b FindMoveSlotIndexLoop
FindMoveSlotIndexDone:
	pop {r1-r5}
	bx lr

; r0 = entity -> r0 = state byte
GetRoomChargeState:
	ldr r1, [r0, #StatusInfoBaseOff]
	cmp r1, #0
	moveq r0, #0
	beq GetRoomChargeStateDone
	ldrb r0, [r1, #RoomChargeStateOff]
GetRoomChargeStateDone:
	bx lr

; r0 = entity
ClearRoomChargeState:
	push {r1-r2}
	ldr r1, [r0, #StatusInfoBaseOff]
	cmp r1, #0
	beq ClearRoomChargeStateDone
	mov r2, #0
	strb r2, [r1, #RoomChargeStateOff]
	strb r2, [r1, #RoomChargeSlotOff]
ClearRoomChargeStateDone:
	pop {r1-r2}
	bx lr

; r0 = entity -> r0 = 1 if secondary effects should be blocked on charge turn
; Kept as safety net; charge turn no longer runs ExecuteMoveEffect.
ShouldBlockRoomChargeSecondaryEffect:
	push {lr}
	bl GetRoomChargeState
	cmp r0, #RoomChargePending
	movne r0, #0
	moveq r0, #1
	pop {pc}

; r0 = entity, r1 = move data pointer
BeginRoomChargeTurn:
	push {r1-r5, lr}
	mov r4, r0
	mov r5, r1
	mov r0, r4
	mov r1, r5
	bl FindMoveSlotIndex
	cmp r0, #0
	bmi BeginRoomChargeTurnDone
	cmp r0, #3
	bgt BeginRoomChargeTurnDone
	mov r2, r0
	ldr r0, [r4, #StatusInfoBaseOff]
	cmp r0, #0
	beq BeginRoomChargeTurnDone
	mov r1, #RoomChargePending
	strb r1, [r0, #RoomChargeStateOff]
	strb r2, [r0, #RoomChargeSlotOff]
BeginRoomChargeTurnDone:
	pop {r1-r5, pc}

; Undo charge-turn UpdateMovePp (−1): call after BeginRoomChargeTurn on skip path.
RestoreChargeMovePp:
	push {r1-r4}
	ldr r1, [r0, #StatusInfoBaseOff]
	cmp r1, #0
	beq RestoreChargeMovePpDone
	ldrb r2, [r1, #RoomChargeSlotOff]
	cmp r2, #3
	bgt RestoreChargeMovePpDone
	add r3, r1, #StatusMoveSlotsBase
	add r3, r3, r2, lsl #3
	ldrb r0, [r3, #6]
	add r0, r0, #1
	strb r0, [r3, #6]
RestoreChargeMovePpDone:
	pop {r1-r4}
	bx lr

; r0 = entity
; If MonsterCannotAttack (vanilla cannot-act, r1=0), drop Pending/Releasing so
; sleep/para/etc. cancel charge instead of forcing release after recovery.
TryForceRoomChargeAction:
	push {r1-r4, lr}
	mov r4, r0
	mov r1, #0
	bl MonsterCannotAttack
	cmp r0, #0
	beq TryForceRoomChargeActionCheckPending
	mov r0, r4
	bl ClearRoomChargeState
	b TryForceRoomChargeActionDone
TryForceRoomChargeActionCheckPending:
	ldr r1, [r4, #StatusInfoBaseOff]
	cmp r1, #0
	beq TryForceRoomChargeActionDone
	ldrb r0, [r1, #RoomChargeStateOff]
	cmp r0, #RoomChargePending
	bne TryForceRoomChargeActionDone
	mov r0, #RoomChargeReleasing
	strb r0, [r1, #RoomChargeStateOff]
	ldrb r2, [r1, #RoomChargeSlotOff]
	add r0, r1, #StatusActionField
	ldrb r3, [r1, #StatusIsPlayerByte]
	cmp r3, #0
	beq TryForceRoomChargeActionAi
	ldrb r1, [r1, #StatusFacingOrTarget]
	bl SetActionUseMovePlayer
	b TryForceRoomChargeActionDone
TryForceRoomChargeActionAi:
	ldrb r3, [r1, #StatusDirection]
	mov r1, r2
	mov r2, r3
	bl SetActionUseMoveAi
TryForceRoomChargeActionDone:
	mov r0, r4
	pop {r1-r4, pc}

; Replaces mov r0, #1 at ExecuteMonsterAction+8 (entity is in sb after mov sb, r0)
RoomChargeExecuteMonsterActionPrologue:
	push {lr}
	mov r0, r9
	bl TryForceRoomChargeAction
	pop {lr}
	mov r0, #1
	bx lr

; Safety: block DealDamage if somehow called while Pending.
DealDamageRoomChargeWrapper:
	push {r4-r7, lr}
	mov r4, r0
	mov r6, r1
	mov r5, r2
	mov r7, r3
	cmp r4, #0
	beq DealDamageRoomChargeVanilla
	cmp r5, #0
	beq DealDamageRoomChargeVanilla
	mov r0, r4
	bl GetRoomChargeState
	cmp r0, #RoomChargePending
	bne DealDamageRoomChargeVanilla
	mov r0, #0
	pop {r4-r7, pc}
DealDamageRoomChargeVanilla:
	mov r0, r4
	mov r1, r6
	mov r2, r5
	mov r3, r7
	pop {r4-r7, lr}
	push {r3, r4, r5, r6, r7, r8, r9, lr}
	b DealDamageBody

; Replaces bl ExecuteMoveEffect
; Charge (state 0 + room move): BeginRoomChargeTurn, RestoreChargeMovePp, skip effect.
; Release (Releasing): run ExecuteMoveEffect, then ClearRoomChargeState.
; Pending here means an earlier attack of this same move use charged (2 attacks per
; turn from Swift Swim / Chlorophyll / Unburden): release now instead of skipping.
; After any release, end the attack loop so a remaining attack does not recharge.
RoomChargeExecuteMoveEffectWrapper:
	push {r4-r7, lr}
	mov r4, r2
	mov r7, r1
	mov r5, r0
	mov r6, r3
	cmp r4, #0
	beq RoomChargeCallExecuteMoveEffect
	cmp r7, #0
	beq RoomChargeCallExecuteMoveEffect
	mov r0, r7
	bl GetRoomChargeState
	cmp r0, #RoomChargeReleasing
	beq RoomChargeCallExecuteMoveEffect
	cmp r0, #RoomChargePending
	beq RoomChargeReleaseSameAction
	; Idle: start charge for room-charge moves, do not run effect.
	bl IsRoomChargeMovePtr
	cmp r0, #0
	beq RoomChargeCallExecuteMoveEffect
	mov r0, r7
	mov r1, r4
	bl BeginRoomChargeTurn
	mov r0, r7
	bl RestoreChargeMovePp
	b RoomChargeExecuteMoveEffectReturn
RoomChargeReleaseSameAction:
	mov r0, r7
	bl BeginSameActionRelease
RoomChargeCallExecuteMoveEffect:
	mov r0, r5
	mov r1, r7
	mov r2, r4
	mov r3, r6
	bl ExecuteMoveEffect
	cmp r7, #0
	beq RoomChargeExecuteMoveEffectReturn
	mov r0, r7
	bl GetRoomChargeState
	cmp r0, #RoomChargeReleasing
	bne RoomChargeExecuteMoveEffectReturn
	mov r0, r7
	bl FinishRoomChargeRelease
RoomChargeExecuteMoveEffectReturn:
	pop {r4-r7, pc}

; Safety net if secondary rolls run while Pending. The state check clobbers
; r0/r1, so restore all incoming arguments before the original probability roll.
RoomChargeDungeonRandOutcomeGate:
	push {r0-r3, r4, lr}
	bl ShouldBlockRoomChargeSecondaryEffect
	cmp r0, #0
	pop {r0-r3, r4, lr}
	movne r0, #0
	bxne lr
	push {r4, r5, r6, lr}
	b DungeonRandOutcomeUserTargetInteractionBody

; r0 = entity. Pending -> Releasing within one action; take back the charge attack's
; RestoreChargeMovePp so the single UpdateMovePp after the attack loop nets -1.
BeginSameActionRelease:
	ldr r1, [r0, #StatusInfoBaseOff]
	cmp r1, #0
	bxeq lr
	mov r2, #RoomChargeReleasing
	strb r2, [r1, #RoomChargeStateOff]
	ldrb r2, [r1, #RoomChargeSlotOff]
	cmp r2, #3
	bxgt lr
	add r3, r1, #StatusMoveSlotsBase
	add r3, r3, r2, lsl #3
	ldrb r2, [r3, #MovePpOff]
	cmp r2, #0
	subne r2, r2, #1
	strneb r2, [r3, #MovePpOff]
	bx lr

; r0 = entity
FinishRoomChargeRelease:
	push {lr}
	bl ClearRoomChargeState
	ldr r1, [r0, #StatusInfoBaseOff]
	cmp r1, #0
	movne r2, #1
	strneb r2, [r1, #StopAttackLoopOff]
	pop {pc}

.pool

.close

.open "overlay_0029.bin", ov_29

.org ExecuteMoveEffectHook1
	bl RoomChargeExecuteMoveEffectWrapper

.org ExecuteMoveEffectHook2
	bl RoomChargeExecuteMoveEffectWrapper

.org ExecuteMonsterActionHook
	bl RoomChargeExecuteMonsterActionPrologue

.org DealDamageHook
	b DealDamageRoomChargeWrapper

.org DungeonRandOutcomeUserTargetInteraction
	b RoomChargeDungeonRandOutcomeGate

.close
