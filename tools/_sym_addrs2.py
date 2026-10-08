import re
from pathlib import Path

t = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py").read_text(
    encoding="utf-8", errors="ignore"
)
keys = ["PERFORMANCE", "performance", "VAR_PERFORMANCE", "guest", "Guest", "level", "Level", "dungeon", "floor", "party", "team"]
for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
    name = m.group(1)
    body = m.group(2)
    blob = (name + " " + body).lower()
    if any(k.lower() in blob for k in keys):
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", body)]
        if len(nums) >= 2:
            dm = re.search(r'"([^"]*)"\s*,\s*"([^"]*)"', body)
            desc = (dm.group(2) if dm else "")[:100].replace("\n", " ")
            print(f"{name}\t0x{nums[0]:X}\t0x{nums[1]:X}\t{desc}")
