"""Dump full Alpha ability name+desc pairs that relate to power/damage."""
from __future__ import annotations

import re
from pathlib import Path

STR = Path(r"C:\Working\SkyTemple\unpacked\nitrofs\MESSAGE\text_e.str")
OUT = Path(r"C:\Working\SkyTemple\tools\_tmp_ability_power_descs.txt")

parts = STR.read_bytes().decode("latin-1").split("\x00")

# Alpha ability names appear to start around index 37743 / descs around 38004
# Vanilla block names ~33081, descs ~33209

POWERISH = re.compile(
    r"power|damage|boosts?|powers? up|doubles?|halves?|Attack|"
    r"punch|bit|slash|recoil|contact|special moves|physical moves|"
    r"type moves|STAB|super-effective|weakens|reduces|pinch|"
    r"low attack|low HP|full HP|sunny|sandstorm|rain|electric terrain|"
    r"added effects|ranged|in front|sound moves|aura",
    re.I,
)

EXCLUDE_ONLY_STATUS = re.compile(
    r"^(?!.*(?:power|damage|boosts the|powers up|doubles|halves|Attack power|inflicts more|inflicted)).*$",
    re.I,
)


def clean(s: str) -> str:
    s = re.sub(r"\[[^\]]+\]", "", s)
    return s.replace("\r", " ").replace("\n", " ").strip()


def dump_block(start: int, end: int, label: str) -> list[str]:
    lines = [f"\n===== {label} [{start}:{end}] ====="]
    # Pair consecutive short-name + longer-desc if possible
    i = start
    while i < end:
        s = parts[i].strip("\x00")
        if not s:
            i += 1
            continue
        plain = clean(s)
        # ability desc format usually starts with ability name in CS:E tags
        if s.startswith("[CS:E]") or (len(plain) < 40 and plain and " " in plain or plain.isalpha() or "'" in plain or "-" in plain):
            # if looks like name-only
            if len(plain) < 36 and "\n" not in s and not plain.endswith(":") and ":" not in plain:
                # find next desc
                desc = None
                di = None
                for j in range(i + 1, min(i + 5, end)):
                    d = parts[j].strip("\x00")
                    if not d:
                        continue
                    cd = clean(d)
                    if len(cd) > 20 or d.startswith("[CS:E]"):
                        desc = d
                        di = j
                        break
                if desc and POWERISH.search(desc):
                    lines.append(f"NAME[{i}] {plain}")
                    lines.append(f"DESC[{di}] {clean(desc)}")
                    lines.append("---")
                i += 1
                continue
        if s.startswith("[CS:E]") and POWERISH.search(s):
            lines.append(f"ENTRY[{i}] {clean(s)}")
            lines.append("---")
        i += 1
    return lines


# Find contiguous ability description blocks by scanning for [CS:E]Xxx[CR]:
desc_indices = []
for i, s in enumerate(parts):
    if re.match(r"^\[CS:E\].+\[CR\]:", s):
        desc_indices.append(i)

lines = [f"ability-desc-like entries: {len(desc_indices)}"]
if desc_indices:
    # cluster into contiguous ranges
    clusters = []
    cur = [desc_indices[0]]
    for x in desc_indices[1:]:
        if x - cur[-1] <= 3:
            cur.append(x)
        else:
            clusters.append(cur)
            cur = [x]
    clusters.append(cur)
    lines.append(f"clusters: {[(c[0], c[-1], len(c)) for c in clusters]}")

    for c in clusters:
        if len(c) < 20:
            continue
        lines.append(f"\n##### CLUSTER {c[0]}-{c[-1]} ({len(c)} entries) #####")
        for i in c:
            s = parts[i]
            if POWERISH.search(s):
                lines.append(f"[{i}] {clean(s)}")

# Also dump Strong Jaw / Strong Jaws naming
for needle in ["Strong Jaw", "Strong Jaws", "Blade Mastery", "Sound Waves", "Marvel Veil", "Wonder Veil", "Royal Majesty", "Unseen Fist", "Shadow Shield", "Solid Guard", "Multitype"]:
    lines.append(f"\n## occurrences of {needle}")
    for i, s in enumerate(parts):
        if needle in s and len(s) < 400:
            lines.append(f"[{i}] {clean(s)[:300]}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT}")
