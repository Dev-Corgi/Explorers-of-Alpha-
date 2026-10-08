.nds
.arm

.include "common/offsetsUS.asm"
.include "generated.inc"

.open "overlay_0029.bin", ov_29
.org ItemIsActive_00
	b Eq_ItemIsActive
.org ItemIsActive_01
	b Eq_ItemIsActive
.org ItemIsActive_02
	b Eq_ItemIsActive
.org ItemIsActive_03
	b Eq_ItemIsActive
.org ItemIsActive_04
	b Eq_ItemIsActive
.org ItemIsActive_05
	b Eq_ItemIsActive
.org ItemIsActive_06
	b Eq_ItemIsActive
.org ItemIsActive_07
	b Eq_ItemIsActive
.org ItemIsActive_08
	b Eq_ItemIsActive
.org ItemIsActive_09
	b Eq_ItemIsActive
.org ItemIsActive_10
	b Eq_ItemIsActive
.org ItemIsActive_11
	b Eq_ItemIsActive
.org ItemIsActive_12
	b Eq_ItemIsActive

.org AbilityIsActive
	b Eq_Ability
.org CalcDamageEntry
	b Eq_CalcDamage
.org GetTypeMatchupBothTypes
	b Eq_Matchup
.org MunchBellyAdd
	mov r0, r0
.org AccuracyStageLoad
	b Eq_Accuracy
.org EvasionStageLoad
	b Eq_Evasion
.org WeatherBandCheck
	b Eq_Weather
.org TryInflictNightmare
	b Eq_Nightmare
.org TryInflictNapping
	b Eq_Napping
.org TryInflictYawning
	b Eq_Yawning
.org LowerDefensiveContinue
	b Eq_DefDrop
.org GetTypeMatchup
	b Eq_FocusMatchup
.org MoveExecuteEntry
	b Eq_MoveBegin
.org DeepBreatherStep
	b Eq_PpEntry
.org ApplyDamage
	b Eq_ApplyDamage
.org BandStageLoad
	b Eq_BandStage

.org PowerBandFlatSkip
	b PowerBandFlatEnd
.org DefBandFlatSkip
	b DefBandFlatEnd
.org ZincBandFlatSkip
	b ZincBandFlatEnd
.org SpecialBandFlatSkip
	b SpecialBandFlatEnd
.org MunchPhysFlatSkip
	b MunchPhysFlatEnd
.org MunchSpecFlatSkip
	b MunchSpecFlatEnd

.org LockonThrown1
	mov r1, #0
.org LockonThrown2
	mov r1, #0
.org LockonThrown3
	mov r1, #0
.org NoAimThrown
	mov r1, #0
.org BounceThrown1
	mov r1, #0
.org BounceThrown2
	mov r1, #0
.org JoyExpCheck
	mov r1, #0
.org PatsyCritCheck
	mov r1, #0
.org WhiffThrownCheck
	mov r1, #0
.org CurveWallCheck
	mov r1, #0
.org RacketWakeCheck
	mov r1, #0
.org PierceThrown
	mov r1, #0

.org LowerOffensiveStat
	b Eq_DistLowerOff
.org LowerDefensiveStat
	b Eq_DistLowerDef
.org BoostOffensiveStat
	b Eq_DistBoostOff
.org BoostDefensiveStat
	b Eq_DistBoostDef
.org BoostHitChanceStat
	b Eq_DistBoostHit
.org LowerHitChanceStat
	b Eq_DistLowerHit
.close

; The summary screen no longer adds a flat band bonus. Item ids never reach 0x10000.
.open "arm9.bin", 0x02000000
.org PowerBandSummaryCheck
	cmp r0, #0x10000
.org MunchAtkSummaryCheck
	cmp r0, #0x10000
.org SpecialBandSummaryCheck
	cmp r0, #0x10000
.org MunchSpaSummaryCheck
	cmp r0, #0x10000
.org DefBandSummaryCheck
	cmp r0, #0x10000
.org ZincBandSummaryCheck
	cmp r0, #0x10000
.close

.open "overlay_0036.bin", ov_36
.org ov_36 + BetterEquipmentCodeAddress
.include "BetterEquipment.asm"
.close
