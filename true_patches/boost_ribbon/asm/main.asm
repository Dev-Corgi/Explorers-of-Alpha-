.nds
.arm

.include "common/offsetsUS.asm"
.include "generated.inc"

.open "overlay_0029.bin", ov_29
.org GetSubMenuStringIdReadSite
	b Boost_CheckString
.org ExecuteMonsterActionBoostHook
	b Boost_ExecHook
.close

.open "overlay_0031.bin", ov_31
.org TmReadMenuHook
	b Boost_MenuHook
.org ItemsMenuTargetActionCheck
	bl Boost_TargetActionCmp
.org ItemsMenuTargetSelected
	b Boost_TargetSelected
.close

.open "overlay_0036.bin", ov_36
.org ov_36 + BoostRibbonCodeAddress
.include "BoostRibbon.asm"
.close
