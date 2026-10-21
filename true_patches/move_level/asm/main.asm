.nds
.relativeinclude on
.arm
.open "arm9.bin", 0x02000000
.include "common/offsetsUS.asm"
.org MoveLevelArm9Code
.include "arm9.asm"
.close

.open "overlay_0029.bin", 0x022DC240
.org MoveLevelOv29Code
.include "ov29.asm"
.close
