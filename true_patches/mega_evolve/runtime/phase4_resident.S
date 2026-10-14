#include "phase4_resident_generated.h"
.syntax unified
.arm
.text
.global ME_OriginDivide
ME_OriginDivide:
 push {r1-r3,lr}
 bl ME_ResidentOrigin
 pop {r1-r3,lr}
 ldr pc,=0x0208fea4
.global ME_LearnOrigin
ME_LearnOrigin:
 push {r1-r3,lr}
 bl ME_ResidentOrigin
 mov r4,r0
 pop {r1-r3,pc}
.global ME_PortraitOrigin
ME_PortraitOrigin:
 push {r0-r4,lr}
 ldrsh r0,[r10]
 bl ME_ResidentOrigin
 mov r7,r0
 pop {r0-r4,pc}
.global ME_ValidSpecies
ME_ValidSpecies:
 push {r0-r2,lr}
 bl ME_ResidentValid
 cmp r0,#0
 strge r0,[sp]
 pop {r0-r2,lr}
 bxge lr
 push {r3,lr}
 ldr pc,=0x02054770
.global ME_SpriteCacheIndex
ME_SpriteCacheIndex:
 push {r1-r3,lr}
 bl ME_ResidentAsset
 pop {r1-r3,lr}
 ldr r2,=0x02353538
 ldr pc,=0x022f738c
.global ME_LoadAsset
ME_LoadAsset:
 push {r1-r3,lr}
 bl ME_ResidentAsset
 mov r6,r0
 pop {r1-r3,pc}
.global ME_StoreAsset
ME_StoreAsset:
 push {r1-r3,lr}
 bl ME_ResidentAsset
 mov r7,r0
 pop {r1-r3,pc}
.global ME_DeleteAsset
ME_DeleteAsset:
 push {r1-r3,lr}
 bl ME_ResidentAsset
 mov r5,r0
 pop {r1-r3,pc}
