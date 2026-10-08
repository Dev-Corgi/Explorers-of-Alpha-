"""Find difficulty decoder: sequential checks of performance flags 56-59."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

FILES = {
    "arm9": (Path(r"c:\Working\SkyTemple\unpacked\arm9.bin"), 0x02000000),
    "ov29": (Path(r"c:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin"), 0x022DC240),
    "ov36": (Path(r"c:\Working\SkyTemple\unpacked\overlay\overlay_0036.bin"), 0x023A7080),
}
OUT = Path(r"c:\Working\SkyTemple\tools\_scan_diff_decode_out.txt")
PERF = 0x0204CA94


def bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def main() -> None:
    lines: list[str] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    # Pattern A: within a 0x80 window, find 2+ distinct immediates from {55,56,57,58,59}
    # used as mov r0,#imm followed within 8 bytes by bl
    for name, (path, load) in FILES.items():
        data = path.read_bytes()
        # Collect all (offset, imm) for mov r0,#imm where next is bl
        sites: list[tuple[int, int, int]] = []  # off, imm, bl_tgt
        for imm in range(0, 80):
            word = 0xE3A00000 | imm
            pat = struct.pack("<I", word)
            off = 0
            while True:
                i = data.find(pat, off)
                if i < 0:
                    break
                if i % 4 == 0 and i + 8 <= len(data):
                    w2 = struct.unpack_from("<I", data, i + 4)[0]
                    if w2 >> 24 == 0xEB:
                        tgt = bl_target(load + i + 4, w2)
                        if tgt == PERF or imm in (55, 56, 57, 58, 59):
                            sites.append((i, imm, tgt))
                off = i + 1

        lines.append(f"=== {name}: mov r0,#imm; bl sites (imm 55-59 or bl PERF) ===")
        for off, imm, tgt in sorted(sites):
            mark = ""
            if tgt == PERF:
                mark = " -> PERF"
            elif imm in (55, 56, 57, 58, 59):
                mark = f" -> 0x{tgt:08X}"
            if mark:
                lines.append(f"  0x{load + off:08X}  imm={imm}{mark}")

        # Cluster analysis for PERF calls with imm 55-59
        perf_sites = [(o, i) for o, i, t in sites if t == PERF]
        for o, imm in perf_sites:
            if imm in (55, 56, 57, 58, 59):
                lines.append(f"\n*** DIFFICULTY/LS PERF CALL {name} 0x{load + o:08X} flag={imm}")
                start = max(0, o - 0x60)
                end = min(len(data), o + 0x80)
                for ins in md.disasm(data[start:end], load + start):
                    lines.append(f"  {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")

    # Pattern B: look for GetPerformanceFlag wrapper in ov36 that takes flag in another reg
    # Search all bl from ov36 into arm9 range that might be wrappers
    lines.append("\n=== ov36 bl into arm9 0x204xxxx-0x206xxxx (possible wrappers) sample ===")
    data = FILES["ov36"][0].read_bytes()
    load = FILES["ov36"][1]
    targets: dict[int, int] = {}
    for off in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if w >> 24 != 0xEB:
            continue
        tgt = bl_target(load + off, w)
        if 0x02040000 <= tgt <= 0x02070000:
            targets[tgt] = targets.get(tgt, 0) + 1
    for tgt, count in sorted(targets.items(), key=lambda x: -x[1])[:40]:
        lines.append(f"  bl 0x{tgt:08X}  x{count}")

    # Pattern C: search for ProcessSpecial-like difficulty - script ops already known
    # Look at global struct offsets mentioned: 0x759 level scaling cache
    lines.append("\n=== ldrb/strb [rN, #0x759] and #0x748 in arm9/ov29/ov36 ===")
    for name, (path, load) in FILES.items():
        data = path.read_bytes()
        for off_imm in (0x748, 0x759, 0x75A, 0x75B, 0x75C):
            # ldrb rt, [rn, #imm] encoding: cond 0101 0101 Rn Rt imm12  => E5DNRIMM
            # Also strb: E5C
            count = 0
            for off in range(0, len(data) - 3, 4):
                w = struct.unpack_from("<I", data, off)[0]
                if (w & 0x0FFF0FFF) == (0x05D00000 | off_imm) or (
                    w & 0x0FFF0FFF
                ) == (0x05C00000 | off_imm):
                    # verify imm12 matches
                    if (w & 0xFFF) != off_imm:
                        continue
                    op = "ldrb" if (w & 0x0FF00000) == 0x05D00000 else "strb"
                    count += 1
                    if count <= 12:
                        lines.append(f"  {name} 0x{load + off:08X}  {op} ?, [?, #0x{off_imm:X}] word=0x{w:08X}")
            if count:
                lines.append(f"  ({name} #0x{off_imm:X}: {count} total)")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
