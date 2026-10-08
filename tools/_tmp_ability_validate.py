"""Validate a few Alpha ability IDs via monster.md + names."""
from __future__ import annotations

from pathlib import Path
from skytemple_files.data.md.handler import MdHandler

# Build name map from string table ordered descs
parts = Path(r"C:\Working\SkyTemple\unpacked\nitrofs\MESSAGE\text_e.str").read_bytes().decode("latin-1").split("\x00")
import re

descs = []
for i in range(37998, 38248):
    s = parts[i]
    m = re.match(r"^\[CS:E\](.+?)\[CR\]:", s)
    if m:
        descs.append(m.group(1))

id_to_name = {i + 1: n for i, n in enumerate(descs)}  # Stench=1

raw = Path(r"C:\Working\SkyTemple\unpacked\nitrofs\BALANCE\monster.md").read_bytes()
md = MdHandler.deserialize(raw)

# Also need monster names - from md ent.md_index_entity or similar string
# Check a few known cases
checks = []
for ent in md.entries[:1200]:
    a1, a2 = int(ent.ability_primary), int(ent.ability_secondary)
    for a in (a1, a2):
        if a in id_to_name:
            pass
    # collect species with Technician
    if a1 == 0x64 or a2 == 0x64:
        checks.append(("Technician holder", ent.md_index, a1, a2, id_to_name.get(a1), id_to_name.get(a2)))
    if a1 == 0x4B or a2 == 0x4B:
        checks.append(("0x4B Strong Jaws?", ent.md_index, a1, a2, id_to_name.get(a1), id_to_name.get(a2)))
    if a1 == 0x84 or a2 == 0x84:
        checks.append(("0x84 Analytic?", ent.md_index, a1, a2, id_to_name.get(a1), id_to_name.get(a2)))
    if a1 == 0x8F or a2 == 0x8F:
        checks.append(("0x8F Tough Claws?", ent.md_index, a1, a2, id_to_name.get(a1), id_to_name.get(a2)))
    if a1 == 0xDC or a2 == 0xDC:
        checks.append(("0xDC Defeatist?", ent.md_index, a1, a2, id_to_name.get(a1), id_to_name.get(a2)))

# Print id map size and sample high IDs
lines = [f"mapped abilities: {len(id_to_name)} last={list(id_to_name.items())[-3:]}"]
lines.append(f"0x64={id_to_name.get(0x64)} 0x4B={id_to_name.get(0x4B)} 0x6C={id_to_name.get(0x6C)} 0x84={id_to_name.get(0x84)}")
lines.append(f"0x8E={id_to_name.get(0x8E)} 0x8F={id_to_name.get(0x8F)} 0xA1={id_to_name.get(0xA1)} 0xDC={id_to_name.get(0xDC)}")
for c in checks[:25]:
    lines.append(str(c))

# Count unused IDs in 1..246
used = set()
for ent in md.entries:
    for a in (int(ent.ability_primary), int(ent.ability_secondary)):
        if a not in (0, 0xFF):
            used.add(a)
unused = [i for i in range(1, 247) if i not in used and i in id_to_name]
lines.append(f"unused among mapped: {len(unused)} -> {[hex(u)+'='+id_to_name[u] for u in unused[:40]]}")

Path(r"C:\Working\SkyTemple\tools\_tmp_ability_validate.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[:40]))
