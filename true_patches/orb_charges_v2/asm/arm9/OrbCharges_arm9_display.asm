; Pinpoint: after "cmp r6, #1" @ 0x0200D3B4, branch on r6 == 9 (orbs).
; Charge-table orbs use the same %s(%d) suffix as stack items; d = remaining (max - [+2]).
; Non-table cat-9 orbs fall through to vanilla @ 0x0200D40C (→ … → r6 == 0xF …).
; Max table: ov29 OrbChargeTableOv29 @ 0x02332200 (charge=3 only; charge=1 vanilla).

.org BuildItemNameCat1Branch
	b OrbCharges_BuildItemNameAfterCat1

.org OrbChargesArm9DisplayCodeAddress

.definelabel CountFmtPlain,         0x02097F50
.definelabel CountFmtColored,       0x02097F34
.definelabel BuildItemNameSprintf,  0x0200D634
.definelabel BuildItemNameAfterName, 0x0200D4F8

; Replaces "bne #0x0200D40C" @ 0x0200D3B8.
OrbCharges_BuildItemNameAfterCat1:
	cmp r6, #1
	beq BuildItemNameStackPath
	cmp r6, #9
	beq OrbCharges_BuildItemNameCat9
	b BuildItemNameAfterCat9

; Cat 9 + ov29 charge table: stack-style %s(remaining) @ D3C0 equivalent.
OrbCharges_BuildItemNameCat9:
	push {r4, r5, lr}
	ldrh r4, [r9, #4]
	cmp r4, #0
	beq OrbCharges_Cat9Vanilla
	mov r0, r4
	bl OrbChargeLookupOv29Table
	cmp r0, #0
	beq OrbCharges_Cat9Vanilla
	mov r5, r0
	ldrh r0, [r9, #2]
	and r0, r0, #0xFF
	sub r3, r5, r0
	add r0, sp, #0x5C
	cmp r7, #0
	beq OrbCharges_Cat9CountPlain
	ldr r1, =CountFmtColored
	bl BuildItemNameSprintf
	b OrbCharges_Cat9Done
OrbCharges_Cat9CountPlain:
	ldr r1, =CountFmtPlain
	bl BuildItemNameSprintf
OrbCharges_Cat9Done:
	pop {r4, r5, lr}
	b BuildItemNameAfterName

OrbCharges_Cat9Vanilla:
	pop {r4, r5, lr}
	b BuildItemNameAfterCat9

; r0 = item id -> r0 = max charges (0 if not in ov29 table)
OrbChargeLookupOv29Table:
	push {r1-r4, lr}
	mov r1, r0
	mov r2, #0
	mov r3, #OrbChargeTableCount
	ldr r12, =OrbChargesOv29CodeAddress
OrbChargeLookupOv29Loop:
	cmp r2, r3
	bge OrbChargeLookupOv29Miss
	lsl r0, r2, #2
	add r0, r12, r0
	ldrh r0, [r0]
	cmp r0, r1
	beq OrbChargeLookupOv29Hit
	add r2, r2, #1
	b OrbChargeLookupOv29Loop
OrbChargeLookupOv29Hit:
	lsl r0, r2, #2
	add r0, r12, r0
	ldrb r0, [r0, #2]
	b OrbChargeLookupOv29Done
OrbChargeLookupOv29Miss:
	mov r0, #0
OrbChargeLookupOv29Done:
	pop {r1-r4, pc}

.pool
