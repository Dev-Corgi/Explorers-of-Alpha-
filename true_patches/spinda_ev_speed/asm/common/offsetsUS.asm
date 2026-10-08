; US Explorers of Sky — Spinda Cafe EV for the CalcStat / Spe V stack.
; Dynamic caves: SpindaEvArm9CodeAddress, SpindaEvResetCaveAddress, SpindaEvTeamSubmenuTable (generated.inc).
; Summary/Drink scratch: dungeon stat cave +0x480 (generated.inc); without that cave, fixed @ 9FB30.
.arm

.include "generated.inc"

arm9 equ 0x02000000
ov_19 equ 0x0238A140
ov_29 equ 0x022DC240
ov_11 equ 0x022DC240

.definelabel GetTeamMember,           0x020555A8
.definelabel GetActiveTeamMember,     0x0205638C
.definelabel GetMonsterInfoForSave,   0x02059118
.definelabel GetMonsterInfoForSaveBody, 0x0205911C
.definelabel GetBaseHp,               0x02052934
.definelabel GetBaseOffensiveStat,    0x020529C4
.definelabel GetBaseDefensiveStat,    0x020529E4
.definelabel GetLvlUpEntry,           0x0205379C

.definelabel SpindaCafeStatePtr, 0x02324DB0

.definelabel PreprocessStringFromId,     0x020235B8
.definelabel GetStringFromFileVeneer,    0x020258B8
.definelabel Strcat,                     0x020897AC
.definelabel EvDrinkRoseNewline,         0x0238E2C0
.definelabel SummaryLayoutCall,          0x02026214

.definelabel SetStringAccuracy,          0x02024360
.definelabel GetMoveField,               0x020A5F40
.definelabel MoveDescStartID,            0x000027A2
.definelabel MoveDescEndID,              0x000029D1
.definelabel NullString,                 0x02099D50
.definelabel StarString,                 0x02099D84
.definelabel HalfStarString,             0x020A3544

.definelabel CreateMonsterSummarySaveHook, 0x0205AE30
.definelabel CreateMonsterSummaryFromMonster, 0x022F89CC
.definelabel CreateMonsterSummaryFromMonsterBody, 0x022F89D0

.definelabel SpindaEvDrinkMenuOpenHook,  0x0238ABC0
.definelabel SpindaEvVanillaDrinkHelper, 0x0238D418
; Stat submenu create: r2 = table, stack[0] = initial row index (s8).
.definelabel SpindaEvStatSubmenuOpenHook, 0x0238AB94
.definelabel SpindaEvTeamSubmenuCreate,   0x0238D3A0
.definelabel SpindaEvDrinkSelectHook,    0x0238ABC4
.definelabel SpindaEvDrinkOutcomeHook,   0x0238B204
.definelabel SpindaEvGummiMaskHook,      0x020119B4
.definelabel SpindaEvGummiMaskJoin,      0x020119EC
.definelabel SpindaEvGummiApplyHook,     0x020119EC
.definelabel EvDrinkSnapHpSpeHook,       0x0238BA88
.definelabel EvDrinkSnapHpAfterHook,     0x0238BAE8
.definelabel EvDrinkAppendHpSpeMsgHook,  0x0238BC98
.definelabel GroundAddMaxHp,             0x02054FB8
.definelabel GroundAddOffensiveStat,     0x02054FEC
.definelabel GroundAddDefensiveStat,     0x02055020

SPINDA_RESET_CAVE_MAX equ 0x3B0

; v2: caps computed at runtime — floor(level/10)*5 per stat, floor(level/10)*13 total.
EV_STAT_CAP_MULT equ 5
EV_EARNED_CAP_MULT equ 13
EV_LEVEL_DIVISOR equ 10

.definelabel SpindaCafeApplyGummiCall,   0x0238BAE0

.definelabel SummarySuffixHookHp,          0x0205A5B4
.definelabel SummarySuffixHookAtkBoost,    0x0205A670
.definelabel SummarySuffixHookSpaBoost,    0x0205A6B4
.definelabel SummarySuffixHookSpaNorm,     0x0205A6E0
.definelabel SummarySuffixHookAtkNorm,     0x0205A710
.definelabel SummarySuffixHookDef,         0x0205A75C
.definelabel SummarySuffixHookSpd,         0x0205A7CC

EV_TEAM_COUNT equ 555

.definelabel SpindaEvTeamSubmenuMenuPtr, 0x0238B474

; Dungeon eat: ApplyGummiBoostsDungeonMode. r2 == 0xFF is Wonder Gummi.
.definelabel ApplyGummiBoostsDungeonMode, 0x0231D0C0
.definelabel ApplyGummiBoostsAfterPrologue, 0x0231D0C4
.definelabel ApplyGummiBoostsEpilogue, 0x0231D460
.definelabel ApplyProteinEffect, 0x02317F50
.definelabel RefreshEntityAfterStatChange, 0x022E3AB4
.definelabel InitTeamMember, 0x022FD3B4
.definelabel InitTeamMemberBody, 0x022FD3B8
.definelabel GetCoroutineInfo, 0x022E7FB8
.definelabel GetCoroutineInfoBody, 0x022E7FBC
.definelabel DungeonFree, 0x022DEAB0
.definelabel DungeonFreeBody, 0x022DEAB4
.definelabel DungeonFloorToGroupFloor, 0x0204F64C
.definelabel GetNbFloorsDungeonGroup, 0x0204F5F8
.definelabel DungeonMasterPtr, 0x02353538
DUNGEON_ID_FLOOR_OFF equ 0x748
DUNGEON_GROUP_FLOOR_OFF equ 0x74B
DAMAGE_SOURCE_DUNGEON_CLEAR equ 634
.definelabel MoveHitRankSite, 0x02323F94
.definelabel MoveHitEpilogue, 0x02324008
.definelabel GravityIsActive, 0x02338390
.definelabel S32DivF, 0x0208FEA4
MoveDataMoveIdOff equ 4
Z_MOVE_SHELL_ID equ 559
WONDER_GUMMI_TYPE equ 0xFF
WONDER_GUMMI_ALL_STAT equ 3
WONDER_GUMMI_HP_CAP equ 999
; ApplyCalcium/Iron/Zinc follow Protein by this stride.
WONDER_GUMMI_STAT_FN_STRIDE equ 0x94

; Drink submenu: display id N shown when table halfword is N+1.
EV_STR_MENU_DISPLAY_BASE equ 19300
EV_STR_MENU_MAX_V        equ 50
EV_STR_MENU_STAT_STRIDE  equ 51
EV_STR_MENU_HP_CODE_BASE equ 19301
EV_STR_MENU_ATK_CODE_BASE equ 19352
EV_STR_MENU_SPA_CODE_BASE equ 19403
EV_STR_MENU_DEF_CODE_BASE equ 19454
EV_STR_MENU_SPD_CODE_BASE equ 19505
EV_STR_MENU_SPE_CODE_BASE equ 19556
EV_STR_MENU_RESET_CODE   equ 19607

EV_STR_SUMMARY_SUFFIX_HP  equ 19240
EV_STR_SUMMARY_SUFFIX_ATK equ 19241
EV_STR_SUMMARY_SUFFIX_SPA equ 19242
EV_STR_SUMMARY_SUFFIX_DEF equ 19243
EV_STR_SUMMARY_SUFFIX_SPD equ 19244
; Drink result: GetStringFromFile / PreprocessStringFromId are 1-based.
EV_STR_ROSE_TEMPLATE_CODE equ 17895
EV_STR_NAME_HP_CODE       equ 19246
EV_STR_NAME_SPE_CODE      equ 19247
