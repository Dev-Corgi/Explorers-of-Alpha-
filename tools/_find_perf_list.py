import re
from pathlib import Path

t = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py").read_text(
    encoding="utf-8", errors="ignore"
)
for pat in ["VAR_PERFORMANCE", "PERFORMANCE_PROGRESS", "PERFORMANCE_LIST", "GAME_MODE", "GetGameDifficulty"]:
    for m in re.finditer(rf"({pat}\w*)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
        name = m.group(1)
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
        if len(nums) >= 2:
            print(name, f"0x{nums[0]:X}", f"0x{nums[1]:X}")
