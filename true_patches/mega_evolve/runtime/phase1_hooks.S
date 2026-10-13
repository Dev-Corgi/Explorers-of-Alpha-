#include "generated.h"
.syntax unified
.arm
.text
.macro entry name
 .global \name
 .type \name,%function
\name:
.endm

entry ME_OriginalApparentWeather
 push {r4,lr}
 ldr pc,=0x02334d0c

entry ME_ApparentWeatherHook
 b ME_ApparentWeather

entry ME_HitAttackerSpeedHook
 push {r4,lr}
 mov r4,r0
 ldr r12,=ENTITY_SPEED
 blx r12
 mov r1,r0
 mov r0,r4
 mov r2,r6
 mov r3,#0
 bl ME_GetSpeed
 pop {r4,pc}

entry ME_HitDefenderSpeedHook
 push {r4,lr}
 mov r4,r0
 ldr r12,=ENTITY_SPEED
 blx r12
 mov r1,r0
 mov r0,r4
 mov r2,r7
 mov r3,#0
 bl ME_GetSpeed
 pop {r4,pc}

entry ME_FromMonsterPrior
 push {r4,r5,r6,lr}
 ldr pc,=FROM_MONSTER_RESUME

entry ME_FromMonsterHook
 push {r4,r5,r6,lr}
 mov r4,r0
 mov r5,r2
 bl ME_FromMonsterPrior
 mov r1,r0
 mov r0,r4
 mov r2,r5
 bl ME_WeatherDefense
 pop {r4,r5,r6,pc}

entry ME_WeatherSelectHook
 push {r0-r4,lr}
 bl ME_ForcedWeather
 cmp r0,#0
 movge r5,r0
 pop {r0-r4,lr}
 cmp r5,#0
 ldr pc,=0x02335550

entry ME_SunPowerHook
 push {r0,r1,r3,lr}
 mov r0,r10
 bl ME_WeatherPower
 mov r2,r0
 pop {r0,r1,r3,pc}

entry ME_RainPowerHook
 b ME_SunPowerHook

entry ME_OriginalWeatherMessage
 push {r1,lr}
 ldr pc,=0x023bf970

entry ME_WeatherMessageHook
 b ME_WeatherMessage

entry ME_WeatherFailureHook
 push {r0,r1,r3,lr}
 bl ME_WeatherFailure
 mov r2,r0
 pop {r0,r1,r3,pc}

entry ME_SubInitMonsterHook
 push {r0-r3,r12,lr}
 bl ME_ResetMonster
 pop {r0-r3,r12,lr}
 push {r3-r11,lr}
 ldr pc,=0x022fddc4

entry ME_ResetSpeedHook
 push {r0-r3,r12,lr}
 mov r0,r6
 bl ME_ResetSpeed
 orr r4,r4,r0
 pop {r0-r3,r12,lr}
 cmp r4,#0
 ldr pc,=0x023196dc
.ltorg
