"""Disassemble recruit-info filler 0x022F9058; find what +0x6 HP is."""
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
OUT = Path(r"C:\Working\SkyTemple\tools\_tmp_recruit_info_out.txt")


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


def main():
    lines = []
    rom = NintendoDSRom.fromFile(str(ROM))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = bytes(rom.files[table[29].fileID])
    text = NA.read_text(encoding="utf-8", errors="ignore")

    # Name 0x022F9058
    pat = re.compile(
        r'=\s*Symbol\(\s*\[[^\]]*\]\s*,\s*\[([^\]]*)\]\s*,\s*None,\s*"([^"]+)"\s*,\s*(?:"""(.*?)"""|"([^"]*)")',
        re.S,
    )
    best = None
    for m in pat.finditer(text):
        for am in re.finditer(r"0x([0-9A-Fa-f]+)", m.group(1)):
            a = int(am.group(1), 16)
            if a <= 0x022F9058 and (best is None or a > best[0]):
                desc = (m.group(3) or m.group(4) or "")[:200].replace("\n", " ")
                best = (a, m.group(2), desc)
    lines.append(f"0x022F9058 nearest: {best}")

    # Dump function
    start = 0x022F9058
    # find end
    end = start + 0x200
    for i in range(0x20, 0x400, 4):
        w = struct.unpack_from("<I", ov29, start - OV29 + i)[0]
        if (w & 0xFFFF0000) == 0xE8BD0000 and (w & 0x8000):
            end = start + i + 4
            break
    lines.append(f"func {start:#x}-{end:#x}")

    for addr in range(start, end, 4):
        w = struct.unpack_from("<I", ov29, addr - OV29)[0]
        note = []
        h = hw(w)
        if h:
            note.append(h)
        if w == 0xE1A00000:
            note.append("nop")
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
        if (w & 0xFFFF0000) == 0xE8BD0000:
            note.append(f"pop {w&0xFFFF:#x}")
        lines.append(f"{addr:08X}  {w:08X}  {'; '.join(note)}")

    # Highlight stores to dest+0x6 / loads from monster+0x12/+0x10
    lines.append("\nNotable HP-related insns:")
    for addr in range(start, end, 4):
        w = struct.unpack_from("<I", ov29, addr - OV29)[0]
        h = hw(w)
        if not h:
            continue
        if any(x in h for x in ("#0x6", "#0x10", "#0x12", "#0xa", "#0xe")):
            lines.append(f"  {addr:08X}  {h}")

    # Also check TeamSync symbol - nearest was SubInitMonster; widen search
    for m in pat.finditer(text):
        name = m.group(2)
        if "team" in name.lower() and (
            "update" in name.lower() or "sync" in name.lower() or "copy" in name.lower()
        ):
            for am in re.finditer(r"0x([0-9A-Fa-f]+)", m.group(1)):
                a = int(am.group(1), 16)
                if 0x022F0000 <= a <= 0x02310000:
                    lines.append(f"team-ish {a:#x} {name}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", len(lines))


if __name__ == "__main__":
    main()
