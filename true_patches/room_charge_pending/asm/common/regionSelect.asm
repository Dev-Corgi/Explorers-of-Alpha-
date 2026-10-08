.relativeinclude on
_REGION equ "US"

.relativeinclude off
.if _REGION == "US"
	.notice "RoomCharge patch: USA"
.else
	.error "RoomCharge patch currently supports US ROMs only"
.endif

.include "offsetsUS.asm"
.include "generated.inc"
