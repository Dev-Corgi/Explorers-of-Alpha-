import re
from pathlib import Path

text = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py"
).read_text(encoding="utf-8", errors="ignore")

pat = re.compile(
    r'=\s*Symbol\(\s*\[[^\]]*\]\s*,\s*\[([^\]]*)\]\s*,\s*None,\s*"([^"]+)"\s*,\s*(?:"""(.*?)"""|"([^"]*)")',
    re.S,
)
keys = (
    "recruit",
    "team_member",
    "joined",
    "ground_monster",
    "update_team",
    "init_team",
    "copy_team",
    "set_team",
    "sync",
    "add_member",
    "generate_team",
)
hits = []
for m in pat.finditer(text):
    addrs, name = m.group(1), m.group(2)
    desc = m.group(3) or m.group(4) or ""
    blob = (name + " " + desc).lower()
    if not any(k in blob for k in keys):
        continue
    am = re.search(r"0x([0-9A-Fa-f]+)", addrs)
    addr = int(am.group(1), 16) if am else None
    hits.append((addr, name, desc[:140].replace("\n", " ")))
hits.sort(key=lambda x: x[0] or 0)
out = []
for a, n, d in hits:
    line = f"{a:#010x} {n}: {d}".encode("ascii", "replace").decode("ascii")
    out.append(line)
    print(line)
out.append(f"total {len(hits)}")
print("total", len(hits))
Path(r"C:\Working\SkyTemple\tools\_tmp_pmdsky_recruit2_out.txt").write_text(
    "\n".join(out), encoding="utf-8"
)

# Also find symbols near our addresses
want = {
    0x022FE048,
    0x022FD3B4,
    0x02055B78,
    0x02048AC4,
    0x020577BC,
    0x02053518,
    0x02052E2C,
    0x02052CF4,
    0x022F7F80,
}
lines = ["", "Near known sites:"]
pat2 = re.compile(
    r'=\s*Symbol\(\s*\[[^\]]*\]\s*,\s*\[([^\]]*)\]\s*,\s*None,\s*"([^"]+)"',
)
all_syms = []
for m in pat2.finditer(text):
    addrs, name = m.group(1), m.group(2)
    for am in re.finditer(r"0x([0-9A-Fa-f]+)", addrs):
        all_syms.append((int(am.group(1), 16), name))
all_syms.sort()
for t in sorted(want):
    near = [s for s in all_syms if abs(s[0] - t) < 0x80]
    lines.append(f"\n{t:#010x}")
    for a, n in near[:15]:
        lines.append(f"  {a:#010x} {n}")
Path(r"C:\Working\SkyTemple\tools\_tmp_pmdsky_recruit2_out.txt").write_text(
    "\n".join(out + lines), encoding="utf-8"
)
print("wrote out file", len(out + lines))
