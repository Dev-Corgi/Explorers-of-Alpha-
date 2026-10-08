from pathlib import Path
import re
import struct

na = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py"
).read_text(encoding="utf-8", errors="ignore")

# Find exclusive item data symbols
for pat in [
    r"ExclusiveItem\w*",
    r"exclusive_item\w*",
    r"EXCLUSIVE_ITEM\w*",
]:
    pass

syms = re.findall(
    r'(\w*(?:Exclusive|exclusive)\w*)\s*=\s*Symbol\(\s*\[([^\]]+)\],\s*\[([^\]]+)\]',
    na,
)
print("=== Exclusive* symbols ===")
for name, rel, abs_ in syms:
    print(f"{name:50s} rel={rel.strip():12s} abs={abs_.strip()}")

# Also search protocol for ExclusiveItemStatBoost struct
proto = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\protocol.py"
).read_text(encoding="utf-8", errors="ignore")
for m in re.finditer(r".{0,80}exclusive.{0,120}", proto, re.I):
    s = m.group(0).replace("\n", " ")
    if "stat" in s.lower() or "boost" in s.lower() or "effect" in s.lower():
        print("PROTO:", s[:200])

# structs.py
st = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\skytemple_files\hardcoded\symbols\manual\structs.py"
).read_text(encoding="utf-8", errors="ignore")
idx = st.lower().find("exclusive")
print("\n=== structs exclusive snippets ===")
while idx >= 0:
    print(st[max(0, idx - 80) : idx + 400])
    print("---")
    idx = st.lower().find("exclusive", idx + 1)
    if idx > 200000:
        break
