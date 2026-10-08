; Explorers of Alpha US.

ov_29 equ 0x022DC240
ov_31 equ 0x02382820
ov_36 equ 0x023A7080

.definelabel AddDungeonSubMenuOption, 0x022EB81C
.definelabel SetActionField,          0x022EB408
.definelabel TryIncreaseHp,           0x023152E4
.definelabel ApplyProteinEffect,      0x02317F50
.definelabel ApplyCalciumEffect,      0x02317FE4
.definelabel ApplyIronEffect,         0x02318078
.definelabel ApplyZincEffect,         0x0231810C
.definelabel RemoveEquivItemScan,     0x0200F558

.definelabel GetSubMenuStringIdReadSite, 0x022EB2DC
.definelabel TmReadMenuHook,             0x02384C54

; ItemsMenu: actions 0x12/13/14 open the team target menu; the chosen slot is
; at [sp,#0x44] and the entity at DungeonPtr->+0x12B28[slot].
.definelabel ItemsMenuTargetActionCheck,    0x02384FA0
.definelabel ItemsMenuTargetSelected,       0x02385068
.definelabel ItemsMenuTargetSelectedResume, 0x0238506C
.definelabel ItemsMenuPlainExit,            0x023850C8
.definelabel DungeonPtr,                    0x02353538

.definelabel ExecuteMonsterActionBoostHook,   0x022FE4D8
.definelabel ExecuteMonsterActionBoostResume, 0x022FE4DC

.definelabel DungeonSubMenuCountPtr,  0x0237C918
.definelabel DungeonSubMenuStringIds, 0x0237C922

ACTION_BOOST equ 43
BOOST_AMOUNT equ 3
; Display string 19121 is shown when the submenu code id is 19122.
BOOST_STRING_DISPLAY_BASE equ 19121

StatusActionField equ 0x4A
