"""Find pmdsky-debug symbols near recruit / TeamSync addresses."""
from __future__ import annotations

import re
from pathlib import Path

NA = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
# Also try json if present
pkgs = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py")
print("files", [p.name for p in pkgs.iterdir()][:40])

text = NA.read_text(encoding="utf-8", errors="ignore")

# Collect all symbols with NA address
# Pattern varies; try several
entries = []
for m in re.finditer(
    r'([A-Za-z0-9_]+)\s*=\s*Symbol\(\s*"([^"]*)"\s*,\s*"""(.*?)"""\s*,\s*address(?:es)?\s*=\s*([^\n]+)',
    text,
    re.S,
):
    entries.append(m.groups())
print("triple-quote symbols", len(entries))

for m in re.finditer(
    r'([A-Za-z0-9_]+)\s*=\s*Symbol\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*,\s*address(?:es)?\s*=\s*([^\n]+)',
    text,
):
    entries.append(m.groups())
print("total symbols matched", len(entries))

TARGETS = {
    0x022FE048,
    0x022FE000,
    0x022FD3B4,
    0x022FD50C,
    0x022FE068,
    0x02055B78,
    0x02055BB8,
    0x02048AC4,
    0x02048B00,
    0x02052D20,
    0x02054024,
    0x020555A8,
    0x020544C8,
    0x020529C4,
}


def parse_addr(s: str):
    s = s.strip().rstrip(",")
    if s.startswith("0x"):
        return {int(s, 16)}
    # {Eu:0x.., Na:0x..}
    out = set()
    for m in re.finditer(r"Na\s*[:=]\s*(0x[0-9A-Fa-f]+)", s):
        out.add(int(m.group(1), 16))
    for m in re.finditer(r"0x[0-9A-Fa-f]+", s):
        out.add(int(m.group(0), 16))
    return out


# Broader: line-based scan for address = 0x... near Symbol names
# Find all NA addresses in file with preceding symbol name
syms = []
for m in re.finditer(
    r'^([A-Z][A-Za-z0-9_]+)\s*=\s*Symbol\(',
    text,
    re.M,
):
    name = m.group(1)
    chunk = text[m.start() : m.start() + 800]
    sm = re.search(r'"([A-Za-z0-9_]+)"', chunk)
    sym = sm.group(1) if sm else name
    # addresses
    addrs = set()
    for am in re.finditer(r"(?:Na|NA|na)\s*[:=]\s*(0x[0-9A-Fa-f]+)", chunk):
        addrs.add(int(am.group(1), 16))
    if not addrs:
        am = re.search(r"address\s*=\s*(0x[0-9A-Fa-f]+)", chunk)
        if am:
            addrs.add(int(am.group(1), 16))
    for a in addrs:
        syms.append((a, name, sym))

print("syms with addrs", len(syms))
syms.sort()

print("\nNear targets:")
for t in sorted(TARGETS):
    # closest symbols
    near = [s for s in syms if abs(s[0] - t) < 0x200]
    print(f"\n-- {t:#010x} --")
    for a, n, s in near[:12]:
        print(f"  {a:#010x} {n} / {s}")

# Keyword search
print("\nKeyword hits:")
keys = ["recruit", "joined", "team_member", "ground_monster", "copy_monster", "update_team", "sync"]
for a, n, s in syms:
    blob = (n + " " + s).lower()
    if any(k in blob for k in keys):
        print(f"{a:#010x} {n} / {s}")
