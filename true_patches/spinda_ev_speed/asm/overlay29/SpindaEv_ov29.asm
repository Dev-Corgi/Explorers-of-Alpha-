; Dungeon Summary: after vanilla prologue, capture member_index then mov r6,r1.

.org CreateMonsterSummaryFromMonsterBody
	bl SummarySaveFromMonsterHook

.org ApplyGummiBoostsDungeonMode
	b WonderGummi_Entry

.org ApplyGummiBoostsEpilogue
	b WonderGummi_Exit

.org InitTeamMember
	b DungeonStat_OnFloorMember

.org DungeonFree
	b DungeonStat_OnDungeonGroupEnd

.org MoveHitRankSite
	b SpindaEv_ZMoveNeverMiss

.org 0x02317F50
 b EvSave_Protein

.org 0x02317FE4
 b EvSave_Calcium

.org 0x02318078
 b EvSave_Iron

.org 0x0231810C
 b EvSave_Zinc

.org 0x023152E4
 b EvSave_Hp

.org 0x022EC308
 b EvSave_LeaderTurn
