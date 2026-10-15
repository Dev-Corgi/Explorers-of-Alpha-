/* Native callbacks, preserving stack arguments and pre-existing patch owners. */
entry ME_NativeAbilityHook
 push {r3,lr}
 mov r2,lr
 bl ME_LegacyAbilityActive
 pop {r3,pc}

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

/* TryActivateWeather invokes its native visual/form callback only after an
 * accepted change or forced fresh application, never a quiet weather query. */
entry ME_WeatherAppliedHook
 push {r0-r3,r12,lr}
 ldr r12,=0x02334e70
 blx r12
 bl ME_NewSunlight
 pop {r0-r3,r12,pc}
.ltorg

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

/* ExecuteMoveEffect is after the ordinary PP boundary. Keep both strikes in
 * the same user action; nested effects get an independent quarter-damage scope. */
entry ME_ParentEffectHook
 push {r4-r9,lr}
 sub sp,sp,#12
 mov r4,r0
 mov r5,r1
 mov r7,r2
 mov r8,r3
 push {r0-r3}
 mov r0,r1
 mov r1,r2
 bl ME_EnterEffect
 mov r6,r0
 pop {r0-r3}
 ldr r12,[sp,#40]
 str r12,[sp]
 ldr r12,=PRIOR_EXECUTE_EFFECT
 blx r12
 mov r9,r0
 mov r0,r6
 bl ME_ParentRepeat
 cmp r0,#0
 beq 1f
 mov r0,r4
 mov r1,r5
 mov r2,r7
 mov r3,r8
 ldr r12,=PRIOR_EXECUTE_EFFECT
 blx r12
1:
 mov r0,r6
 bl ME_LeaveEffect
 mov r0,r9
 add sp,sp,#12
 pop {r4-r9,pc}
.ltorg

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
#ifdef ME_PHASE4
 bl ME_QuickReady
 mov r0,r4
#endif
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
#ifdef ME_TRIAL_TOWER
 bl ME_TowerReset
#endif
 pop {r4,pc}

entry ME_HitBoundaryHook
 push {r0-r3,r12,lr}
 ldr r12,=0x022e81f8
 blx r12
 sub sp,sp,#8
 ldr r12,[sp,#0xb0]
 str r12,[sp]
 mov r0,r8
 mov r1,r7
 mov r2,r10
 mov r3,r6
 bl ME_ReportHit
 add sp,sp,#8
 pop {r0-r3,r12,pc}

.ltorg

entry ME_ExecuteActionHook
 push {r4-r8,lr}
 mov r4,r0
 ldr r5,[r4,#4]
 ldr r6,[r4,#0xb4]
 ldrh r6,[r6,#0x4a]
 bl ME_ActorStarts
 mov r0,r4
 bl ME_BlockMagnetWalk
 mov r0,r4
 bl ME_ExecuteActionPrior
 mov r7,r0
 mov r0,r4
 mov r1,r5
 mov r2,r6
 bl ME_ActorFinishes
 mov r0,r7
 pop {r4-r8,pc}
entry ME_ExecuteActionPrior
 push {r3-r9,lr}
 ldr pc,=0x022fe4c0
.ltorg

entry ME_BerryConsumeHook
 push {r0-r3,r12,lr}
 mov r0,r8
 add r1,sp,#32 /* UseSingleUseItem's copied item at original sp+8. */
 bl ME_KeepBerry
 cmp r0,#0
 pop {r0-r3,r12,lr}
 bxne lr
 ldr pc,=0x022eb60c
.ltorg

entry ME_FloorTrapHook
 push {r0-r3,r12,lr}
 cmp r11,#0 /* Native force-effect argument: direct activation skips avoidance. */
 bne 1f
 mov r0,r5
 bl ME_TrapAvoid
 cmp r0,#0
 pop {r0-r3,r12,lr}
 ldrne pc,=0x022ee2f4
 mov r0,r9
 ldr pc,=0x022ee1dc
1:
 pop {r0-r3,r12,lr}
 mov r0,r9
 ldr pc,=0x022ee1dc

entry ME_BlowAwayHook
 push {r0-r3,r12,lr}
 bl ME_ForcedMoveBlocked
 cmp r0,#0
 pop {r0-r3,r12,lr}
 movne r0,#0
 bxne lr
 push {r3-r11,lr}
 ldr pc,=0x0231fde4
.ltorg

entry ME_WeightMultiplierHook
 push {r1-r4,r12,lr}
 ldr r12,=0x020528fc
 blx r12
 mov r2,r0
 mov r0,r7
 mov r1,r6
 bl ME_WeightForMove
 pop {r1-r4,r12,pc}
.ltorg

entry ME_BoostSpeedMoveHook
 push {r4-r6,lr}
 mov r4,r0
 mov r5,r1
 push {r0-r3}
 mov r0,r2
 bl ME_EnterSpeedMove
 mov r6,r0
 pop {r0-r3}
 mov r0,r4
 mov r1,r5
 bl ME_BoostSpeedMovePrior
 mov r4,r0
 mov r0,r6
 bl ME_LeaveSpeedMove
 mov r0,r4
 pop {r4-r6,pc}
entry ME_BoostSpeedMovePrior
 push {r3,lr}
 ldr pc,=0x0232792c
.ltorg

entry ME_IncreaseMovementHook
 push {r4-r8,lr}
 sub sp,sp,#8
 mov r4,r1
 mov r6,#0
 mov r7,#0
 cmp r4,#0
 beq 1f
 ldr r5,[r4]
 cmp r5,#1
 bne 1f
 ldr r5,[r4,#0xb4]
 cmp r5,#0
 beq 1f
 ldr r6,[r5,#0x114]
 ldrb r7,[r5,#0x118]
1:
 ldr r12,[sp,#32] /* fifth native argument */
 str r12,[sp]
 bl ME_IncreaseMovementPrior
 mov r8,r0
 mov r0,r4
 mov r1,r6
 mov r2,r7
 bl ME_SpeedMoveApplied
 mov r0,r8
 add sp,sp,#8
 pop {r4-r8,pc}
entry ME_IncreaseMovementPrior
 push {r3-r9,lr}
 ldr pc,=0x02314814 /* replay original entry and retain the existing COT jump */
.ltorg

/* Actual target r4 and move r8, after redirection/Stalwart has resolved. */
entry ME_TargetGuardHook
 push {r0-r3,r12,lr}
 mov r0,r9
 mov r1,r4
 mov r2,r8
 bl ME_TargetBlocked
 cmp r0,#0
 pop {r0-r3,r12,lr}
 ldrne pc,=0x02332818
 mov r0,r4
 ldr pc,=0x0232eab0
.ltorg

entry ME_DefenseDropHook
 push {r0-r3,r12,lr}
 bl ME_DefenseDropBlocked
 cmp r0,#0
 pop {r0-r3,r12,lr}
 ldreq pc,=PRIOR_DEFENSE_DROP
 mov r0,#0
 bx lr
.ltorg

entry ME_NoGuardHitHook
 push {r0-r3,r12,lr}
 bl ME_NoGuardHit
 cmp r0,#0
 pop {r0-r3,r12,lr}
 movne r0,#1
 bxne lr
 ldr pc,=PRIOR_HIT_CHECK
.ltorg

entry ME_SpawnTraitReadHook
 push {r1-r3,r12,lr}
 mov r0,r5
 mov r1,#1
 bl ME_ReadAppearanceTrait
 pop {r1-r3,r12,pc}
entry ME_AppearanceTraitReadHook
 push {r1-r3,r12,lr}
 mov r0,r5
 mov r1,#0
 bl ME_ReadAppearanceTrait
 pop {r1-r3,r12,pc}
.ltorg

entry ME_FriskCoefficientHook
 push {r0-r2,lr}
 mov r0,r3
 bl ME_FriskCoefficient
 mov r3,r0
 pop {r0-r2,pc}
.ltorg

entry ME_R7CoefficientHook
 push {r0-r2,lr}
 mov r0,r7
 bl ME_FriskCoefficient
 mov r7,r0
 pop {r0-r2,pc}
.ltorg

entry ME_FriendGuardCoefficientHook
 push {r0-r2,lr}
 mov r0,r7
 bl ME_FriendGuardCoefficient
 mov r7,r0
 pop {r0-r2,pc}
.ltorg

entry ME_FilterMultiplierHook
 push {r0,r1,r3,lr}
 mov r0,r10
 mov r1,r9
 bl ME_FilterMultiplier
 mov r2,r0
 pop {r0,r1,r3,pc}
.ltorg

entry ME_GutsRatioHook
 add r4,r4,r4,lsl #1
 lsl r11,r11,#1
 bx lr

/* Skip Thief/Covet's extra damage and secondary-effect chance. Retain its
 * existing fixed-item, bag-space, held-item transfer and bag bookkeeping body. */
entry ME_PickpocketTransfer
 push {r3-r8,lr}
 sub sp,sp,#4
 mov r8,r0
 mov r7,r1
 mov r4,#1
 mov r3,#0
 str r3,[sp]
 ldr pc,=0x0232c354
.ltorg

entry ME_SheerForceObserveHook
 push {r0-r3,r12,lr}
 mov r4,r3
 bl ME_ObserveSecondaryMove
 pop {r0-r3,r12,pc}

/* Keep the conditional flags used by Reckless's following STRNE. */
entry ME_PowerSixFifthsHook
 push {r1-r3,r12,lr}
 mrs r12,cpsr
 push {r12}
 bl ME_FriskCoefficient
 pop {r12}
 msr cpsr_f,r12
 pop {r1-r3,r12,pc}

entry ME_PinchMultiplierHook
 push {r0,r1,r3,lr}
 bl ME_PinchMultiplier
 mov r2,r0
 pop {r0,r1,r3,pc}

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

entry ME_IntimidateAuraHook
 mov r0,r10
 b ME_IntimidateAura
entry ME_AttackDropTraitHook
 push {r3,lr}
 bl ME_AttackDropTrait
 pop {r3,pc}
entry ME_MagnetDefenseHook
 push {r0-r3,r12,lr}
 mov r0,r10
 mov r1,r9
 mov r2,r4
 add r3,sp,#24
 bl ME_MagnetDefenseStage
 mov r4,r0
 pop {r0-r3,r12,lr}
 cmp r4,#0
 bx lr
entry ME_AttackStageHook
 push {r0,r2-r4,r12,lr}
 ldr r2,[sp,#0x5c]
 mov r0,r10
 mov r1,r9
 add r3,sp,#24
 bl ME_AttackCalculationStage
 mov r1,r0
 pop {r0,r2-r4,r12,pc}
entry ME_UnawareHitStagesHook
 push {r0-r3,r12,lr}
 mov r0,r7
 mov r1,r6
 bl ME_UnawareHitStages
 tst r0,#1
 movne r9,#10
 tst r0,#2
 movne r10,#10
 pop {r0-r3,r12,lr}
 cmp r10,#0
 bx lr
entry ME_EndSleepHook
 push {r4-r6,lr}
 sub sp,sp,#8
 mov r4,r1
 ldr r5,[r1,#0xb4]
 ldrb r5,[r5,#0xbd]
 ldr r12,[sp,#24]
 str r12,[sp]
 bl ME_EndSleepPrior
 mov r6,r0
 mov r0,r4
 mov r1,r5
 bl ME_WokeUp
 mov r0,r6
 add sp,sp,#8
 pop {r4-r6,pc}
entry ME_EndSleepPrior
 push {r3-r9,lr}
 ldr pc,=0x02305fe0
entry ME_LiquidOozeHook
 push {r0-r3,r12,lr}
 ldr r12,=0x023b05f0
 blx r12
 str r0,[sp]
 str r1,[sp,#4]
 mov r3,r1
 mov r0,r8
 mov r1,r7
 mov r2,r6
 bl ME_LiquidOozeHit
 pop {r0-r3,r12,pc}
entry ME_SoundMoveIdHook
 push {r4,lr}
 sub sp,sp,#8
 strh r0,[sp,#4]
 mov r0,sp
 ldr r12,=0x02013d5c
 blx r12
 add sp,sp,#8
 pop {r4,pc}
entry ME_HalfMultiplierHook
 push {r0,r1,r3,lr}
 bl ME_HalfMultiplier
 mov r2,r0
 pop {r0,r1,r3,pc}
entry ME_StrongDamageWeatherHook
 push {r1-r3,r12,lr}
 sub sp,sp,#4
 mov r1,r0
 mov r0,r7
 bl ME_StrongDamageWeather
 add sp,sp,#4
 pop {r1-r3,r12,lr}
 cmp r0,#1
 bx lr
entry ME_StrongSunImmuneHook
 mov r0,#1
 strb r0,[r6,#0x10]
 mov r0,#0
 str r0,[r6]
 bx lr
.ltorg

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
