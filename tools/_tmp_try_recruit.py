"""Disassemble TryRecruit and find HP/V writes into team_member / ground."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROM = Path(
    r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed.nds"
)
ROM_V = Path(r"C:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
OV29 = 0x022DC240
ARM9 = 0x02000000

# From pmdsky
TRY_RECRUIT = 0x0230E064
RECRUIT_CHECK = 0x0230DBD0
PREPARE_MENU = 0x022E8080


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
        print(f"{addr:08X}  {w:08X}  {'; '.join(note)}")


def find_end(data, load, start, limit=0x800):
    """Heuristic: next push {..lr} after some progress, or pop pc."""
    off = start - load
    for i in range(0x20, limit, 4):
        w = struct.unpack_from("<I", data, off + i)[0]
        if (w & 0xFFFF0000) == 0xE8BD0000 and (w & 0x8000):
            return start + i + 4
        if i > 0x40 and (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):
            return start + i
    return start + limit


def main():
    for tag, path in (("patched", ROM), ("vanilla", ROM_V)):
        print(f"\n########## {tag} ##########")
        arm9, ov29 = load(path)
        end = find_end(ov29, OV29, TRY_RECRUIT, 0x600)
        print(f"TryRecruit {TRY_RECRUIT:#x} .. {end:#x} ({end-TRY_RECRUIT} bytes)")
        dump(ov29, OV29, TRY_RECRUIT, end, f"{tag} TryRecruit")

        # Highlight stores to +0x10 / +0xa / +0xe / +0x12 within TryRecruit
        print(f"\n{tag} TryRecruit notable stores/loads:")
        for addr in range(TRY_RECRUIT, end, 4):
            w = struct.unpack_from("<I", ov29, addr - OV29)[0]
            h = hw(w)
            if not h:
                continue
            if any(x in h for x in ("#0xa", "#0x10", "#0xe", "#0x12", "#0x1a", "#0x1c")):
                print(f"  {addr:08X}  {h}")
            if h.startswith("str") and ("#0x" in h):
                # also show all strh/strb
                if h.startswith("strh") or h.startswith("strb"):
                    print(f"  {addr:08X}  {h}")

        # Also dump callees that look like join helpers - collect unique bl targets in body
        targets = []
        for addr in range(TRY_RECRUIT, end, 4):
            w = struct.unpack_from("<I", ov29, addr - OV29)[0]
            if (w >> 25) & 7 != 5 or not ((w >> 24) & 1):
                continue
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            dest = addr + 8 + (imm << 2)
            targets.append((addr, dest))
        print(f"\n{tag} TryRecruit BL targets:")
        for a, d in targets:
            print(f"  {a:08X} -> {d:#010x}")


if __name__ == "__main__":
    main()
