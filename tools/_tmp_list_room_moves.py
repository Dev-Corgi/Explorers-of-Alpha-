import re
from pathlib import Path

IDS = [
    82, 101, 112, 113, 118, 131, 149, 150, 168, 219, 230, 238, 256, 270, 278, 296,
    361, 362, 437, 460, 484, 521, 523, 538, 554,
]
WIKI = Path(__file__).resolve().parents[1] / ".cursor" / "agent-tools" / "058ff33e-241d-4c0b-b2bb-d427dadf94e1.txt"
if not WIKI.is_file():
    WIKI = Path(r"C:\Users\82106\.cursor\projects\c-Working-SkyTemple\agent-tools\058ff33e-241d-4c0b-b2bb-d427dadf94e1.txt")

found: dict[int, str] = {}
if WIKI.is_file():
    for line in WIKI.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+)\s*\|", line)
        if m:
            mid = int(m.group(1))
            if mid in IDS:
                found[mid] = m.group(2).strip()

for mid in IDS:
    print(f"{mid:4d}  {found.get(mid, '?')}")

missing = [m for m in IDS if m not in found]
if missing:
    print("missing:", missing)
