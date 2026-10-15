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
entry ME_TowerSpeciesHook
 push {r4,lr}
 ldr r12,=0x023da090
 blx r12
 bl ME_TowerSpecies
 pop {r4,pc}
.ltorg
