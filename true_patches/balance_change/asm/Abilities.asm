; Official names, workbook E-column effects. Ability IDs remain stable.
.open "overlay_0029.bin", ov_29
.org BalanceAbilitySpeedSite
    b BalanceAbility_Speed
.org BalanceAbilityStabQuerySite
    bl BalanceAbility_StabQuery
.org BalanceAbilityStabFactorSite
    b BalanceAbility_StabFactor
.org BalanceAbilityDamageSite
    b BalanceAbility_Damage
.org BalanceAbilityMoveSite
    b BalanceAbility_Move
.org BalanceAbilityActionSite
    b BalanceAbility_ActionScope
.org BalanceAbilityFaintSite
    b BalanceAbility_Faint
.close

.open "overlay_0036.bin", ov_36
; Disable Adaptate's old Normal-to-secondary-type conversion.
.org BalanceAbilityOldAdaptateSite
    b 0x023D4C5C
.org BalanceAbilityOldAdaptateTypeSite
    b 0x023DAE3C
.org BalanceAbilityOldAdaptatePowerSite
    b 0x023D94BC
; Disable Sky Pact's Flying-move repeat attack check, retaining Skill Link.
.org BalanceAbilityOldSkySite
    b 0x023AF148
; Disable Sound Waves' old x1.5 move-power boost. Damage scaling is below.
.org BalanceAbilityOldSoundSite
    b 0x023AF9E8
.close

; Continue the dynamically allocated balance_change cave.
.open "overlay_0036.bin", ov_36
.org BalanceChange_AbilitiesStart

BalanceAbility_Speed:
    push {r0-r3, lr}
    mov r0, r8
    mov r1, #142
    bl BalanceAbilityIsActive
    cmp r0, #0
    beq BalanceAbility_SpeedDone
    mov r0, r8
    bl BalanceAbility_FullHp
    cmp r0, #0
    addne r4, r4, #2
BalanceAbility_SpeedDone:
    pop {r0-r3, lr}
    cmp r4, #0
    b BalanceAbilitySpeedSite + 4

; r0 entity, returns boolean. Include the new Adaptability ID 24 and ID 99.
BalanceAbility_StabQuery:
    push {r4, lr}
    mov r4, r0
    mov r1, #99
    bl BalanceAbilityIsActive
    cmp r0, #0
    bne BalanceAbility_StabQueryDone
    mov r0, r4
    mov r1, #24
    bl BalanceAbilityIsActive
BalanceAbility_StabQueryDone:
    pop {r4, pc}

BalanceAbility_StabFactor:
    ldr r2, =BalanceAbility_Stab17
    b BalanceAbilityStabFactorSite + 4

; r0 entity, checks the complete maximum HP including its boost, capped at int16.
BalanceAbility_FullHp:
    ldr r2, [r0, #0xB4]
    ldrsh r0, [r2, #0x10]
    ldrsh r1, [r2, #0x12]
    ldrsh r2, [r2, #0x16]
    add r1, r1, r2
    ldr r2, =32767
    cmp r1, r2
    movgt r1, r2
    cmp r0, r1
    moveq r0, #1
    movne r0, #0
    bx lr
.pool

; Final calculated damage: r8 result, r10 attacker, r9 defender.
; Original CalcDamage frame keeps the move ID at sp+0xF4.
BalanceAbility_Damage:
    push {r0-r7, lr}
    ldr r7, [r8]
    cmp r7, #0
    ble BalanceAbility_DamageDone
    ldr r4, [sp, #0x118]
    mov r0, r4
    bl BalanceMoveIsSound
    cmp r0, #0
    beq BalanceAbility_DamageAura
    mov r0, r10
    mov r1, #148
    bl BalanceAbilityIsActive
    cmp r0, #0
    beq BalanceAbility_DamageSoundDefense
    ldr r0, [r8]
    mov r1, #6
    mul r0, r1, r0
    mov r1, #5
    bl BalanceSignedDivide
    str r0, [r8]
BalanceAbility_DamageSoundDefense:
    mov r0, r9
    mov r1, #148
    bl BalanceAbilityIsActive
    cmp r0, #0
    beq BalanceAbility_DamageAura
    ldr r0, [r8]
    mov r1, #4
    mul r0, r1, r0
    mov r1, #5
    bl BalanceSignedDivide
    str r0, [r8]
BalanceAbility_DamageAura:
    ldr r0, [sp, #0x30] ; calculated attack type (original sp+0xC)
    cmp r0, #16
    moveq r5, #177
    beq BalanceAbility_DamageAuraScan
    cmp r0, #18
    bne BalanceAbility_DamageDone
    mov r5, #176
BalanceAbility_DamageAuraScan:
    ldrb r6, [r10, #0x25]
    cmp r6, #0xFF
    beq BalanceAbility_DamageDone
    mov r0, r10
    mov r1, r5
    bl BalanceAbility_RoomHas
    cmp r0, #0
    beq BalanceAbility_DamageDone
    mov r0, r10
    mov r1, #178
    bl BalanceAbility_RoomHas
    cmp r0, #0
    beq BalanceAbility_DamageDone
    ldr r0, [r8]
    mov r1, #4
    mul r0, r1, r0
    mov r1, #5
    bl BalanceSignedDivide
    str r0, [r8]
BalanceAbility_DamageDone:
    ; Positive damage remains at least 1; immunities remain zero.
    ldr r0, [r8]
    cmp r7, #0
    ble BalanceAbility_DamageRestore
    cmp r0, #1
    movlt r0, #1
    strlt r0, [r8]
BalanceAbility_DamageRestore:
    pop {r0-r7, lr}
    str r1, [r8, #4]
    b BalanceAbilityDamageSite + 4
.pool

; r0 reference entity, r1 ability. Any living, unsuppressed holder in its room.
BalanceAbility_RoomHas:
    push {r4-r8, lr}
    mov r5, r1
    ldrb r6, [r0, #0x25]
    mov r7, #0
    ldr r4, =DungeonPtr
    ldr r4, [r4]
    ldr r0, =0x12B78
    add r4, r4, r0
BalanceAbility_RoomLoop:
    ldr r8, [r4, r7, lsl #2]
    mov r0, r8
    bl BalanceIsMonster
    cmp r0, #0
    beq BalanceAbility_RoomNext
    ldr r0, [r8, #0xB4]
    ldrsh r0, [r0, #0x10]
    cmp r0, #0
    ble BalanceAbility_RoomNext
    ldrb r0, [r8, #0x25]
    cmp r0, r6
    bne BalanceAbility_RoomNext
    mov r0, r8
    mov r1, r5
    bl BalanceAbilityIsActive
    cmp r0, #0
    movne r0, #1
    popne {r4-r8, pc}
BalanceAbility_RoomNext:
    add r7, r7, #1
    cmp r7, #20
    blt BalanceAbility_RoomLoop
    mov r0, #0
    pop {r4-r8, pc}
.pool

; Scope Grim Neigh to one ExecuteMoveEffect action, including all its targets.
; Save/restore the outer action's context for nested move effects.
BalanceAbility_Move:
    push {r4-r8, lr}
    sub sp, sp, #8
    ldr r4, =BalanceAbility_Action
    ldr r5, [r4]
    ldr r6, [r4, #4]
    ldr r7, [r4, #8]
    ldr r8, [r4, #12]
    str r1, [r4]
    push {r0-r3}
    ldrh r3, [r2, #4]
    str r3, [r4, #12]
    mov r3, #0
    str r3, [r4, #4]
    str r3, [r4, #8]
    ldrh r0, [r2, #4]
    bl BalanceMoveGetCategory
    cmp r0, #2
    movne r0, #1
    moveq r0, #0
    str r0, [r4, #8]
    pop {r0-r3}
    ldr r12, [sp, #32]
    str r12, [sp] ; preserve ExecuteMoveEffect's fifth argument
    bl BalanceAbility_MoveInvoke
    str r5, [r4]
    str r6, [r4, #4]
    str r7, [r4, #8]
    str r8, [r4, #12]
    add sp, sp, #8
    pop {r4-r8, pc}
BalanceAbility_MoveInvoke:
    push {r3-r11, lr}
    b BalanceAbilityMoveSite + 4
.pool

; HandleFaint body, after the earlier Z-gauge entry hook saved the prologue.
BalanceAbility_Faint:
    push {r0-r7, lr}
    mov r4, r0
    mov r5, r2
    cmp r4, r5
    beq BalanceAbility_FaintDone
    ldr r6, =BalanceAbility_Action
    ldr r0, [r6]
    cmp r0, r5
    bne BalanceAbility_FaintDone
    ldr r0, [r6, #4]
    cmp r0, #0
    bne BalanceAbility_FaintDone
    ldr r0, [r6, #8]
    cmp r0, #0
    beq BalanceAbility_FaintDone
    ldr r0, =BalanceAbility_Scope
    ldr r1, [r0]
    cmp r1, r5
    bne BalanceAbility_FaintSource
    ldr r1, [r0, #4]
    cmp r1, #0
    bne BalanceAbility_FaintDone
BalanceAbility_FaintSource:
    ; Only a move damage source matching the executing move is eligible.
    ldr r0, [r6, #12]
    ldr r1, [sp, #4]
    cmp r1, r0
    bne BalanceAbility_FaintDone
    mov r0, r5
    bl BalanceIsMonster
    cmp r0, #0
    beq BalanceAbility_FaintDone
    ldr r0, [r4, #0xB4]
    ldrb r1, [r0, #6]
    ldrb r2, [r0, #8]
    eor r1, r1, r2
    ldr r0, [r5, #0xB4]
    ldrb r2, [r0, #6]
    ldrb r3, [r0, #8]
    eor r2, r2, r3
    cmp r1, r2
    beq BalanceAbility_FaintDone
    mov r0, r5
    mov r1, #171
    bl BalanceAbilityIsActive
    cmp r0, #0
    beq BalanceAbility_FaintDone
    mov r0, #1
    str r0, [r6, #4]
    ldr r1, =BalanceAbility_Scope
    ldr r2, [r1]
    cmp r2, r5
    streq r0, [r1, #4]
    mov r0, r5
    mov r1, r5
    mov r2, #1
    mov r3, #1
    bl BalanceBoostOffensiveStat
BalanceAbility_FaintDone:
    pop {r0-r7, lr}
    sub sp, sp, #0xBC
    b BalanceAbilityFaintSite + 4
.pool

; One UseMove action can call ExecuteMoveEffect repeatedly (multi-hit/linked moves).
; Keep the once-per-action bit across those calls and isolate nested users.
BalanceAbility_ActionScope:
    push {r4-r6, lr}
    sub sp, sp, #8
    ldr r4, =BalanceAbility_Scope
    ldr r5, [r4]
    ldr r6, [r4, #4]
    str r0, [r4]
    mov r12, #0
    str r12, [r4, #4]
    ldr r12, [sp, #24]
    str r12, [sp]
    bl BalanceAbility_ActionInvoke
    str r5, [r4]
    str r6, [r4, #4]
    add sp, sp, #8
    pop {r4-r6, pc}
BalanceAbility_ActionInvoke:
    push {r4-r11, lr}
    b BalanceAbilityActionSite + 4
.pool

.align 4
BalanceAbility_Stab17:
    ; Native fx64_16 stores upper32 first, lower32 second (16 fractional bits).
    .word 0, 0x0001B333
BalanceAbility_Action:
    .word 0, 0, 0, 0
BalanceAbility_Scope:
    .word 0, 0
.close
