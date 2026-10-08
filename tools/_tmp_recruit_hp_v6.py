"""Dump ov29 team-create / recruit-join sites and remaining ground+0xA writers."""
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
    cs = {14: "", 1: "ne", 0: "eq"}.get(cond, f"?{cond}")
    return f"{op}{cs} r{rd}, [r{rn}, #{imm:#x}]" if imm is not None else f"{op}{cs}"


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
        print(f"{addr:08X}  {w:08X}  {'; '.join(note)}")


def find_start(data, load, addr):
    off = addr - load
    for i in range(0, 0x800, 4):
        w = struct.unpack_from("<I", data, off - i)[0]
        if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):
            return addr - i
    return addr


def xrefs_to(data, load, target):
    out = []
    for off in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if (w >> 25) & 7 != 5:
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        addr = load + off
        if addr + 8 + (imm << 2) == target:
            out.append((addr, "bl" if (w >> 24) & 1 else "b"))
    return out


def main():
    arm9, ov29 = load(ROM)

    # Sites near InitTeamMember that write +0x10
    for site in (0x022FD290, 0x022FD9AC, 0x022FDB4C, 0x022FDC50):
        start = find_start(ov29, OV29, site)
        print(f"\n## site {site:#x} func {start:#x}")
        print("xrefs:", xrefs_to(ov29, OV29, start)[:20])
        dump(ov29, OV29, max(start, site - 0x40), site + 0x40, f"near {site:#x}")

    # Dump 0x02052e2c (called before team+0x10 fill)
    dump(arm9, ARM9, 0x02052E20, 0x02052E50, "02052e2c preamble")
    start = find_start(arm9, ARM9, 0x02052E2C)
    print("02052e2c func", hex(start), "xrefs arm9", xrefs_to(arm9, ARM9, start)[:15])
    print("xrefs ov29", xrefs_to(ov29, OV29, start)[:15])
    dump(arm9, ARM9, start, min(start + 0x100, 0x02052E50), "fn 02052e2c")

    # Remaining ground +0xA writers - dump each
    for site in (
        0x02052F14,
        0x02053518,
        0x02055F6C,
        0x02057724,
        0x02057A94,
        0x02057DE0,
        0x02057F9C,
    ):
        start = find_start(arm9, ARM9, site)
        print(f"\n## ground+0xA writer {site:#x} in {start:#x}")
        dump(arm9, ARM9, site - 0x30, site + 0x20, f"writer {site:#x}")

    # Search ov29 for strh to #0x10 where preceding insn loads from #0x12
    # with FIXED decode (any register matching)
    print("\n=== ov29 ldrsh/ldrh #0x12 then strh #0x10 within 40B (any rd) ===")
    for off in range(0, len(ov29) - 44, 4):
        w = struct.unpack_from("<I", ov29, off)[0]
        h = hw(w)
        if not h or not (h.startswith("ldrsh") or h.startswith("ldrh")):
            continue
        if "#0x12" not in h:
            continue
        for k in range(4, 40, 4):
            w2 = struct.unpack_from("<I", ov29, off + k)[0]
            h2 = hw(w2)
            if h2 and h2.startswith("strh") and "#0x10" in h2:
                print(f"  {OV29+off:08X} {h} ... {OV29+off+k:08X} {h2}")
                break

    # Vanilla compare for TeamSync only
    romv = NintendoDSRom.fromFile(str(Path(r"C:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")))
    table = loadOverlayTable(romv.arm9OverlayTable, lambda _i, _n: b"")
    ov29v = bytes(romv.files[table[29].fileID])
    print("\n=== vanilla ov29 ldrsh #0x12 then strh #0x10 ===")
    for off in range(0, len(ov29v) - 44, 4):
        w = struct.unpack_from("<I", ov29v, off)[0]
        h = hw(w)
        if not h or not h.startswith("ldrsh") or "#0x12" not in h:
            continue
        for k in range(4, 40, 4):
            w2 = struct.unpack_from("<I", ov29v, off + k)[0]
            h2 = hw(w2)
            if h2 and h2.startswith("strh") and "#0x10" in h2:
                print(f"  {OV29+off:08X} {h} ... {OV29+off+k:08X} {h2}")
                break

    # Key: does InitTeamMember or recruit-join WRITE team+0x10 from dungeon?
    # Search strh #0x10 where rn points to team - look for GetActiveTeamMember result stores
    # Dump function at 0x022F7F?? that contains TeamSync calls - find its start
    join = find_start(ov29, OV29, 0x022F834C)
    print(f"\nTeamSync caller func start {join:#x}")
    print("xrefs", xrefs_to(ov29, OV29, join)[:20])
    dump(ov29, OV29, 0x022F8200, 0x022F8380, "before TeamSync call site")

    # Search for "recruit" related: bl to 0x02055b78 from ov29 already none.
    # Try bl 0x020577bc (team fill from ground)
    print("\nxrefs to 0x020577BC", xrefs_to(arm9, ARM9, 0x020577BC), xrefs_to(ov29, OV29, 0x020577BC))

    # Alpha cave at 0x023b81f0 - what does it do?
    # ov36 load 0x023A7080 - may be in arm9 overlay table entry 36
    try:
        ov36 = bytes(rom.files[table[36].fileID]) if False else None
    except Exception:
        ov36 = None
    rom = NintendoDSRom.fromFile(str(ROM))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    if 36 in table:
        ov36 = bytes(rom.files[table[36].fileID])
        OV36 = table[36].ramAddress
        print(f"ov36 load {OV36:#x} size {len(ov36)}")
        # dump around 0x023b81f0
        if OV36 <= 0x023B81F0 < OV36 + len(ov36):
            dump(ov36, OV36, 0x023B81F0, 0x023B8280, "Alpha cave 023b81f0")


if __name__ == "__main__":
    main()
