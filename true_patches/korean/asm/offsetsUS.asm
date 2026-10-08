; Korean text engine — arm9 hook sites and resume points (EoS US / Alpha, vanilla bytes).

; Hook sites
.definelabel KoDrawCharFetch, 0x020158E0          ; ldrb r8,[r6],#1
.definelabel KoDrawGlyphCall, 0x02015A30          ; bl 0x02025480
.definelabel KoWidthCharFetch, 0x020161E0         ; ldrb r0,[r4],#1
.definelabel KoWidthGlyphEntry, 0x0201628C        ; push {r3,lr}
.definelabel KoLeadCheck, 0x020206C8              ; cmp r0,#0x81 ...
.definelabel KoGlyphPrep, 0x02025480              ; push {r3,lr} (function replaced)
.definelabel KoFontLookupEntry, 0x02025C7C        ; push {r4,lr}
.definelabel KoFontLookupExit, 0x02025D38         ; pop {r4,pc}
.definelabel KoMeasureCharFetch, 0x0203807C       ; ldrb r5,[r0,#0xfc]
.definelabel KoCopyCharFetch, 0x020892BC          ; ldr r0,[r0,#-4]
.definelabel KoCopyCharStore, 0x020892C4          ; strb r0,[sp,#0x2c]
.definelabel KoPuRegion2, 0x0207A520              ; PU region 2 word 0x023E0021

; Resume points
.definelabel KoDrawCharResume, 0x020158E4
.definelabel KoDrawGlyphResume, 0x02015A2C
.definelabel KoDrawContinue, 0x02015BC4
.definelabel KoWidthCharResume, 0x020161E4
.definelabel KoWidthBody, 0x02016290
.definelabel KoLeadSingle, 0x020206F0
.definelabel KoLeadJoin, 0x020206E0
.definelabel KoFontLookupBody, 0x02025C80
.definelabel KoMeasureCharResume, 0x02038080
.definelabel KoCopyCharSingle, 0x020892C0
.definelabel KoCopyCharJoin, 0x020892C8

; Current font state pointer (same literal as the vanilla draw path).
.definelabel KoFontStatePtr, 0x020AF710
