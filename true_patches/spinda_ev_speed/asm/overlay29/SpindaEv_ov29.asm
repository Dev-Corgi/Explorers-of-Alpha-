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
