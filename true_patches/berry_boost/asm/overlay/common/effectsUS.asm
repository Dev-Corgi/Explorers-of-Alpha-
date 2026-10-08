; Vanilla overlay29 stat-boost APIs (Z-Move berry pattern).

.definelabel BoostOffensiveStat,  0x0231399C
.definelabel BoostDefensiveStat,  0x02313B08
.definelabel FocusStatUp,         0x023140E4
.definelabel Sleepless,           0x02311F80

OFFENSIVE_STAT_ATTACK         equ 0
OFFENSIVE_STAT_SP_ATTACK      equ 1
DEFENSIVE_STAT_DEFENSE        equ 0
DEFENSIVE_STAT_SP_DEFENSE     equ 1
FOCUS_STAT_ACCURACY           equ 0
FOCUS_STAT_EVASION            equ 1
BERRY_STAT_STAGES             equ 2

; GenericBerryBellyFill message token (vanilla ApplyCheriBerryEffect literal pool).
BERRY_BELLY_MSG               equ 0xBE9
