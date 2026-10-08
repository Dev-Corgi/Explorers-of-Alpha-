.nds
.arm

.include "common/offsetsUS.asm"

.open "overlay_0029.bin", ov_29
.include "overlay/OrbCharges_ov29_hooks.asm"
.close

.open "overlay_0036.bin", ov_36
.include "overlay/OrbCharges_ov36.asm"
.close

.open "overlay_0031.bin", ov_31
.include "overlay/OrbCharges_ov31.asm"
.close
