import re
from pathlib import Path

t = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py").read_text(
    encoding="utf-8", errors="ignore"
)
for name in [
    "GetPerformanceFlagWithChecks",
    "CheckTeamMemberIdx",
    "GetPartyMembers",
    "GetActiveTeamMember",
    "AddGuestMonster",
    "GuestMonsterToGroundMonster",
    "GUEST_MONSTER_DATA",
    "TEAM_MEMBER_TABLE",
    "GetLevel",
    "SetLevel",
    "InitDungeonMonsters",
    "GenerateFixedFloorMonsters",
]:
    m = re.search(rf"{name}\s*=\s*Symbol\((.*?)\)\n\n", t, re.S)
    if not m:
        print(name, "MISSING")
        continue
    dm = re.search(r'"([^"]*)"', m.group(1))
    print(name, dm.group(1) if dm else "?")
