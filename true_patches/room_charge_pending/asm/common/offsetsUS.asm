; US Explorers of Sky addresses (Alpha hack base)
arm9 equ 0x02000000
ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

.definelabel ExecuteMoveEffect,          0x0232E864
.definelabel ExecuteMoveEffectHook1,     0x02322B50
.definelabel ExecuteMoveEffectHook2,     0x023238AC
.definelabel ExecuteMonsterAction,       0x022FE4BC
.definelabel ExecuteMonsterActionHook,    0x022FE4C4
.definelabel DealDamage,                  0x02332B20
.definelabel DealDamageHook,             0x02332B20
.definelabel DealDamageBody,             0x02332B24
.definelabel SetActionUseMovePlayer,     0x022EBC98
.definelabel SetActionUseMoveAi,         0x022EBCBC
.definelabel DungeonRandOutcomeUserTargetInteraction, 0x02324934
.definelabel DungeonRandOutcomeUserTargetInteractionBody, 0x02324938
; Same helper vanilla uses before ClearTwoTurnStatus on cannot-act.
.definelabel MonsterCannotAttack,         0x02300DCC

; RoomChargeCodeFileOff — ov36 file offset from generated.inc

StatusInfoBaseOff       equ 0xB4
StatusMoveSlotsBase     equ 0x124
MoveSlotSize            equ 8
MoveDataMoveIdOff       equ 4
MovePpOff               equ 6

StatusActionField       equ 0x4A
StatusFacingOrTarget    equ 0x4E
StatusDirection         equ 0x4C
StatusIsPlayerByte      equ 0x7

; Cleared at the start of each attack; the move-use attack loop (GetNumberOfAttacks)
; stops when it is nonzero.
StopAttackLoopOff       equ 0x163

RoomChargeStateOff      equ 0x173
RoomChargeSlotOff       equ 0x174
RoomChargePending       equ 1
RoomChargeReleasing     equ 2
