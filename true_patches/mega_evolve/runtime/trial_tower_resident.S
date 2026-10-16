/* ov36 is the native shared resident overlay in ground and dungeon modes.
 * These tiny entry points must not dispatch through the dungeon heap loader. */
.syntax unified
.arm
.text
#include "tower_resident_generated.h"
.macro query name, value, prior, instruction
.balign 4
.global \name
\name:
 cmp r0,#TT_DUNGEON
 moveq r0,#\value
 bxeq lr
 \instruction
 ldr pc,=\prior
.endm
query ME_TowerFloors,99,0x0204f580,"cmp r0,#0xb4"
query ME_TowerGroup,TT_GROUP,0x0204f5cc,"cmp r0,#0xb4"
query ME_TowerPreceding,0,0x0204f5e4,"cmp r0,#0xb4"
query ME_TowerGroupFloors,99,0x0204f5fc,"cmp r0,#0xb4"
query ME_TowerSwapId,TT_DUNGEON,0x0206a718,"mov r12,#0"
query ME_TowerSwapIndex,TT_DUNGEON,0x0206a754,"mvn r1,#0"
query ME_TowerMap,TT_MARKER,0x0206a850,"cmp r0,#0xb4"
/* Join the native special-restriction checks AFTER progress/mode checks.
 * Keep the selected dungeon ID intact for unlock checks and actual entry. */
.global ME_TowerEntryFlags
ME_TowerEntryFlags:
 cmp r5,#TT_DUNGEON
 ldreq r0,=0x4001
 popeq {r3-r5,pc}
 cmp r5,#0x26
 ldr pc,=0x0204f428
.global ME_TowerEntryCheck
ME_TowerEntryCheck:
 cmp r9,#TT_DUNGEON
 ldreq r0,=0x4001
 popeq {r3-r9,pc}
 cmp r9,#0x26
 ldr pc,=0x0204f4fc
/* Only the warning selector aliases Zero Isle South. The stack selection,
 * DUNGEON_ENTER variables and dungeon_init must remain Trial Tower. */
.global ME_TowerWarning
ME_TowerWarning:
 ldrsh r1,[sp,#4]
 cmp r1,#TT_DUNGEON
 moveq r1,#TT_SOURCE
 ldr pc,=0x022ddad0
.global ME_TowerName
ME_TowerName:
 ldr r12,=TT_NAME_ALIAS_0
 cmp r1,r12
 ldrne r12,=TT_NAME_ALIAS_1
 cmpne r1,r12
 ldrne r12,=TT_NAME_ALIAS_2
 cmpne r1,r12
 ldrne r12,=TT_NAME_ALIAS_3
 cmpne r1,r12
 ldreq r1,=TT_NAME_ID
 push {r3-r5,lr}
 ldr pc,=0x0202578c
/* Append the new dungeon only to the ordinary main-game departure list.
 * Preserve the list's original 180 IDs and all special-episode/dojo lists. */
.global ME_TowerMenu
ME_TowerMenu:
 push {r0-r3,r5-r12,lr}
 sub sp,sp,#4
 ldr r5,=TT_MENU_PTR
 ldr r5,[r5,#4]
 cmp r5,#0
 beq .Lmenu_done
 cmp r4,#TT_MENU_CAPACITY
 bhs .Lmenu_done
 ldr r0,[r5,#8]
 cmp r0,#0
 bne .Lmenu_done
 mov r0,#TT_DUNGEON
 ldr r12,=0x0204cf9c
 blx r12
 cmp r0,#1
 cmpne r0,#3
 bne .Lmenu_done
 add r1,r5,r4,lsl #1
 mov r2,#TT_DUNGEON
 strh r2,[r1,#0x18]
 add r1,r5,r4,lsl #2
 str r0,[r1,#0x1c4]
 add r4,r4,#1
.Lmenu_done:
 add sp,sp,#4
 pop {r0-r3,r5-r12,lr}
 ldr r0,=TT_MENU_PTR
 ldr pc,=0x022ffe0c
.ltorg
.global ME_TowerResidentEnd
ME_TowerResidentEnd:
