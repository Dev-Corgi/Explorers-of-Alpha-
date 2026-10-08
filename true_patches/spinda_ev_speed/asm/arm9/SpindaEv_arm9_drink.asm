; APPLY hook → ExtraBits @ A3550. Mask stays in arm9 cave.

.org SpindaEvGummiMaskHook
	bl EvDrinkMaskAndInc
	b SpindaEvGummiMaskJoin

.org SpindaEvGummiApplyHook
	bl SpindaEvResetCaveAddress
