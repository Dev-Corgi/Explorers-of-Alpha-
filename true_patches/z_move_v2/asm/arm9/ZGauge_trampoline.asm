; Z gauge in WRAM. Cleared when a dungeon-group outing ends (DungeonFree
; + end-reason / last-group-floor filter), including Escape Orb.
.open "arm9.bin", 0x02000000

; Restore vanilla results-window path if a prior build hooked it.
.org GetDungeonResultMsg
	push {r3, r4, r5, r6, lr}

.org GetDungeonResultMsgCallSite
	bl GetDungeonResultMsg

; Clear abandoned trampoline next to AF3D0 descriptor / AF408 BSS.
.org ZMoveArm9GaugeCaveOldAf3e0
.fill 0x30, 0

.org ZMoveArm9GaugeCave
	bx lr

.pool

.close
