; Separate permanent/outing save schema. No first-floor reset.
.org SpindaEvDungeonStatCave
DungeonStat_OnFloorMember:
 push {r3-r10, lr}
 b InitTeamMemberBody
DungeonStat_OnDungeonGroupEnd:
 push {r0-r3, r12, lr}
 bl DungeonStat_IsDungeonGroupOutingEnd
 cmp r0, #0
 blne EvSave_GroupEnd
 pop {r0-r3, r12, lr}
 b SpindaEv_PriorDungeonFree
DungeonStat_IsDungeonGroupOutingEnd:
	push {r4, r5, lr}
	ldr r4, =DungeonMasterPtr
	ldr r5, [r4, #4]
	cmp r5, #0
	ldreq r5, [r4]
	movs r4, r5
	beq DungeonStat_GroupEndNo
	add r0, r4, #0x2C000
	add r0, r0, #0xA00
	ldrh r0, [r0, #0x66]
	ldr r1, =DAMAGE_SOURCE_DUNGEON_CLEAR
	cmp r0, r1
	bne DungeonStat_GroupEndYes
	add r0, r4, #0x4A
	add r0, r0, #0x700
	add r1, r4, #0x48
	add r1, r1, #0x700
	bl DungeonFloorToGroupFloor
	ldrb r5, [r4, #DUNGEON_GROUP_FLOOR_OFF]
	ldrb r0, [r4, #DUNGEON_ID_FLOOR_OFF]
	bl GetNbFloorsDungeonGroup
	cmp r5, r0
	movge r0, #1
	movlt r0, #0
	pop {r4, r5, pc}
DungeonStat_GroupEndYes:
	mov r0, #1
	pop {r4, r5, pc}
DungeonStat_GroupEndNo:
	mov r0, #0
	pop {r4, r5, pc}


; Record Wonder Gummi (type 0xFF) then run the original prologue.
WonderGummi_Entry:
	push {r0-r3, r12, lr}
	mov r0, r1
	bl EvSave_Begin
	pop {r0-r3, r12, lr}
	push {r4, lr}
	cmp r2, #WONDER_GUMMI_TYPE
	moveq r4, #1
	movne r4, #0
	ldr r12, =WonderGummiPending
	strb r4, [r12]
	pop {r4, lr}
	push {r3-r11, lr}
	b ApplyGummiBoostsAfterPrologue

WonderGummiPending:
	.byte 0
	.align 4

; Wonder Gummi exit was in the dungeon-stat cave; kept here with Entry so
; both live in the arm9 code cave (dungeon-stat needs room for peel/snap).
WonderGummi_Exit:
	ldr r4, =WonderGummiPending
	ldrb r0, [r4]
	mov r1, #0
	strb r1, [r4]
	cmp r0, #0
	beq WonderGummi_Epilogue
	ldr r4, =ApplyProteinEffect
	mov r5, #4
WonderGummi_StatLoop:
	mov r0, r10
	mov r1, r9
	mov r2, #WONDER_GUMMI_ALL_STAT
	blx r4
	add r4, r4, #WONDER_GUMMI_STAT_FN_STRIDE
	subs r5, r5, #1
	bne WonderGummi_StatLoop
	ldr r2, [r9, #0xb4]
	ldrsh r0, [r2, #0xc]
	cmp r0, #0
	blt WonderGummi_HpBar
	cmp r0, #4
	bge WonderGummi_HpBar
	bl GetActiveTeamMember
	cmp r0, #0
	beq WonderGummi_HpBar
	ldrb r1, [r0, #0x10]
	add r1, r1, #WONDER_GUMMI_ALL_STAT
	cmp r1, #0xff
	movgt r1, #0xff
	strb r1, [r0, #0x10]
WonderGummi_HpBar:
	ldr r2, [r9, #0xb4]
	ldrsh r3, [r2, #0x12]
	ldrsh r1, [r2, #0x16]
	add r0, r3, #WONDER_GUMMI_ALL_STAT
	add r12, r0, r1
	ldr r4, =WONDER_GUMMI_HP_CAP
	cmp r12, r4
	subgt r0, r4, r1
	cmp r0, r3
	movlt r0, r3
	sub r12, r0, r3
	strh r0, [r2, #0x12]
	add r1, r0, r1
	cmp r1, r4
	movgt r1, r4
	ldrsh r0, [r2, #0x10]
	add r0, r0, r12
	cmp r0, r1
	movgt r0, r1
	strh r0, [r2, #0x10]
	mov r0, r9
	bl RefreshEntityAfterStatChange
WonderGummi_Epilogue:
	bl EvSave_End
	add sp, sp, #8
	pop {r3-r11, pc}


EvSave_Protein:
 push {r4-r8, lr}
 mov r4, r0
 mov r5, r1
 mov r6, r2
 mov r7, r3
 mov r0, r1
 bl EvSave_Begin
 mov r0, r4
 mov r1, r5
 mov r2, r6
 mov r3, r7
 bl EvSave_OriginalProtein
 mov r4, r0
 bl EvSave_End
 mov r0, r4
 pop {r4-r8, pc}

EvSave_Calcium:
 push {r4-r8, lr}
 mov r4, r0
 mov r5, r1
 mov r6, r2
 mov r7, r3
 mov r0, r1
 bl EvSave_Begin
 mov r0, r4
 mov r1, r5
 mov r2, r6
 mov r3, r7
 bl EvSave_OriginalCalcium
 mov r4, r0
 bl EvSave_End
 mov r0, r4
 pop {r4-r8, pc}

EvSave_Iron:
 push {r4-r8, lr}
 mov r4, r0
 mov r5, r1
 mov r6, r2
 mov r7, r3
 mov r0, r1
 bl EvSave_Begin
 mov r0, r4
 mov r1, r5
 mov r2, r6
 mov r3, r7
 bl EvSave_OriginalIron
 mov r4, r0
 bl EvSave_End
 mov r0, r4
 pop {r4-r8, pc}

EvSave_Zinc:
 push {r4-r8, lr}
 mov r4, r0
 mov r5, r1
 mov r6, r2
 mov r7, r3
 mov r0, r1
 bl EvSave_Begin
 mov r0, r4
 mov r1, r5
 mov r2, r6
 mov r3, r7
 bl EvSave_OriginalZinc
 mov r4, r0
 bl EvSave_End
 mov r0, r4
 pop {r4-r8, pc}

EvSave_Hp:
 push {r4-r8, lr}
 mov r4, r0
 mov r5, r1
 mov r6, r2
 mov r7, r3
 mov r0, r1
 bl EvSave_Begin
 mov r0, r4
 mov r1, r5
 mov r2, r6
 mov r3, r7
 ldr r8, [sp, #24]
 sub sp, sp, #8
 str r8, [sp]
 bl EvSave_OriginalHp
 add sp, sp, #8
 mov r4, r0
 bl EvSave_End
 mov r0, r4
 pop {r4-r8, pc}

EvSave_LeaderTurn:
 push {r0-r3, r12, lr}
 bl EvSave_DungeonImport
 pop {r0-r3, r12, lr}
 push {r3-r11, lr}
 b 0x022EC30C

; Private special processes used by the one-time migration prompt.
EvSave_SpecialProcess:
 cmp r1, #240
 beq EvSave_LegacyPending
 cmp r1, #241
 moveq r0, #0
 beq EvSave_Convert
 cmp r1, #242
 moveq r0, #1
 beq EvSave_Convert
 push {r3-r11, lr}
 b 0x022E711C
EvSave_StartNewGame:
 push {r0-r3, r12, lr}
 bl EvSave_NewGame
 pop {r0-r3, r12, lr}
 push {r3, r4, lr}
 b 0x020487C8
.pool
.if . > SpindaEvDungeonStatCave + 0x800
 .error "save wrappers exceed trampoline region"
.endif

.org SpindaEvDungeonStatCave + 0x800
EvSave_OriginalRead:
 push {r3-r5, lr}
 b 0x02048ED4

.org SpindaEvDungeonStatCave + 0x810
EvSave_OriginalWrite:
 push {r4-r6, lr}
 b 0x02048E78

.org SpindaEvDungeonStatCave + 0x820
EvSave_OriginalCopy:
 push {r3-r5, lr}
 b 0x02059338

.org SpindaEvDungeonStatCave + 0x830
EvSave_OriginalMonsters:
 push {r4-r8, lr}
 b 0x02059228

.org SpindaEvDungeonStatCave + 0x840
EvSave_OriginalProtein:
 push {r4-r6, lr}
 b 0x02317F54

.org SpindaEvDungeonStatCave + 0x850
EvSave_OriginalCalcium:
 push {r4-r6, lr}
 b 0x02317FE8

.org SpindaEvDungeonStatCave + 0x860
EvSave_OriginalIron:
 push {r4-r6, lr}
 b 0x0231807C

.org SpindaEvDungeonStatCave + 0x870
EvSave_OriginalZinc:
 push {r4-r6, lr}
 b 0x02318110

.org SpindaEvDungeonStatCave + 0x880
EvSave_OriginalHp:
 push {r3-r11, lr}
 b 0x023152E8

.org SpindaEvDungeonStatCave + 0x1000
.incbin "save_v1.bin"
.if . > SpindaEvDungeonStatCave + 0x1D00
 .error "save runtime exceeds allocated cave"
.endif
.org SpindaEvDungeonStatCave + 0x1D00
 .fill 3904, 0 ; roster-indexed resident State
.org SpindaEvDungeonStatCave + 0x2D00
 .fill 16, 0 ; cafe scratch

.org 0x02048ED0
 b EvSave_Read

.org 0x02048E74
 b EvSave_Write

.org 0x02059334
 b EvSave_CopyMonster

.org 0x02059224
 b EvSave_ReadMonsters

.org 0x020487C4
 b EvSave_StartNewGame

.org 0x02059118
 push {r4-r8, lr} ; stock serializer, no peel/unpeel
