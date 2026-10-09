ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

; Existing Alpha code sites / functions, not locations for new code caves.
BugFixHailRegenBonusSite equ 0x023111F0
BugFixMirrorAttackSite equ 0x023BB0B0
BugFixMirrorDefenseSite equ 0x023BB10C
BugFixMirrorHitChanceSite equ 0x023BB168
BugFixTraceAbilityReadSite equ 0x022F9538
BugFixGasSuppressionSite equ 0x023C03A8

MirrorAttackResume equ 0x023BB0CC
MirrorDefenseResume equ 0x023BB128
MirrorHitChanceResume equ 0x023BB184
AlphaStatChangeSource equ 0x023BB478
AlphaStatChangeTarget equ 0x023BB47C
MirrorArmorMessagePool equ 0x023BB3C4
TraceAbilityReadContinue equ 0x022F953C
TraceSlotCheckContinue equ 0x022F9554
AbilitySuppressionContinue equ 0x02301D08

AbilityIsActiveVeneer equ 0x02301D78
IsMonster equ 0x02301A60
LogMessageById equ 0x0234B2A4
DungeonPtr equ 0x02353538
NEUTRALIZING_GAS equ 0xA0
TRACE equ 0x28
