; Ground Poke pickup restores BELLY_RESTORE belly on the Pokemon that picked it up.
; r0 is the money amount. Log flag is 0 and max belly is not raised.

.open "overlay_0029.bin", ov_29

.org LeaderPokePickupSite
	bl BetterPoke_OnLeaderPickup

.org AllyPokePickupSite
	bl BetterPoke_OnAllyPickup

.close

.open "overlay_0036.bin", ov_36

.org ov_36 + BetterPokeCodeAddress

; r4 is the leader entity and is callee-saved.
BetterPoke_OnLeaderPickup:
	push {lr}
	sub sp, sp, #4
	bl AddMoneyCarried
	mov r0, r4
	mov r1, r4
	mov r2, #BELLY_RESTORE
	mov r3, #0
	str r3, [sp]
	bl TryIncreaseBelly
	add sp, sp, #4
	pop {pc}

; r8 is the ally entity. r4 is the item pointer and the caller uses it next.
BetterPoke_OnAllyPickup:
	push {lr}
	sub sp, sp, #4
	bl AddMoneyCarried
	mov r0, r8
	mov r1, r8
	mov r2, #BELLY_RESTORE
	mov r3, #0
	str r3, [sp]
	bl TryIncreaseBelly
	add sp, sp, #4
	pop {pc}

.close
