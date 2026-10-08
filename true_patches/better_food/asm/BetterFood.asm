; After a dungeon item effect, food and gummis also restore PP_RESTORE PP
; on every move of the Pokemon that ate the item (the defender).

.open "overlay_0029.bin", ov_29

.org ApplyItemEffectSite
	b BetterFood_OnApply

.close

.open "overlay_0036.bin", ov_36

.org ov_36 + BetterFoodCodeAddress

; Incoming: r0-r2 unused here, r3 = attacker, [sp] = defender, [sp,#4] = item.
BetterFood_OnApply:
	push {r0, r1, r2, r3, r4, r5, r6, lr}
	ldr r5, [sp, #0x20]
	ldr r6, [sp, #0x24]
	ldmia sp, {r0, r1, r2, r3}
	push {r5, r6}
	bl BetterFood_Resume
	add sp, sp, #8
	mov r0, r5
	mov r1, r6
	bl BetterFood_TryRestore
	pop {r0, r1, r2, r3, r4, r5, r6, pc}

BetterFood_Resume:
	push {r3, r4, r5, r6, r7, r8, r9, r10, lr}
	b ApplyItemEffectBody

; r0 = defender, r1 = item. Skip if the item is missing/sticky or the eater is muzzled.
BetterFood_TryRestore:
	push {r4, r5, r6, lr}
	mov r4, r0
	mov r5, r1
	cmp r5, #0
	beq BetterFood_Skip
	ldrb r0, [r5]
	tst r0, #ITEM_EXISTS
	beq BetterFood_Skip
	tst r0, #ITEM_STICKY
	bne BetterFood_Skip
	ldrh r0, [r5, #ITEM_ID_OFF]
	bl GetItemCategoryVeneer
	cmp r0, #CATEGORY_FOOD_GUMMIES
	bne BetterFood_Skip
	mov r0, r4
	bl EntityIsValid
	cmp r0, #0
	beq BetterFood_Skip
	ldr r0, [r4]
	cmp r0, #ENTITY_MONSTER
	bne BetterFood_Skip
	ldr r6, [r4, #MONSTER_INFO_OFF]
	cmp r6, #0
	beq BetterFood_Skip
	ldrb r0, [r6, #MUZZLED_OFF]
	cmp r0, #1
	beq BetterFood_Skip
	mov r0, r4
	mov r1, r4
	mov r2, #PP_RESTORE
	mov r3, #1
	bl RestoreAllMovePP
BetterFood_Skip:
	pop {r4, r5, r6, pc}

	.pool

.close
