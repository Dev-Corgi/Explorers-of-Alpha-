"""Locate ability enums / effect tables in venv packages."""
from __future__ import annotations

from pathlib import Path

root = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages")
out = Path(r"C:\Working\SkyTemple\tools\_tmp_ability_enum_files.txt")
hits = []
for p in root.rglob("*"):
    if not p.is_file():
        continue
    n = p.name.lower()
    path_l = str(p).lower()
    if "abilit" in n or ("abilit" in path_l and p.suffix in {".py", ".json", ".yaml", ".yml", ".toml", ".rs", ".md"}):
        hits.append(str(p))
    elif n in {"enums.py", "ability.py", "abilities.py", "ability_id.py"}:
        hits.append(str(p))

# Also search file contents for TECHNICIAN / HUGE_POWER in pmdsky and skytemple
content_hits = []
for base in [
    root / "pmdsky_debug_py",
    root / "skytemple_files",
    root / "skytemple",
]:
    if not base.exists():
        continue
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix not in {".py", ".json", ".yaml", ".yml", ".md", ".xml"}:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "TECHNICIAN" in txt or "HUGE_POWER" in txt or "ability_id" in txt.lower() or "AbilityId" in txt:
            content_hits.append(str(p))

lines = ["=== filename hits ==="] + hits + ["", "=== content hits ==="] + content_hits
out.write_text("\n".join(lines), encoding="utf-8")
print(f"filename hits {len(hits)}, content hits {len(content_hits)} -> {out}")
for h in content_hits[:40]:
    print(h)
