; Disarm the Monster House the leader spawns in. Outlaw hideouts still activate.

.open "overlay_0029.bin", ov_29

.org FloorEntryMonsterHouseSite
	bl NoImmediateHouse_OnFloorEntry

.close

.open "overlay_0036.bin", ov_36

.org ov_36 + NoImmediateHouseCodeAddress

; r0 = leader entity, r1 = force_create_monster_house. Returns as the replaced bl.
NoImmediateHouse_OnFloorEntry:
	push {r4, r5, lr}
	mov r4, r0
	mov r5, r1
	bl IsOutlawMonsterHouseFloor
	cmp r0, #0
	bne NoImmediateHouse_Call
	mov r0, r4
	bl GetTileAtEntity
	ldrb r1, [r0, #7]
	cmp r1, #0xff
	beq NoImmediateHouse_Call
	ldr r2, =DungeonPtr
	ldr r2, [r2]
	add r3, r2, #0x4000
	ldrb r3, [r3, #0xc9]
	cmp r3, #0xff
	beq NoImmediateHouse_Call
	cmp r1, r3
	bne NoImmediateHouse_Call
	mov r0, r3
	bl NoImmediateHouse_ClearRoom
NoImmediateHouse_Call:
	mov r0, r4
	mov r1, r5
	bl FloorEntryTryMonsterHouse
	pop {r4, r5, pc}

; r0 = room index. Clears f_in_monster_house on every tile and forgets the room.
NoImmediateHouse_ClearRoom:
	push {r4, r5, r6, r7, r8, lr}
	mov r4, r0
	ldr r2, =DungeonPtr
	ldr r2, [r2]
	add r3, r2, #0x4000
	mov r1, #0xff
	strb r1, [r3, #0xc9]
	add r2, r2, #0x2e8
	add r2, r2, #0xec00
	mov r3, #ROOM_DATA_STRIDE
	mla r6, r4, r3, r2
	ldrsh r7, [r6, #6]
	ldrsh r8, [r6, #8]
	ldrsh r5, [r6, #4]
NoImmediateHouse_Y:
	cmp r5, r8
	bgt NoImmediateHouse_Done
	ldrsh r4, [r6, #2]
NoImmediateHouse_X:
	cmp r4, r7
	bgt NoImmediateHouse_YNext
	mov r0, r4
	mov r1, r5
	bl GetTile
	ldrh r1, [r0]
	bic r1, r1, #TILE_MONSTER_HOUSE
	strh r1, [r0]
	add r4, r4, #1
	b NoImmediateHouse_X
NoImmediateHouse_YNext:
	add r5, r5, #1
	b NoImmediateHouse_Y
NoImmediateHouse_Done:
	pop {r4, r5, r6, r7, r8, pc}
	.pool

.close
