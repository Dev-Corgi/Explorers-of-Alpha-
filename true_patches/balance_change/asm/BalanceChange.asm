; Fixed-room boss movesets that the level-up learnset can't produce.
; Outlaw level is party max + 10 (cap 100). Outlaw max HP is 2 * CalcStat.
; Difficulty rebalance: enemy fx mults, LS, spawn/trap/EXP/move-scale tweaks.

.open "arm9.bin", arm9

.org GetOutlawLevelSite
	b BalanceChange_OutlawLevel

.org GetOutlawLeaderLevelSite
	b BalanceChange_OutlawLevel

.org GetOutlawMinionLevelSite
	b BalanceChange_OutlawLevel

.close

.open "overlay_0029.bin", ov_29

.org GetMonsterMovesEntrySite
	b BalanceChange_GetMonsterMoves

.org OutlawSpawnLevelSite
	bl BalanceChange_StoreOutlawLevel

.org OutlawHpSite
	bl BalanceChange_OutlawHp

.close

.open "overlay_0036.bin", ov_36

; ---- in-place difficulty rebalance (Alpha ov36) ----

; Difficult +0x1A..+0x1D ×7/8: remove
.org 0x023AC54C
	b 0x023AC60C

; Spawn density: Hardcore uses Expert block
.org 0x023AA26C
	b 0x023AA254

; Extra spawn roll: Hardcore 50% -> Expert 25%
.org 0x023AC494
	moveq r2, #0x19

; Traps / periodic: Hardcore period same as Expert (12)
.org 0x023AC950
	cmp r0, #4
	moveq r1, #0xC

; Floor event divisor: always 10
.org 0x023AA814
	mov r4, #0xA
	mov r4, #0xA

; Forced move scaling (ginseng 99): never
.org 0x023AA020
	b 0x023AA064

; EXP Expert+ halves: skip (Vanilla rules)
.org 0x023B5F14
	pop {r0, r1, r2, r3}
	b 0x02311120

; Hardcore belly/cost half: check unused flag instead of Hardcore (59)
.org 0x023D4408
	mov r2, #0

; IsLevelResetDungeon Hardcore early-out: check unused flag
.org 0x023D8114
	mov r2, #0

; Empty move-slot ÷4: nop the lsr
.org 0x023AF7D4
	nop

; Hooks into cave
.org DiffRebalance_ApplyEnemyMultsSite
	b DiffRebalance_ApplyEnemyMults

.org DiffRebalance_A5MultSite
	b DiffRebalance_A5Mult

.org DiffRebalance_VanillaLSSite
	b DiffRebalance_VanillaLS

.org DiffRebalance_EHLSStoreSite
	b DiffRebalance_EHLSStore

.org ov_36 + BalanceChangeCodeAddress

; r0 = [output] 4 move IDs, r1 = monster ID, r2 = level. Same contract as GetMonsterMoves.
BalanceChange_GetMonsterMoves:
	push {r4, r5}
	ldr r12, =DungeonPtr
	ldr r12, [r12]
	cmp r12, #0
	beq BalanceChange_Stock
	add r12, r12, #FIXED_ROOM_ID_HI
	ldrb r12, [r12, #FIXED_ROOM_ID_LO]
	mov r3, r1
	cmp r3, #GENDER_ID_OFFSET
	subge r3, r3, #GENDER_ID_OFFSET
	ldr r4, =BalanceChange_BossMoves
BalanceChange_Next:
	ldrh r5, [r4]
	cmp r5, #0
	beq BalanceChange_Stock
	cmp r5, r3
	ldreqb r5, [r4, #2]
	cmpeq r5, r12
	addne r4, r4, #BOSS_ENTRY_SIZE
	bne BalanceChange_Next
	add r4, r4, #4
	mov r3, #0
BalanceChange_Copy:
	ldrh r5, [r4, r3]
	strh r5, [r0, r3]
	add r3, r3, #2
	cmp r3, #8
	blt BalanceChange_Copy
	pop {r4, r5}
	bx lr
BalanceChange_Stock:
	pop {r4, r5}
	push {r3, r4, r5, r6, r7, r8, r9, r10, lr}
	b GetMonsterMovesEntrySite + 4
	.pool

.include "generated/boss_moves.asm"

; r0 = min(highest active-party level + 10, 100). Guests are skipped.
; Slots 0-3. Level is the byte at team member +2. Empty party yields 10.
BalanceChange_OutlawLevel:
	push {r4, r5, r6, lr}
	mov r4, #0
	mov r5, #0
BalanceChange_OutlawLevelNext:
	mov r0, r4
	bl GetActiveTeamMember
	cmp r0, #0
	beq BalanceChange_OutlawLevelSlot
	ldrb r1, [r0]
	tst r1, #1
	beq BalanceChange_OutlawLevelSlot
	mov r6, r0
	ldrsh r0, [r6, #8]
	bl IsGuestTeamMember
	cmp r0, #0
	bne BalanceChange_OutlawLevelSlot
	ldrb r0, [r6, #2]
	cmp r0, r5
	movgt r5, r0
BalanceChange_OutlawLevelSlot:
	add r4, r4, #1
	cmp r4, #4
	blt BalanceChange_OutlawLevelNext
	add r0, r5, #10
	cmp r0, #100
	movgt r0, #100
	pop {r4, r5, r6, pc}

; r4 = outlaw spawn struct. Preserves r0 (the caller stores it at +6/+7).
BalanceChange_StoreOutlawLevel:
	push {r0, r1, r2, r3, r5, lr}
	bl BalanceChange_OutlawLevel
	strh r0, [r4, #4]
	pop {r0, r1, r2, r3, r5, lr}
	bx lr

; r5 = monster, r7 = spawn struct. Behavior 1-5 is the outlaw, its hidden and
; fleeing forms, the monster-house leader, and minions. Max HP is
; 2 * CalcStat(species, level, HP, V=0). If base_stats_speed is absent,
; double whatever is already at +0x12. Cap 32767. Caller writes current HP
; from r2.
BalanceChange_OutlawHp:
	ldrb r0, [r7, #2]
	cmp r0, #1
	blt BalanceChange_OutlawHpLoad
	cmp r0, #5
	bgt BalanceChange_OutlawHpLoad
	push {r1, r3, r4, lr}
	ldr r0, =BaseStats_CalcStat
	cmp r0, #0
	beq BalanceChange_OutlawHpDouble
	ldrsh r0, [r5, #2]
	ldrb r1, [r5, #0xa]
	mov r2, #0
	mov r3, #0
	bl BaseStats_CalcStat
	b BalanceChange_OutlawHpTwice
BalanceChange_OutlawHpDouble:
	ldrsh r0, [r5, #0x12]
BalanceChange_OutlawHpTwice:
	lsl r0, r0, #1
	ldr r1, =32767
	cmp r0, r1
	movgt r0, r1
	strh r0, [r5, #0x12]
	pop {r1, r3, r4, lr}
BalanceChange_OutlawHpLoad:
	ldrsh r2, [r5, #0x12]
	bx lr
	.pool

; ============================================================
; Difficulty rebalance cave helpers
; fx base 256 = 1.0x; Vanilla 0.8x (0xCD), D/E 1.0x, Hardcore 1.2x (0x133)
; ============================================================

; Out: r0 = fx multiplier for current difficulty.
DiffRebalance_EnemyFx:
	push {r1, lr}
	bl GetDifficulty
	mov r1, #0x100
	cmp r0, #1
	moveq r1, #0xCD
	cmp r0, #4
	ldreq r1, =0x133
	mov r0, r1
	pop {r1, pc}
	.pool

; r7 = monster*. Write Atk/SpA/Def/SpD fx from difficulty.
DiffRebalance_WriteFxR7:
	push {r0, r1, lr}
	bl DiffRebalance_EnemyFx
	str r0, [r7, #0x34]
	str r0, [r7, #0x38]
	str r0, [r7, #0x3C]
	str r0, [r7, #0x40]
	pop {r0, r1, pc}

; Replace Vanilla team 1.15x wipe: apply enemy fx to slots 4..0x13.
; r8 = dungeon** (caller context). Continues at DiffRebalance_ApplyEnemyMultsCont.
DiffRebalance_ApplyEnemyMults:
	push {r0, r1, r2, r3, r4, r5, r6, r7, lr}
	bl DiffRebalance_EnemyFx
	mov r4, r0
	mov r5, #4
DiffRebalance_EnemyLoop:
	ldr r0, [r8]
	add r0, r0, r5, lsl #2
	add r0, r0, #0x12000
	ldr r6, [r0, #0xB28]
	mov r0, r6
	bl EntityIsValid
	cmp r0, #1
	bne DiffRebalance_EnemyNext
	ldr r7, [r6, #0xB4]
	cmp r7, #0
	beq DiffRebalance_EnemyNext
	str r4, [r7, #0x34]
	str r4, [r7, #0x38]
	str r4, [r7, #0x3C]
	str r4, [r7, #0x40]
DiffRebalance_EnemyNext:
	add r5, r5, #1
	cmp r5, #0x14
	blt DiffRebalance_EnemyLoop
	pop {r0, r1, r2, r3, r4, r5, r6, r7, lr}
	b DiffRebalance_ApplyEnemyMultsCont

; Dungeon 0xA5 Expert+ mult immediates -> shared writer; then F9/accuracy path.
; Arrives after cmp#3 / ldm already restored r0; r7 = monster*.
DiffRebalance_A5Mult:
	push {r0, r1, lr}
	bl DiffRebalance_WriteFxR7
	pop {r0, r1, lr}
	b DiffRebalance_A5MultCont

; Vanilla LS: if LS on, cap spawn byte to party-max encoding (r7); no 0.8x.
; r4 = spawn level byte, r5 = dest, r7 = party_max*2.
DiffRebalance_VanillaLS:
	push {r0, r1, r2, lr}
	mov r0, #0
	mov r1, #0x4E
	mov r2, #0x37
	bl 0x0204B678
	cmp r0, #1
	bne DiffRebalance_VanillaLSDone
	cmp r4, r7
	movgt r4, r7
	strb r4, [r5]
DiffRebalance_VanillaLSDone:
	pop {r0, r1, r2, lr}
	b DiffRebalance_LSLoopCont

; Expert: max(spawn, party). Hardcore: always party max (same as Difficult).
; Special-dungeon 0xC8 path already handled before this site.
DiffRebalance_EHLSStore:
	push {r0, r1, lr}
	bl GetDifficulty
	cmp r0, #4
	beq DiffRebalance_HardcoreLSSet
	cmp r4, r7
	strltb r7, [r5]
	b DiffRebalance_EHLSDone
DiffRebalance_HardcoreLSSet:
	strb r7, [r5]
DiffRebalance_EHLSDone:
	pop {r0, r1, lr}
	b DiffRebalance_LSLoopCont

.close
