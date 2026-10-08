#!/usr/bin/env python3
import re
from pathlib import Path

import yaml

IDS = yaml.safe_load(
    (
        Path(__file__).resolve().parents[1]
        / "true_patches/room_charge_v4/data/target_moves.yaml"
    ).read_text(encoding="utf-8")
)["move_ids"]

WIKI = Path(r"C:\Users\82106\.cursor\projects\c-Working-SkyTemple\agent-tools\058ff33e-241d-4c0b-b2bb-d427dadf94e1.txt")
BULB = Path(r"C:\Users\82106\.cursor\projects\c-Working-SkyTemple\agent-tools\4142d07b-38cb-48d5-b06f-30feac77169c.txt")

names: dict[int, str] = {}

if WIKI.is_file():
    for line in WIKI.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+)\s*\|", line)
        if m:
            names[int(m.group(1))] = m.group(2).strip()

if BULB.is_file():
    text = BULB.read_text(encoding="utf-8")
    for mid in range(560):
        if mid in names:
            continue
        m = re.search(rf"(?:^|\s){mid:03d}\s+0x[0-9A-Fa-f]{{2,4}}\s+\[([^\]]+)\]", text)
        if m:
            names[mid] = m.group(1)

for mid in IDS:
    print(f"{mid:4d}  {names.get(mid, '?')}")
