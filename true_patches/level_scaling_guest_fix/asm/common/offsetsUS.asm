; US Explorers of Sky — level_scaling_guest_fix

arm9 equ 0x02000000
ov_29 equ 0x022DC240
ov_36 equ 0x023A7080

.definelabel CheckTeamMemberIdx, 0x02056264
; 0x55AA / 0x5AA5, and negative member_idx.
.definelabel IsGuestTeamMember, 0x02056228
.definelabel GetActiveTeamMember, 0x0205638C

; ov29 — max-level candidate collection (before str r6, [r4, r7, lsl #2]).
.definelabel LevelScaleCollectStoreSite, 0x022F7A0C
.definelabel LevelScaleCollectLoopNext, 0x022F7A14

; ov29 — party level apply loop (after GetActiveTeamMember).
.definelabel LevelScalePartyLoopAfterGetSite, 0x022F7CEC
.definelabel LevelScalePartyLoopBody, 0x022F7CF0
.definelabel LevelScalePartyLoopNextSlot, 0x022F7DB8

; arm9 — broken per-slot guest check (was bl with slot index 0–3).
.definelabel LevelScaleArm9PerSlotGuestSite, 0x02058680
.definelabel LevelScaleArm9PerSlotContinue, 0x0205868C

; arm9 — dungeon entry scaling loop (after GetActiveTeamMember).
.definelabel LevelScaleArm9DungeonEntryAfterGetSite, 0x02058604
.definelabel LevelScaleArm9DungeonEntryActiveCheck, 0x02058608
.definelabel LevelScaleArm9DungeonEntryNextSlot, 0x02058628

; arm9 — dungeon team stat init (active member path).
.definelabel LevelScaleArm9StatInitProcessSite, 0x02057838
.definelabel LevelScaleArm9StatInitSkipSlot, 0x020578D0

; ov36 — Alpha Level Scaling party-max (level byte +2).
; Hook replaces ldrb r4, [r0] before the level is folded into the max.
; Slot limit was cmp r1,#3 (slots 0–2). Other party walks use cmp #4.
.definelabel LevelScaleAlphaPartyMaxHook, 0x023D9114
.definelabel LevelScaleAlphaPartyMaxUseLevel, 0x023D9120
.definelabel LevelScaleAlphaPartyMaxNext, 0x023D9134
.definelabel LevelScaleAlphaPartyMaxSlotLimit, 0x023D9138

; ov36 — Alpha spawn-list rewrite (ldrb high byte). Kecleon skips this.
.definelabel LevelScaleAlphaSpawnLdrbSite, 0x023D9164
.definelabel LevelScaleAlphaSpawnAfterLdrb, 0x023D9168
.definelabel LevelScaleAlphaSpawnNext, 0x023D9274

; ov29 — GetMonsterLevelToSpawn species compare.
.definelabel GetMonsterLevelCmpSite, 0x022E7E7C
.definelabel GetMonsterLevelCmpContinue, 0x022E7E80
