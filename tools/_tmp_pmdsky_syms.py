"""Dump pmdsky NA symbols related to ability power/damage."""
from __future__ import annotations

import re
from pathlib import Path

p = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
t = p.read_text(encoding="utf-8", errors="ignore")
out = []
for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
    name = m.group(1)
    body = m.group(2)
    dm = re.search(r'"([^"]*)"\s*,\s*"([^"]*)"', body)
    if not dm:
        continue
    sym, desc = dm.group(1), dm.group(2)
    blob = (name + " " + desc).lower()
    keys = [
        "technician",
        "tinted_lens",
        "solid_rock",
        "filter",
        "sniper",
        "adaptab",
        "overgrow",
        "blaze",
        "torrent",
        "swarm",
        "huge_power",
        "pure_power",
        "iron_fist",
        "reckless",
        "hustle",
        "rivalry",
        "guts",
        "flash_fire",
        "thick_fat",
        "heatproof",
        "dry_skin",
        "solar_power",
        "flower_gift",
        "download",
        "slow_start",
        "scrappy",
        "type_matchup",
        "super-effective",
        "not-very",
        "stab",
        "damage multi",
        "power thresh",
        "power boost",
        "ability",
        "half damage",
        "1.5",
        "50%",
    ]
    if any(k in blob for k in keys) or "MULTIPLIER" in name or "THRESHOLD" in name:
        out.append(f"{name}: {desc.replace(chr(10), ' ')[:300]}")

Path(r"C:\Working\SkyTemple\tools\_tmp_pmdsky_power_syms.txt").write_text(
    "\n---\n".join(out), encoding="utf-8"
)
print(len(out), "symbols")
