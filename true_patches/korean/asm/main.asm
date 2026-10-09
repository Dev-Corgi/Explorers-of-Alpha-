.nds
.arm

.include "offsetsUS.asm"
.include "generated.inc"

.open "overlay_0036.bin", 0x023A7080
.org KoreanCaveAddress
.area KoreanCaveSize
.include "Korean.asm"
.endarea
.close

.open "arm9.bin", 0x02000000
.org KoDrawCharFetch
	b Ko_DrawCharFetch
.org KoDrawGlyphCall
	bl KoGlyphPrepKorean
.org KoWidthCharFetch
	b Ko_WidthCharFetch
.org KoWidthGlyphEntry
	b Ko_GlyphWidth

; Dense lead bytes 0x88..0x9E join only with a valid trail byte.
.org KoLeadCheck
	b Ko_ReadChar
	blt KoLeadSingle
	cmp r0, #0x9E
	bgt KoLeadSingle
	ldrb r1, [r6, #1]
	b Ko_TrailCheck
	addne r6, r6, #1
	orrne r0, r1, r0, lsl #8
	movne r0, r0, lsl #0x10
	movne r0, r0, lsr #0x10

; Glyph prep: the vanilla function is only reached through KoDrawGlyphCall.
.org KoGlyphPrep
	bx lr
KoGlyphPrepKorean:
	cmp r0, #0x8800
	bxlt lr
	cmp r0, #0x9F00
	bxgt lr
	bl Ko_GlyphLookup
	mov r2, #0
	add r1, sp, #0x4D0
@@clear:
	str r3, [r1, r2]
	add r2, r2, #4
	cmp r2, #0x124
	ble @@clear
	mov lr, #0
	add r1, r0, #4
	sub r0, r0, #4
	str r0, [sp, #0x4D0]
	b Ko_RenderRows
; Save the glyph pointer in the existing render frame, outside its pixel buffer.
; Runtime data must not occupy a PC-relative literal slot inside ARM9 code.
.org KoGlyphPrep + 0x48
KoRenderReturn:
	ldr r0, [sp, #0x4D0]
	ldr r3, [r15, #0xC]
	ldr r3, [r3]
	ldr r3, [r3]
	str r3, [sp, #0x1C]
	b KoDrawContinue
	.word KoFontStatePtr

.org KoFontLookupEntry
	b Ko_GlyphLookup
.org KoFontLookupExit
	pop {r4-r7, pc}
.org KoMeasureCharFetch
	b Ko_MeasureCharFetch
.org KoCopyCharFetch
	b Ko_CopyCharFetch
.org KoCopyCharStore
	strb r4, [sp, #0x2C]
.org KoNameCursorSite
	b Ko_NameCursor
.org 0x02038110
	bl Ko_NameDrawGlyph
.org 0x020381C0
	bl Ko_NameDrawGlyph
.org 0x02038254
	bl Ko_NameDrawGlyph
.org KoNameDrawGlyphSite
	bl Ko_NameDrawGlyph
.org KoPuRegion2
	.word 0x023F001F
.org KoPreprocessCopy
	b Ko_PreprocessCopy
.close
