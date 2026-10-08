; US Explorers of Alpha - belly_union

ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

.definelabel DungeonPtrAddr,        0x02353538
.definelabel LeaderPtrAddr,         0x0235355C
.definelabel CeManualFlag,          0x023A7090
.definelabel EntityIsValid,         0x0230F008

.definelabel TryDecreaseBelly,      0x023168D8
.definelabel TryIncreaseBelly,      0x02316BB0
.definelabel SubInitMonster,        0x022FDDC0
TryDecreaseBody equ TryDecreaseBelly + 4
TryIncreaseBody equ TryIncreaseBelly + 4

.definelabel BuDrainGateSite,       0x0230FD0C
.definelabel BuTightScaleSite,      0x0230FD28
.definelabel BuTightContinue,       0x0230FD34
.definelabel BuAfterBellySite,      0x0231013C
.definelabel BuSkipDrainTarget,     0x0231013C
.definelabel BuDecreaseSite,        0x023168D8
.definelabel BuIncreaseSite,        0x02316BB0
.definelabel BuTeamInitSite,        0x022FD62C
.definelabel BuMonsterInitSite,     0x022FDB9C
.definelabel BuSubInitSite,         0x022E0540
.definelabel BuHungerSite,          0x0231CD50
.definelabel BuFillASite,           0x02309E74
.definelabel BuFillBSite,           0x0230A144
.definelabel BuFillCSite,           0x0230A394
.definelabel BuMoveFillSite,        0x0232E7F8
.definelabel BuMoveWriteSite,       0x0232ED08
.definelabel BuMoveSetSite,         0x0232ACD0
.definelabel BuSkipDrainSite,       0x023D6E94
.definelabel ItemIsActive_09,       0x02311034

; Return addresses of ItemIsActive calls inside the walk-drain formula.
; Munch Belt (the call that returns to 0x0230FD84) is included so a second
; copy still reports a count; better_equipment ignores that result.
BuRetTight     equ 0x0230FD28
BuRetStamina   equ 0x0230FD44
BuRetDiet      equ 0x0230FD64
BuRetHeal      equ 0x0230FD74
BuRetMunch     equ 0x0230FD84
BuRetItem18    equ 0x0230FD94
BuRetItem21    equ 0x0230FDA4
BuRetAlpha1    equ 0x023C0E24
BuRetAlpha2    equ 0x023C0E34
BuRetAlpha3    equ 0x023C0E44
BuRetAlpha4    equ 0x023C0E54
BuRetAlpha5    equ 0x023C0E64
