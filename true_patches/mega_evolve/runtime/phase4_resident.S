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
 ldr r3,=FIRST
 cmp r0,r3
 ldrlt r3,=ME_ResidentOrigin
 ldrge r3,=LEARN_SPECIES
 blx r3
 mov r4,r0
 pop {r1-r3,pc}
.global ME_PortraitOrigin
ME_PortraitOrigin:
 push {r0-r4,lr}
 ldrsh r0,[r10]
 ldr r3,=FIRST
 cmp r0,r3
 ldrlt r3,=ME_ResidentOrigin
 ldrge r3,=PORTRAIT_SPECIES
 blx r3
 mov r7,r0
 pop {r0-r4,pc}
.global ME_NameDivide
ME_NameDivide:
 ldr ip,=FIRST
 cmp r0,ip
 blt ME_OriginDivide
 push {r0-r3,r4,lr}
 ldr r3,=NAME_SPECIES
 blx r3
 cmp r0,#0
 beq 4f
 mov r4,r0
 pop {r0-r3}
 mov r0,r4,lsr #16
 mov r1,r4,lsl #16
 mov r1,r1,lsr #16
 ldr r2,=8735
 sub r1,r1,r2
 pop {r4,pc}
4:
 pop {r0-r3,r4,lr}
 b ME_OriginDivide
.global ME_NormalEvolutionHook
ME_NormalEvolutionHook:
 push {r0-r4,lr}
 ldrsh r4,[r0,#4]
 sub r4,r4,#233
 cmp r4,#600
 subge r4,r4,#600
 cmp r4,#0
 cmpne r4,#28
 bne 5f
 ldr r3,=NEW_EVOLUTION
 blx r3
 cmp r0,#0
 pop {r0-r4,lr}
 bxne lr
 b 6f
5:
 pop {r0-r4,lr}
6:
 push {r3-r11,lr}
 ldr pc,=0x02059b1c
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
 ldreq pc,=CHUNK_DECODE
 ldr pc,=0x0201f5cc
.global ME_ResidentSpriteBytesHook
ME_ResidentSpriteBytesHook:
 ldr r2,=FIRST
 cmp r0,r2
 bge ME_ResidentSpriteBytes
 ldr r2,=0x020b09b4
 ldr pc,=0x02052820
#endif
