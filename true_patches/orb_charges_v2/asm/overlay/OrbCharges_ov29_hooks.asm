; ov29 hook stubs only — handlers live in ov36 cave.

.org RemoveUsedItemClearPath
	b OrbCharges_RemoveUsedItemClearHook

.org GetSubMenuStringId_Continue
	b OrbCharges_CheckUseSubMenuString

.org WazaEffectLaunch
	b OrbFx_Dispatch

.org ShouldUsePp
	b OrbFx_ShouldUsePp

.org ResetFloor
	b OrbFx_ResetFloor

.org EndOfTurnCall
	bl OrbFx_EndTurn

.org CalcDamagePowerStore
	b OrbFx_StorePower

.org BuDrainGateSite
	bl OrbFx_DietDrainGate

.org DungeonFree
	b OrbCharges_OnDungeonGroupEnd

.pool
