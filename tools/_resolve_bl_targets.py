import re
from pathlib import Path

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
t = PMDSKY.read_text(encoding="utf-8", errors="ignore")

targets = [0x4B678, 0x4B988, 0x4B4EC, 0x4AFC0, 0x56264]
rev = {}
for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
    nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
    if nums:
        rev[nums[0]] = m.group(1)

for tgt in targets:
    print(hex(tgt), rev.get(tgt, "?"))

# search names with ScriptVar GetVar flag performance
for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
    name = m.group(1)
    body = m.group(2)
    if any(k in body.lower() for k in ["performance", "0x4e", "progress_list", "script var"]):
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", body)]
        if nums and nums[0] in (0x4B678, 0x4B988, 0x4B4EC):
            print("match", name, [hex(n) for n in nums[:2]])
