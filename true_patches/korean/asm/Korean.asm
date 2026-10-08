; Korean glyph engine (port of the unofficial EoS Korean patch).
; Game codes: lead 0x88..0x9E, trail 0x80..0xFE -> index (lead-0x88)*127 + trail-0x80
; into KoGlyphTable at 0x023E0000 (0x1C bytes per glyph: 4-byte header + 12 rows x 16 bits, 1bpp).
; Index 0 is a blank glyph for codes outside the table.

; r0 = code -> r0 = glyph entry. Clobbers r1, r2.
Ko_GlyphEntry:
	and r1, r0, #0xFF
	subs r1, r1, #0x80
	movlt r1, #0
	blt @@index
	mov r2, r0, lsr #8
	sub r2, r2, #0x88
	rsb r2, r2, r2, lsl #7
	add r1, r1, r2
	ldr r2, =KoGlyphCount
	cmp r1, r2
	movhs r1, #0
@@index:
	ldr r2, =KoGlyphTable
	rsb r1, r1, r1, lsl #3
	add r0, r2, r1, lsl #2
	bx lr

; Font glyph lookup entry (replaces push {r4,lr}; exit pops {r4-r7,pc}).
Ko_GlyphLookup:
	push {r4-r7, lr}
	cmp r0, #0x8800
	blo KoFontLookupBody
	cmp r0, #0x9F00
	bgt KoFontLookupBody
	bl Ko_GlyphEntry
	mov r3, #0
	pop {r4-r7, pc}

; Glyph width lookup entry (replaces push {r3,lr}); returns entry - 4.
Ko_GlyphWidth:
	push {r3, lr}
	cmp r0, #0x8800
	blt KoWidthBody
	cmp r0, #0x9F00
	bgt KoWidthBody
	bl Ko_GlyphEntry
	sub r0, r0, #4
	pop {r3, pc}

; 2-bit -> 2-pixel 4bpp expansion table; must sit right before Ko_RenderRows.
Ko_BitTable:
	.word 0xFFF00F00

; r1 = glyph rows, lr = 0. Expands 12 rows into the stack glyph buffer.
Ko_RenderRows:
	add r0, sp, #0x560
	sub r0, r0, #4
	sub r9, r15, #0x14
@@row:
	ldrb r2, [r1], #1
	and r3, r2, #3
	ldrb r3, [r9, r3]
	strb r3, [r0], #1
	mov r3, r2, lsr #2
	and r3, r3, #3
	ldrb r3, [r9, r3]
	strb r3, [r0], #1
	mov r3, r2, lsr #4
	and r3, r3, #3
	ldrb r3, [r9, r3]
	strb r3, [r0], #1
	mov r3, r2, lsr #6
	ldrb r3, [r9, r3]
	strb r3, [r0], #1
	ldrb r2, [r1], #1
	and r3, r2, #3
	ldrb r3, [r9, r3]
	strb r3, [r0], #1
	mov r3, r2, lsr #2
	and r3, r3, #3
	ldrb r3, [r9, r3]
	strb r3, [r0], #1
	mov r3, r2, lsr #4
	and r3, r3, #3
	ldrb r3, [r9, r3]
	strb r3, [r0], #1
	mov r3, r2, lsr #6
	ldrb r3, [r9, r3]
	strb r3, [r0], #1
	add r0, r0, #4
	add lr, lr, #1
	cmp lr, #0xC
	blt @@row
	b KoRenderReturn

; Width pass: read a 1- or 2-byte character into r0.
Ko_WidthCharFetch:
	ldrb r0, [r4], #1
	cmp r0, #0x88
	blt KoWidthCharResume
	cmp r0, #0x9F
	bgt KoWidthCharResume
	ldrb r1, [r4], #1
	orr r0, r1, r0, lsl #8
	b KoWidthCharResume

; Draw pass: read a character into r8; 2-byte codes go straight to glyph drawing.
Ko_DrawCharFetch:
	ldrb r8, [r6], #1
	cmp r8, #0x88
	blt KoDrawCharResume
	cmp r8, #0x9F
	bgt KoDrawCharResume
	ldrb r0, [r6], #1
	orr r8, r0, r8, lsl #8
	b KoDrawGlyphResume

; Lead-byte check: r1 = trail byte. A terminator or '[' keeps the lead single.
Ko_TrailCheck:
	cmp r1, #0
	beq KoLeadSingle
	cmp r1, #0x5B
	b KoLeadJoin

; Character copy: keep both bytes of a 2-byte code together.
Ko_CopyCharFetch:
	ldrb r4, [r0, #-4]
	cmp r4, #0x88
	blt KoCopyCharSingle
	cmp r4, #0x9F
	bgt KoCopyCharSingle
	ldrb r0, [r0, #-3]
	cmp r0, #0
	beq KoCopyCharSingle
	strb r4, [sp, #0x2C]
	strb r0, [sp, #0x2D]
	mov r6, #2
	b KoCopyCharJoin

Ko_SkipTrail:
	.word 0

; Measure pass: r5 = character; the trail byte of a 2-byte code is skipped next call.
Ko_MeasureCharFetch:
	; Only the immutable address is a literal; the flag itself is a runtime load.
	; Preserve r3 at every exit: this hook replaces a single ldrb instruction.
	push {r3}
	ldr r3, =Ko_SkipTrail
	ldrb r2, [r3]
	cmp r2, #1
	addeq r6, r6, #1
	addeq r0, r1, r6
	moveq r2, #0
	streqb r2, [r3]
	ldrb r5, [r0, #0xFC]
	cmp r5, #0x88
	blt @@resume
	cmp r5, #0x9F
	bgt @@resume
	ldrb r0, [r0, #0xFD]
	cmp r0, #0
	beq @@resume
	orr r5, r5, r0, lsl #8
	mov r2, #1
	strb r2, [r3]
@@resume:
	pop {r3}
	b KoMeasureCharResume

.pool
