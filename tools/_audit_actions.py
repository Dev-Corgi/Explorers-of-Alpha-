import sys, struct, urllib.request, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

# What is action 0x2a / 42 in vanilla?
text = urllib.request.urlopen("https://raw.githubusercontent.com/UsernameFodder/pmdsky-debug/master/headers/types/dungeon_mode/enums.h", timeout=30).read().decode("utf-8","replace")
# search action enum
for m in re.finditer(r"ACTION_[A-Z0-9_]+\s*=\s*(0x[0-9a-fA-F]+|\d+)", text):
    name, val = m.group(0).split("=")
    name=name.strip(); val=val.strip()
    v = int(val, 0)
    if v in (0x26, 0x28, 0x29, 0x2a, 0x2b, 0x31, 0x38, 38, 40, 41, 42, 43, 49, 56):
        print(f"{name} = {v} ({v:#x})")

# Also try actions.h
for path in ["headers/types/dungeon_mode/actions.h", "headers/types/common/enums.h", "headers/types/dungeon_mode/dungeon_mode_enums.h"]:
    try:
        t=urllib.request.urlopen(f"https://raw.githubusercontent.com/UsernameFodder/pmdsky-debug/master/{path}", timeout=20).read().decode("utf-8","replace")
    except Exception as e:
        print(path, e)
        continue
    print("===", path)
    for m in re.finditer(r".{0,40}ACTION_.{0,60}", t):
        s=m.group()
        if any(x in s for x in ["0x2a", "42", "BAG", "TREASURE", "ITEM", "MOVE", "0x26", "0x28", "0x29"]):
            print(s[:100])
