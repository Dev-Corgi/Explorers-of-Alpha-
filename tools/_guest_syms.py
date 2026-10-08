import re
from pathlib import Path

p = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
t = p.read_text(encoding="utf-8", errors="ignore")
for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
    name = m.group(1)
    body = m.group(2)
    dm = re.search(r'"([^"]*)"\s*,\s*"([^"]*)"', body)
    if not dm:
        continue
    addr, desc = dm.group(1), dm.group(2)
    blob = (name + " " + desc).lower()
    if any(k in blob for k in ["guest", "performance", "team_member", "active_team", "party", "team_level", "scale"]):
        print(f"{name}\t{addr}\t{desc[:120]}")
