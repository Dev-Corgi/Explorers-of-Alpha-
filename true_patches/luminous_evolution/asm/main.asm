.nds
.arm
.include "generated.inc"
.open "arm9.bin", 0x02000000
.org 0x02052AC4
 add r2,r1,#8 ; read original MD requirements; disconnect Alpha Stone override
.org 0x02059B0C
 mov r0,#5 ; Spring unlocked, rather than postgame hero-evolution flag 10
.org 0x0205A230
 mov r0,#5
 b 0x0205A258 ; retain true/false status and ordinary requirements
.org 0x02039F30
 bl Spring_Eligibility
.org 0x02039F74
 bl Spring_Eligibility
.org 0x02039FF0
 bl Spring_Eligibility

; Resident species writer: retain the whole 0x44-byte permanent record; change
; species and vanilla evolution-history levels only. No XP-table conversion,
; implicit nickname change or stat bonus.
; The original 0x0205A288 caller still handles Shedinja and roster allocation.
.org 0x0205A340
.area 0xF0,0
 push {r4,r5,r6,lr}
 sub sp,sp,#0x48
 mov r4,r0
 mov r5,r2
 mov r6,sp
 mov r12,#0x11
Spring_CopyRecord:
 ldr r3,[r1],#4
 str r3,[r6],#4
 subs r12,r12,#1
 bne Spring_CopyRecord
 strh r5,[sp,#4]
 ldrb r0,[sp,#6]
 cmp r0,#0
 ldreqb r0,[sp,#1]
 streqb r0,[sp,#6]
 beq Spring_HistoryDone
 ldrb r0,[sp,#7]
 cmp r0,#0
 ldreqb r0,[sp,#1]
 streqb r0,[sp,#7]
Spring_HistoryDone:
 ldrsh r0,[r4]
 mvn r2,#0
 cmp r0,r2
 beq Spring_NewRecord
 mov r1,sp
 bl 0x02055D7C
 b Spring_RecordDone
Spring_NewRecord:
 mov r0,sp
 bl 0x02055CCC
 strh r0,[r4]
Spring_RecordDone:
 ldrsh r0,[r4]
 add sp,sp,#0x48
 pop {r4,r5,r6,pc}
.endarea
.close

.open "overlay_0016.bin", 0x0238A140
.org SpringCave
.incbin "spring.bin"
.org SpringStubs
Spring_InitStub:
 push {r0-r3,r12,lr}
 bl Spring_Prepare
 pop {r0-r3,r12,lr}
 push {r3,lr}
 b 0x0238C14C
Spring_SubmenuA:
 bl Spring_Submenu
 b 0x0238B0C4
Spring_SubmenuB:
 bl Spring_Submenu
 b 0x0238C0C4
Spring_ActionStub:
 push {r0-r3,r12,lr}
 mov r0,r4
 bl Spring_Action
 cmp r0,#0
 pop {r0-r3,r12,lr}
 bne 0x0238C9B0
 cmp r4,#1
 b 0x0238C580
.org OriginalTargetLabel
 push {r3-r6,lr}
 b 0x0238CB34
.org 0x0238C148
 b Spring_InitStub
.org 0x0238A614 ; state 14: selected Pokemon's submenu, not state 6 entry menu
 b Spring_SubmenuA
.org 0x0238B614
 b Spring_SubmenuB
.org 0x0238C57C
 b Spring_ActionStub
.org 0x0238CBD0
 b Spring_Count
.org 0x0238CB30
 b Spring_TargetLabel
.org 0x0238C484
 bl Spring_Possibilities
.org 0x0238ABB4
 bl Spring_Convert
.org 0x0238BBB4
 bl Spring_Convert
.org 0x0238AB14
 bl Spring_RecordEvolution
.org 0x0238BB14
 bl Spring_RecordEvolution
.org 0x0238AAF8
 mov r0,#0 ; retain even a species-default nickname; skip native auto-renaming
.org 0x0238BAF8
 mov r0,#0
.org 0x0238AC04
 nop ; doping is not a cached stat and must never receive evolution bonuses
.org 0x0238BC04
 nop
.close
