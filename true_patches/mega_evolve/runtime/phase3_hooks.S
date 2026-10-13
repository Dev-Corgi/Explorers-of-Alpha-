/* Native callbacks, preserving stack arguments and pre-existing patch owners. */
entry ME_NativeAbilityHook
 mov r2,lr
 b ME_LegacyAbilityActive

entry ME_TypeHook
 push {r4-r6,lr}
 mov r4,r0
 mov r5,r1
 ldr r12,=PRIOR_MOVE_TYPE
 blx r12
 mov r1,r0
 mov r2,r5
 mov r0,r4
 bl ME_ConvertType
 pop {r4-r6,pc}

entry ME_ActionHook
 push {r4-r8,lr}
 sub sp,sp,#8
 push {r0-r3}
 bl ME_BeginUserAction
 mov r6,r0
 pop {r0-r3}
 ldr r12,[sp,#32]
 str r12,[sp]
 ldr r12,=PRIOR_USE_MOVE
 blx r12
 mov r4,r0
 mov r0,r6
 bl ME_EndAction
 mov r0,r4
 add sp,sp,#8
 pop {r4-r8,pc}

entry ME_MovementHook
 push {r4-r6,lr}
 push {r0-r3}
 bl ME_EnterMovement
 mov r4,r0
 pop {r0-r3}
 bl ME_MovementPrior
 mov r5,r0
 mov r0,r4
 bl ME_LeaveMovement
 mov r0,r5
 pop {r4-r6,pc}
entry ME_MovementPrior
 push {r4-r8,lr}
 ldr pc,=0x022ffdf8

entry ME_CalculationHook
 push {r4-r8,lr}
 sub sp,sp,#24
 push {r0-r3}
 bl ME_EnterCalculation
 mov r6,r0
 pop {r0-r3}
 ldr r12,[sp,#48]
 str r12,[sp]
 ldr r12,[sp,#52]
 str r12,[sp,#4]
 ldr r12,[sp,#56]
 str r12,[sp,#8]
 ldr r12,[sp,#60]
 str r12,[sp,#12]
 ldr r12,[sp,#64]
 str r12,[sp,#16]
 ldr r12,=PRIOR_CALC_DAMAGE
 blx r12
 mov r4,r0
 mov r0,r6
 bl ME_LeaveCalculation
 mov r0,r4
 add sp,sp,#24
 pop {r4-r8,pc}

entry ME_DamageTailHook
 push {r0-r7,r12,lr}
 sub sp,sp,#8
 ldr r4,[sp,#0x124] /* original CalcDamage sp+0xf4: move ID */
 str r4,[sp]
 mov r0,r10
 mov r1,r9
 mov r2,r8
 ldr r3,[sp,#0x3c] /* original sp+0xc: calculated attack type */
 bl ME_AdjustDamage
 add sp,sp,#8
 pop {r0-r7,r12,lr}
 ldr pc,=0x0230d040

entry ME_FaintHook
 push {r0-r3,r12,lr}
 bl ME_FaintBoundary
 pop {r0-r3,r12,lr}
 ldr pc,=PRIOR_FAINT

entry ME_TurnHook
 push {r4-r6,lr}
 mov r4,r0
 bl ME_TurnPrior
 mov r5,r0
 mov r0,r4
 bl ME_TurnTick
 mov r0,r5
 pop {r4-r6,pc}
entry ME_TurnPrior
 push {r3-r11,lr}
 ldr pc,=0x0231108c

entry ME_InitHook
 push {r4-r6,lr}
 mov r4,r1
 bl ME_InitPrior
 mov r5,r0
 mov r0,r4
 bl ME_FloorEntry
 mov r0,r5
 pop {r4-r6,pc}
entry ME_InitPrior
 push {r3-r8,lr}
 ldr pc,=0x022fd9d8

entry ME_FreeHook
 push {r4,lr}
 ldr r12,=PRIOR_DUNGEON_FREE
 blx r12
 bl ME_FreeAbilities
 pop {r4,pc}

entry ME_HitBoundaryHook
 push {r0-r3,r12,lr}
 bl 0x022e81f8
 sub sp,sp,#8
 ldr r12,[sp,#0xb0]
 str r12,[sp]
 mov r0,r8
 mov r1,r7
 mov r2,r10
 ldrb r3,[r6,#0xc]
 bl ME_HitEvent
 add sp,sp,#8
 pop {r0-r3,r12,pc}

.ltorg

entry ME_RedirectHook
 push {r0-r3,r12,lr}
 mov r0,r9
 bl ME_RedirectBlocked
 cmp r0,#0
 pop {r0-r3,r12,lr}
 ldrne pc,=0x0232eaac
 mov r0,r6
 ldr pc,=0x0232e9c4
.ltorg
#include "phase3_status_generated.S"

entry ME_CanUseMoveHook
 push {r0-r3,r12,lr}
 bl ME_MoveAllowed
 cmp r0,#0
 popeq {r0-r3,r12,lr}
 moveq r0,#0
 bxeq lr
 cmp r0,#2
 pop {r0-r3,r12,lr}
 moveq r2,#0 /* Exhausted lock: Struggle bypasses PP check, retains seal/disable checks. */
 push {r3-r5,lr}
 ldr pc,=0x02324b28
.ltorg
