"""Find recruit join writers: xrefs to TeamSync / RecruitHp / stores of maxHP into team+0x10."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROM_P = Path(
    r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed.nds"
)
ROM_V = Path(r"C:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
OV29 = 0x022DC240
ARM9 = 0x02000000


def load(path):
    rom = NintendoDSRom.fromFile(str(path))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return bytes(rom.arm9), bytes(rom.files[table[29].fileID])


def decode_hw(word):
    if (word >> 25) & 7:
        return None
    if ((word >> 4) & 0xF) != 0xB:
        return None
    L = (word >> 20) & 1
    S = (word >> 6) & 1
    H = (word >> 5) & 1
    U = (word >> 23) & 1
    I = (word >> 22) & 1
    P = (word >> 24) & 1
    rn = (word >> 16) & 0xF
    rd = (word >> 12) & 0xF
    imm = ((word >> 4) & 0xF0) | (word & 0xF) if I else None
    if H and not S:
        op = "ldrh" if L else "strh"
    elif H and S:
        op = "ldrsh" if L else None
    else:
        return None
    if op is None:
        return None
    cond = (word >> 28) & 0xF
    cs = "" if cond == 14 else f"?{cond}"
    if I and P and U:
        return f"{op}{cs} r{rd}, [r{rn}, #{imm:#x}]"
    return f"{op}{cs}"


def find_bl_to(data, load, target):
    hits = []
    for off in range(0, len(data) - 3, 4):
        word = struct.unpack_from("<I", data, off)[0]
        if (word >> 25) & 7 != 5:
            continue
        if (word >> 24) & 1 != 1:  # need BL (or B)
            # include B too
            pass
        link = (word >> 24) & 1
        imm = word & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        addr = load + off
        dest = addr + 8 + (imm << 2)
        if dest == target:
            hits.append((addr, "bl" if link else "b", word))
    return hits


def dump(data, load, start, end, title):
    print(f"\n=== {title} ===")
    for addr in range(start, end, 4):
        w = struct.unpack_from("<I", data, addr - load)[0]
        hw = decode_hw(w)
        extra = f"  {hw}" if hw else ""
        # branch
        if (w >> 25) & 7 == 5:
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            dest = addr + 8 + (imm << 2)
            link = (w >> 24) & 1
            print(f"{addr:08X}  {w:08X}  {'bl' if link else 'b'} {dest:#010x}{extra}")
        elif w == 0xE1A00000:
            print(f"{addr:08X}  {w:08X}  nop")
        elif hw:
            print(f"{addr:08X}  {w:08X}  {hw}")
        elif (w >> 26) & 3 == 1 and not ((w >> 25) & 1):
            B = (w >> 22) & 1
            L = (w >> 20) & 1
            U = (w >> 23) & 1
            rn = (w >> 16) & 0xF
            rd = (w >> 12) & 0xF
            imm = w & 0xFFF
            op = ("ldr" if L else "str") + ("b" if B else "")
            print(f"{addr:08X}  {w:08X}  {op} r{rd}, [r{rn}, #{'+' if U else '-'}{imm:#x}]")
        elif (w & 0xFFFF0000) == 0xE92D0000:
            print(f"{addr:08X}  {w:08X}  push {{{w & 0xFFFF:#x}}}")
        elif (w & 0xFFFF0000) == 0xE8BD0000:
            print(f"{addr:08X}  {w:08X}  pop {{{w & 0xFFFF:#x}}}")
        else:
            print(f"{addr:08X}  {w:08X}")


def main():
    for tag, path in (("patched", ROM_P), ("vanilla", ROM_V)):
        print(f"\n########## {tag} ##########")
        arm9, ov29 = load(path)

        # Confirm vanilla TeamSyncMaxHp insn
        for addr in (0x022FE064, 0x022FE068, 0x022FE06C):
            w = struct.unpack_from("<I", ov29, addr - OV29)[0]
            print(f"{tag} {addr:#x}: {w:08X} {decode_hw(w)}")

        for addr in (0x02048AF8, 0x02048B00, 0x02048B04, 0x02048B0C):
            w = struct.unpack_from("<I", arm9, addr - ARM9)[0]
            print(f"{tag} {addr:#x}: {w:08X} {decode_hw(w)}")

        print("\nXrefs to TeamSync 0x022FE048:")
        for a, k, w in find_bl_to(ov29, OV29, 0x022FE048):
            print(f"  {a:#010x} {k}")
        print("Xrefs to RecruitHp fn 0x02048AC4:")
        for a, k, w in find_bl_to(arm9, ARM9, 0x02048AC4):
            print(f"  arm9 {a:#010x} {k}")
        for a, k, w in find_bl_to(ov29, OV29, 0x02048AC4):
            print(f"  ov29 {a:#010x} {k}")
        print("Xrefs to RecruitInit 0x02055B78:")
        for a, k, w in find_bl_to(arm9, ARM9, 0x02055B78):
            print(f"  arm9 {a:#010x} {k}")
        for a, k, w in find_bl_to(ov29, OV29, 0x02055B78):
            print(f"  ov29 {a:#010x} {k}")

        # ov29 strh #0x10 that are NOT to r13 (stack) — candidate team/dungeon writers
        print("\nov29 strh #0x10 (non-SP):")
        for off in range(0, len(ov29) - 3, 4):
            w = struct.unpack_from("<I", ov29, off)[0]
            s = decode_hw(w)
            if not s or not s.startswith("strh"):
                continue
            if "#0x10" not in s:
                continue
            rn = (w >> 16) & 0xF
            if rn == 13:
                continue
            addr = OV29 + off
            print(f"  {addr:08X}  {s}")

        # Look at function containing 0x022E8794, 0x022E8CD4 near TeamSync region
        # and any strh #0x10 between 0x022FDxxx-0x022FExxx
        print("\nstrh #0x10 in InitTeamMember/TeamSync neighborhood 0x022FD000-0x022FF000:")
        for off in range(0x022FD000 - OV29, 0x022FF000 - OV29, 4):
            w = struct.unpack_from("<I", ov29, off)[0]
            s = decode_hw(w)
            if s and s.startswith("strh") and "#0x10" in s:
                print(f"  {OV29+off:08X}  {s}")

        # Disassemble potential "create team member from monster" near xrefs
        # Also dump 0x020569CC (called after recruit path)
        dump(arm9, ARM9, 0x020569C0, 0x02056A80, f"{tag} after-recruit 0x20569cc")
        dump(arm9, ARM9, 0x020555A0, 0x02055640, f"{tag} 0x20555a8")
        dump(arm9, ARM9, 0x020544C0, 0x02054540, f"{tag} 0x20544c8")

        # Search arm9 for strhne/strh to #0xa right after loading #0x12 (maxhp pattern)
        print("\narm9 pattern: ldrsh .* #0x12 within 16B before strh #0xa:")
        for off in range(0, len(arm9) - 20, 4):
            w = struct.unpack_from("<I", arm9, off)[0]
            s = decode_hw(w)
            if not s or not s.startswith("ldrsh") or "#0x12" not in s:
                continue
            for k in range(4, 20, 4):
                w2 = struct.unpack_from("<I", arm9, off + k)[0]
                s2 = decode_hw(w2)
                if s2 and s2.startswith("strh") and "#0xa" in s2:
                    print(f"  {ARM9+off:08X} {s} ... {ARM9+off+k:08X} {s2}")
                    break
        print("\nov29 pattern: ldrsh #0x12 then strh #0x10:")
        for off in range(0, len(ov29) - 20, 4):
            w = struct.unpack_from("<I", ov29, off)[0]
            s = decode_hw(w)
            if not s or not s.startswith("ldrsh") or "#0x12" not in s:
                continue
            for k in range(4, 24, 4):
                w2 = struct.unpack_from("<I", ov29, off + k)[0]
                s2 = decode_hw(w2)
                if s2 and s2.startswith("strh") and "#0x10" in s2:
                    print(f"  {OV29+off:08X} {s} ... {OV29+off+k:08X} {s2}")
                    break


if __name__ == "__main__":
    main()
