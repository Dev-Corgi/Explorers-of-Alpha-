"""Map ability IDs to Alpha names/descriptions and extract Technician digit."""
from __future__ import annotations

import re
import struct
from pathlib import Path

STR = Path(r"C:\Working\SkyTemple\unpacked\nitrofs\MESSAGE\text_e.str")
OUT = Path(r"C:\Working\SkyTemple\tools\_tmp_ability_id_map.txt")
OV29 = Path(r"C:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin")

parts = STR.read_bytes().decode("latin-1").split("\x00")

# Vanilla-ish name block starts at Thick Fat = ID 2? Looking at earlier:
# 33081 Thick Fat (0x2), 33085 Intimidate (0x6)...
# Actually names may not be contiguous with unused.

# Better approach: dump names from 37743 onward consecutively matching Alpha desc cluster order
# Name block 37743+ and desc block 37998+

# Extract ordered names from Alpha name list
# From earlier report exact names start 37743 Thick Fat

# Dump raw consecutive ability-like short strings from 37740-37990
name_block = []
for i in range(37740, 37995):
    s = parts[i].strip("\x00")
    if not s:
        name_block.append((i, ""))
        continue
    plain = re.sub(r"\[[^\]]+\]", "", s).strip()
    name_block.append((i, plain if len(plain) < 40 and "\n" not in s else f"LONG:{plain[:40]}"))

# Desc block with raw (keep digits tags)
desc_block = []
for i in range(37998, 38250):
    s = parts[i]
    if re.match(r"^\[CS:E\].+\[CR\]:", s):
        # keep numeric tags
        raw = s.replace("\r", "\\r").replace("\n", "\\n")
        plain = re.sub(r"\[[^\]]+\]", lambda m: m.group(0) if any(c.isdigit() for c in m.group(0)) else "", s)
        plain2 = re.sub(r"\[CS:[^\]]+\]|\[CR\]", "", s)
        plain2 = plain2.replace("\r", " ").replace("\n", " ")
        desc_block.append((i, plain2.strip(), raw[:250]))

# Vanilla Ability enum order (1..0x7B)
VANILLA = [
    (0x01, "Stench"),
    (0x02, "Thick Fat"),
    (0x03, "Rain Dish"),
    (0x04, "Drizzle"),
    (0x05, "Arena Trap"),
    (0x06, "Intimidate"),
    (0x07, "Rock Head"),
    (0x08, "Air Lock"),
    (0x09, "Hyper Cutter"),
    (0x0A, "Shadow Tag"),
    (0x0B, "Speed Boost"),
    (0x0C, "Battle Armor"),
    (0x0D, "Sturdy"),
    (0x0E, "Suction Cups"),
    (0x0F, "Clear Body"),
    (0x10, "Torrent"),
    (0x11, "Guts"),
    (0x12, "Rough Skin"),
    (0x13, "Shell Armor"),
    (0x14, "Natural Cure"),
    (0x15, "Damp"),
    (0x16, "Limber"),
    (0x17, "Magnet Pull"),
    (0x18, "White Smoke"),
    (0x19, "Synchronize"),
    (0x1A, "Overgrow"),
    (0x1B, "Swift Swim"),
    (0x1C, "Sand Stream"),
    (0x1D, "Sand Veil"),
    (0x1E, "Keen Eye"),
    (0x1F, "Inner Focus"),
    (0x20, "Static"),
    (0x21, "Shed Skin"),
    (0x22, "Huge Power"),
    (0x23, "Volt Absorb"),
    (0x24, "Water Absorb"),
    (0x25, "Forecast"),
    (0x26, "Serene Grace"),
    (0x27, "Poison Point"),
    (0x28, "Trace"),
    (0x29, "Oblivious"),
    (0x2A, "Truant"),
    (0x2B, "Run Away"),
    (0x2C, "Sticky Hold"),
    (0x2D, "Cloud Nine"),
    (0x2E, "Illuminate"),
    (0x2F, "Early Bird"),
    (0x30, "Hustle"),
    (0x31, "Drought"),
    (0x32, "LightningRod"),
    (0x33, "CompoundEyes"),
    (0x34, "Marvel Scale"),
    (0x35, "Wonder Guard"),
    (0x36, "Insomnia"),
    (0x37, "Levitate"),
    (0x38, "Plus"),
    (0x39, "Pressure"),
    (0x3A, "Liquid Ooze"),
    (0x3B, "Color Change"),
    (0x3C, "Soundproof"),
    (0x3D, "Effect Spore"),
    (0x3E, "Flame Body"),
    (0x3F, "Minus"),
    (0x40, "Own Tempo"),
    (0x41, "Magma Armor"),
    (0x42, "Water Veil"),
    (0x43, "Swarm"),
    (0x44, "Cute Charm"),
    (0x45, "Immunity"),
    (0x46, "Blaze"),
    (0x47, "Pickup"),
    (0x48, "Flash Fire"),
    (0x49, "Vital Spirit"),
    (0x4A, "Chlorophyll"),
    (0x4B, "Pure Power"),
    (0x4C, "Shield Dust"),
    (0x4D, "Ice Body"),
    (0x4E, "Stall"),
    (0x4F, "Anger Point"),
    (0x50, "Tinted Lens"),
    (0x51, "Hydration"),
    (0x52, "Frisk"),
    (0x53, "Mold Breaker"),
    (0x54, "Unburden"),
    (0x55, "Dry Skin"),
    (0x56, "Anticipation"),
    (0x57, "Scrappy"),
    (0x58, "Super Luck"),
    (0x59, "Gluttony"),
    (0x5A, "Solar Power"),
    (0x5B, "Skill Link"),
    (0x5C, "Reckless"),
    (0x5D, "Sniper"),
    (0x5E, "Slow Start"),
    (0x5F, "Heatproof"),
    (0x60, "Download"),
    (0x61, "Simple"),
    (0x62, "Tangled Feet"),
    (0x63, "Adaptability"),
    (0x64, "Technician"),
    (0x65, "Iron Fist"),
    (0x66, "Motor Drive"),
    (0x67, "Unaware"),
    (0x68, "Rivalry"),
    (0x69, "Bad Dreams"),
    (0x6A, "No Guard"),
    (0x6B, "Normalize"),
    (0x6C, "Solid Rock"),
    (0x6D, "Quick Feet"),
    (0x6E, "Filter"),
    (0x6F, "Klutz"),
    (0x70, "Steadfast"),
    (0x71, "Flower Gift"),
    (0x72, "Poison Heal"),
    (0x73, "Magic Guard"),
    (0x74, "Multitype"),
    (0x75, "Honey Gather"),
    (0x76, "Aftermath"),
    (0x77, "Snow Cloak"),
    (0x78, "Snow Warning"),
    (0x79, "Forewarn"),
    (0x7A, "Storm Drain"),
    (0x7B, "Leaf Guard"),
]

# Pair vanilla IDs with Alpha desc cluster (starts Stench at 37998)
# Descs are NOT 1:1 consecutive - some IDs skipped in listing earlier because no power match
# Build full desc list for all [CS:E] entries in cluster

all_descs = []
for i in range(37998, 38248):
    s = parts[i]
    if re.match(r"^\[CS:E\].+\[CR\]:", s):
        # extract name
        m = re.match(r"^\[CS:E\](.+?)\[CR\]:\s*(.*)", s, re.S)
        if m:
            name = m.group(1)
            body = m.group(2).replace("\r", " ").replace("\n", " ").strip()
            # keep digit placeholders visible
            body_vis = body
            # also extract raw digit sequences outside tags
            tags = re.findall(r"\[[^\]]+\]", s)
            all_descs.append((i, name, body, tags))

lines = []
lines.append(f"Alpha desc entries in cluster: {len(all_descs)}")
# First 123 should map to vanilla IDs 1..123? count
# Vanilla has 0x7B = 123 abilities from 1

first123 = all_descs[:123]
lines.append("\n=== First 123 descs vs vanilla enum ===")
for (aid, vname), (i, aname, body, tags) in zip(VANILLA, first123):
    renamed = "" if vname == aname else f"  [RENAMED from {vname}]"
    lines.append(f"0x{aid:02X} ({aid:3d}) {aname}{renamed}")
    lines.append(f"         {body[:200]}")
    if tags:
        digit_tags = [t for t in tags if any(c.isdigit() for c in t)]
        if digit_tags:
            lines.append(f"         tags: {digit_tags}")

lines.append("\n=== Extended Alpha abilities after vanilla 123 ===")
for idx, (i, aname, body, tags) in enumerate(all_descs[123:], start=0x7C):
    lines.append(f"0x{idx:02X} ({idx:3d})? idx_guess {aname}")
    lines.append(f"         {body[:220]}")
    digit_tags = [t for t in tags if any(c.isdigit() for c in t)]
    if digit_tags:
        lines.append(f"         tags: {digit_tags}")

# Technician special - show raw
for i, s in enumerate(parts):
    if "Technician" in s and "power" in s.lower():
        lines.append(f"\nTECH RAW[{i}]: {s!r}")

# Read ROM technician threshold
# Overlay 29 load address for NA is typically 0x22DC440 or similar; symbol says file offset 0x7ADC
off = 0x7ADC
data = OV29.read_bytes()
val = struct.unpack_from("<h", data, off)[0]
lines.append(f"\nOV29@{off:#x} int16 Technician threshold = {val}")
# also search for nearby bytes if Alpha changed it
# search for pattern of threshold comparisons - find all occurrences of value 4 as halfword near ability code is hard

# Search string for "power of" near Technician
for i, s in enumerate(parts):
    if s.startswith("[CS:E]Technician"):
        lines.append(f"TECH DESC[{i}]: {s!r}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT}, descs={len(all_descs)}, tech_thresh={val}")
