.balign 4
entry ME_TowerSpawnHook
 push {r4,lr}
 mov r4,r0
 ldr r12,=0x023da080
 blx r12
 mov r0,r4
 bl ME_TowerSpawn
 mov r0,r4
 pop {r4,pc}
entry ME_TowerStatsHook
 cmp r9,#6
 bne .Ltt_stats_done
 push {r0-r3,r12,lr}
 bl ME_TowerStats
 pop {r0-r3,r12,lr}
.Ltt_stats_done:
 ldrb r0,[r8]
 ldr pc,=0x023438c0
.ltorg
entry ME_TowerSelectHook
 push {r0-r3,r12,lr}
 bl ME_TowerChooseKey
 cmp r0,#0
 beq .Ltt_old_key
 strb r0,[r7,#0x12]
 pop {r0-r3,r12,lr}
 ldr pc,=0x023dbbf8
.Ltt_old_key:
 pop {r0-r3,r12,lr}
 mov r0,#12
 ldr pc,=0x023dbbd8
.ltorg
entry ME_TowerFloorHook
 push {r0-r3,r12,lr}
 bl ME_TowerFloorReset
 pop {r0-r3,r12,lr}
 push {r3-r11,lr}
 ldr pc,=0x022e6fc0
.ltorg
entry ME_TowerFixedLoadedHook
 push {r0-r3,r12,lr}
 bl ME_TowerFixedLoaded
 pop {r0-r3,r12,lr}
 pop {r3,pc}
.ltorg
/* Keep the caller's two stack arguments at the native offsets. */
entry ME_TowerItemHook
 push {r0-r3,r12,lr}
 add r3,sp,#24
 bl ME_TowerItem
 str r0,[sp]
 pop {r0-r3,r12,lr}
 ldr pc,=0x02344430
.ltorg
entry ME_TowerTeamHook
 push {r4,lr}
 ldr r12,=0x022fc50c
 blx r12
 mov r4,r0
 bl ME_TowerResolveReward
 mov r0,r4
 pop {r4,pc}
.ltorg
entry ME_TowerSpeciesHook
 push {r4,lr}
 ldr r12,=0x023da090
 blx r12
 bl ME_TowerSpecies
 pop {r4,pc}
.ltorg
