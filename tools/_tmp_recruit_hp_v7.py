"""Inspect remaining ground+0xA writers and dungeon-recruit team slot init."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROM = Path(
    r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed.nds"
)
ARM9 = 0x02000000
OV29 = 0x022DC240


def load(path):
    rom = NintendoDSRom.fromFile(str(path))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return bytes(rom.arm9), bytes(rom.files[table[29].fileID]), rom, table


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
        # mov #imm
        if ((w >> 21) & 0x7F) == 0x1A and (w >> 25) & 1 and (w >> 28) == 0xE:
            rd = (w >> 12) & 0xF
            rot = (w >> 8) & 0xF
            imm8 = w & 0xFF
            val = ((imm8 >> (2*rot)) | (imm8 << (32-2*rot))) & 0xFFFFFFFF if rot else imm8
            note.append(f"mov r{rd}, #{val:#x}")
        print(f"{addr:08X}  {w:08X}  {'; '.join(note)}")


def main():
    arm9, ov29, rom, table = load(ROM)

    # Full dump of recruit-adjacent ground+0xA writer
    dump(arm9, ARM9, 0x02055F20, 0x02055FC0, "0x2055f6c vicinity (recruit-adjacent)")
    dump(arm9, ARM9, 0x020534E0, 0x02053560, "0x2053518 vicinity")
    dump(arm9, ARM9, 0x020576E0, 0x02057760, "0x2057724 vicinity")
    dump(arm9, ARM9, 0x02057A50, 0x02057AD0, "0x2057a94 vicinity")
    dump(arm9, ARM9, 0x02057DA0, 0x02057E20, "0x2057de0 vicinity")
    dump(arm9, ARM9, 0x02057F60, 0x02057FE0, "0x2057f9c vicinity")
    dump(arm9, ARM9, 0x02052F00, 0x02052F60, "GroundRefreshV")

    # Does RecruitHpOverwrite's r4 (ground*) get team copy that uses +0xA?
    # Trace: after 0x2048ac4, callers at 0x2048ab4 etc.
    dump(arm9, ARM9, 0x020484F0, 0x020485A0, "RecruitHp callers 0x20485xx")
    dump(arm9, ARM9, 0x02048A00, 0x02048AC0, "RecruitHp callers 0x2048axx")

    # Search entire arm9+ov29 for: strh to #0x10 where the VALUE register was
    # recently loaded via ldrsh #0x12 OR ldrh #0x12 OR was result of add of those
    # Already know TeamSync. Also find strb to #0x10 (HP V as byte!)
    print("\n=== strb #0x10 (HP V low byte writers) arm9 ===")
    for off in range(0, len(arm9) - 3, 4):
        w = struct.unpack_from("<I", arm9, off)[0]
        if (w >> 26) & 3 != 1:
            continue
        if (w >> 25) & 1:
            continue
        if not ((w >> 22) & 1):  # B
            continue
        if (w >> 20) & 1:  # L
            continue
        if not ((w >> 24) & 1) or not ((w >> 23) & 1):
            continue
        imm = w & 0xFFF
        if imm != 0x10:
            continue
        rn = (w >> 16) & 0xF
        if rn == 13:
            continue
        rd = (w >> 12) & 0xF
        print(f"  {ARM9+off:08X}  strb r{rd}, [r{rn}, #0x10]")

    print("\n=== strb #0x10 ov29 (non-sp) sample near team funcs ===")
    for off in range(0, len(ov29) - 3, 4):
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w >> 26) & 3 != 1 or (w >> 25) & 1:
            continue
        if not ((w >> 22) & 1) or (w >> 20) & 1:
            continue
        if not ((w >> 24) & 1) or not ((w >> 23) & 1):
            continue
        if (w & 0xFFF) != 0x10:
            continue
        rn = (w >> 16) & 0xF
        if rn == 13:
            continue
        addr = OV29 + off
        if 0x022FD000 <= addr <= 0x022FF000 or 0x02315000 <= addr <= 0x02316000:
            rd = (w >> 12) & 0xF
            print(f"  {addr:08X}  strb r{rd}, [r{rn}, #0x10]")

    # Life seed path writes strb to team+0x10 - already known in BaseStats
    # Check WonderGummi in patched full ROM later

    # Critical: when TeamSync nops maxHP write, does the PRECEDING
    # team-member creation for a NEW recruit write max HP?
    # Look for ov29 code that: GetActiveTeamMember / allocate, then
    # copies from monster+0x12 to team+0x10 with DIFFERENT pattern
    # (e.g. ldrh, or mov then strh, or stm)

    # stm/ldm copy of HP halfwords?
    print("\n=== ov29 stm/strd near TeamSync (0x22FE048) ===")
    dump(ov29, OV29, 0x022FE048, 0x022FE0A0, "TeamSync body")

    # Search for recruit in ov29 via string refs or known pmdsky addresses from web
    # Try common: TryRecruit / HandleRecruit at various
    # Scan for bl to TeamSync and show 64B before each call with annotation
    print("\n=== contexts of bl TeamSync ===")
    for off in range(0, len(ov29) - 3, 4):
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w >> 25) & 7 != 5 or not ((w >> 24) & 1):
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        if OV29 + off + 8 + (imm << 2) != 0x022FE048:
            continue
        addr = OV29 + off
        print(f"\n--- bl TeamSync at {addr:#x} ---")
        dump(ov29, OV29, addr - 0x50, addr + 0x10, f"ctx {addr:#x}")


if __name__ == "__main__":
    main()
