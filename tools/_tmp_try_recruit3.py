"""Map TryRecruit stack+0xAC layout to team_member fields; find HP source."""
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
OUT = Path(r"C:\Working\SkyTemple\tools\_tmp_try_recruit3_out.txt")


def hw(word):
    if (word >> 25) & 7:
        return None
    opx = (word >> 4) & 0xF
    if (opx & 9) != 9:
        return None
    S, H = (opx >> 2) & 1, (opx >> 1) & 1
    L, I, U = (word >> 20) & 1, (word >> 22) & 1, (word >> 23) & 1
    rn, rd = (word >> 16) & 0xF, (word >> 12) & 0xF
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


def main():
    lines = []
    rom = NintendoDSRom.fromFile(str(ROM))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = bytes(rom.files[table[29].fileID])
    arm9 = bytes(rom.arm9)

    # Every store to sp+#0xAC .. sp+#0xAC+0x68 in TryRecruit
    lines.append("Stores into recruit stack struct (sp+0xAC == team_member[0]):")
    for addr in range(0x0230E064, 0x0230E55C, 4):
        w = struct.unpack_from("<I", ov29, addr - OV29)[0]
        # str* [r13, #imm]
        if (w >> 26) & 3 == 1 and not ((w >> 25) & 1):
            if ((w >> 16) & 0xF) != 13:
                continue
            if (w >> 20) & 1:  # load
                continue
            imm = w & 0xFFF
            if not ((w >> 23) & 1):
                continue
            if 0xAC <= imm <= 0xAC + 0x70:
                B = (w >> 22) & 1
                rd = (w >> 12) & 0xF
                team_off = imm - 0xAC
                op = "strb" if B else "str"
                lines.append(
                    f"  {addr:08X}  {op} r{rd}, [sp, #{imm:#x}]  -> team+{team_off:#x}"
                )
        h = hw(w)
        if h and "r13" in h and h.startswith("str"):
            # parse imm
            m = re.search(r"#(-?0x[0-9a-f]+)", h)
            if not m:
                continue
            imm = int(m.group(1), 16)
            if 0xAC <= abs(imm) <= 0xAC + 0x70 or 0xAC <= imm <= 0xAC + 0x70:
                team_off = imm - 0xAC
                lines.append(f"  {addr:08X}  {h}  -> team+{team_off:#x}")

    # Specifically show what feeds team+0x10 (sp+0xBC) and team+0xE (sp+0xBA)
    lines.append("\nContext around fills of sp+0xBA / sp+0xBC / sp+0xBE:")
    for addr in range(0x0230E180, 0x0230E220, 4):
        w = struct.unpack_from("<I", ov29, addr - OV29)[0]
        h = hw(w)
        note = h or ""
        if (w >> 25) & 7 == 5:
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            dest = addr + 8 + (imm << 2)
            note += f" {'bl' if (w>>24)&1 else 'b'} {dest:#x}"
        if (w & 0x0E000000) == 0x04000000 and not ((w >> 25) & 1):
            B = (w >> 22) & 1
            L = (w >> 20) & 1
            U = (w >> 23) & 1
            rn = (w >> 16) & 0xF
            rd = (w >> 12) & 0xF
            imm = w & 0xFFF
            op = ("ldr" if L else "str") + ("b" if B else "")
            note += f" {op} r{rd}, [r{rn}, #{'+' if U else '-'}{imm:#x}]"
        lines.append(f"{addr:08X}  {w:08X}  {note}")

    # Who calls TryRecruit?
    lines.append("\nXrefs to TryRecruit:")
    for off in range(0, len(ov29) - 3, 4):
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w >> 25) & 7 != 5:
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        if OV29 + off + 8 + (imm << 2) == 0x0230E064:
            lines.append(f"  {OV29+off:#010x} {'bl' if (w>>24)&1 else 'b'}")

    # Dump 0x02056698 properly - called with team index before copy
    # Actually 0x2056698 sets roster slot. Then GetActiveTeamMember, then memcpy.

    # After memcpy, InitTeamMember uses team_member - BaseStats_InitHp reads team+0x10 as HP V!
    # So whatever was memcpy'd into team+0x10 IS the HP V shown.

    # Trace r8: is it monster? Check loads from r8 of +0x12 (maxhp)
    lines.append("\nTryRecruit accesses of r8 offsets:")
    for addr in range(0x0230E064, 0x0230E55C, 4):
        w = struct.unpack_from("<I", ov29, addr - OV29)[0]
        h = hw(w)
        if h and "[r8," in h:
            lines.append(f"  {addr:08X}  {h}")
        if (w & 0x0E000000) == 0x04000000 and not ((w >> 25) & 1):
            if ((w >> 16) & 0xF) == 8:
                B = (w >> 22) & 1
                L = (w >> 20) & 1
                U = (w >> 23) & 1
                rd = (w >> 12) & 0xF
                imm = w & 0xFFF
                op = ("ldr" if L else "str") + ("b" if B else "")
                lines.append(
                    f"  {addr:08X}  {op} r{rd}, [r8, #{'+' if U else '-'}{imm:#x}]"
                )

    lines.append("\nTryRecruit accesses of r4 (monster) offsets:")
    for addr in range(0x0230E064, 0x0230E55C, 4):
        w = struct.unpack_from("<I", ov29, addr - OV29)[0]
        h = hw(w)
        if h and "[r4," in h:
            lines.append(f"  {addr:08X}  {h}")

    # pmdsky name for 0x2056698 area - search description Join
    text = NA.read_text(encoding="utf-8", errors="ignore")
    for needle in (
        "0x2056698",
        "0x02056698",
        "0x20585b4",
        "0x020585b4",
        "0x20584fc",
        "0x020584fc",
        "0x22fe048",
        "0x022fe048",
        "0x2055b78",
        "0x02055b78",
        "0x20577bc",
        "0x020577bc",
        "0x20534bc",
        "0x020534bc",
        "0x20530d4",
        "0x020530d4",
    ):
        idx = text.lower().find(needle)
        if idx < 0:
            lines.append(f"no sym text for {needle}")
            continue
        # walk back for name
        chunk = text[max(0, idx - 200) : idx + 80]
        m = re.search(r'"([A-Za-z0-9_]+)"\s*,\s*(?:"""|")', chunk)
        lines.append(f"{needle}: context name={m.group(1) if m else '?'}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT, "lines", len(lines))


if __name__ == "__main__":
    main()
