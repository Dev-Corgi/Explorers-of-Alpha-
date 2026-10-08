; Pattern B — item_cd stubs call these helpers in the ov29 cave (stat + status cure).
.nds
.arm

.include "common/offsetsUS.asm"
.include "lib/dunlib_us.asm"

.open "overlay_0036.bin", ov_36

.org BerryBoostCodeAddress

ApplyCheriBoostEffect:
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
	bne ApplyCheriBoostEffect_Done
	mov r0, r6
	mov r1, r5
	bl EndBurnClassStatus
ApplyCheriBoostEffect_Done:
	pop {r4, r5, r6, pc}

ApplyPechaBoostEffect:
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
	bhi ApplyPechaBoostEffect_Done
	mov r0, r6
	mov r1, r5
	bl EndBurnClassStatus
ApplyPechaBoostEffect_Done:
	pop {r4, r5, r6, pc}

ApplyRawstBoostEffect:
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
	bne ApplyRawstBoostEffect_Done
	mov r0, r6
	mov r1, r5
	bl EndBurnClassStatus
ApplyRawstBoostEffect_Done:
	pop {r4, r5, r6, pc}

ApplyChestoBoostEffect:
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

ApplyAspearBoostEffect:
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
	bne ApplyAspearBoostEffect_Done
	mov r0, r4
	mov r1, r5
	bl EndBurnClassStatus
ApplyAspearBoostEffect_Done:
	mov r0, r4
	bl ApplyAspearBellyFill
	pop {r4, r5, r6, pc}

.close
