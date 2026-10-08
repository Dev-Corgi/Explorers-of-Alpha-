; US Explorers of Sky — no_immediate_house

ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

.definelabel IsOutlawMonsterHouseFloor, 0x0234928C
.definelabel GetTileAtEntity,           0x022E1628
.definelabel GetTile,                   0x023360FC
.definelabel FloorEntryTryMonsterHouse, 0x02305814
.definelabel DungeonPtr,                0x02353538

; RunDungeon floor start: bl FloorEntryTryMonsterHouse(leader, force_create flag).
.definelabel FloorEntryMonsterHouseSite, 0x022DFAC4

; dungeon_generation_info.monster_house_room
MONSTER_HOUSE_ROOM_OFF equ 0x40C9
; room_data[0]
ROOM_DATA_OFF equ 0xEEE8
ROOM_DATA_STRIDE equ 0x1C
TILE_MONSTER_HOUSE equ 0x40
