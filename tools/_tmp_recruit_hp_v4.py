"""Fixed ldrsh decode; dump join/TeamSync callers; find maxHP copies into team/ground V slots."""
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


def load(path):
    rom = NintendoDSRom.fromFile(str(path))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return bytes(rom.arm9), bytes(rom.files[table[29].fileID])


def hw(word):
    """Decode ARM halfword/signed-byte transfer. Returns (op, rd, rn, imm|None, cond)."""
    if (word >> 25) & 7:
        return None
    opx = (word >> 4) & 0xF
    # bits: 1 S H 1
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
    if op is None:
        return None
    imm = ((word >> 4) & 0xF0) | (word & 0xF) if I else None
    if imm is not None and not U:
        imm = -imm
    return op, rd, rn, imm, cond, P


def hw_s(word):
    r = hw(word)
    if not r:
        return None
    op, rd, rn, imm, cond, P = r
    cs = {14: "", 1: "ne", 0: "eq"}.get(cond, f"?{cond}")
    if imm is None:
        return f"{op}{cs} r{rd}, [r{rn}, r?]"
    if P:
        return f"{op}{cs} r{rd}, [r{rn}, #{imm:#x}]"
    return f"{op}{cs} r{rd}, [r{rn}], #{imm:#x}"


def dump(data, load, start, end, title):
    print(f"\n=== {title} ===")
    for addr in range(start, end, 4):
        w = struct.unpack_from("<I", data, addr - load)[0]
        parts = []
        h = hw_s(w)
        if h:
            parts.append(h)
        if (w >> 25) & 7 == 5:
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            dest = addr + 8 + (imm << 2)
            link = (w >> 24) & 1
            parts.append(f"{'bl' if link else 'b'} {dest:#010x}")
        if w == 0xE1A00000:
            parts.append("nop")
        if (w & 0x0E000000) == 0x04000000 and not ((w >> 25) & 1):
            B = (w >> 22) & 1
            L = (w >> 20) & 1
            U = (w >> 23) & 1
            rn = (w >> 16) & 0xF
            rd = (w >> 12) & 0xF
            imm = w & 0xFFF
            op = ("ldr" if L else "str") + ("b" if B else "")
            parts.append(f"{op} r{rd}, [r{rn}, #{'+' if U else '-'}{imm:#x}]")
        if (w & 0xFFFF0000) == 0xE92D0000:
            parts.append(f"push {w & 0xFFFF:#x}")
        if (w & 0xFFFF0000) == 0xE8BD0000:
            parts.append(f"pop {w & 0xFFFF:#x}")
        # mov imm
        if ((w >> 21) & 0x7F) == 0x1A and (w >> 25) & 1 and (w >> 28) == 0xE:
            rd = (w >> 12) & 0xF
            rot = (w >> 8) & 0xF
            imm8 = w & 0xFF
            val = (
                ((imm8 >> (2 * rot)) | (imm8 << (32 - 2 * rot))) & 0xFFFFFFFF
                if rot
                else imm8
            )
            parts.append(f"mov r{rd}, #{val:#x}")
        print(f"{addr:08X}  {w:08X}  {'; '.join(parts) if parts else ''}")


def scan_maxhp_to_v(data, load, title):
    """ldrsh #0x12 (max HP) followed soon by strh to #0x10 or #0xa."""
    print(f"\n=== {title}: ldrsh #0x12 -> strh #0x10/#0xa ===")
    for off in range(0, len(data) - 32, 4):
        w = struct.unpack_from("<I", data, off)[0]
        r = hw(w)
        if not r:
            continue
        op, rd, rn, imm, cond, P = r
        if op != "ldrsh" or imm not in (0x12,):
            continue
        src_rd = rd
        for k in range(4, 32, 4):
            w2 = struct.unpack_from("<I", data, off + k)[0]
            r2 = hw(w2)
            if not r2:
                continue
            op2, rd2, rn2, imm2, cond2, P2 = r2
            if op2 == "strh" and imm2 in (0x10, 0xA) and rd2 == src_rd:
                print(
                    f"  {load+off:08X} {hw_s(w)}  ->  {load+off+k:08X} {hw_s(w2)}"
                )
                break


def scan_curhp_to_team10(data, load, title):
    """ldrsh #0x10 (could be cur HP on dungeon) -> strh #0x10 on different base."""
    print(f"\n=== {title}: ldrsh #0x10 -> strh #0x10 (different rn) ===")
    for off in range(0, len(data) - 24, 4):
        w = struct.unpack_from("<I", data, off)[0]
        r = hw(w)
        if not r:
            continue
        op, rd, rn, imm, cond, P = r
        if op != "ldrsh" or imm != 0x10:
            continue
        for k in range(4, 24, 4):
            w2 = struct.unpack_from("<I", data, off + k)[0]
            r2 = hw(w2)
            if not r2:
                continue
            op2, rd2, rn2, imm2, cond2, P2 = r2
            if op2 == "strh" and imm2 == 0x10 and rd2 == rd and rn2 != rn:
                print(
                    f"  {load+off:08X} {hw_s(w)}  ->  {load+off+k:08X} {hw_s(w2)}"
                )
                break


def main():
    for tag, path in (("patched", ROM), ("vanilla", ROM_V)):
        print(f"\n########## {tag} ##########")
        arm9, ov29 = load(path)
        for addr, blob, base in (
            (0x022FE064, ov29, OV29),
            (0x022FE068, ov29, OV29),
            (0x02048AF8, arm9, ARM9),
            (0x02048B00, arm9, ARM9),
        ):
            w = struct.unpack_from("<I", blob, addr - base)[0]
            print(f"{addr:#x}: {w:08X} {hw_s(w)}")

        scan_maxhp_to_v(ov29, OV29, f"{tag} ov29")
        scan_maxhp_to_v(arm9, ARM9, f"{tag} arm9")
        scan_curhp_to_team10(ov29, OV29, f"{tag} ov29")

        # TeamSync callers and surrounding join logic
        dump(ov29, OV29, 0x022F7F80, 0x022F8520, f"{tag} around TeamSync callers")
        dump(ov29, OV29, 0x022FD250, 0x022FD2C0, f"{tag} 022FD290 site")
        dump(ov29, OV29, 0x022FD980, 0x022FDC80, f"{tag} 022FD9AC-FDC50 sites")

        # Wild spawn: do Atk/Def uint8 caches get non-zero? And is there HP-related field?
        # Spawn path writes +0x12 max HP; check if anything writes team from spawn stats
        dump(ov29, OV29, 0x022FE2FC, 0x022FE2FC + 0x20, f"{tag} SpawnMonster entry")


if __name__ == "__main__":
    main()
