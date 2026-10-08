; US Explorers of Sky — utility_patch

ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

.definelabel GetTile, 0x023360FC
.definelabel CanSeeTarget, 0x022E274C
.definelabel DIRECTIONS_XY, 0x0235171C

; ShouldLeaderKeepRunning success: mov r0, #1 before the epilogue.
.definelabel ShouldLeaderKeepRunningOkSite, 0x022F35C8
.definelabel ShouldLeaderKeepRunningEpilogue, 0x022F35CC

ENTITY_MONSTER equ 1
MONSTER_INFO_OFF equ 0xB4
IS_NOT_TEAM_MEMBER_OFF equ 6
TILE_MONSTER_OFF equ 0xC
