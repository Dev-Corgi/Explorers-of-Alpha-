; Name pages 0 and 1: two symbol keys become one dialogue syllable.
; r1 = keyboard, r4 = key code, r12 = page. A finished syllable is deleted
; as one character when the cursor sits on the trailing zero.

Ka_OnKey:
	push {r6, r7, lr}
	cmp r12, #1
	bhi @@orig
	movs r0, r4, lsr #8
	bne @@orig
	ldr r0, =Ka_SymIndex
	and r2, r4, #0xFF
	ldrb r6, [r0, r2]
	ldrb r3, [r1, #0x1C]
	cmp r3, #0
	beq @@orig
	cmp r3, #2
	blo @@pending
	ldr r0, [r1, #0xF8]
	sub r2, r3, #2
	ldrb r2, [r0, r2]
	sub r0, r3, #1
	ldr r7, [r1, #0xF8]
	ldrb r7, [r7, r0]
	bl Ka_IsSyllable
	cmp r0, #0
	bne @@orig
	b @@have_prev
@@pending:
	ldr r0, [r1, #0xF8]
	sub r2, r3, #1
	ldrb r7, [r0, r2]
@@have_prev:
	ldr r0, =Ka_SymIndex
	ldrb r2, [r0, r7]
	cmp r2, #0xFF
	beq @@san
	cmp r6, #0xFF
	beq @@san
	ldrb r0, [r1, #0x15]
	cmp r0, #1
	beq @@san
	ldrb r0, [r1, #0x1B]
	cmp r3, r0
	bhs @@san
	mov r0, #78
	mul r0, r2, r0
	add r0, r0, r6
	ldr r6, =KaPairCount
	cmp r0, r6
	bhs @@san
	ldr r6, =Ka_Codes
	add r0, r6, r0, lsl #1
	ldrh r4, [r0]
	ldrb r2, [r1, #0x1B]
	sub r6, r2, #2
	cmp r6, r3
	blt @@store
@@shift:
	ldr r0, [r1, #0xF8]
	ldrb r7, [r0, r6]
	add r2, r6, #1
	strb r7, [r0, r2]
	sub r6, r6, #1
	cmp r6, r3
	bge @@shift
@@store:
	ldr r0, [r1, #0xF8]
	sub r2, r3, #1
	mov r7, r4, lsr #8
	strb r7, [r0, r2]
	and r7, r4, #0xFF
	strb r7, [r0, r3]
	add r3, r3, #1
	strb r3, [r1, #0x1C]
	pop {r6, r7, lr}
	b KaInsertOk
@@san:
	ldr r0, =Ka_Sanitize
	ldrb r2, [r0, r7]
	cmp r2, #0
	beq @@orig
	ldr r0, [r1, #0xF8]
	sub r6, r3, #1
	strb r2, [r0, r6]
@@orig:
	pop {r6, r7, lr}
	sub r0, r4, #0x104
	b KaOnKeyResume

; r2 = lead, r7 = trail. r0 = 1 when that pair is a dialogue syllable.
Ka_IsSyllable:
	push {r3, r6, lr}
	cmp r2, #0x88
	blo @@no
	cmp r2, #0x9F
	bhs @@no
	cmp r7, #0x80
	blo @@no
	sub r0, r2, #0x88
	mov r6, #127
	mul r6, r0, r6
	sub r0, r7, #0x80
	add r0, r6, r0
	ldr r6, =KaGlyphMax
	cmp r0, r6
	bhs @@no
	ldr r6, =Ka_Bits
	and r2, r0, #7
	mov r0, r0, lsr #3
	ldrb r0, [r6, r0]
	mov r0, r0, lsr r2
	ands r0, r0, #1
	pop {r3, r6, lr}
	bx lr
@@no:
	mov r0, #0
	pop {r3, r6, lr}
	bx lr

Ka_Del:
	push {r3, r4, r5, r6, r7, lr}
	ldr r0, =KaKeyboard
	ldr r1, [r0]
	ldrb r2, [r1, #0x16]
	cmp r2, #1
	bhi @@vanilla
	ldrb r2, [r1, #0x10]
	cmp r2, #0
	bne @@vanilla
	ldrb r3, [r1, #0x1C]
	cmp r3, #2
	blo @@vanilla
	ldr r0, [r1, #0xF8]
	ldrb r4, [r0, r3]
	cmp r4, #0
	bne @@vanilla
	sub r2, r3, #1
	ldrb r7, [r0, r2]
	sub r2, r3, #2
	ldrb r2, [r0, r2]
	bl Ka_IsSyllable
	cmp r0, #0
	beq @@vanilla
	sub r3, r3, #2
	strb r3, [r1, #0x1C]
	ldr r0, [r1, #0xF8]
	mov r2, #0
	strb r2, [r0, r3]
	add r4, r3, #1
	strb r2, [r0, r4]
	mov r0, #0
	bl KaSound
	ldr r0, =KaKeyboard
	ldr r0, [r0]
	ldrsb r0, [r0]
	bl KaRedrawName
	bl KaRedrawCursor
	mov r0, #0
	pop {r3, r4, r5, r6, r7, pc}
@@vanilla:
	pop {r3, r4, r5, r6, r7, lr}
	push {r3, lr}
	b KaDelResume

.pool
.align 4
.include "ka_data.asm"
