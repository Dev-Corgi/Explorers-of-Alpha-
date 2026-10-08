; Pattern A — all boosted berries via overlay hooks (Cheri/Pecha/Rawst/Chesto/Aspear).
.nds
.arm

.include "common/offsetsUS.asm"
.include "lib/dunlib_us.asm"

.open "overlay_0029.bin", ov_29

.org ApplyItemEffect_ItemCdLoader
	b ApplyItemEffect_ItemCdHook

.org ApplyCheriBerryEffect
	b ApplyCheriBerryBoost_Patched

.org ApplyPechaBerryEffect
	b ApplyPechaBerryBoost_Patched

.org ApplyRawstBerryEffect
	b ApplyRawstBerryBoost_Patched

.org ApplyChestoBerryEffect
	b ApplyChestoBerryBoost_Patched

.org BerryBoostCodeAddress

; Alpha Aspear (344) bypasses item_cd effect 100 and runs here instead.
; Replaces vanilla @ 0x0231B9A8 (ldrsh r0, [r6, #4]).
ApplyItemEffect_ItemCdHook:
	ldrsh r0, [r6, #4]
	cmp r0, #ASPEAR_ITEM_ID
	bne ApplyItemEffect_ItemCdNormal
	mov r0, r8
	mov r1, r7
	bl ApplyAspearBerryBoost_Patched
	b ItemJumpAddress

ApplyItemEffect_ItemCdNormal:
	push {r5, r6, r7, r8}
	mov r6, r0
	b ApplyItemEffect_ItemCdLoaderBody

ApplyCheriBerryBoost_Patched:
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

ApplyPechaBerryBoost_Patched:
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

ApplyRawstBerryBoost_Patched:
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

ApplyChestoBerryBoost_Patched:
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

ApplyAspearBerryBoost_Patched:
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
	mov r0, r4
	bl ApplyAspearBellyFill
	pop {r4, r5, r6, pc}

.close
