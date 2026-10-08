.nds
.arm

.include "offsets.asm"
.include "generated.inc"

.open "overlay_0036.bin", 0x023A7080
.org KaCaveAddress
.area KaCaveSize
.include "Assemble.asm"
.endarea
.close

.open "arm9.bin", 0x02000000
.org KaOnKeySite
	b Ka_OnKey
.org KaDelSite
	b Ka_Del
.close
