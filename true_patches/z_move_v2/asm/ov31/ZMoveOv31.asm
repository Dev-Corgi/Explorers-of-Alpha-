.open "overlay_0031.bin", 0x02382820

.org ZMoveMenuHook
	b ZMove_Ov31MenuHook

.org ZMoveMoveConfirmHook
	bl ZMove_SetActionFieldDispatch

.org DungeonMenuBeforeMoneyHook
	bl ZMove_DrawThenGetMoney

.close
