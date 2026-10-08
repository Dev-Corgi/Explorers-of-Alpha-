; US Explorers of Sky — status_adjust (Protect + Endure, Spite/Grudge PP halved, stat stage limits)

ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

; [monster+0xD6] ticked by TickStatusAndHealthRegen (0x02311420) before the holder acts.
; Shared Counter/Mini Counter/Metal Burst inflict (r2 = status id 4/0xA/0xF):
; add r0, r0, #1 after CalcStatusDuration.
.definelabel CounterStatusDurationAddSite,    0x02318E18
.definelabel CounterStatusDurationAddResume,  0x02318E1C

; TryInflictProtectStatus: add r3, r0, #1 after CalcStatusDuration (status id 7).
.definelabel ProtectStatusDurationAddSite,    0x02319278
.definelabel ProtectStatusDurationAddResume,  0x0231927C

; TryInflictMirrorCoatStatus: add r1, r0, #1 after CalcStatusDuration (status id 8).
.definelabel MirrorCoatStatusDurationAddSite,   0x02319330
.definelabel MirrorCoatStatusDurationAddResume, 0x02319334

; TryInflictEndureStatus: add r1, r0, #1 after CalcStatusDuration (status id 9).
.definelabel EndureStatusDurationAddSite,     0x023193CC
.definelabel EndureStatusDurationAddResume,   0x023193D0

; DoMoveSpite loop: strbne r1(=0), [r8, #6] on the target's last-used move (slot flag 0x10).
.definelabel SpitePpZeroSite,                 0x02326860
.definelabel SpitePpZeroResume,               0x02326864

; ExecuteMonsterAction, Grudge ([monster+0x155] set by ApplyDamage):
; strbne r1(=0), [lr, #6] on the attacker's last-used move.
.definelabel GrudgePpZeroSite,                0x022FEC64
.definelabel GrudgePpZeroResume,              0x022FEC68

; CalcDamage: physical + Reflect (status 1) and special + Light Screen (status 3)
; each load the shared fx64 factor. Alpha's factor is 0xCC00/65536 (~79.7% damage).
; Alpha beq's the status hits into an ov36 exclusive-item trampoline that can
; skip the multiply; we retarget those beq's straight at the mul entries.
.definelabel ReflectStatusBranch,            0x0230CCB8
.definelabel ReflectDamageMulEntry,          0x0230CCD0
.definelabel ReflectDamageMulLoad,           0x0230CCDC
.definelabel LightScreenStatusBranch,        0x0230CD04
.definelabel LightScreenDamageMulEntry,      0x0230CD1C
.definelabel LightScreenDamageMulLoad,       0x0230CD28

; Q16.16 floor(65536/3). Damage is multiplied by this, so the hit takes 1/3.
SCREEN_DAMAGE_ONE_THIRD equ 0x5555

MoveSlotPpOff             equ 6

; Stat stages (atk/spa/def/spd at monster+0x24..0x2A, accuracy/evasion at +0x2C/+0x2E).
; Neutral is 10. Vanilla range 0..20 (10 steps each way); this patch uses 10 +- 6.
STAT_STAGE_MIN equ 4
STAT_STAGE_MAX equ 16

; Lower/BoostOffensiveStat, Lower/BoostDefensiveStat: r0 = current stage, r4 = new stage.
.definelabel StatStageLowerOffensiveFloor,          0x023137A8
.definelabel StatStageLowerDefensiveFloor,          0x0231393C
.definelabel StatStageBoostOffensiveCeil,           0x02313AA0
.definelabel StatStageBoostOffensiveCeilNop,        0x02313AA4
.definelabel StatStageBoostDefensiveCeil,           0x02313C0C
.definelabel StatStageBoostDefensiveCeilNop,        0x02313C10
; Boost/LowerHitChanceStat limit checks and clamps.
; 0x0231CE1C raises Atk and Sp. Atk by (max - current).
; 0x0231E818 AI weight, 0x0232DAD0 random pick among stats below max.
; CheckSelf: StatusCheckerCheck (move redundant when the user's stage is at max).
; CheckTarget: StatusCheckerCheckOnTarget (target stage at max, or at min for drops).
.definelabel StatStageBoostHitChanceMaxCheck,       0x0231419C
.definelabel StatStageBoostHitChanceClampCmp,       0x023141B8
.definelabel StatStageBoostHitChanceClampMov,       0x023141BC
.definelabel StatStageLowerHitChanceMinCheck,       0x02314354
.definelabel StatStageLowerHitChanceClampCmp,       0x02314370
.definelabel StatStageLowerHitChanceClampMov,       0x02314374
.definelabel StatStageMaxOffensiveAtk,              0x0231CE38
.definelabel StatStageMaxOffensiveSpa,              0x0231CE54
.definelabel StatStageAiSpAtkWeight,                0x0231E818
.definelabel StatStageRandomPick1,                  0x0232DAFC
.definelabel StatStageRandomPick2,                  0x0232DB0C
.definelabel StatStageRandomPick3,                  0x0232DB24
.definelabel StatStageRandomPick4,                  0x0232DB3C
.definelabel StatStageCheckSelf01,                  0x02333664
.definelabel StatStageCheckSelf02,                  0x02333678
.definelabel StatStageCheckSelf03,                  0x023336B4
.definelabel StatStageCheckSelf04,                  0x023336C8
.definelabel StatStageCheckSelf05,                  0x02333718
.definelabel StatStageCheckSelf06,                  0x02333720
.definelabel StatStageCheckSelf07,                  0x02333784
.definelabel StatStageCheckSelf08,                  0x02333838
.definelabel StatStageCheckSelf09,                  0x02333840
.definelabel StatStageCheckSelf10,                  0x02333888
.definelabel StatStageCheckSelf11,                  0x023338D8
.definelabel StatStageCheckSelf12,                  0x02333B04
.definelabel StatStageCheckSelf13,                  0x02333B18
.definelabel StatStageCheckSelf14,                  0x02333B2C
.definelabel StatStageCheckSelf15,                  0x02333BA0
.definelabel StatStageCheckSelf16,                  0x02333BA8
.definelabel StatStageCheckSelf17,                  0x02333C4C
.definelabel StatStageCheckSelf18,                  0x02333C54
.definelabel StatStageCheckSelf19,                  0x02333CC0
.definelabel StatStageCheckSelf20,                  0x02333CC8
.definelabel StatStageCheckSelf21,                  0x02333E50
.definelabel StatStageCheckSelf22,                  0x02333E58
.definelabel StatStageCheckSelf23,                  0x02333E60
.definelabel StatStageCheckSelf24,                  0x02333E68
.definelabel StatStageCheckSelf25,                  0x02333ED4
.definelabel StatStageCheckSelf26,                  0x02333EDC
.definelabel StatStageCheckSelf27,                  0x02333EE4
.definelabel StatStageCheckSelf28,                  0x02333EEC
.definelabel StatStageCheckSelf29,                  0x02333F48
.definelabel StatStageCheckSelf30,                  0x02333F84
.definelabel StatStageCheckTarget01,                0x0233498C
.definelabel StatStageCheckTarget02,                0x02334994
.definelabel StatStageCheckTarget03,                0x02334B38
.definelabel StatStageCheckTarget04,                0x02334B40
.definelabel StatStageCheckTarget05,                0x02334528
.definelabel StatStageCheckTarget06,                0x02334648
.definelabel StatStageCheckTarget07,                0x02334770
.definelabel StatStageCheckTarget08,                0x02334784
.definelabel StatStageCheckTarget09,                0x02334798
.definelabel StatStageCheckTarget10,                0x023347A0
.definelabel StatStageCheckTarget11,                0x023348A8
.definelabel StatStageCheckTarget12,                0x0233492C
.definelabel StatStageCheckTarget13,                0x02334C78
