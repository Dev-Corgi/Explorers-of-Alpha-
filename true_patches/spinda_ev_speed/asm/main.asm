.nds
.arm

.include "common/offsetsUS.asm"

.open "arm9.bin", arm9
.include "arm9/SpindaEv_arm9.asm"
.include "arm9/SpindaEv_arm9_display.asm"
.include "arm9/SpindaEv_arm9_drink.asm"
.include "arm9/SpindaEv_arm9_extrabits.asm"
.include "arm9/SpindaEv_arm9_dungeon_stats.asm"
.include "arm9/SpindaEv_arm9_accuracy_stars.asm"
.close

.open "overlay_0019.bin", ov_19
.include "overlay19/SpindaEv_ov19.asm"
.close

.open "overlay_0029.bin", ov_29
.include "overlay29/SpindaEv_ov29.asm"
.close

.open "overlay_0011.bin", ov_11
.include "overlay11/SpindaEv_ov11.asm"
.close
