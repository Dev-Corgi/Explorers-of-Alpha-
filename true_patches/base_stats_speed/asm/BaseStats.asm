; Phase 0 tables, phase-1 hit rank, phase-2 spawn/level-up, phase-3 combat,
; phase-4 speed on the hit check, phase-5 recompute on evolution,
; phase-6 Strong Enemy keeps table HP (Charmander seats: party-max, boosted rooms +5/HPx2);
; Helping Ally writes CalcStat HP.
; Phase 8: summary Stats tab prints CalcStat and Speed (arm9 copy).
;
; MoveHitCheck reaches BaseStats_HitRank with:
;   r6 = defender entity, r7 = attacker entity
;   r8 = move accuracy after the flat ability/item adjustments
;   r9 = accuracy stage, already clamped to 0..20 (Lens +2 included when that hook ran)
;   r10 = evasion stage, not yet clamped (Bright +2 included when that hook ran)
;   [sp, #8] = roll, 0..99
;   10 is the neutral stage. stage = r9 - r10.
;   rank = stage >= 0 ? (3+stage)/3 : 3/(3-stage)
;   Spe = CalcStat(species, level, 5, doping=0)
;   Accuracy (waza +0x0B) is the move hit value. Miss Accuracy is unused.
;   MoveHitCheck's second pass returns hit. The formula runs once.
;   hit when roll < floor(r8 * rank * (atkSpe/defSpe)^0.25)
;   (atkSpe/defSpe)^0.25 is isqrt(isqrt((atkSpe<<16)/defSpe)) / 16
;
; BaseStats_CalcStat
;   r0 = monster.md index (gender copies allowed)
;   r1 = level
;   r2 = stat (0 HP, 1 Atk, 2 Def, 3 SpA, 4 SpD, 5 Spe)
;   r3 = doping added to the base stat (signed)
;   returns r0 = floor stat, saturated to 0..32767
;
; BaseStats_EvoRate
;   r0 = monster.md index
;   returns r0 = 0 (x1.0), 1 (x1.15), 2 (x1.38)
;
; effective = base + doping
; staged    = floor(effective * rate / 100)
; HP        = floor(staged * 2 * level / 100) + level + 10
; other     = floor(staged * 2 * level / 100) + 5

.open "overlay_0029.bin", ov_29

.org MoveHitCheck
	b BaseStats_HitOnce

.org MoveHitRankSite
	b BaseStats_HitRank

; After Alpha's Strong Enemy / Helping Ally check. Doping is 0 here.
.org SpawnHpResume
	b BaseStats_SpawnHp
.org SpawnAtkResume
	b BaseStats_SpawnAtk
.org SpawnDefResume
	b BaseStats_SpawnDef

; Write CalcStat at the new level. Do not add m_level gains.
.org LevelUpStatApply
	b BaseStats_LevelUp

.org LevelUpSaveOldLevel
	bl BaseStats_SaveOldLevel

.org LevelUpDeltasExp
	b BaseStats_DeltasExp

.org LevelUpDeltasJoy
	b BaseStats_DeltasJoy

.org LevelUpSpeDigit
	bl BaseStats_SetSpeDigit

.org CalcDamageStatLoad
	b BaseStats_CombatAD
.org CalcDamageDownloadLoad
	b BaseStats_Download

; After EvolveMonster writes the new species and calls InitMonster.
.org EvolveAfterInitSite
	b BaseStats_Evolve

; Strong Enemy (6) and Helping Ally (0xA) after SpawnMonster.
.org FixedRoomAfterSpawn
	b BaseStats_FixedApply

.org InitTeamMemberHpCopy
	b BaseStats_InitHp

; HP current/max leftover used 999-1. int16 ceiling is 32767 = 0x8000-1.
.org HpCapImmRevive
	rsb r0, r3, #0x8000
.org HpCapImmFixed
	rsb lr, r6, #0x8000
.org HpCapImmGuest
	rsb r0, r3, #0x8000

.include "generated/hp_caps_ov29.inc"

.close

.open "overlay_0036.bin", ov_36

.org ov_36 + BaseStatsCodeAddress
BaseStats_CalcStat:
	b BaseStats_CalcStatBody
BaseStats_EvoRate:
	b BaseStats_EvoRateBody

BaseStats_CalcStatBody:
	push {r4, r5, r6, r7, lr}
	mov r4, r1
	mov r5, r2
	mov r6, r3
	cmp r5, #6
	bhs BaseStats_CalcZero
	bl BaseStats_Primary
	mov r7, r0
	ldr r1, =BaseStats_Stats
	add r2, r7, r7, lsl #1
	lsl r2, r2, #1
	add r2, r2, r5
	ldrb r0, [r1, r2]
	add r0, r0, r6
	cmp r0, #0
	movlt r0, #0
	ldr r1, =32767
	cmp r0, r1
	movgt r0, r1
	mov r6, r0
	ldr r1, =BaseStats_Rates
	ldrb r1, [r1, r7]
	adr r2, BaseStats_Percent
	ldrb r1, [r2, r1]
	mul r0, r6, r1
	mov r1, #100
	bl SoftDiv
	lsl r1, r0, #1
	mul r0, r1, r4
	mov r1, #100
	bl SoftDiv
	cmp r5, #0
	bne BaseStats_Other
	add r0, r0, r4
	add r0, r0, #10
	b BaseStats_Clamp
BaseStats_Other:
	add r0, r0, #5
BaseStats_Clamp:
	cmp r0, #0
	movlt r0, #0
	ldr r1, =32767
	cmp r0, r1
	movgt r0, r1
	pop {r4, r5, r6, r7, pc}
BaseStats_CalcZero:
	mov r0, #0
	pop {r4, r5, r6, r7, pc}

BaseStats_EvoRateBody:
	push {lr}
	bl BaseStats_Primary
	ldr r1, =BaseStats_Rates
	ldrb r0, [r1, r0]
	pop {pc}

; r0 = monster.md index -> primary index 0..599
BaseStats_Primary:
	ldr r1, =BaseStats_PrimaryCount
	cmp r0, r1
	movhs r0, #0
	ldr r1, =BaseStats_PrimaryTable
	lsl r2, r0, #1
	ldrh r0, [r1, r2]
	ldr r1, =BaseStats_SpeciesCount
	cmp r0, r1
	movhs r0, #0
	bx lr

BaseStats_Percent:
	.byte 100, 115, 138
	.align 4
	.pool

.org ov_36 + BaseStatsCodeAddress + BaseStats_PrimaryOff
BaseStats_PrimaryTable:
	.incbin "generated/primary.bin"

.org ov_36 + BaseStatsCodeAddress + BaseStats_RateOff
BaseStats_Rates:
	.incbin "generated/evo_rate.bin"

.org ov_36 + BaseStatsCodeAddress + BaseStats_StatsOff
BaseStats_Stats:
	.incbin "generated/base_stats.bin"

.org ov_36 + BaseStatsCodeAddress + BaseStats_SentinelOff
	.word 0xB5A7E001

.org ov_36 + BaseStatsCodeAddress + BaseStats_HitOff
; Second MoveHitCheck (Miss Accuracy) returns hit. First call uses Accuracy.
BaseStats_HitOnce:
	cmp r3, #0
	movne r0, #1
	bxne lr
	mov r3, #1
	push {r4, r5, r6, r7, r8, r9, r10, r11, lr}
	b MoveHitCheckBody

; Room at HitOff is tight. The body lives at SpeedOff.
BaseStats_HitRank:
	b BaseStats_HitSpeed

.org ov_36 + BaseStatsCodeAddress + BaseStats_SpawnOff
; Spawn HP is CalcStat with V=0. The four uint8 fields are doping V,
; so wild spawn writes 0 and leaves them for later drink/temp adds.

BaseStats_SpawnHp:
	mov r2, #0
	mov r3, #0
	bl BaseStats_CalcStat
	add sp, #0xc
	pop {r3, r4, r5, r6, r7, r8, pc}

BaseStats_SpawnAtk:
	mov r0, #0
	add sp, #0xc
	pop {r4, r5, r6, r7, r8, r9, pc}

BaseStats_SpawnDef:
	mov r0, #0
	add sp, #0xc
	pop {r4, r5, r6, r7, r8, r9, pc}

; r5 = new level, r7 = monster, fp = species, sl = entity.
; Keep the uint8 V bytes. Recalc HP from team HP V.
BaseStats_LevelUp:
	mov r6, #1
	ldrsh r4, [r7, #0x12]
	mov r0, r7
	bl BaseStats_MonsterHpV
	mov r3, r0
	mov r0, r11
	mov r1, r5
	mov r2, #0
	bl BaseStats_CalcStat
	strh r0, [r7, #0x12]
	sub r0, r0, r4
	ldrsh r1, [r7, #0x10]
	add r0, r1, r0
	cmp r0, #1
	movlt r0, #1
	ldrsh r1, [r7, #0x12]
	ldr r2, =32767
	cmp r1, r2
	movgt r1, r2
	cmp r0, r1
	movgt r0, r1
	strh r0, [r7, #0x10]
	mov r6, #1
	mov r0, r10
	bl LevelUpRefresh
	mov r0, r10
	bl LevelUpIqCheck
	ldr r0, [sp, #4]
	mov r1, r10
	mov r2, r9
	ldr r3, [sp, #8]
	bl LevelUpTryLearn
	b LevelUpAfterStats

	.align 4
	.pool

.org ov_36 + BaseStatsCodeAddress + BaseStats_CombatOff
; r0 = monster, r1 = category 0/1, r2 = 0 offense / 1 defense.
; r3 doping = matching uint8 V + vanilla exclusive cache (+0x224 / +0x226).
BaseStats_FromMonster:
	push {r4, r5, r6, lr}
	mov r4, r0
	mov r5, r2
	mov r6, r1
	add r3, r4, #0x1a
	add r3, r3, r6
	cmp r5, #0
	addne r3, r3, #2
	ldrb r3, [r3]
	add r0, r4, #0x200
	cmp r5, #0
	addeq r0, r0, #0x24
	addne r0, r0, #0x26
	ldrb r0, [r0, r6]
	add r3, r3, r0
	add r2, r6, r6
	cmp r5, #0
	addeq r2, r2, #1
	addne r2, r2, #2
	ldrsh r0, [r4, #2]
	ldrb r1, [r4, #0xa]
	bl BaseStats_CalcStat
	pop {r4, r5, r6, pc}

; CalcDamage A/D. Stages and ability multipliers stay in the vanilla frame.
; Exclusive flats are already in FromMonster r3; resume past 0x0230C2F0.
BaseStats_CombatAD:
	ldr r1, [sp, #0x18]
	mov r0, r6
	mov r2, #0
	bl BaseStats_FromMonster
	strh r0, [r5, #0xc]
	lsl r0, r0, #8
	ldr r1, [sp, #0x44]
	ldr r2, =OffensiveStageTable
	ldr r1, [r2, r1, lsl #2]
	bl Fx32Mul
	ldr r1, [sp, #0x3c]
	bl Fx32Mul
	asr r0, r0, #8
	str r0, [sp, #0x90]
	cmp r4, #0
	movlt r4, #0
	cmp r4, #0x14
	movgt r4, #0x14
	strb r4, [r5, #0xb]
	ldr r1, [sp, #0x18]
	mov r0, r7
	mov r2, #1
	bl BaseStats_FromMonster
	strh r0, [r5, #0xe]
	lsl r0, r0, #8
	ldr r1, =DefensiveStageTable
	ldr r1, [r1, r4, lsl #2]
	bl Fx32Mul
	ldr r1, [sp, #0x38]
	bl Fx32Mul
	asr r0, r0, #8
	str r0, [sp, #0x94]
	b CalcDamageAfterStats

; Download compares defender Def vs SpD. Same formula as combat A/D.
BaseStats_Download:
	push {lr}
	sub sp, #4
	mov r0, r7
	mov r1, #0
	mov r2, #1
	bl BaseStats_FromMonster
	str r0, [sp]
	mov r0, r7
	mov r1, #1
	mov r2, #1
	bl BaseStats_FromMonster
	ldr r1, [sp]
	add sp, #4
	pop {lr}
	b CalcDamageDownloadCmp

	.pool
.if . > ov_36 + BaseStatsCodeAddress + BaseStats_SpeedOff
	.error "Combat A/D block overlaps the hit-speed block"
.endif

.org ov_36 + BaseStatsCodeAddress + BaseStats_SpeedOff
; r6 defender entity, r7 attacker entity, r8 accuracy.
; r4/r5 hold rank num/den. Do not push: [sp,#8] is the 0..99 roll.
BaseStats_HitSpeed:
	cmp r10, #0
	movlt r10, #0
	cmp r10, #0x14
	movgt r10, #0x14
	sub r0, r9, r10
	cmp r0, #0
	blt BaseStats_HitNeg
	add r4, r0, #3
	mov r5, #3
	b BaseStats_HitSpe
BaseStats_HitNeg:
	mov r4, #3
	rsb r5, r0, #3
BaseStats_HitSpe:
	mov r0, r7
	bl BaseStats_EntitySpe
	mov r9, r0
	mov r0, r6
	bl BaseStats_EntitySpe
	cmp r0, #1
	movlt r0, #1
	mov r1, r0
	lsl r0, r9, #16
	bl SoftDiv
	cmp r0, #1
	movlt r0, #1
	bl BaseStats_ISqrt
	bl BaseStats_ISqrt
	mov r1, r0
	mul r0, r8, r4
	mul r2, r0, r1
	mov r0, r2
	lsl r1, r5, #4
	bl SoftDiv
	ldr r1, [sp, #8]
	cmp r1, r0
	movlt r0, #1
	movge r0, #0
	b MoveHitEpilogue

; r0 = dungeon entity. Spe = CalcStat(id, level, 5, Spe V).
BaseStats_EntitySpe:
	push {r4, r5, lr}
	ldr r4, [r0, #0xb4]
	cmp r4, #0
	moveq r0, #5
	beq BaseStats_EntitySpeDone
	mov r0, r4
	bl BaseStats_MonsterSpeV
	mov r5, r0
	ldrsh r0, [r4, #2]
	ldrb r1, [r4, #0xa]
	mov r2, #5
	mov r3, r5
	bl BaseStats_CalcStat
	cmp r0, #1
	movlt r0, #1
BaseStats_EntitySpeDone:
	pop {r4, r5, pc}

; r0 = n. Integer square root, 0..2^32-1.
BaseStats_ISqrt:
	mov r1, r0
	mov r2, #0
	mov r3, #1
	lsl r3, r3, #30
BaseStats_ISqrtAlign:
	cmp r3, r1
	lsrhi r3, r3, #2
	bhi BaseStats_ISqrtAlign
BaseStats_ISqrtLoop:
	cmp r3, #0
	beq BaseStats_ISqrtDone
	add r0, r2, r3
	cmp r1, r0
	blo BaseStats_ISqrtShift
	sub r1, r1, r0
	lsr r2, r2, #1
	add r2, r2, r3
	b BaseStats_ISqrtNext
BaseStats_ISqrtShift:
	lsr r2, r2, #1
BaseStats_ISqrtNext:
	lsr r3, r3, #2
	b BaseStats_ISqrtLoop
BaseStats_ISqrtDone:
	mov r0, r2
	bx lr

	.pool
.if . > ov_36 + BaseStatsCodeAddress + BaseStats_EvoOff
	.error "Hit-speed block overlaps the evolve block"
.endif

.org ov_36 + BaseStatsCodeAddress + BaseStats_EvoOff
; Recalc HP from current V. Do not write the uint8 V bytes.
BaseStats_WriteMonster:
	push {r4, r5, r6, r7, lr}
	mov r7, r0
	ldrsh r4, [r7, #0x12]
	mov r0, r7
	bl BaseStats_MonsterHpV
	mov r3, r0
	ldrsh r0, [r7, #2]
	ldrb r1, [r7, #0xa]
	mov r2, #0
	bl BaseStats_CalcStat
	ldr r1, =32767
	cmp r0, r1
	movgt r0, r1
	strh r0, [r7, #0x12]
	sub r0, r0, r4
	ldrsh r1, [r7, #0x10]
	add r0, r1, r0
	cmp r0, #1
	movlt r0, #1
	ldrsh r1, [r7, #0x12]
	ldr r2, =32767
	cmp r1, r2
	movgt r1, r2
	cmp r0, r1
	movgt r0, r1
	strh r0, [r7, #0x10]
	pop {r4, r5, r6, r7, pc}

; r6 = monster, r7 = entity. Species is already the evolved form.
BaseStats_Evolve:
	mov r0, r6
	bl BaseStats_WriteMonster
	mov r0, r7
	b EvolveAfterInitContinue

	.align 4
	.pool

.org ov_36 + BaseStatsCodeAddress + BaseStats_FixedOff
; r0 = entity from SpawnMonster. r9 = spawn type.
; Types 6 and 0xA still run ApplyFixedRoomStats for flags / exp / IQ.
; Strong Enemy (6) keeps the table HP on +0x12/+0x10, except Charmander
; placeholder seats (stats_entry == 30 and fixed_room_id >= 200): party
; max level, then HP = CalcStat(HP)×1.25; selected rooms use max+5 / HPx2.
; Helping Ally (0xA) rewrites HP
; from CalcStat. Combat A/D still use CalcStat.
BaseStats_FixedApply:
	cmp r9, #6
	cmpne r9, #0xA
	bne FixedRoomAfterSpawnContinue
	push {r0, r4, r5, r6, r7, lr}
	mov r4, r0
	mov r5, r9
	ldr r6, [sp, #0x28]
	mov r1, r6
	ldr r2, [sp, #0x24]
	bl ApplyFixedRoomStats
	; The table's four base stats are not doping. Clear them only here,
	; immediately after initial fixed-room creation; HP/flags/exp/IQ stay.
	ldr r0, [r4, #0xB4]
	cmp r0, #0
	beq BaseStats_FixedDone
	mov r1, #0
	strb r1, [r0, #0x1a]
	strb r1, [r0, #0x1b]
	strb r1, [r0, #0x1c]
	strb r1, [r0, #0x1d]
	cmp r5, #6
	bne BaseStats_FixedHelping
	mov r0, r4
	mov r1, r6
	bl BaseStats_CharmanderSeScale
	b BaseStats_FixedDone
BaseStats_FixedHelping:
	ldr r0, [r4, #0xB4]
	cmp r0, #0
	beq BaseStats_FixedDone
	bl BaseStats_WriteMonster
BaseStats_FixedDone:
	pop {r0, r4, r5, r6, r7, lr}
	b FixedRoomAfterSpawnContinue

; r0 = highest active-party level (slots 0-3). Guests skipped. Empty = 0.
BaseStats_PartyMaxLevel:
	push {r4, r5, r6, lr}
	mov r4, #0
	mov r5, #0
BaseStats_PartyMaxNext:
	mov r0, r4
	bl GetActiveTeamMember
	cmp r0, #0
	beq BaseStats_PartyMaxSlot
	ldrb r1, [r0]
	tst r1, #1
	beq BaseStats_PartyMaxSlot
	mov r6, r0
	ldrsh r0, [r6, #8]
	bl IsGuestTeamMember
	cmp r0, #0
	bne BaseStats_PartyMaxSlot
	ldrb r0, [r6, #2]
	cmp r0, r5
	movgt r5, r0
BaseStats_PartyMaxSlot:
	add r4, r4, #1
	cmp r4, #4
	blt BaseStats_PartyMaxNext
	mov r0, r5
	pop {r4, r5, r6, pc}

; r0 = entity, r1 = stats_entry. Alpha Charmander-seat filter only.
BaseStats_CharmanderSeScale:
	push {r4, r5, r6, r7, lr}
	mov r4, r0
	cmp r1, #0x1E
	bne BaseStats_CharmanderSeDone
	ldr r0, =DungeonPtr
	ldr r0, [r0]
	cmp r0, #0
	beq BaseStats_CharmanderSeDone
	add r0, r0, #FIXED_ROOM_ID_HI
	ldrb r0, [r0, #FIXED_ROOM_ID_LO]
	cmp r0, #0xC8
	blt BaseStats_CharmanderSeDone
	bl BaseStats_CharmanderBoostRoom
	ldr r7, [r4, #0xB4]
	cmp r7, #0
	beq BaseStats_CharmanderSeDone
	bl BaseStats_PartyMaxLevel
	cmp r0, #0
	beq BaseStats_CharmanderSeDone
	cmp r6, #1
	addeq r0, r0, #5
	cmp r0, #100
	movgt r0, #100
	strb r0, [r7, #0xa]
	mov r5, r0
	ldrsh r0, [r7, #2]
	mov r1, r5
	mov r2, #0
	mov r3, #0
	bl BaseStats_CalcStat
	cmp r6, #1
	moveq r0, r0, lsl #1
	addne r0, r0, r0, lsr #2
	ldr r1, =32767
	cmp r0, r1
	movgt r0, r1
	strh r0, [r7, #0x12]
	strh r0, [r7, #0x10]
BaseStats_CharmanderSeDone:
	pop {r4, r5, r6, r7, pc}

	.align 4
	.pool
.if . > ov_36 + BaseStatsCodeAddress + BaseStats_InitOff
	.error "Fixed block overlaps the init block"
.endif

.org ov_36 + BaseStatsCodeAddress + BaseStats_InitOff
; r0 = fixed room. r6 = 1 only for boosted Charmander seats.
; Bits 0,2,6,11,14,15,17,18,19,20,21 represent rooms 200..221.
BaseStats_CharmanderBoostRoom:
	mov r6, #0
	cmp r0, #250
	moveq r6, #1
	bxeq lr
	sub r0, r0, #200
	cmp r0, #21
	bxhi lr
	ldr r6, =0x3EC845
	mov r6, r6, lsr r0
	and r6, r6, #1
	bx lr
	.pool

; r5 = team_member*, r8 = dungeon monster*, r3 = 0.
; Replaces the max-HP copy. The uint8 V copy still runs after this.
; Guests use the same CalcStat(V) path as the hero and partner.
BaseStats_InitHp:
	push {r3, r5, r8, lr}
	ldrb r3, [r5, #0x10]
	ldrsh r0, [r8, #2]
	ldrb r1, [r8, #0xa]
	mov r2, #0
	bl BaseStats_CalcStat
	strh r0, [r8, #0x12]
	ldrsh r1, [r8, #0x10]
	cmp r1, #1
	movlt r1, r0
	cmp r1, r0
	movgt r1, r0
	strh r1, [r8, #0x10]
	pop {r3, r5, r8, lr}
	b InitTeamMemberAfterHp

; r0 = dungeon monster -> r0 = HP V from the active team_member, else 0.
BaseStats_MonsterHpV:
	push {r1, r4, lr}
	mov r4, #0x10
	b BaseStats_MonsterTeamV

; r0 = dungeon monster -> r0 = Spe V (team+0x11), else 0.
BaseStats_MonsterSpeV:
	push {r1, r4, lr}
	mov r4, #0x11
BaseStats_MonsterTeamV:
	ldrsh r1, [r0, #0xc]
	cmp r1, #0
	blt BaseStats_MonsterTeamVZero
	cmp r1, #4
	bge BaseStats_MonsterTeamVZero
	mov r0, r1
	bl GetActiveTeamMember
	cmp r0, #0
	beq BaseStats_MonsterTeamVZero
	ldrb r0, [r0, r4]
	pop {r1, r4, pc}
BaseStats_MonsterTeamVZero:
	mov r0, #0
	pop {r1, r4, pc}

	.pool
.if . > ov_36 + BaseStatsCodeAddress + BaseStats_UiOff
	.error "InitTeamMember block overlaps the summary UI"
.endif

.org ov_36 + BaseStatsCodeAddress + BaseStats_UiOff
; Summary stats page (arm9 0x0205A4B4 case 2) and the two summary fills.
; ov36 stays resident on ground and in dungeons. The arm9 file tail is
; inside the static BSS (0x020B3380-0x022BCA80) and is cleared at boot.
BaseStats_UiStats:
	push {r5, r7, r8, r9, r10, lr}
	add r10, sp, #0x18
	ldrsh r8, [r6]
	ldr r9, [r6, #0x2C]
	; SprintfTagged / DrawWindowText ids are table index + 1.
	; Attack: r3 = V + vanilla exclusive boost (was a post-CalcStat flat).
	mov r0, r8
	mov r1, r9
	mov r2, #1
	ldrb r3, [r6, #0x34]
	ldrb r5, [r6, #0x39]
	add r3, r3, r5
	bl BaseStats_CalcStat
	ldr r2, =0x957
	cmp r5, #0
	addne r2, r2, #1
	mov r1, r2
	mov r2, #0x42
	bl BaseStats_UiDraw
	; Defense
	mov r0, r8
	mov r1, r9
	mov r2, #2
	ldrb r3, [r6, #0x36]
	ldrb r5, [r6, #0x3B]
	add r3, r3, r5
	bl BaseStats_CalcStat
	ldr r2, =0x95B
	cmp r5, #0
	addne r2, r2, #1
	mov r1, r2
	mov r2, #0x42
	bl BaseStats_UiDraw
	; SpA / SpD labels (table 2389).
	mov r0, #0
	ldr r1, =2390
	mov r2, #0x4E
	bl BaseStats_UiDraw
	; Sp. Atk
	mov r0, r8
	mov r1, r9
	mov r2, #3
	ldrb r3, [r6, #0x35]
	ldrb r5, [r6, #0x3A]
	add r3, r3, r5
	bl BaseStats_CalcStat
	ldr r2, =0x959
	cmp r5, #0
	addne r2, r2, #1
	mov r1, r2
	mov r2, #0x4E
	bl BaseStats_UiDraw
	; Sp. Def
	mov r0, r8
	mov r1, r9
	mov r2, #4
	ldrb r3, [r6, #0x37]
	ldrb r5, [r6, #0x3C]
	add r3, r3, r5
	bl BaseStats_CalcStat
	ldr r2, =0x95D
	cmp r5, #0
	ldrne r2, =0x95C
	mov r1, r2
	mov r2, #0x4E
	bl BaseStats_UiDraw
	; Spe on the HP row, right of current/max (table 19140).
	mov r0, r8
	mov r1, r9
	mov r2, #5
	ldrb r3, [r6, #0x3d]
	bl BaseStats_CalcStat
	ldr r1, =19141
	mov r2, #0x36
	bl BaseStats_UiDraw
	pop {r5, r7, r8, r9, r10, lr}
	b SummaryStatsAtkContinue

; Ground summary fill: team +0x10 is HP V. Write CalcStat HP and Spe V at +0x3D.
; Exclusive HP is folded into CalcStat at SummaryHpExclusiveAdd (vanilla amount).
BaseStats_UiHpFill:
	push {r4, r5, r6, lr}
	mov r5, r8
	mov r6, r9
	ldrb r3, [r5, #0x10]
	ldrsh r0, [r5, #0xc]
	ldrb r1, [r5, #2]
	mov r2, #0
	bl BaseStats_CalcStat
	str r0, [r6, #0x24]
	str r0, [r6, #0x28]
	ldrb r0, [r5, #0x11]
	strb r0, [r6, #0x3d]
	pop {r4, r5, r6, lr}
	b SummaryHpFillContinue

; After exclusive boosts land on the stack: r3 = HP V + vanilla excl HP.
; r0 is still the HP cap from the earlier pool load. r8 = team, r9 = summary.
BaseStats_UiHpExclusive:
	push {r0, r2, r3, r4, lr}
	ldrsh r3, [sp, #0x18]
	ldrb r4, [r8, #0x10]
	add r3, r3, r4
	ldrsh r0, [r8, #0xc]
	ldrb r1, [r8, #2]
	mov r2, #0
	bl BaseStats_CalcStat
	str r0, [r9, #0x24]
	mov r1, r0
	pop {r0, r2, r3, r4, lr}
	str r1, [r9, #0x28]
	b SummaryHpExclusiveContinue

; ApplyExclusive epilogue: bake exclusive HP effects (0x4C/0x4D/0x4E) into
; CalcStat r3, rewrite +0x12, subtract that amount from +0x16 so other flats
; (e.g. effect 0x38) stay as post-CalcStat boosts. r7=monster; r4 has
; already become monster+0x124 (the move list), so it is not an entity.
; The original function returned early for monster+6 != 0. Read the
; exclusive-effect bitmap directly, with the same bit helper as its wrapper.
BaseStats_FoldExclusiveHp:
	push {r0, r1, r2, r3, r5, r6, lr}
	mov r5, #0
	add r0, r7, #0x228
	mov r1, #0x4c
	bl ExclusiveEffectBitCheck
	cmp r0, #0
	beq BaseStats_FoldExcl4d
	ldr r0, =ExclusiveHpAmount
	ldrsh r0, [r0]
	add r5, r5, r0
BaseStats_FoldExcl4d:
	add r0, r7, #0x228
	mov r1, #0x4d
	bl ExclusiveEffectBitCheck
	cmp r0, #0
	beq BaseStats_FoldExcl4e
	ldr r0, =ExclusiveHpAmount
	ldrsh r0, [r0]
	add r0, r0, r0
	add r5, r5, r0
BaseStats_FoldExcl4e:
	add r0, r7, #0x228
	mov r1, #0x4e
	bl ExclusiveEffectBitCheck
	cmp r0, #0
	beq BaseStats_FoldExclHave
	ldr r0, =ExclusiveHpAmount
	ldrsh r0, [r0]
	add r1, r0, r0, lsl #1
	add r5, r5, r1
BaseStats_FoldExclHave:
	cmp r5, #0
	beq BaseStats_FoldExclDone
	mov r0, r7
	bl BaseStats_MonsterHpV
	add r3, r0, r5
	ldrsh r0, [r7, #2]
	ldrb r1, [r7, #0xa]
	mov r2, #0
	bl BaseStats_CalcStat
	strh r0, [r7, #0x12]
	ldrsh r1, [r7, #0x16]
	sub r1, r1, r5
	strh r1, [r7, #0x16]
	ldrsh r2, [r7, #0x12]
	add r2, r2, r1
	ldrsh r1, [r7, #0x10]
	cmp r1, #1
	movlt r1, r2
	cmp r1, r2
	movgt r1, r2
	strh r1, [r7, #0x10]
BaseStats_FoldExclDone:
	pop {r0, r1, r2, r3, r5, r6, lr}
	pop {r4, r5, r6, r7, r8, pc}

	.pool

; r0 = value, r1 = string id, r2 = y
; r4 = window, r10 = original sp of the summary drawer
BaseStats_UiDraw:
	push {r7, lr}
	mov r7, r2
	str r0, [r10, #0x90]
	add r3, r10, #0x6C
	sub sp, #4
	str r3, [sp]
	add r0, r10, #0xBC
	mov r2, r1
	mov r1, #0xC8
	mov r3, #0
	bl SprintfTagged
	add sp, #4
	mov r0, r4
	mov r1, #4
	mov r2, r7
	add r3, r10, #0xBC
	bl DrawWindowText
	pop {r7, pc}

; Dungeon summary fill (ov29 0x022F8A18): r5 = monster, r7 = summary, r3 = 0.
; Level copy, then Spe V into +0x3D.
BaseStats_UiDungeonFill:
	ldrb r0, [r5, #0xa]
	str r0, [r7, #0x2c]
	push {r1, r2, r3, lr}
	mov r0, r5
	bl BaseStats_MonsterSpeV
	strb r0, [r7, #0x3d]
	pop {r1, r2, r3, lr}
	b DungeonSummaryLevelContinue

	.pool

; New-game / recruit / species-refresh: V slots start at 0.
BaseStats_ZeroGroundV:
	mov r1, #0
	strh r1, [r0, #0xa]
	strb r1, [r0, #0xc]
	strb r1, [r0, #0xd]
	strb r1, [r0, #0xe]
	strb r1, [r0, #0xf]
	bx lr

BaseStats_ZeroInitV:
	mov r0, r8
	bl BaseStats_ZeroGroundV
	b GroundInitVContinue

BaseStats_ZeroRefreshV:
	mov r0, r4
	bl BaseStats_ZeroGroundV
	b GroundRefreshVContinue

BaseStats_ZeroRecruitV:
	mov r0, #0
	strh r0, [sp, #0x1e]
	strb r0, [sp, #0x20]
	strb r0, [sp, #0x21]
	strb r0, [sp, #0x22]
	strb r0, [sp, #0x23]
	b RecruitInitVContinue

; GuestMonsterToGroundMonster: V slots start at 0, same as recruit/new-game.
; Dungeon stats are CalcStat. r0 is dest+0x14 and r2 is 0 for the
; learned-move bitset write.
BaseStats_ZeroGuestV:
	mov r1, #0
	strh r1, [r5, #0xa]
	strb r1, [r5, #0xc]
	strb r1, [r5, #0xd]
	strb r1, [r5, #0xe]
	strb r1, [r5, #0xf]
	mov r2, #0
	add r0, r5, #0x14
	b GuestInitVContinue

; Passthrough. v23 copied Spe here; guests now use CalcStat like the hero.
BaseStats_GuestSpeAfterHp:
	strh r0, [r6, #0xe]
	b InitMentryHpStoreContinue

; LevelUpBody still has the pre-loop level in r7+0x0A. Multi-level
; batches keep that value for the one stats line after LevelUp returns.
BaseStats_SaveOldLevel:
	ldrb r0, [r7, #0xa]
	ldr r1, =BaseStats_OldLevel
	str r0, [r1]
	bx lr

; r0 = dungeon monster, r1 = dest of 5 words: HP Atk Def SpA SpD.
; Spe goes to BaseStats_SpeDelta. V is the current doping byte.
BaseStats_WriteLevelUpDeltas:
	push {r4, r5, r6, r7, r8, r9, r10, lr}
	mov r4, r0
	mov r5, r1
	ldrb r6, [r4, #0xa]
	ldr r0, =BaseStats_OldLevel
	ldr r7, [r0]
	cmp r7, #1
	movlt r7, #1
	cmp r7, #0x64
	movgt r7, #0x64
	cmp r6, #1
	movlt r6, #1
	cmp r6, #0x64
	movgt r6, #0x64
	ldrsh r8, [r4, #2]
	mov r9, #0
BaseStats_DeltaLoop:
	cmp r9, #0
	beq BaseStats_DeltaVHp
	cmp r9, #5
	beq BaseStats_DeltaVSpe
	cmp r9, #1
	ldreqb r3, [r4, #0x1a]
	cmp r9, #2
	ldreqb r3, [r4, #0x1c]
	cmp r9, #3
	ldreqb r3, [r4, #0x1b]
	cmp r9, #4
	ldreqb r3, [r4, #0x1d]
	b BaseStats_DeltaHaveV
BaseStats_DeltaVHp:
	mov r0, r4
	bl BaseStats_MonsterHpV
	mov r3, r0
	b BaseStats_DeltaHaveV
BaseStats_DeltaVSpe:
	mov r0, r4
	bl BaseStats_MonsterSpeV
	mov r3, r0
BaseStats_DeltaHaveV:
	mov r10, r3
	mov r0, r8
	mov r1, r6
	mov r2, r9
	mov r3, r10
	bl BaseStats_CalcStat
	push {r0}
	mov r0, r8
	mov r1, r7
	mov r2, r9
	mov r3, r10
	bl BaseStats_CalcStat
	pop {r1}
	sub r1, r1, r0
	cmp r9, #5
	ldreq r0, =BaseStats_SpeDelta
	streq r1, [r0]
	strne r1, [r5, r9, lsl #2]
	add r9, r9, #1
	cmp r9, #6
	blt BaseStats_DeltaLoop
	pop {r4, r5, r6, r7, r8, r9, r10, pc}

; EXP / Joy Seed wrappers. dest is the existing HP/Atk/Def/SpA/SpD slots.
BaseStats_DeltasExp:
	mov r0, r5
	add r1, sp, #0x48
	bl BaseStats_WriteLevelUpDeltas
	cmp r8, #0
	b LevelUpDeltasExpContinue

BaseStats_DeltasJoy:
	mov r0, r9
	add r1, sp, #0x84
	bl BaseStats_WriteLevelUpDeltas
	add r1, sp, #0x60
	mov r0, r5
	b LevelUpDeltasJoyContinue

; number_vals is only 0..4. [string:1] copies the pointer as 16-bit units, so
; ASCII "3\0" becomes 0x0033 and leftover bytes draw as ■ / &. Write the
; digits into the format buffer instead, same as the '+' already in 3863.
BaseStats_SetSpeDigit:
	push {r1, r2, r3, r4, r6, lr}
	ldr r0, =BaseStats_SpeDelta
	ldr r0, [r0]
	ldr r1, =BaseStats_SpeText
	bl BaseStats_Itoa
	ldr r1, =BaseStats_String1Tag
	mov r4, r5
BaseStats_FindTag:
	ldrb r0, [r4]
	cmp r0, #0
	beq BaseStats_SpeAppend
	mov r2, r4
	mov r3, r1
	mov r6, #10
BaseStats_TagCmp:
	ldrb r0, [r2], #1
	ldrb r12, [r3], #1
	cmp r0, r12
	bne BaseStats_FindNext
	subs r6, r6, #1
	bne BaseStats_TagCmp
	ldr r1, =BaseStats_SpeText
BaseStats_SpeCopy:
	ldrb r0, [r1], #1
	strb r0, [r4], #1
	cmp r0, #0
	bne BaseStats_SpeCopy
	b BaseStats_SpeDigitDone
BaseStats_FindNext:
	add r4, r4, #1
	ldr r1, =BaseStats_String1Tag
	b BaseStats_FindTag
BaseStats_SpeAppend:
	mov r0, r5
	ldr r1, =BaseStats_SpeText
	bl Strcat
BaseStats_SpeDigitDone:
	pop {r1, r2, r3, r4, r6, lr}
	ldrb r0, [r5]
	bx lr

; r0 = signed int, r1 = dest. Writes a NUL-terminated decimal.
; SoftDiv clobbers r2/r3; keep the dividend in r7.
BaseStats_Itoa:
	push {r2, r3, r4, r5, r6, r7, lr}
	mov r4, r1
	cmp r0, #0
	bge BaseStats_ItoaPos
	mov r2, #0x2D
	strb r2, [r4], #1
	rsb r0, r0, #0
BaseStats_ItoaPos:
	mov r6, r4
	add r5, r4, #11
	mov r2, #0
	strb r2, [r5]
	cmp r0, #0
	bne BaseStats_ItoaLoop
	sub r5, r5, #1
	mov r2, #0x30
	strb r2, [r5]
	b BaseStats_ItoaCopy
BaseStats_ItoaLoop:
	mov r7, r0
	mov r1, #10
	bl SoftDiv
	mov r2, #10
	mul r2, r0, r2
	sub r2, r7, r2
	add r2, r2, #0x30
	sub r5, r5, #1
	strb r2, [r5]
	cmp r0, #0
	bne BaseStats_ItoaLoop
BaseStats_ItoaCopy:
	ldrb r2, [r5], #1
	strb r2, [r6], #1
	cmp r2, #0
	bne BaseStats_ItoaCopy
	pop {r2, r3, r4, r5, r6, r7, pc}

	.align 4
	.pool
BaseStats_OldLevel:
	.word 0
BaseStats_SpeDelta:
	.word 0
BaseStats_SpeText:
	.byte 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
BaseStats_String1Tag:
	.ascii "[string:1]"
	.align 4

; Life Seed / Sitrus max-HP boost: add r4 to HP V, rewrite +0x12 from CalcStat.
; r4 = boost, r6 = entity, r9 = monster. r4==0 or non-team keeps the vanilla add.
; Guests use the same V add as the rest of the party.
BaseStats_LifeSeed:
	push {r0, r1, r2, r3, lr}
	cmp r4, #0
	beq BaseStats_LifeSeedVanilla
	ldrsh r0, [r9, #0xc]
	cmp r0, #0
	blt BaseStats_LifeSeedVanilla
	cmp r0, #4
	bge BaseStats_LifeSeedVanilla
	bl GetActiveTeamMember
	cmp r0, #0
	beq BaseStats_LifeSeedVanilla
	ldrb r1, [r0, #0x10]
	add r1, r1, r4
	cmp r1, #0
	movlt r1, #0
	cmp r1, #0xff
	movgt r1, #0xff
	strb r1, [r0, #0x10]
	mov r3, r1
	ldrsh r0, [r9, #2]
	ldrb r1, [r9, #0xa]
	mov r2, #0
	bl BaseStats_CalcStat
	ldrsh r1, [r9, #0x12]
	strh r0, [r9, #0x12]
	sub r0, r0, r1
	ldrsh r1, [r9, #0x10]
	add r1, r1, r0
	cmp r1, #1
	movlt r1, #1
	strh r1, [r9, #0x10]
	pop {r0, r1, r2, r3, lr}
	ldr r0, =32767
	mov r2, r0
	b TryIncreaseHpAfterBoost
BaseStats_LifeSeedVanilla:
	pop {r0, r1, r2, r3, lr}
	ldrsh r1, [r9, #0x12]
	b TryIncreaseHpBoostResume

	.pool
.if . > ov_36 + BaseStatsCodeAddress + BaseStats_CaveBytes
	.error "V writers / summary UI run past the cave"
.endif

.close

.open "arm9.bin", ov_arm9

.include "generated/hp_caps_arm9.inc"

.org SummaryStatsAtkLoad
	b BaseStats_UiStats

.org SummaryHpFill
	b BaseStats_UiHpFill

.org SummaryHpExclusiveAdd
	b BaseStats_UiHpExclusive

.org GroundInitV
	b BaseStats_ZeroInitV

.org GroundRefreshV
	b BaseStats_ZeroRefreshV

.org RecruitInitV
	b BaseStats_ZeroRecruitV

.org GuestInitV
	b BaseStats_ZeroGuestV

.org InitMentryHpStore
	b BaseStats_GuestSpeAfterHp

.org GroundLevelUpV
	b GroundLevelUpVContinue

.org RecruitHpOverwrite
	nop

.close

.open "overlay_0029.bin", ov_29

.org DungeonSummaryLevel
	b BaseStats_UiDungeonFill

.org TeamSyncMaxHp
	nop

; TryRecruit: summary max HP was written into team +0x10 (now HP|Spe V).
; Keep the following strh; force the value to 0 so recruits start at V=0.
.org TryRecruitHpVStore
	mov r1, #0

.org TryIncreaseHpBoost
	b BaseStats_LifeSeed

.org ApplyExclusiveEpilogue
	b BaseStats_FoldExclusiveHp

.close
