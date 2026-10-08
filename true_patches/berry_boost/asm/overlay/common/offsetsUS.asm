ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

.definelabel ItemJumpAddress, 0x0231CB14
.definelabel EndBurnClassStatus, 0x023061A8
.definelabel TryInflictFocusEnergyStatus, 0x02315D84
.definelabel GenericBerryBellyFill, 0x0234B350
.definelabel ApplyAspearBellyFill, 0x022E3AB4

.definelabel ApplyCheriBerryEffect, 0x0231CBEC
.definelabel ApplyPechaBerryEffect, 0x0231CC18
.definelabel ApplyRawstBerryEffect, 0x0231CC4C
.definelabel ApplyChestoBerryEffect, 0x0231CC78

.definelabel ApplyItemEffect_ItemCdLoader, 0x0231B9A8
.definelabel ApplyItemEffect_ItemCdLoaderBody, 0x0231B9AC
.definelabel ApplyViolentSeedEffect, 0x0231CE1C

ASPEAR_ITEM_ID equ 344

; Pattern B cave helpers -> generated.inc

.include "generated.inc"
