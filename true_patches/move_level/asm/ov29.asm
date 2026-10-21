.org ExecuteMonsterActionHook
bl MoveLevel_ActionStart

.org GetMovePower
bl MoveLevel_GetPower

.org ApplyItemEffectSite
bl MoveLevel_ItemEffect

.org MoveHitEpilogue
b MoveLevel_HitEpilogue

MoveLevel_ActionStart:
push {r0-r3,lr}
mov r0, r9
bl MoveLevel_BeginAction
pop {r0-r3,lr}
bl MoveLevel_PriorActionStart
bx lr

MoveLevel_GetPower:
push {r4-r6,lr}
mov r4, r0
mov r5, r1
bl MoveLevel_PriorGetPower
mov r6, r0
mov r0, r4
mov r1, r5
mov r2, r6
bl MoveLevel_ScalePower
pop {r4-r6,pc}

MoveLevel_HitEpilogue:
push {r0,r6,r7,r11,lr}
mov r2, r0
mov r0, r7
mov r1, r11
bl MoveLevel_OnHit
pop {r0,r6,r7,r11,lr}
add sp, sp, #0xc
pop {r4-r11,pc}

MoveLevel_ItemEffect:
push {r0-r5,lr}
mov r4, r0
mov r5, r1
bl MoveLevel_PriorItemEffect
mov r0, r4
mov r1, r5
bl MoveLevel_ItemGinseng
pop {r0-r5,pc}
