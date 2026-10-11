.open "overlay_0029.bin", ov_29
.org BetterSeedThrownSite
    bl BetterSeed_Thrown
.org BetterSeedFrontSite
    bl BetterSeed_Front
.org BetterSeedExplosionDamageSite
    bl BetterSeed_ExplosionDamage
.close

.open "overlay_0036.bin", ov_36
.org ov_36 + BetterSeedCodeAddress
.area 384

; These callers have already selected/unfrozen the target. Do not damage it
; first: a lethal direct hit would delete the entity needed by TryExplosion.
BetterSeed_Thrown:
    ldr r12, [r1, #0xB4]
    ldrb r12, [r12, #6]
    cmp r12, #0
    beq BetterSeed_PriorThrown
    b BetterSeed_Explode
BetterSeed_Front:
    ldr r12, [r1, #0xB4]
    ldrb r12, [r12, #6]
    cmp r12, #0
    beq BetterSeed_PriorFront
BetterSeed_Explode:
    push {r4, r5, r6, lr}
    sub sp, sp, #16
    mov r4, r0
    mov r5, r1
    ; Copy the center so entity removal during damage cannot move it.
    ldr r6, [r5, #4]
    str r6, [sp, #8]
    mov r6, #SEED_EXPLOSION
    str r6, [sp]
    ldr r6, =597 ; DAMAGE_SOURCE_BLAST_SEED (not self-explosion)
    str r6, [sp, #4]
    add r2, sp, #8
    mov r3, #2
    bl TryExplosion
    mov r0, #1
    add sp, sp, #16
    pop {r4, r5, r6, pc}

; Native explosion processing still performs immunity checks and enumerates
; affected tiles. Only our marked damage calls switch away from HP/fixed damage.
BetterSeed_ExplosionDamage:
    ldr r12, [sp, #4]
    cmp r12, #SEED_EXPLOSION
    bne BetterSeed_PriorExplosionDamage
    push {r4, r5, r6, lr}
    sub sp, sp, #16
    mov r4, r0
    mov r5, r1
    add r0, sp, #8
    ldr r1, =0x195 ; regular projectile move, same as damage_formula's seed
    bl InitMove
    mov r0, #0x100
    str r0, [sp]
    mov r0, #87 ; Blast Seed item ID
    str r0, [sp, #4]
    mov r0, r4
    mov r1, r5
    add r2, sp, #8
    mov r3, #100
    bl DealDamageProjectile
    add sp, sp, #16
    pop {r4, r5, r6, pc}
.pool
.endarea
.close
