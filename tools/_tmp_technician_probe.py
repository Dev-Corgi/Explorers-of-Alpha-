"""Find Technician threshold in Alpha OV29 / ARM9 and dump raw Technician strings."""
from __future__ import annotations

import re
import struct
from pathlib import Path

parts = Path(r"C:\Working\SkyTemple\unpacked\nitrofs\MESSAGE\text_e.str").read_bytes().decode("latin-1").split("\x00")
out = []
for i, s in enumerate(parts):
    if "Technician" in s:
        out.append(f"[{i}] {s!r}")

# Search binaries for halfword 4 in data-looking regions, and for ability-check patterns
# Compare with Vanilla Rom overlay if present

paths = {
    "alpha_ov29": Path(r"C:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin"),
    "alpha_arm9": Path(r"C:\Working\SkyTemple\unpacked\arm9.bin"),
}
# Find vanilla overlay for comparison
van_roots = [
    Path(r"C:\Working\SkyTemple\Vanilla Rom"),
    Path(r"C:\Working\SkyTemple\Export Rom"),
]
for vr in van_roots:
    for p in vr.rglob("overlay_0029.bin"):
        paths[f"van_{p.parent.name}"] = p
        break

# From pmdsky NA: absolute address 0x22C455C
# OV29 NA load address is 0x22DCB80? Need to check
# Actually symbol: file offset [0x7ADC], absolute [0x22C455C]
# So load_base = 0x22C455C - 0x7ADC = 0x22BCA80? That seems wrong for ov29.
# Wait - maybe it's in ARM9!
# arm9 NA often loads at 0x02000000
# 0x22C455C - 0x02000000 = 0x2C455C - too large for arm9
# Overlay 29 NA load: from pmdsky

from pathlib import Path as P
na = P(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py").read_text(encoding="utf-8", errors="ignore")
# find OVERLAY29 load address and TECHNICIAN
m = re.search(r'TECHNICIAN_MOVE_POWER_THRESHOLD = Symbol\(\s*\[(0x[0-9A-Fa-f]+)\],\s*\[(0x[0-9A-Fa-f]+)\]', na)
out.append(f"TECH symbol offsets: {m.groups() if m else None}")

# Find which binary contains absolute address - look at LoadOverlay table
# Search both for the documented description pattern: the value 4 as int16 in a table of chance values
# Adjacent: BLAZE_KICK at 0x7AC0 = 10, FLAMETHROWER, etc.

# Search alpha arm9 and ov29 for sequence of known chance values from pmdsky
# SACRED_FIRE etc - easier: search for IsRecoilMove / technician logic by finding
# cmp with immediate after GetMovePower

ov = paths["alpha_ov29"].read_bytes()
arm = paths["alpha_arm9"].read_bytes()

# In vanilla EoS wiki/docs: Technician boosts if power <= 4
# Search for: ldrsh/ldrh of a pool value that is 4, used near ability 0x64
# Practical approach: find all `cmp rX, #4` near mov #0x64 within 0x80 bytes

def find_tech_candidates(blob: bytes, label: str):
    hits = []
    # mov rN, #0x64
    for reg in range(16):
        mov = struct.pack("<I", 0xE3A00000 | (reg << 12) | 0x64)
        start = 0
        while True:
            j = blob.find(mov, start)
            if j < 0:
                break
            window = blob[j : j + 0x100]
            # look for cmp Rx, #4  => E35X0004 or E15X00B4 (cmp with imm)
            for k in range(0, len(window) - 4, 4):
                w = struct.unpack_from("<I", window, k)[0]
                # cmp rn, #imm: cond E, opcode 0x35, or cmn etc
                # Encoding: E35n0imm for cmp rn,#imm (32-bit imm12)
                if (w & 0xFFF00000) == 0xE3500000 and (w & 0xFF) == 4:
                    hits.append((j, j + k, w, reg))
                # also cmp with #60 (0x3C) Gen9 style
                if (w & 0xFFF00000) == 0xE3500000 and (w & 0xFF) in (60, 0x3C, 50, 40, 70):
                    hits.append((j, j + k, w, reg))
            start = j + 4
    out.append(f"{label}: technician-nearby cmp-imm hits: {len(hits)}")
    for h in hits[:30]:
        out.append(f"  mov@ {h[0]:#x} cmp@{h[1]:#x} word={h[2]:08X} mov_reg=r{h[3]}")

find_tech_candidates(ov, "ov29")
find_tech_candidates(arm, "arm9")

# Also search for literal pool value 4 used as threshold - look for
# GetMovePower symbol usage. From z_move offsets: GetMovePower 0x0230231C
# That's in ov29. Relative file offset = 0x0230231C - ov29_load
# From true_patches offsetsUS for damage formula

off_file = Path(r"C:\Working\SkyTemple\true_patches\damage_formula\asm\common\offsetsUS.asm")
if off_file.exists():
    out.append(off_file.read_text(encoding="utf-8", errors="ignore")[:2000])

# Search string for power digit in technician using special tags like [M:B?] or similar
for i, s in enumerate(parts):
    if s.startswith("[CS:E]Technician"):
        # show all char codes around 'power'
        idx = s.lower().find("power")
        snippet = s[max(0, idx - 20) : idx + 80]
        out.append(f"snippet codes: {[hex(ord(c)) for c in snippet]}")
        out.append(f"snippet repr: {snippet!r}")

Path(r"C:\Working\SkyTemple\tools\_tmp_technician_probe.txt").write_text("\n".join(out), encoding="utf-8")
print("wrote probe", len(out))
