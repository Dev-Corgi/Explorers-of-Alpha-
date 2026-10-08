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
	cmp r0, #0x9E
	bgt KoWidthCharResume
	ldrb r1, [r4]
	cmp r1, #0x80
	blo KoWidthCharResume
	cmp r1, #0xFE
	bhi KoWidthCharResume
	add r4, r4, #1
	orr r0, r1, r0, lsl #8
	b KoWidthCharResume

; Draw pass: read a character into r8; 2-byte codes go straight to glyph drawing.
Ko_DrawCharFetch:
	ldrb r8, [r6], #1
	cmp r8, #0x88
	blt KoDrawCharResume
	cmp r8, #0x9E
	bgt KoDrawCharResume
	ldrb r0, [r6]
	cmp r0, #0x80
	blo KoDrawCharResume
	cmp r0, #0xFE
	bhi KoDrawCharResume
	add r6, r6, #1
	orr r8, r0, r8, lsl #8
	b KoDrawGlyphResume

; Lead-byte check: only dense trails 0x80..0xFE may be joined.
Ko_ReadChar:
	cmp r0, #0x88
	blo @@legacy
	cmp r0, #0x9E
	bhi KoLeadSingle
	ldrb r1, [r6, #1]
	b Ko_TrailCheck
@@legacy:
	cmp r0, #0x81
	blo KoLeadSingle
	cmp r0, #0x84
	bls @@trail
	cmp r0, #0x87
	bne KoLeadSingle
@@trail:
	ldrb r1, [r6, #1]
	cmp r1, #0
	beq KoLeadSingle
	cmp r1, #0x5B
	beq KoLeadSingle
	cmp r1, #0
	b KoLeadJoin

Ko_TrailCheck:
	cmp r1, #0x80
	blo KoLeadSingle
	cmp r1, #0xFE
	bhi KoLeadSingle
	; The ARM9 join instructions execute on NE; every valid trail is nonzero.
	cmp r1, #0
	b KoLeadJoin

; PreprocessString uses a different copier from KoLeadCheck. Both bytes of a
; dense glyph must be consumed here, otherwise trails 0x81..0x84/0x87 look like
; legacy leads and can swallow the NUL after a dungeon name. Preserve the
; legacy SJIS path for the remaining English symbols.
Ko_PreprocessCopy:
	cmp r0, #0x88
	blo @@legacy
	cmp r0, #0x9E
	bhi KoPreprocessCopySingle
	ldrb r2, [r5, #1]
	cmp r2, #0x80
	blo KoPreprocessCopySingle
	cmp r2, #0xFE
	bhi KoPreprocessCopySingle
	b KoPreprocessCopyPair
@@legacy:
	cmp r0, #0x81
	blo KoPreprocessCopySingle
	cmp r0, #0x84
	bls @@trail
	cmp r0, #0x87
	bne KoPreprocessCopySingle
@@trail:
	ldrb r2, [r5, #1]
	cmp r2, #0
	beq KoPreprocessCopySingle
	cmp r2, #0x5B
	beq KoPreprocessCopySingle
	b KoPreprocessCopyPair

; Character copy: keep both bytes of a 2-byte code together.
Ko_CopyCharFetch:
	; %c receives an integer code (lead << 8 | trail), not two raw bytes.
	ldr r0, [r0, #-4]
	mov r4, r0, lsr #8
	cmp r4, #0x88
	blo @@single
	cmp r4, #0x9E
	bhi @@single
	and r0, r0, #0xFF
	cmp r0, #0x80
	blo @@single
	cmp r0, #0xFE
	bhi @@single
	strb r4, [sp, #0x2C]
	strb r0, [sp, #0x2D]
	mov r6, #2
	b KoCopyCharJoin
@@single:
	mov r4, r0
	b KoCopyCharSingle

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
	cmp r5, #0x9E
	bgt @@resume
	ldrb r0, [r0, #0xFD]
	cmp r0, #0x80
	blo @@resume
	cmp r0, #0xFE
	bhi @@resume
	orr r5, r5, r0, lsl #8
	mov r2, #1
	strb r2, [r3]
@@resume:
	pop {r3}
	b KoMeasureCharResume

.pool
