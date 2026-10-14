#include "phase6_generated_asm.h"
.syntax unified
.arm
.text
.global ME_SpringInitStub
ME_SpringInitStub:
 push {r0-r3,ip,lr}
 bl ME_Spring_Prepare
 pop {r0-r3,ip,lr}
 push {r3,lr}
 ldr pc,=0x0238c14c
.global ME_SpringSubmenuA
ME_SpringSubmenuA:
 bl ME_Spring_Submenu
 ldr pc,=0x0238b0c4
.global ME_SpringSubmenuB
ME_SpringSubmenuB:
 bl ME_Spring_Submenu
 ldr pc,=0x0238c0c4
.global ME_SpringActionStub
ME_SpringActionStub:
 push {r0-r3,ip,lr}
 mov r0,r4
 bl ME_Spring_Action
 cmp r0,#0
 pop {r0-r3,ip,lr}
 ldrne pc,=0x0238c9b0
 cmp r4,#1
 ldr pc,=0x0238c580
.global ME_SpringNativeTargetLabel
ME_SpringNativeTargetLabel:
 push {r3-r6,lr}
 ldr pc,=0x0238cb34
