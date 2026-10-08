"""Dump TryRecruit team-slot fill + name callees via pmdsky."""
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
ARM9 = 0x02000000
NA = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")


def hw(word):
    if (word >> 25) & 7:
        return None
    opx = (word >> 4) & 0xF
    if (opx & 9) != 9:
        return None
    S = (opx >> 2) & 1
    H = (opx >> 1) & 1
    L = (word >> 20) & 1
    I = (word >> 22) & 1
    U = (word >> 23) & 1
    rn = (word >> 16) & 0xF
    rd = (word >> 12) & 0xF
    cond = (word >> 28) & 0xF
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
    cs = {14: "", 1: "ne", 0: "eq"}.get(cond, f"?{cond}")
    return f"{op}{cs} r{rd}, [r{rn}, #{imm:#x}]" if imm is not None else op


def dump(data, load, start, end, title, lines):
    lines.append(f"\n=== {title} ===")
    for addr in range(start, end, 4):
        w = struct.unpack_from("<I", data, addr - load)[0]
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


def load_syms():
    text = NA.read_text(encoding="utf-8", errors="ignore")
    pat = re.compile(
        r'=\s*Symbol\(\s*\[[^\]]*\]\s*,\s*\[([^\]]*)\]\s*,\s*None,\s*"([^"]+)"'
    )
    syms = []
    for m in pat.finditer(text):
        for am in re.finditer(r"0x([0-9A-Fa-f]+)", m.group(1)):
            syms.append((int(am.group(1), 16), m.group(2)))
    syms.sort()
    return syms


def name_of(syms, addr):
    best = None
    for a, n in syms:
        if a <= addr:
            best = (a, n)
        else:
            break
    if best and addr - best[0] < 0x200:
        return f"{best[1]}+{addr-best[0]:#x}" if addr != best[0] else best[1]
    return "?"


def main():
    lines = []
    rom = NintendoDSRom.fromFile(str(ROM))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    arm9 = bytes(rom.arm9)
    ov29 = bytes(rom.files[table[29].fileID])
    syms = load_syms()

    # Name TryRecruit BL targets
    lines.append("TryRecruit BL targets named:")
    for off in range(0x0230E064 - OV29, 0x0230E55C - OV29, 4):
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w >> 25) & 7 != 5 or not ((w >> 24) & 1):
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        dest = OV29 + off + 8 + (imm << 2)
        lines.append(f"  {OV29+off:08X} -> {dest:#010x} {name_of(syms, dest)}")

    # Dump end of TryRecruit around InitTeamMember
    dump(ov29, OV29, 0x0230E3C0, 0x0230E55C, "TryRecruit tail (team join)", lines)

    # Dump arm9 helpers
    for addr, span in (
        (0x020585B4, 0x100),
        (0x020584FC, 0x80),
        (0x02056698, 0x120),
        (0x020530D4, 0x100),
        (0x020534BC, 0x80),
    ):
        dump(arm9, ARM9, addr, addr + span, f"{name_of(syms, addr)} @ {addr:#x}", lines)
        # highlight strh #0x10 / #0xa
        for a in range(addr, addr + span, 4):
            w = struct.unpack_from("<I", arm9, a - ARM9)[0]
            h = hw(w)
            if h and h.startswith("strh") and ("#0x10" in h or "#0xa" in h):
                lines.append(f"  !! {a:08X} {h}")

    # Name TeamSync
    lines.append(f"\n0x022FE048 = {name_of(syms, 0x022FE048)}")
    lines.append(f"0x02055B78 = {name_of(syms, 0x02055B78)}")
    lines.append(f"0x02048AC4 = {name_of(syms, 0x02048AC4)}")
    lines.append(f"0x020577BC = {name_of(syms, 0x020577BC)}")
    lines.append(f"0x02053514 = {name_of(syms, 0x02053514)}")
    lines.append(f"0x02052CF4 = {name_of(syms, 0x02052CF4)}")

    # Wider name lookup for TeamSync
    for a, n in syms:
        if abs(a - 0x022FE048) < 0x20:
            lines.append(f"  close: {a:#x} {n}")

    Path(r"C:\Working\SkyTemple\tools\_tmp_try_recruit2_out.txt").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print("wrote", len(lines), "lines")


if __name__ == "__main__":
    main()
