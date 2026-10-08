"""Stars table + Technician code site analysis + ability name ID validation."""
from __future__ import annotations

import struct
from pathlib import Path

out = []
arm = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
ov = Path(r"C:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin").read_bytes()

# MOVE_POWER_STARS_TABLE vanilla offset 0x99CD4 - may differ in Alpha
for off in [0x99CD4, 0x99CE0, 0x99CC0]:
    vals = [struct.unpack_from("<i", arm, off + i)[0] for i in range(0, 24, 4)]
    out.append(f"arm9@{off:#x}: {vals}")

# Read power_stars_scale files
ps = Path(r"C:\Working\SkyTemple\true_patches\power_stars_scale")
for p in ps.rglob("*"):
    if p.is_file() and p.suffix in {".yaml", ".asm", ".md", ".py"}:
        out.append(f"\n==== {p.name} ====")
        out.append(p.read_text(encoding="utf-8", errors="ignore")[:2500])

# Disassemble candidate Technician site: mov r0,#0x64 @ 0x1361c then cmp r8,#4 @ 0x136e4
def dis_window(blob, start, n=64):
    lines = []
    for i in range(0, n * 4, 4):
        off = start + i
        if off + 4 > len(blob):
            break
        w = struct.unpack_from("<I", blob, off)[0]
        lines.append(f"  {off:06X}: {w:08X}")
    return "\n".join(lines)

for site in [0x1361C, 0x3413C, 0x40C34, 0x41340, 0x6C494]:
    out.append(f"\n==== site {site:#x} ====")
    out.append(dis_window(ov, site - 0x20, 80))

# Search pmdsky for IsPunchMove / IronFist / GetMovePower related
na = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py").read_text(
    encoding="utf-8", errors="ignore"
)
import re

for name in [
    "IsPunchMove",
    "IsRecoilMove",
    "IsJawMove",
    "IsSoundMove",
    "GetMovePower",
    "CalcDamage",
    "ApplyDamage",
    "FlashFire",
    "HugePower",
    "PurePower",
]:
    if name in na:
        m = re.search(rf"{name}[^\n]*", na)
        # get Symbol block
        m2 = re.search(rf"{name}\s*=\s*Symbol\((.*?)\)\n\n", na, re.S)
        if m2:
            dm = re.search(r'"([^"]*)"\s*,\s*"([^"]*)"', m2.group(1))
            if dm:
                out.append(f"\nSYM {dm.group(1)}: {dm.group(2)[:300]}")

# Validate ability IDs via monster.md: count unique ability bytes used
try:
    from ndspy.rom import NintendoDSRom  # may not exist
except Exception:
    pass

# Parse monster.md with skytemple if available
try:
    from skytemple_files.common.types.file_types import FileType
    from skytemple_files.common.util import get_ppmdu_config_for_rom
    from ndspy.rom import NintendoDSRom

    # Prefer loading from unpacked via skytemple MdHandler directly
    from skytemple_files.data.md.handler import MdHandler

    raw = Path(r"C:\Working\SkyTemple\unpacked\nitrofs\BALANCE\monster.md").read_bytes()
    md = MdHandler.deserialize(raw)
    abilities = set()
    for ent in md.entries:
        for a in (ent.ability_primary, ent.ability_secondary):
            if a and int(a) not in (0, 0xFF):
                abilities.add(int(a))
    out.append(f"\nUnique ability IDs in monster.md: {len(abilities)}")
    out.append("IDs: " + ",".join(f"{x:#x}" for x in sorted(abilities)))
    # max id
    out.append(f"max={max(abilities):#x} min={min(abilities):#x}")
except Exception as e:
    out.append(f"\nmonster.md parse failed: {e!r}")
    # manual: monster.md entry size often 0x44 bytes; ability bytes at known offsets
    raw = Path(r"C:\Working\SkyTemple\unpacked\nitrofs\BALANCE\monster.md").read_bytes()
    out.append(f"monster.md size={len(raw)}")

Path(r"C:\Working\SkyTemple\tools\_tmp_tech_stars.txt").write_text("\n".join(out), encoding="utf-8")
print("done", len(out))
