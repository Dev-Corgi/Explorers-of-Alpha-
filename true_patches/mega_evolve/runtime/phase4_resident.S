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
#ifdef PHASE5
.global ME_ResidentSpriteExternalHook
ME_ResidentSpriteExternalHook:
 cmp r1,#2
 bhi 3f
 ldr ip,=SPRITE_FIRST
 cmp r2,ip
 movge r3,#0
 ldrge pc,=LOAD_NEW_SPRITE
3:
 push {r3-r9,lr}
 ldr pc,=0x0201d594
.global ME_ResidentSpriteSwapHook
ME_ResidentSpriteSwapHook:
 cmp r2,#2
 bhi 2f
 ldr ip,=SPRITE_FIRST
 cmp r3,ip
 ldrge pc,=REPLACE_NEW_SPRITE
2:
 push {r4-r8,lr}
 ldr pc,=0x0201d688
.global ME_ResidentSpritePackHook
ME_ResidentSpritePackHook:
 cmp r1,#2
 bhi 1f
 ldr ip,=SPRITE_FIRST
 cmp r2,ip
 ldrge pc,=LOAD_NEW_SPRITE
1:
 push {r3-r9,lr}
 ldr pc,=0x0201d488
.global ME_ResidentSpriteSizeHook
ME_ResidentSpriteSizeHook:
 ldr r2,=0x3557454d
 ldr r3,[r0]
 cmp r2,r3
 ldreq r0,[r0,#4]
 bxeq lr
 ldrb r2,[r0]
 ldr pc,=0x020204f0
.global ME_ResidentSpriteDecodeHook
ME_ResidentSpriteDecodeHook:
 ldr r3,=0x3557454d
 ldr ip,[r2]
 cmp r3,ip
 beq ME_ResidentDecode
 ldr pc,=0x0201f5cc
.global ME_ResidentSpriteBytesHook
ME_ResidentSpriteBytesHook:
 ldr r2,=FIRST
 cmp r0,r2
 bge ME_ResidentSpriteBytes
 ldr r2,=0x020b09b4
 ldr pc,=0x02052820
#endif
