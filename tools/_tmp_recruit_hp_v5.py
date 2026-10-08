"""Dump 0x02057888 team+0x10 writer and guest path; xrefs; compare vanilla."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROM = Path(
    r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed.nds"
)
ROM_V = Path(r"C:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
ROM_FULL = Path(
    r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed+spinda_ev_speed.nds"
)
ARM9 = 0x02000000
OV29 = 0x022DC240


def load(path):
    rom = NintendoDSRom.fromFile(str(path))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return bytes(rom.arm9), bytes(rom.files[table[29].fileID])


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
    P = (word >> 24) & 1
    rn = (word >> 16) & 0xF
    rd = (word >> 12) & 0xF
    cond = (word >> 28) & 0xF
    if H and not S:
        op = "ldrh" if L else "strh"
    elif H and S:
        op = "ldrsh" if L else None
    elif S and not H:
        op = "ldrsb" if L else None
    else:
        return None
    if not op:
        return None
    imm = ((word >> 4) & 0xF0) | (word & 0xF) if I else None
    if imm is not None and not U:
        imm = -imm
    cs = {14: "", 1: "ne", 0: "eq", 10: "ge", 11: "lt"}.get(cond, f"?{cond}")
    if imm is None:
        return f"{op}{cs} r{rd}, [r{rn}, rm]"
    return f"{op}{cs} r{rd}, [r{rn}, #{imm:#x}]"


def dump(data, load, start, end, title):
    print(f"\n=== {title} ===")
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
            link = (w >> 24) & 1
            note.append(f"{'bl' if link else 'b'} {dest:#010x}")
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
        if ((w >> 21) & 0x7F) == 0x1A and (w >> 25) & 1 and (w >> 28) == 0xE:
            rd = (w >> 12) & 0xF
            rot = (w >> 8) & 0xF
            imm8 = w & 0xFF
            val = (
                ((imm8 >> (2 * rot)) | (imm8 << (32 - 2 * rot))) & 0xFFFFFFFF
                if rot
                else imm8
            )
            note.append(f"mov r{rd}, #{val:#x}")
        # add/sub imm rough
        if ((w >> 26) & 3) == 0 and (w >> 25) & 1 and (w >> 28) == 0xE:
            opc = (w >> 21) & 0xF
            names = {
                2: "sub",
                4: "add",
                0xD: "mov",
                0xA: "cmp",
            }
            if opc in names and opc != 0xD:
                rd = (w >> 12) & 0xF
                rn = (w >> 16) & 0xF
                rot = (w >> 8) & 0xF
                imm8 = w & 0xFF
                val = (
                    ((imm8 >> (2 * rot)) | (imm8 << (32 - 2 * rot))) & 0xFFFFFFFF
                    if rot
                    else imm8
                )
                if opc == 0xA:
                    note.append(f"cmp r{rn}, #{val:#x}")
                else:
                    note.append(f"{names[opc]} r{rd}, r{rn}, #{val:#x}")
        print(f"{addr:08X}  {w:08X}  {'; '.join(note)}")


def xrefs(data, load, target):
    hits = []
    for off in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if (w >> 25) & 7 != 5:
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        addr = load + off
        dest = addr + 8 + (imm << 2)
        if dest == target:
            hits.append((addr, "bl" if (w >> 24) & 1 else "b"))
    return hits


def find_start(data, load, addr):
    off = addr - load
    for i in range(0, 0x400, 4):
        w = struct.unpack_from("<I", data, off - i)[0]
        if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):
            return addr - i
    return addr


def main():
    for tag, path in (("base_stats", ROM), ("vanilla", ROM_V), ("full", ROM_FULL)):
        print(f"\n########## {tag} ##########")
        arm9, ov29 = load(path)
        # Function containing 0x02057888
        start = find_start(arm9, ARM9, 0x02057888)
        print(f"func start for 2057888: {start:#x}")
        dump(arm9, ARM9, start, 0x02057940, f"{tag} team+0x10 writer fn")
        print("xrefs to that func:")
        for a, k in xrefs(arm9, ARM9, start):
            print(f"  arm9 {a:#x} {k}")
        for a, k in xrefs(ov29, OV29, start):
            print(f"  ov29 {a:#x} {k}")

        # Guest path around ZeroGuestV
        dump(arm9, ARM9, 0x02052E50, 0x02052EC0, f"{tag} GuestInitV")

        # Broader: any remaining strh to #0xa of a computed maxhp-like value
        # Also strh #0x10 where source is halfword from dungeon/stack
        print(f"\n{tag} all arm9 strh #0x10 (non-sp) near 0x02055xxx-0x02058xxx:")
        for addr in range(0x02055000, 0x02059000, 4):
            w = struct.unpack_from("<I", arm9, addr - ARM9)[0]
            h = hw(w)
            if h and h.startswith("strh") and "#0x10" in h and "r13" not in h:
                print(f"  {addr:08X}  {h}")
        print(f"{tag} all arm9 strh #0xa (non-sp) 0x02052xxx-0x02058xxx:")
        for addr in range(0x02052000, 0x02059000, 4):
            w = struct.unpack_from("<I", arm9, addr - ARM9)[0]
            h = hw(w)
            if h and h.startswith("strh") and "#0xa" in h and "r13" not in h:
                # check if patched site
                mark = "  [GuestInit strh]" if addr == 0x02052E78 else ""
                mark += "  [RecruitHp]" if addr == 0x02048B00 else ""
                mark += "  [GroundInit]" if addr == 0x02052D24 else ""
                print(f"  {addr:08X}  {h}{mark}")

        # Check if 0x2057888 region copies V bytes too
        # Search ov29 for bl to GetActiveTeamMember then soon strh #0x10
        print(f"\n{tag} ov29: bl GetActiveTeamMember then strh #0x10 within 64B")
        for off in range(0, len(ov29) - 68, 4):
            w = struct.unpack_from("<I", ov29, off)[0]
            if (w >> 25) & 7 != 5 or not ((w >> 24) & 1):
                continue
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            dest = OV29 + off + 8 + (imm << 2)
            if dest != 0x0205638C:
                continue
            for k in range(4, 68, 4):
                w2 = struct.unpack_from("<I", ov29, off + k)[0]
                h = hw(w2)
                if h and h.startswith("strh") and "#0x10" in h:
                    print(f"  {OV29+off:08X} bl GetActiveTeamMember ... {OV29+off+k:08X} {h}")
                    break


if __name__ == "__main__":
    main()
