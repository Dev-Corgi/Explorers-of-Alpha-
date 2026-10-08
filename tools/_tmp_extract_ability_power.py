"""Extract ability names/descriptions related to move power from text_e.str."""
from __future__ import annotations

import re
from pathlib import Path

OUT = Path(r"C:\Working\SkyTemple\tools\_tmp_ability_power_report.txt")
STR = Path(r"C:\Working\SkyTemple\unpacked\nitrofs\MESSAGE\text_e.str")

data = STR.read_bytes().decode("latin-1")
# SkyTemple string files often use length-prefixed or null-separated blocks.
# Prefer null-split first; also keep raw for regex context.
parts = data.split("\x00")
print(f"null-split parts: {len(parts)}")

KNOWN = [
    "Technician",
    "Huge Power",
    "Pure Power",
    "Tough Claws",
    "Iron Fist",
    "Reckless",
    "Strong Jaw",
    "Mega Launcher",
    "Sand Force",
    "Sheer Force",
    "Analytic",
    "Rivalry",
    "Hustle",
    "Defeatist",
    "Toxic Boost",
    "Flare Boost",
    "Overgrow",
    "Blaze",
    "Torrent",
    "Swarm",
    "Adaptability",
    "Neuroforce",
    "Stakeout",
    "Sharpness",
    "Water Bubble",
    "Steelworker",
    "Gorilla Tactics",
    "Solar Power",
    "Flower Gift",
    "Guts",
    "Flash Fire",
    "Thick Fat",
    "Heatproof",
    "Dry Skin",
    "Sniper",
    "Tinted Lens",
    "Unaware",
    "Slow Start",
    "Normalize",
    "Parental Bond",
    "Beast Boost",
    "Soul-Heart",
    "Moxie",
    "Download",
    "Plus",
    "Minus",
    "Scrappy",
    "Mold Breaker",
    "Teravolt",
    "Turboblaze",
    "Justified",
    "Anger Point",
    "Defiant",
    "Competitive",
    "Intimidate",
    "Quick Feet",
    "Marvel Scale",
    "Sap Sipper",
    "Storm Drain",
    "Motor Drive",
    "Water Absorb",
    "Volt Absorb",
    "Punk Rock",
    "Transistor",
    "Dragon's Maw",
    "Aerilate",
    "Pixilate",
    "Refrigerate",
    "Galvanize",
    "Solid Rock",
    "Filter",
    "Multiscale",
    "Lightningrod",
    "Lightning Rod",
    "Rattled",
    "Power Spot",
    "Battery",
    "Friend Guard",
    "Aura Break",
    "Fairy Aura",
    "Dark Aura",
    "Quark Drive",
    "Protosynthesis",
    "Orichalcum Pulse",
    "Hadron Engine",
    "Vessel of Ruin",
    "Sword of Ruin",
    "Tablets of Ruin",
    "Beads of Ruin",
    "Sharpness",
    "Rocky Payload",
    "Supreme Overlord",
    "Cud Chew",
    "Wind Power",
    "Wind Rider",
    "Electromorphosis",
    "Well-Baked Body",
    "Thermal Exchange",
    "Toxic Debris",
    "Guard Dog",
    "Zero to Hero",
    "Commander",
    "Embody Aspect",
    "Toxic Chain",
    "Supersweet Syrup",
    "Hospitality",
    "Mind's Eye",
    "Seed Sower",
    "Anger Shell",
    "Cleanse",
    "Purifying Salt",
    "Lingering Aroma",
    "Good as Gold",
    "Mycelium Might",
    "Opportunist",
    "Costar",
    "Earth Eater",
    "Toxic Boost",
    "Flare Boost",
    "Sheer Force",
]

POWER_RE = re.compile(
    r"(boosts? the power|power of (?:its |the )?moves?|Attack power|"
    r"increases? (?:the )?(?:power|damage)|more powerful|powers? up|"
    r"doubles? (?:its |the )?(?:Attack|power|damage)|"
    r"halves? (?:the )?(?:power|damage|Attack)|"
    r"reduces? (?:the )?(?:power|damage)|"
    r"weakens? (?:the )?(?:power|damage)|"
    r"damage (?:dealt|inflicted)|"
    r"stronger (?:moves?|attacks?)|"
    r"moves? (?:become|are) (?:more )?(?:powerful|stronger)|"
    r"physical moves|special moves|contact moves|"
    r"punching moves|biting moves|pulse moves|aura moves|"
    r"slicing moves|sound moves|recoil|"
    r"base power|move power|"
    r"power (?:<=|≤|less than|of 60|of 50|below))",
    re.I,
)

# Build index of short name strings
name_hits: list[tuple[int, str]] = []
desc_hits: list[tuple[int, str]] = []
for i, s in enumerate(parts):
    t = s.strip("\x00")
    if not t:
        continue
    # strip common control tags for matching
    plain = re.sub(r"\[[^\]]+\]", "", t)
    plain = plain.replace("\r", " ").replace("\n", " ")
    is_known = any(k == plain.strip() or k in plain for k in KNOWN if len(k) > 2)
    # Ability names are typically short single-line
    if len(plain.strip()) < 36 and "\n" not in t and POWER_RE.search(plain) is None:
        if plain.strip() in KNOWN or any(plain.strip() == k for k in KNOWN):
            name_hits.append((i, plain.strip()))
    if POWER_RE.search(t) or POWER_RE.search(plain):
        desc_hits.append((i, t[:500].replace("\r", "\\r").replace("\n", "\\n")))

# Broader: find all ability-like name/desc pairs by scanning for known names as exact short strings
exact_names = []
for i, s in enumerate(parts):
    plain = re.sub(r"\[[^\]]+\]", "", s).strip()
    if plain in KNOWN:
        exact_names.append((i, plain))

lines: list[str] = []
lines.append(f"=== Exact known ability name string indices ({len(exact_names)}) ===")
for i, n in exact_names:
    lines.append(f"[{i}] {n}")
    # look ahead for description (next non-empty nearby)
    for j in range(i + 1, min(i + 6, len(parts))):
        d = parts[j].strip()
        if not d:
            continue
        if len(d) > 20:
            lines.append(f"  DESC[{j}]: {d[:400]!r}")
            break

lines.append("\n=== Descriptions matching power/damage regex ===")
# Deduplicate by content
seen = set()
for i, d in desc_hits:
    key = d[:120]
    if key in seen:
        continue
    seen.add(key)
    lines.append(f"[{i}] {d}")

# Also dump all contexts around "boosts the power" in raw text
lines.append("\n=== Raw contexts: 'boosts the power' ===")
for m in re.finditer(r".{0,80}boosts? the power.{0,200}", data, re.I | re.DOTALL):
    ctx = m.group(0).replace("\x00", "|").replace("\r", " ").replace("\n", " ")
    lines.append(ctx)
    lines.append("---")

lines.append("\n=== Raw contexts: power of ===")
for m in re.finditer(r".{0,60}power of .{0,160}", data, re.I):
    ctx = m.group(0).replace("\x00", "|").replace("\r", " ").replace("\n", " ")
    if "move" in ctx.lower() or "attack" in ctx.lower() or "boost" in ctx.lower():
        lines.append(ctx)
        lines.append("---")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT} ({len(lines)} lines)")
print(f"exact names: {len(exact_names)}")
print(f"power descs: {len(desc_hits)}")
