; ov31 hook sites: single-branch stubs only. Handlers live in ov29 cave
; (inline .org code here clobbered mov r0,#0xC @ 0x02384C4C → wrong submenu strings).

.org OrbUseMenuSaveItemSite
	b OrbCharges_SaveItemBeforeFill

.org OrbUseMenuAfterAddSite
	b OrbCharges_AfterAddSubMenuOption

.org OrbUseMenuAfterAddAltSite
	b OrbCharges_AfterAddSubMenuOptionAlt

.pool
