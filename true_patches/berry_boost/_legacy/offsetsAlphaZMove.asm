; Alpha / Z-Move+TMRead base: Chesto & Aspear past Z-Move used end (~1EA4).
; Z-Move cave max ends at 0x02332000 — berries start there (no reservation overlap).
ov_29 equ 0x022DC240

.definelabel ItemJumpAddress, 0x0231CB14
.definelabel EndBurnClassStatus, 0x023061A8
.definelabel TryInflictFocusEnergyStatus, 0x02315D84
.definelabel GenericBerryBellyFill, 0x0234B350
.definelabel ApplyAspearBellyFill, 0x022E3AB4

.definelabel ApplyCheriBerryEffect, 0x0231CBEC
.definelabel ApplyPechaBerryEffect, 0x0231CC18
.definelabel ApplyRawstBerryEffect, 0x0231CC4C

.definelabel ApplyCheriBoostEffect, 0x02330100
.definelabel ApplyPechaBoostEffect, 0x02330200
.definelabel ApplyRawstBoostEffect, 0x02330300
.definelabel ApplyChestoBoostEffect, 0x02332000
.definelabel ApplyAspearBoostEffect, 0x02332100
