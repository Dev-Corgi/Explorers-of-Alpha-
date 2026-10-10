; Z-Move v2: ov29/ov31 hooks + ov36 cave (type effects, runtime, menu helpers).
.nds
.arm

.include "common/offsetsUS.asm"
.include "common/typesUS.asm"

.open "overlay_0029.bin", 0x022DC240

.org GetSubMenuStringId + 0x14
	b ZMove_GetSubMenuStringIdHook

; Undo prior ZGauge hooks: floor HUD / session open-close are not outing end.
.org AllocTopScreenStatus
	push {r3, lr}

; RunDungeon entry -> overlay36_loader (EnsureOv36Loaded + RunDungeonBody).

.org DungeonFree
	b ZMove_OnDungeonGroupEnd

.org DealDamageBody
	b ZMove_DealDamageBodyEntry

.org ApplyDamage
	b ZMove_ApplyDamageHook

.org HandleFaint
	b ZMove_HandleFaintHook

.org TeachItemHandler
	b TeachItemHandler_EntryHook

.org LevelUp
	b ZMove_LevelUpForceRestore

.org RestorePpAllMovesSetFlags
	b ZMove_RestorePpForceRestore

.org FloorHudAfterUpdateHook
	add sp, sp, #0x1C

.org BottomHudAfterBellyHook
	add sp, sp, #0xBC

.org GetMoveTypeForMonster
	b ZMove_GetMoveTypeForMonsterHook

.org GetMovePower
	b ZMove_GetMovePowerHook

.org IsRoomChargeMove
	b ZMove_IsRoomChargeMoveHook

.org CalcDamageJudgmentTypeHookSite
	b ZMove_CalcDamageJudgmentTypeHook
	b CalcDamageAfterJudgmentTypeStore

.org ExecuteMoveEffectHook1
	bl ZMove_ExecuteMoveEffectWrapper

.org ExecuteMoveEffectHook2
	bl ZMove_ExecuteMoveEffectWrapper

.org UseItemBeforeUsedMoveMessageHookSite
	bl ZMove_BeforeUsedMoveMessage

.org UseItemBeforeUsedMoveMessageHookSiteB
	bl ZMove_BeforeUsedMoveMessage

.org UseItemBeforeUsedMoveMessageHookSiteC
	bl ZMove_BeforeUsedMoveMessage

.org ExecuteMonsterActionEpilogueCleanup2Return
	b ZMove_Cleanup2Return

.close

.open "overlay_0036.bin", 0x023A7080

.org ZMoveOv29CodeAddress

; When tm_read is absent, generated.inc points Prior* here (+0 / +8).
ZMove_PriorSubMenuStringCheckFallback:
	mov r4, r1
	b GetSubMenuStringId_Continue

ZMove_PriorCleanupTryRestoreNoOp:
	bx lr

; room_charge_v4 / no v1 helper: safe return-0 (never jump to Alpha padding).
ZMove_RoomChargeMoveNoOp:
	mov r0, #0
	bx lr

ZMove_RoomChargeStateNoOp:
	mov r0, #0
	bx lr

; When tm_read is absent, LevelUp / RestorePp hooks jump here after ForceRestore.
ZMove_PriorLevelUpFallback:
	push {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
	b LevelUpBody

ZMove_PriorRestorePpFallback:
	push {r4, r5, r6, r7, r8, lr}
	b RestorePpAllMovesSetFlagsBody

; DungeonFree entry: DUNGEON_PTR_MASTER is still live (working copy may be 0).
ZMove_OnDungeonGroupEnd:
	push {r0-r3, lr}
	bl ZMove_IsDungeonGroupOutingEnd
	cmp r0, #0
	beq ZMove_OnDungeonGroupEndResume
	bl ZMove_SetZGaugeZero
ZMove_OnDungeonGroupEndResume:
	pop {r0-r3, lr}
	b ZMove_PriorDungeonFree

; r0=1: faint/escape/give-up, or clear of the last floor in the group.
ZMove_IsDungeonGroupOutingEnd:
	push {r4, r5, lr}
	ldr r4, =DungeonMasterPtr
	ldr r5, [r4, #4]
	cmp r5, #0
	ldreq r5, [r4]
	movs r4, r5
	beq ZMove_GroupEndNo
	add r0, r4, #0x2C000
	add r0, r0, #0xA00
	ldrh r0, [r0, #0x66]
	ldr r1, =DAMAGE_SOURCE_DUNGEON_CLEAR
	cmp r0, r1
	bne ZMove_GroupEndYes
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
ZMove_GroupEndYes:
	mov r0, #1
	pop {r4, r5, pc}
ZMove_GroupEndNo:
	mov r0, #0
	pop {r4, r5, pc}

.align 4
ZMoveSelectedEntity:
.word 0

ZMoveSelectedStatus:
.word 0

ZMoveSelectedMoveSlot:
.word 0

ZMovePendingFlag:
.byte 0

ZMoveTwoTurnDeferred:
.byte 0
.align 4

ZMovePendingEntity:
.word 0

ZMoveActiveType:
.byte 0
.align 4

ZMoveEffectApplied:
.byte 0
.align 4

ZMoveTypeMessageLogged:
.byte 0
.align 4

ZMoveSlotBackup:
.fill 8, 0

; Z gauge lives in WRAM (ZGauge / ZGaugeRamAddress) so ov29 unload keeps it.
; Sanitize >MAX (uninit WRAM) to 0.
ZMove_GetZGauge:
	ldr r0, =ZGauge
	ldrh r0, [r0]
	cmp r0, #Z_GAUGE_MAX
	movhi r0, #0
	bx lr

ZMove_SetZGaugeZero:
	ldr r0, =ZGauge
	mov r1, #0
	strh r1, [r0]
	bx lr

; r0 = amount to add (clamped to Z_GAUGE_MAX).
ZMove_AddZGauge:
	push {r1, r2, lr}
	ldr r1, =ZGauge
	ldrh r2, [r1]
	cmp r2, #Z_GAUGE_MAX
	movhi r2, #0
	add r2, r2, r0
	cmp r2, #Z_GAUGE_MAX
	movhi r2, #Z_GAUGE_MAX
	strh r2, [r1]
	pop {r1, r2, pc}

.pool

; DealDamageBody entry: r0=attacker r1=defender r2=move r3=mult.
; Save args across gauge helper calls (GetLeader clobbers caller-saved regs).
ZMove_DealDamageBodyEntry:
	push {r0, r1, r2, r3, lr}
	bl ZMove_TryAddZGaugeLeaderAttack
	pop {r0, r1, r2, r3, lr}
	sub sp, sp, #0x28
	b DealDamageAfterPrologue

; Leader used a non-status move (+1). Called from DealDamageBody prologue.
ZMove_TryAddZGaugeLeaderAttack:
	push {r4, r5, lr}
	mov r4, r0
	mov r5, r2
	cmp r4, #0
	beq ZMove_TryAddZGaugeLeaderAttack_Done
	cmp r5, #0
	beq ZMove_TryAddZGaugeLeaderAttack_Done
	bl GetLeader
	cmp r4, r0
	bne ZMove_TryAddZGaugeLeaderAttack_Done
	ldrh r0, [r5, #MoveDataMoveIdOff]
	bl GetMoveCategory
	cmp r0, #MOVE_CATEGORY_STATUS
	beq ZMove_TryAddZGaugeLeaderAttack_Done
	mov r0, #Z_GAUGE_GAIN_LEADER_ATTACK
	bl ZMove_AddZGauge
ZMove_TryAddZGaugeLeaderAttack_Done:
	pop {r4, r5, pc}

; ApplyDamage entry: run gauge logic, then vanilla prologue (must not skip push).
ZMove_ApplyDamageHook:
	push {r4, r5, r6, lr}
	mov r4, r0
	mov r5, r1
	mov r6, r2
	ldr r0, [r6]
	cmp r0, #0
	beq ZMove_ApplyDamageHook_Continue
	bl GetLeader
	cmp r5, r0
	bne ZMove_ApplyDamageHook_Continue
	mov r0, #Z_GAUGE_GAIN_LEADER_HIT
	bl ZMove_AddZGauge
ZMove_ApplyDamageHook_Continue:
	mov r0, r4
	mov r1, r5
	mov r2, r6
	pop {r4, r5, r6, lr}
	push {r4, r5, r6, r7, r8, r9, r10, r11, lr}
	b ApplyDamageBody

; HandleFaint entry: +2 for non-team faints, then vanilla prologue.
ZMove_HandleFaintHook:
	; GetTeamMemberIndex clobbers r1-r3. Preserve HandleFaint's damage
	; source (r1) and optional message/context pointer (r2) before the call.
	push {r1-r4, r12, lr}
	mov r4, r0
	mov r0, r4
	bl GetTeamMemberIndex
	cmp r0, #4
	blo ZMove_HandleFaintHook_Continue
	mov r0, #Z_GAUGE_GAIN_ENEMY_FAINT
	bl ZMove_AddZGauge
ZMove_HandleFaintHook_Continue:
	mov r0, r4
	pop {r1-r4, r12, lr}
	push {r4, r5, r6, r7, r8, r9, r10, r11, lr}
	b HandleFaintBody

; r0 = window id. Dungeon menu status: Z row above Money (x=0x73 y=0, Money @ y=0xc).
; Uses PreprocessString so [M:S6] yellow matches dungeon HP/Lv text (Snprintf ignores color tags).
ZMove_DrawZGaugeHudMenuMoneyRow:
	push {r4, r5, r6, lr}
	mov r4, r0
	sub sp, sp, #0xC0
	bl ZMove_GetZGauge
	str r0, [sp, #0x2C]
	add r5, sp, #8
	add r0, sp, #0x58
	mov r1, #0x64
	ldr r2, =ZMove_ZGaugeHudFmt
	mov r3, #0
	str r5, [sp]
	bl PreprocessString
	mov r0, r4
	mov r1, #0x73
	mov r2, #0
	add r3, sp, #0x58
	bl DrawTextInWindow
	add sp, sp, #0xC0
	pop {r4, r5, r6, pc}

; ov31 @ 0x23828F8: draw Z row, then GetMoneyCarried (r10/sl = window id in caller).
ZMove_DrawThenGetMoney:
	push {r4, lr}
	mov r0, r10
	bl ZMove_DrawZGaugeHudMenuMoneyRow
	pop {r4, lr}
	b GetMoneyCarried

ZMove_ZGaugeHudFmt:
.ascii "[M:S6]Z : [value:0:3]/100[CR]", 0
.align 4

; --- Runtime overrides while Z-Move pending (shell move 559: custom type/power). ---

ZMove_ReadActiveTypeByte:
	ldr r0, =ZMoveActiveType
	ldrb r0, [r0]
	bx lr

ZMove_GetMovePowerHook:
	ldr r2, =ZMovePendingFlag
	ldrb r2, [r2]
	cmp r2, #0
	beq ZMove_GetMovePower_Original
	ldrh r2, [r1, #MoveDataMoveIdOff]
	ldr r3, =Z_MOVE_SHELL_ID
	cmp r2, r3
	bne ZMove_GetMovePower_Original
	push {lr}
	bl ZMove_ReadActiveTypeByte
	cmp r0, #TYPE_NORMAL
	movne r0, #Z_MOVE_POWER
	popne {lr}
	bxne lr
	mov r0, #Z_MOVE_POWER_NORMAL
	pop {lr}
	bx lr

ZMove_GetMovePower_Original:
	push {r3, r4, r5, lr}
	b GetMovePowerBody

ZMove_GetMoveTypeForMonsterHook:
	ldr r2, =ZMovePendingFlag
	ldrb r2, [r2]
	cmp r2, #0
	beq ZMove_GetMoveTypeForMonster_Original
	ldrh r2, [r1, #MoveDataMoveIdOff]
	ldr r3, =Z_MOVE_SHELL_ID
	cmp r2, r3
	bne ZMove_GetMoveTypeForMonster_Original
	ldr r0, =ZMoveActiveType
	ldrb r0, [r0]
	bx lr

ZMove_GetMoveTypeForMonster_Original:
	push {r3, r4, r5, lr}
	b GetMoveTypeForMonsterBody

ZMove_IsRoomChargeMoveHook:
	ldr r1, =ZMovePendingFlag
	ldrb r1, [r1]
	cmp r1, #0
	beq ZMove_IsRoomChargeMove_Original
	; Z-Move turn: never treat Judgment shell as room-charge during ValidateMoveTarget.
	mov r0, #0
	bx lr

; PriorIsRoomChargeMove is always a full function (room_charge / tm_read stub / local no-op).
ZMove_IsRoomChargeMove_Original:
	b PriorIsRoomChargeMove

; CalcDamage type override. Judgement (467) keeps the user type.
; Z-Move shell (559) uses ZMoveActiveType only while a Z-Move is pending.
ZMove_CalcDamageJudgmentTypeHook:
	ldr r0, [sp, #0xf4]
	ldr r1, =Z_MOVE_SHELL_ID
	cmp r0, r1
	bne ZMove_CalcDamageJudgmentType_CheckJudgment
	ldr r2, =ZMovePendingFlag
	ldrb r2, [r2]
	cmp r2, #0
	beq CalcDamageAfterJudgmentTypeStore
	ldr r2, =ZMoveActiveType
	ldrb r0, [r2]
	b ZMove_CalcDamageJudgmentType_Store
ZMove_CalcDamageJudgmentType_CheckJudgment:
	ldr r1, =JUDGMENT_MOVE_ID
	cmp r0, r1
	bne CalcDamageAfterJudgmentTypeStore
ZMove_CalcDamageJudgmentType_Vanilla:
	ldrb r0, [r6, #AttackerPrimaryTypeOff]
ZMove_CalcDamageJudgmentType_Store:
	str r0, [sp, #0xc]
	b CalcDamageAfterJudgmentTypeStore

ZMove_GetSubMenuStringIdHook:
	cmp r6, #ACTION_Z_MOVE
	beq ZMove_ReturnZMoveString
	b PriorSubMenuStringCheck

ZMove_ReturnZMoveString:
	ldr r0, =STRING_ID_Z_MOVE_MENU
	pop {r3, r4, r5, r6, r7, pc}

; ov31 move submenu @ 0x023859C0: r6 = entity, r7 = status
; Only inject Z when the gauge is full, and only patch the string if Add actually
; appended ACTION_Z_MOVE (Add can no-op on full/duplicate — never write count-1 blind).
ZMove_TryAppendZMoveOption:
	push {r4, lr}
	bl ZMove_GetZGauge
	cmp r0, #Z_GAUGE_MAX
	bne ZMove_TryAppendZMoveOption_Done
	ldr r0, =ZMoveSelectedEntity
	str r6, [r0]
	ldr r0, =ZMoveSelectedStatus
	str r7, [r0]
	ldr r0, =MoveMenuSelectedSlotPtr
	ldr r0, [r0]
	and r0, r0, #3
	ldr r1, =ZMoveSelectedMoveSlot
	str r0, [r1]
	ldr r1, =DungeonSubMenuCountPtr
	ldr r4, [r1]
	mov r0, #ACTION_Z_MOVE
	mov r1, #1
	bl AddDungeonSubMenuOption
	ldr r1, =DungeonSubMenuCountPtr
	ldr r0, [r1]
	cmp r0, r4
	beq ZMove_TryAppendZMoveOption_Done
	cmp r0, #0
	beq ZMove_TryAppendZMoveOption_Done
	sub r0, r0, #1
	lsl r0, r0, #3
	ldr r1, =DungeonSubMenuStringIds
	sub r2, r1, #6
	ldrh r2, [r2, r0]
	cmp r2, #ACTION_Z_MOVE
	bne ZMove_TryAppendZMoveOption_Done
	ldr r2, =STRING_ID_Z_MOVE_MENU
	strh r2, [r1, r0]
ZMove_TryAppendZMoveOption_Done:
	pop {r4, pc}

ZMove_Ov31MenuHook:
	push {lr}
	bl ZMove_TryAppendZMoveOption
	bl SortSubMenu
	pop {lr}
	b ZMoveMenuResume

; TeachItemHandler entry: force-restore tm_read + Z-Move slot 3 before moveset edits.
TeachItemHandler_EntryHook:
	push {r3, lr}
	bl ZMove_ForceRestoreAllPendingSlots
	pop {r3, lr}
	push {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
	b TeachItemHandlerResume

; LevelUp entry: restore before learn-move UI (Joy Seed / exp / evolution).
ZMove_LevelUpForceRestore:
	push {r0-r3, lr}
	bl ZMove_ForceRestoreAllPendingSlots
	pop {r0-r3, lr}
	b PriorLevelUp

; Revive PP path: restore + clear stuck charge deferral before PP rewrite.
ZMove_RestorePpForceRestore:
	push {r0-r3, lr}
	bl ZMove_ForceRestoreAllPendingSlots
	pop {r0-r3, lr}
	b PriorRestorePp

; Clear deferral flags, drop charge status on pending entity, then restore both patches.
ZMove_ForceRestoreAllPendingSlots:
	push {r4, lr}
	ldr r4, =ZMovePendingEntity
	ldr r4, [r4]
	mov r0, #0
	ldr r1, =ZMoveTwoTurnDeferred
	strb r0, [r1]
	cmp r4, #0
	beq ZMove_ForceRestoreAll_DoRestore
	mov r0, r4
	bl ClearTwoTurnStatus
ZMove_ForceRestoreAll_DoRestore:
	mov r0, #0
	bl PriorCleanupTryRestore
	mov r0, #0
	bl ZMove_TryRestoreSlotForEntity
	pop {r4, pc}

ZMove_RestoreAllPendingSlots:
	b ZMove_ForceRestoreAllPendingSlots

; Slot restore after entity validation (chained from tm_read PostValidateRestoreBl when applied).
ZMove_TryRestoreSlotForEntity:
	push {r4-r8, lr}
	mov r8, r0
	ldr r4, =ZMovePendingFlag
	ldrb r0, [r4]
	cmp r0, #0
	beq ZMove_TryRestoreSlotDone
	ldr r5, =ZMovePendingEntity
	ldr r5, [r5]
	cmp r5, #0
	beq ZMove_TryRestoreSlotClear
	cmp r8, #0
	beq ZMove_TryRestoreSlotAfterEntityGate
	cmp r8, r5
	bne ZMove_TryRestoreSlotDone
ZMove_TryRestoreSlotAfterEntityGate:
	bl ZMove_LoadEntityStatus
	cmp r6, #0
	beq ZMove_TryRestoreSlotClear
	ldr r0, =ZMoveTwoTurnDeferred
	ldrb r0, [r0]
	cmp r0, #0
	beq ZMove_TryRestoreSlotDoRestore
	mov r0, r5
	add r1, r6, #StatusMoveSlot3Off
	bl IsChargingTwoTurnMove
	cmp r0, #0
	bne ZMove_TryRestoreSlotDone
	mov r0, r5
	bl PriorGetRoomChargeState
	cmp r0, #RoomChargePending
	beq ZMove_TryRestoreSlotDone
ZMove_TryRestoreSlotDoRestore:
	mov r7, #ZMoveTempMoveSlot
	ldr r0, =ZMoveSlotBackup
	add r1, r6, #StatusMoveSlotsBase
	add r1, r1, r7, lsl #3
	ldmia r0, {r2, r3}
	stmia r1, {r2, r3}
ZMove_TryRestoreSlotClear:
	mov r0, #0
	strb r0, [r4]
	mov r0, #0
	ldr r1, =ZMoveTwoTurnDeferred
	strb r0, [r1]
	mov r0, #0
	ldr r1, =ZMoveEffectApplied
	strb r0, [r1]
	mov r0, #0
	ldr r1, =ZMoveTypeMessageLogged
	strb r0, [r1]
	mov r0, #0
	ldr r1, =ZMovePendingEntity
	str r0, [r1]
ZMove_TryRestoreSlotDone:
	pop {r4-r8, pc}

ZMove_TryRestoreSlot:
	mov r0, #0
	b ZMove_TryRestoreSlotForEntity

; --- Temporary slot 3 backup/restore + Z-Move (559) executor. ---

ZMove_BackupMoveSlot:
	push {r0-r3, lr}
	mov r7, #ZMoveTempMoveSlot
	add r0, r6, #StatusMoveSlotsBase
	add r0, r0, r7, lsl #3
	ldr r1, =ZMoveSlotBackup
	ldmia r0, {r2, r3}
	stmia r1, {r2, r3}
	pop {r0-r3, pc}

ZMove_RestoreMoveSlotFromBackup:
	push {r4-r7, lr}
	mov r6, r0
	mov r7, #ZMoveTempMoveSlot
	ldr r0, =ZMoveSlotBackup
	add r1, r6, #StatusMoveSlotsBase
	add r1, r1, r7, lsl #3
	ldmia r0, {r2, r3}
	stmia r1, {r2, r3}
	pop {r4-r7, pc}

; r10 = entity, r6 = status -> r0 = 1 on success
ZMove_CallMoveMenuUseSlot3:
	push {r4, r5, lr}
	mov r4, #ZMoveTempMoveSlot
	mov r5, #ZMoveTempMoveSlot
	bl CheckDungeonMoveValidateGate
	cmp r0, #0
	beq ZMove_CallMoveMenuUseSlot3_SetAction
	mov r0, r10
	add r1, r6, #StatusMoveSlotsBase
	add r1, r1, r5, lsl #3
	bl ValidateMoveTarget
	cmp r0, #0
	beq ZMove_CallMoveMenuUseSlot3_Fail
ZMove_CallMoveMenuUseSlot3_SetAction:
	mov r0, r10
	bl GetTeamMemberIndex
	mov r1, r0
	add r0, r6, #StatusActionField
	mov r2, r4
	bl SetActionUseMovePlayer
	mov r0, #1
	pop {r4, r5, pc}
ZMove_CallMoveMenuUseSlot3_Fail:
	mov r0, #0
	pop {r4, r5, pc}

; r10 = entity -> r0 = 1 on success
ZMove_SetupAction:
	push {r4-r7, lr}
	ldr r0, =ZMoveSelectedStatus
	ldr r6, [r0]
	cmp r6, #0
	beq ZMove_SetupAction_Fail
	ldr r0, =ZMoveSelectedEntity
	ldr r0, [r0]
	mov r10, r0
	cmp r10, #0
	beq ZMove_SetupAction_Fail
	bl ZMove_GetZGauge
	cmp r0, #Z_GAUGE_MAX
	bne ZMove_SetupAction_Fail
	ldr r0, =ZMoveSelectedMoveSlot
	ldr r7, [r0]
.if ZMOVE_DEBUG_FORCE_TYPE != 0
	mov r0, #ZMOVE_DEBUG_FORCE_TYPE
.else
	add r1, r6, #StatusMoveSlotsBase
	add r1, r1, r7, lsl #3
	mov r0, r10
	bl GetMoveTypeForMonster
.endif
	ldr r1, =ZMoveActiveType
	strb r0, [r1]
	mov r0, #0
	ldr r1, =ZMoveTwoTurnDeferred
	strb r0, [r1]
	mov r0, r6
	bl ZMove_BackupMoveSlot
	mov r7, #ZMoveTempMoveSlot
	add r0, r6, #StatusMoveSlotsBase
	add r0, r0, r7, lsl #3
	ldr r1, =Z_MOVE_SHELL_ID
	bl InitMove
	bl ZMove_CallMoveMenuUseSlot3
	cmp r0, #0
	beq ZMove_SetupAction_RestoreFail
	ldr r0, =ZMovePendingEntity
	str r10, [r0]
	mov r0, #0
	ldr r1, =ZMoveEffectApplied
	strb r0, [r1]
	mov r0, #1
	ldr r1, =ZMovePendingFlag
	strb r0, [r1]
	bl ZMove_SetZGaugeZero
	mov r0, #1
	pop {r4-r7, pc}
ZMove_SetupAction_RestoreFail:
	mov r0, #0
	ldr r1, =ZMoveTwoTurnDeferred
	strb r0, [r1]
	mov r0, r6
	bl ZMove_RestoreMoveSlotFromBackup
ZMove_SetupAction_Fail:
	mov r0, #0
	pop {r4-r7, pc}

; r0 = string id for current ZMoveActiveType (19102 + type, clamped).
ZMove_GetActiveTypeStringId:
	ldr r0, =ZMoveActiveType
	ldrb r0, [r0]
	cmp r0, #0
	beq ZMove_GetActiveTypeStringIdDefault
	cmp r0, #Z_MOVE_TYPE_COUNT
	ldr r1, =STRING_ID_Z_POWER_MESSAGE_BASE
	addlo r0, r1, r0
	movhs r0, r1
	bx lr
ZMove_GetActiveTypeStringIdDefault:
	ldr r0, =STRING_ID_Z_POWER_MESSAGE_BASE
	bx lr

; r6 = user — before vanilla LogMessageWithPopupCheckUser ("used move!").
ZMove_BeforeUsedMoveMessage:
	push {r4, lr}
	mov r4, r6
	mov r0, r4
	bl ZMove_TryLogZPowerMessage
	mov r0, r4
	pop {r4, pc}

; r0 = user entity — "[name] surrounded itself with its [Type] Z-Power!"
ZMove_TryLogZPowerMessage:
	push {r4, lr}
	mov r4, r0
	ldr r0, =ZMovePendingFlag
	ldrb r0, [r0]
	cmp r0, #0
	beq ZMove_TryLogZPowerMessage_Done
	ldr r0, =ZMovePendingEntity
	ldr r0, [r0]
	cmp r0, r4
	bne ZMove_TryLogZPowerMessage_Done
	ldr r0, =ZMoveTypeMessageLogged
	ldrb r0, [r0]
	cmp r0, #0
	bne ZMove_TryLogZPowerMessage_Done
	bl ZMove_GetActiveTypeStringId
	mov r1, r0
	mov r0, r4
	bl LogMessageByIdWithPopupCheckUser
	mov r0, #Z_MOVE_MESSAGE_WAIT_FRAMES
	mov r1, #Z_MOVE_MESSAGE_WAIT_PARAM
	bl MessageWaitAfterPopup
	mov r0, #1
	ldr r1, =ZMoveTypeMessageLogged
	strb r0, [r1]
ZMove_TryLogZPowerMessage_Done:
	pop {r4, pc}

; ov31 @ 0x02385FC0: r1 = action id, r5 = status+0x4A (move-interaction confirm).
ZMove_SetActionFieldDispatch:
	cmp r1, #ACTION_Z_MOVE
	beq ZMove_SetActionFieldDispatch_DoZMove
	b SetActionField

ZMove_SetActionFieldDispatch_DoZMove:
	push {r4, lr}
	ldr r0, =ZMoveSelectedStatus
	ldr r6, [r0]
	ldr r0, =ZMoveSelectedEntity
	ldr r10, [r0]
	bl ZMove_SetupAction
	cmp r0, #0
	beq ZMove_SetActionFieldDispatch_Fail
	pop {r4, lr}
	pop {r3, r4, r5, pc}

ZMove_SetActionFieldDispatch_Fail:
	mov r0, r10
	ldr r1, =STRING_ID_MOVE_FAILED
	bl LogMessageByIdQuiet
	add r0, r6, #StatusActionField
	mov r1, #1
	bl SetActionField
	pop {r4, lr}
	pop {r3, r4, r5, pc}

.pool

; Hook args: r0=target struct, r1=user, r2=move, r3=move slot
ZMove_ExecuteMoveEffectWrapper:
	push {r4-r7, lr}
	mov r7, r0
	mov r4, r1
	mov r5, r2
	mov r6, r3
	ldr r0, =ZMovePendingFlag
	ldrb r0, [r0]
	cmp r0, #0
	bne ZMove_ExecuteMoveEffectWrapper_Direct
	mov r0, r7
	mov r1, r4
	mov r2, r5
	mov r3, r6
	bl PriorExecuteMoveEffectCall
	b ZMove_ExecuteMoveEffectWrapper_TypeFx
ZMove_ExecuteMoveEffectWrapper_Direct:
	mov r0, r7
	mov r1, r4
	mov r2, r5
	mov r3, r6
	bl ExecuteMoveEffect
ZMove_ExecuteMoveEffectWrapper_TypeFx:
	mov r0, r4
	mov r1, r7
	mov r2, r5
	bl ZMove_TryApplyTypeEffect
	pop {r4-r7, pc}

; r5 = entity -> r6 = status (0 if entity or vtable is null).
ZMove_LoadEntityStatus:
	ldr r0, [r5]
	cmp r0, #0
	moveq r6, #0
	bxeq lr
	ldr r6, [r5, #0xB4]
	bx lr

; When tm_read is absent: Cleanup2Return hook restores tm_read + Z-Move slot 3.
ZMove_Cleanup2Return:
	ldr r12, =ZMovePendingFlag
	ldrb r12, [r12]
	cmp r12, #0
	beq ZMove_Cleanup2Return_Skip
	push {r4, lr}
	mov r4, r0
	mov r0, #0
	bl PriorCleanupTryRestore
	mov r0, #0
	bl ZMove_TryRestoreSlotForEntity
	mov r0, r4
	pop {r4, lr}
ZMove_Cleanup2Return_Skip:
	bx lr

.include "ZMoveExecuteEffects.asm"

.pool

.close
