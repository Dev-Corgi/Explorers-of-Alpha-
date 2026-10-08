"""Identify r8 struct at TryRecruit call site; confirm HP->team+0x10."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROM = Path(
    r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed.nds"
)
OV29 = 0x022DC240
NA = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
OUT = Path(r"C:\Working\SkyTemple\tools\_tmp_try_recruit4_out.txt")


def hw(word):
    if (word >> 25) & 7:
        return None
    opx = (word >> 4) & 0xF
    if (opx & 9) != 9:
        return None
    S, H = (opx >> 2) & 1, (opx >> 1) & 1
    L, I, U = (word >> 20) & 1, (word >> 22) & 1, (word >> 23) & 1
    rn, rd = (word >> 16) & 0xF, (word >> 12) & 0xF
    if H and not S:
        op = "ldrh" if L else "strh"
    elif H and S:
        op = "ldrsh" if L else None
    else:
        return None
    if not op:
        return None
    imm = ((word >> 4) & 0xF0) | (word & 0xF) if I else None
    if imm is not None and not U:
        imm = -imm
    return f"{op} r{rd}, [r{rn}, #{imm:#x}]" if imm is not None else op


def dump(data, load, start, end, title, lines):
    lines.append(f"\n=== {title} ===")
    for addr in range(start, end, 4):
        w = struct.unpack_from("<I", data, addr - load)[0]
        note = []
        h = hw(w)
        if h:
            note.append(h)
        if (w >> 25) & 7 == 5:
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            dest = addr + 8 + (imm << 2)
            note.append(f"{'bl' if (w>>24)&1 else 'b'} {dest:#010x}")
        if (w & 0x0E000000) == 0x04000000 and not ((w >> 25) & 1):
            B = (w >> 22) & 1
            L = (w >> 20) & 1
            U = (w >> 23) & 1
            rn = (w >> 16) & 0xF
            rd = (w >> 12) & 0xF
            imm = w & 0xFFF
            op = ("ldr" if L else "str") + ("b" if B else "")
            note.append(f"{op} r{rd}, [r{rn}, #{'+' if U else '-'}{imm:#x}]")
        if (w & 0xFFFF0000) == 0xE92D0000:
            note.append(f"push {w&0xFFFF:#x}")
        lines.append(f"{addr:08X}  {w:08X}  {'; '.join(note)}")


def main():
    lines = []
    rom = NintendoDSRom.fromFile(str(ROM))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = bytes(rom.files[table[29].fileID])
    text = NA.read_text(encoding="utf-8", errors="ignore")

    # Caller of TryRecruit
    dump(ov29, OV29, 0x0230A7E0, 0x0230A8C0, "TryRecruit caller", lines)

    # Find symbol name for caller function
    pat = re.compile(
        r'=\s*Symbol\(\s*\[[^\]]*\]\s*,\s*\[([^\]]*)\]\s*,\s*None,\s*"([^"]+)"\s*,\s*(?:"""(.*?)"""|"([^"]*)")',
        re.S,
    )
    syms = []
    for m in pat.finditer(text):
        for am in re.finditer(r"0x([0-9A-Fa-f]+)", m.group(1)):
            addr = int(am.group(1), 16)
            desc = (m.group(3) or m.group(4) or "")[:120].replace("\n", " ")
            syms.append((addr, m.group(2), desc))
    syms.sort()

    def nearest(addr):
        best = None
        for a, n, d in syms:
            if a <= addr:
                best = (a, n, d)
            else:
                break
        return best

    for label, addr in (
        ("caller", 0x0230A858),
        ("TryRecruit", 0x0230E064),
        ("TeamSync?", 0x022FE048),
        ("RecruitInit?", 0x02055B78),
        ("InitSpecialEpisode?", 0x02048A84),
    ):
        b = nearest(addr)
        if b:
            lines.append(
                f"{label} {addr:#x} -> {b[1]} @ {b[0]:#x} (+{addr-b[0]}) | {b[2][:100]}"
            )

    # Search pmdsky for monster struct field at +6 HP-like
    # Also: dungeon monster +0x12 max HP - does anything in TryRecruit read it?
    lines.append("\nDoes TryRecruit ever touch monster+0x10/+0x12 via r4?")
    # r4 is monster only early; overwritten in V loop. Early uses:
    dump(ov29, OV29, 0x0230E0A0, 0x0230E0D0, "early r4 monster", lines)

    # Check: is r8 = monster+0xA? species at monster+0x2 not +0x0.
    # pmdsky monster: look for "max_hp_stat" offset
    for key in ("max_hp", "hp_stat", "MonsterId", "struct monster", "offsets"):
        pass
    # Find Monster structure documentation
    for m in re.finditer(r'Monster\s*=\s*Symbol|monster\+\+0x|\"monster\"', text):
        pass
    # Search descriptions mentioning offset 0x6 and hp
    hits = []
    for m in pat.finditer(text):
        desc = (m.group(3) or m.group(4) or "").lower()
        name = m.group(2)
        if "0x6" in desc and "hp" in desc:
            hits.append(name + ": " + desc[:120])
    lines.append("\nSymbols mentioning 0x6 and hp:")
    lines.extend(hits[:20] or ["(none)"])

    # Look for struct field tables in pmdsky - Entity / Monster
    idx = text.find("max_hp_stat")
    if idx >= 0:
        lines.append("\nmax_hp_stat context:")
        lines.append(text[idx - 100 : idx + 200].replace("\n", " | "))
    idx = text.find("\"hp\"")
    
    # Critical confirmation from known layouts:
    # If r8 is dungeon monster, species is at +0x2, not +0x0.
    # TryRecruit loads species from r8+0 for team+0xC.
    # So r8 is likely monster_id-bearing compact struct OR monster with different base.
    # Check InitTeamMember args from TryRecruit:
    # r0=ldrsh[r8,#0], r1=ldrsh[r8,#2], r2=ldrsh[r8,#4], r3=team_member*
    lines.append("\nInitTeamMember call args from TryRecruit:")
    lines.append("  r0 = [r8,#0], r1=[r8,#2], r2=[r8,#4], r3=team_member*")
    b = nearest(0x022FD3B4)
    if b:
        lines.append(f"  InitTeamMember desc: {b[2]}")

    # Read InitTeamMember start to see param meaning
    dump(ov29, OV29, 0x022FD3B4, 0x022FD420, "InitTeamMember prologue", lines)

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("done", len(lines))


if __name__ == "__main__":
    main()
