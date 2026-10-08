"""Diff base unpacked arm9 vs EoA arm9; find hooks/branches in tail."""
from __future__ import annotations

import struct
from pathlib import Path

BASE = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin")
EOA = Path(r"C:\Working\SkyTemple\tools\_tmp_eoa_arm9.bin")
OUT = Path(r"C:\Working\SkyTemple\tools\_eoa_arm9_diff.txt")
TAIL = len(BASE.read_bytes())


def regions(a: bytes, b: bytes) -> list[tuple[int, int]]:
    out = []
    start = None
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            if start is None:
                start = i
        elif start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, n))
    return out


def scan_arm_branches(data: bytes, start: int, end: int) -> list[str]:
    lines = []
    i = start
    while i + 3 < end:
        w = struct.unpack_from("<I", data, i)[0]
        top = w >> 24
        if top == 0xEA:  # ARM b
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x01000000
            tgt = i + 8 + (imm << 2)
            if tgt >= TAIL:
                lines.append(f"  ARM b @ 0x{i:X} -> 0x{tgt:X} (tail)")
        elif top in (0xEB, 0xFA):  # bl / blx
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x01000000
            tgt = i + 8 + (imm << 2)
            lines.append(f"  ARM {'bl' if top==0xEB else 'blx'} @ 0x{i:X} -> 0x{tgt:X}")
        i += 4
    return lines


def main() -> None:
    base = BASE.read_bytes()
    eoa = EOA.read_bytes()
    lines = [f"base=0x{len(base):X} eoa=0x{len(eoa):X} tail@0x{TAIL:X}"]

    changed = regions(base, eoa)
    lines.append(f"Changed overlapping regions: {len(changed)}")
    for s, e in changed[:30]:
        lines.append(f"  0x{s:X}-0x{e:X} ({e-s} bytes)")

    # branches from base into tail
    lines.append("\nBranches from base region into tail:")
    lines.extend(scan_arm_branches(eoa, 0, TAIL)[:50])

    # search tail for ARM function prologue stmfd sp!, {..lr}
    tail = eoa[TAIL:]
    lines.append(f"\nTail size 0x{len(tail):X}")
    prologues = []
    for i in range(0, len(tail) - 3, 4):
        w = struct.unpack_from("<I", tail, i)[0]
        # stmfd sp!, {..., lr} common: e92d4xxx
        if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):
            prologues.append(TAIL + i)
    lines.append(f"ARM prologues in tail: {len(prologues)} (first 30)")
    for p in prologues[:30]:
        lines.append(f"  0x{p:X}")

    # Search tail for ASCII strings
    lines.append("\nPrintable strings in tail (len>=8):")
    cur = []
    strs = []
    for i, b in enumerate(tail):
        if 32 <= b < 127:
            cur.append(chr(b))
        else:
            if len(cur) >= 8:
                strs.append((TAIL + i - len(cur), "".join(cur)))
            cur = []
    for off, s in strs[:40]:
        if any(k in s.lower() for k in ["level", "guest", "team", "scale", "perf", "flag"]):
            lines.append(f"  0x{off:X}: {s}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
