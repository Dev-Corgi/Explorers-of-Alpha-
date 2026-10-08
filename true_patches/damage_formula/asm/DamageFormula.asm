; Main-series style base damage inside CalcDamage + Blast Seed power path.
; Damage base = ((2*L/5 + 2) * P * A / D) / 50 + 2
; Then vanilla continues: Type × STAB × Crit × Random (±12.5%).
; Non-team attackers: ×64/85 (EnemyPenalty).

.open "overlay_0029.bin", ov_29

.org CalcDamageBaseFormula
	b DamageFormula_MainSeriesBase

.org BlastSeedFixedCallThrown
	bl DamageFormula_BlastSeedByPower

.org BlastSeedFixedCallFront
	bl DamageFormula_BlastSeedByPower

; Normal critical hits and Sunny-Fire / Rain-Water: 1.25 -> 1.5.
.org DamageMultiplier1_5Lower
	.word 0x18000

.close

.open "overlay_0036.bin", ov_36

.org ov_36 + DamageFormulaCodeAddress

; Replace CalcDamageFixedNoCategory calls from ApplyBlastSeedEffect.
; r0=attacker r1=defender (r2 old fixed damage ignored)
; Uses projectile move 0x195 + power 80 → DealDamageProjectile.
.align 4
DamageFormula_BlastSeedByPower:
	push {r4-r7, lr}
	sub sp, #0x20
	mov r4, r0
	mov r5, r1
	add r0, sp, #8
	ldr r1, =0x195
	bl InitMove
	mov r0, #0x100
	str r0, [sp]
	mov r0, #87
	str r0, [sp, #4]
	mov r0, r4
	mov r1, r5
	add r2, sp, #8
	mov r3, #80
	bl DealDamageProjectile
	add sp, #0x20
	pop {r4-r7, pc}

.pool

; Live CalcDamage frame (sp unchanged until we push):
;   [sp,#0x90]=A  [sp,#0x94]=D  [sp,#0x10]=P  r6=attacker monster (level @+0xA)
.align 4
DamageFormula_MainSeriesBase:
	push {r4, r5, r7, lr}
	ldr r4, [sp, #0xA0]          ; A  (0x90 + 0x10)
	ldr r5, [sp, #0xA4]          ; D
	ldr r7, [sp, #0x20]          ; P  (0x10 + 0x10)
	ldrb r0, [r6, #0xA]          ; L
	cmp r5, #1
	movlt r5, #1                 ; avoid /0

	; r0 = 2*L/5 + 2
	lsl r0, r0, #1
	mov r1, #5
	bl SoftDiv
	add r0, r0, #2

	; r0 = (2*L/5+2) * P * A
	mul r0, r7, r0
	mul r0, r4, r0

	; / D / 50 + 2
	mov r1, r5
	bl SoftDiv
	mov r1, #50
	bl SoftDiv
	add r4, r0, #2               ; base in r4

	; EnemyPenalty: non-team member → ×64/85
	bl SomeDungeonFlagCheck
	cmp r0, #0
	bne DamageFormula_StoreBase
	ldrb r0, [r6, #6]
	cmp r0, #0
	beq DamageFormula_StoreBase
	mov r0, #64
	mul r0, r4, r0
	mov r1, #85
	bl SoftDiv
	mov r4, r0

DamageFormula_StoreBase:
	; Fx64 at [sp,#0xB0] of CalcDamage frame (= +0xC0 while we still have push)
	add r0, sp, #0xC0
	mov r1, r4
	bl IntToFx64
	pop {r4, r5, r7, lr}
	b CalcDamageAfterBaseFormula

.pool
.close
