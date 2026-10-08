; US Explorers of Alpha - control_mode_enhance

ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

.definelabel DungeonPtrAddr,        0x02353538
.definelabel LeaderPtrAddr,         0x0235355C
.definelabel SwapLeader,            0x023A7388
.definelabel CalcSpeedStageWrapper, 0x022FFF4C
.definelabel SpeedStageGate,        0x023A7300
.definelabel SpeedTableAddr,        0x02352284
.definelabel LeaderMenuFn,           0x022F0EDC
; RunLeaderTurn calls the leader menu after the speed check.
.definelabel CmeLeaderMenuSite,     0x022EC460
.definelabel GetActiveTeamMember,   0x0205638C
.definelabel IsGuestTeamMember,     0x02056228

; Ally turn, the same calls the auto ally loop makes for one party member.
.definelabel GuestSetActorCam,      0x01FFBDF4
.definelabel GuestRefreshLeader,    0x022F92D8
.definelabel GuestAiDecide,         0x02311088
.definelabel GuestEntityValid,      0x022EC608
.definelabel GuestAfterDecide,      0x023026FC
.definelabel GuestArmAi,            0x02307D54
.definelabel GuestPreExecute,       0x02308340
.definelabel GuestExecute,          0x022FE4BC
.definelabel GuestRoundAbort,       0x022EC7E8
.definelabel GuestTickWait,         0x022E0620
.definelabel GuestFollowupExtra,    0x022EF9C8

; Alpha control mode state (ov36 head). 1 = manual, 0 = auto.
; The next byte is the Start-toggle cooldown.
.definelabel CeManualFlag,          0x023A7090

; ExecuteRound entry, the stack adjust before the leader turn. Runs once per
; fractional tick, not when the manual scan restarts on the next ally.
.definelabel CmeRoundEntrySite,     0x022EBD0C
; Ally loop: ldrb r0, [monster, #7]. Non-zero skips that ally.
.definelabel CmeAllySkipSite,       0x022EBDA8

; Alpha control mode code in ov36: every load of monster_slot_ptrs[0] used as the
; home leader.
.definelabel CmeToggleGateSite,     0x023A7144
.definelabel CmeToggleMessageSite,  0x023A7198
.definelabel CmeTurnEndHomeSite,    0x023A71F4
.definelabel CmeAfterTurnHomeSite,  0x023A7354
.definelabel CmeScanHomeSite,       0x023A73F8
.definelabel CmeScanStartSite,      0x023A742C
.definelabel CmeScanLoopSite,       0x023A7430
.definelabel CmeScanStepSite,       0x023A7434
; Scan bails out when the manual flag is 0, which drops into the ally loop.
.definelabel CmeScanStaySite,       0x023A73C4
.definelabel CmeScanGiveTurnSite,   0x023A7494
.definelabel CmeScanEndSite,        0x023A74B0
; Party-slot init at the start of a floor. Original insn is push {r4-r8, lr}.
.definelabel CmeFloorInitSite,      0x022E1640
.definelabel CmeFloorInitResume,    0x022E1644
; RunLeaderTurn, after its push. r0 is still the fractional-turn argument.
.definelabel CmeRunLeaderTurnSite,  0x022EC30C
