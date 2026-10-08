import re
from pathlib import Path

t = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py").read_text(
    encoding="utf-8", errors="ignore"
)
keys = ["level", "Level", "scale", "Scale", "guest", "Guest", "team", "Team", "enemy", "Enemy", "floor", "Floor", "spawn", "Spawn", "dungeon", "Dungeon"]
for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
    name = m.group(1)
    body = m.group(2)
    if not any(k in name or k in body for k in keys):
        continue
    if any(k in (name + body).lower() for k in ["level", "scale", "guest", "team level", "enemy level", "floor level", "reset level", "mon level", "party"]):
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", body)]
        if len(nums) >= 2:
            dm = re.search(r'"([^"]*)"\s*,\s*"([^"]*)"', body)
            desc = (dm.group(2) if dm else "")[:120].replace("\n", " ")
            print(f"{name}\t0x{nums[0]:X}\t{desc}")
