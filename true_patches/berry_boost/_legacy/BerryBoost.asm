; Dedicated item effect helpers in overlay 29, same style as ApplyViolentSeedEffect.
.nds
.arm

.include "common/offsetsUS.asm"
.include "lib/dunlib_us.asm"

.definelabel EndBurnClassStatus, 0x023061A8
.definelabel TryInflictFocusEnergyStatus, 0x02315D84

.open "overlay_0029.bin", ov_29

.org BerryBoostCodeAddress

; r0: user, r1: target
ApplyCheriBerryBoost:
	push {r4, r5, r6, lr}
	mov r5, r1
	mov r6, r0
	mov r0, r6
	mov r1, r5
	mov r2, #1
	mov r3, #2
	bl AttackStatUp
	ldr r2, [r5, #0xB4]
	ldrb r2, [r2, #0xBF]
	cmp r2, #4
	bne ApplyCheriBerryBoost_Done
	mov r0, r6
	mov r1, r5
	bl EndBurnClassStatus
ApplyCheriBerryBoost_Done:
	pop {r4, r5, r6, pc}

ApplyPechaBerryBoost:
	push {r4, r5, r6, lr}
	mov r5, r1
	mov r6, r0
	mov r0, r6
	mov r1, r5
	mov r2, #0
	mov r3, #2
	bl DefenseStatUp
	mov r0, r6
	mov r1, r5
	mov r2, #1
	mov r3, #2
	bl DefenseStatUp
	ldr r2, [r5, #0xB4]
	ldrb r2, [r2, #0xBF]
	add r2, r2, #0xFE
	and r2, r2, #0xFF
	cmp r2, #1
	bhi ApplyPechaBerryBoost_Done
	mov r0, r6
	mov r1, r5
	bl EndBurnClassStatus
ApplyPechaBerryBoost_Done:
	pop {r4, r5, r6, pc}

ApplyRawstBerryBoost:
	push {r4, r5, r6, lr}
	mov r5, r1
	mov r6, r0
	mov r0, r6
	mov r1, r5
	mov r2, #0
	mov r3, #2
	bl AttackStatUp
	ldr r2, [r5, #0xB4]
	ldrb r2, [r2, #0xBF]
	cmp r2, #1
	bne ApplyRawstBerryBoost_Done
	mov r0, r6
	mov r1, r5
	bl EndBurnClassStatus
ApplyRawstBerryBoost_Done:
	pop {r4, r5, r6, pc}

ApplyChestoBerryBoost:
	push {r4, r5, r6, lr}
	mov r5, r1
	mov r4, r0
	mov r6, r5
	mov r0, r4
	mov r1, r5
	mov r2, #1
	bl FocusStatUp
	mov r6, r5
	mov r0, r4
	mov r1, r5
	mov r2, #1
	bl FocusStatUp
	mov r0, r4
	mov r1, r5
	bl Sleepless
	pop {r4, r5, r6, pc}

ApplyAspearBerryBoost:
	push {r4, r5, r6, lr}
	mov r5, r1
	mov r4, r0
	mov r6, r5
	mov r0, r4
	mov r1, r5
	mov r2, #0
	bl FocusStatUp
	mov r6, r5
	mov r0, r4
	mov r1, r5
	mov r2, #0
	bl FocusStatUp
	mov r0, r4
	mov r1, r5
	bl TryInflictFocusEnergyStatus
	ldr r2, [r5, #0xB4]
	ldrb r2, [r2, #0xBF]
	cmp r2, #5
	bne ApplyAspearBerryBoost_Done
	mov r0, r4
	mov r1, r5
	bl EndBurnClassStatus
ApplyAspearBerryBoost_Done:
	pop {r4, r5, r6, pc}

.close
