#!/usr/bin/env python3
"""Scan vanilla xrefs into ov29 cave slot [0x2351380, 0x2351400)."""
from __future__ import annotations

import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OV29 = 0x022DC240
ARM9 = 0x02000000
OV36 = 0x023A7080
RANGE_LO, RANGE_HI = 0x02351380, 0x02351400


def bl_target(addr: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return addr + 8 + (imm << 2)


def arm_ldr_pc_pool(addr: int, word: int) -> int | None:
    cond = (word >> 28) & 0xF
    if cond == 0xF or (word >> 25) & 7 != 1:
        return None
    if ((word >> 16) & 0xF) != 0xF:
        return None
    imm12 = word & 0xFFF
    if not ((word >> 23) & 1):
        imm12 = -imm12
    return ((addr + 8) & ~3) + imm12


def thumb_bl_target(addr: int, hw1: int, hw2: int) -> int | None:
    if (hw1 & 0xF800) != 0xF000 or (hw2 & 0xC000) != 0xC000:
        return None
    s = (hw1 >> 10) & 1
    j1 = (hw2 >> 13) & 1
    j2 = (hw2 >> 11) & 1
    i1 = ~(j1 ^ s) & 1
    i2 = ~(j2 ^ s) & 1
    imm10 = hw1 & 0x3FF
    imm11 = hw2 & 0x7FF
    imm = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if imm & 0x1000000:
        imm -= 0x2000000
    return (addr + 4) + imm


def scan_binary(name: str, data: bytes, base: int, ov29: bytes) -> list[tuple]:
    hits: list[tuple] = []
    ov_end = OV29 + len(ov29)
    n = len(data)
    for off in range(0, n - 3, 2):
        addr = base + off
        if off + 4 <= n:
            word = struct.unpack_from("<I", data, off)[0]
            hi = word >> 24
            if hi in (0xEA, 0xEB):
                tgt = bl_target(addr, word)
                if RANGE_LO <= tgt < RANGE_HI:
                    hits.append((f"arm_{'bl' if hi == 0xEB else 'b'}", addr, off, tgt, None))
            pool = arm_ldr_pc_pool(addr, word)
            if pool is not None and RANGE_LO <= pool < RANGE_HI:
                pval = None
                if OV29 <= pool < ov_end:
                    pval = struct.unpack_from("<I", ov29, pool - OV29)[0]
                hits.append(("arm_ldr_pc", addr, off, pool, pval))
            if RANGE_LO <= word < RANGE_HI:
                hits.append(("word_literal", addr, off, word, word))
            if word == 0x02351384:
                hits.append(("exact_2351384", addr, off, word, word))
        if off + 4 <= n:
            hw1 = struct.unpack_from("<H", data, off)[0]
            hw2 = struct.unpack_from("<H", data, off + 2)[0]
            tgt = thumb_bl_target(addr, hw1, hw2)
            if tgt is not None and RANGE_LO <= tgt < RANGE_HI:
                hits.append(("thumb_bl", addr, off, tgt, None))
            if (hw1 & 0xF800) == 0x4800:
                imm = (hw1 & 0xFF) * 4
                pool = ((addr + 4) & ~2) + imm
                if RANGE_LO <= pool < RANGE_HI:
                    hits.append(("thumb_ldr_pc", addr, off, pool, None))
    return hits


def scan_hud_ldr_high(ov29: bytes, code_lo: int, code_hi: int, watch_lo: int, watch_hi: int, label: str) -> None:
    print(f"\n--- {label}: ldr[pc] from [{code_lo:#x},{code_hi:#x}) -> [{watch_lo:#x},{watch_hi:#x}) ---")
    count = 0
    for off in range(code_lo - OV29, code_hi - OV29, 4):
        if off < 0 or off + 4 > len(ov29):
            continue
        addr = OV29 + off
        word = struct.unpack_from("<I", ov29, off)[0]
        pool = arm_ldr_pc_pool(addr, word)
        if pool is None or not (watch_lo <= pool < watch_hi):
            continue
        pval = struct.unpack_from("<I", ov29, pool - OV29)[0]
        cave = " [IN CAVE RANGE]" if RANGE_LO <= pool < RANGE_HI else ""
        print(f"  {addr:#010x} -> pool {pool:#010x} = {pval:#010x}{cave}")
        count += 1
    if count == 0:
        print("  (none)")


def main() -> None:
    van29 = (REPO / "unpacked/overlay/overlay_0029.bin").read_bytes()
    arm9 = (REPO / "unpacked/arm9.bin").read_bytes()
    ov36_path = REPO / "unpacked/overlay/overlay_0036.bin"
    ov36 = ov36_path.read_bytes() if ov36_path.exists() else b""
    ov_end = OV29 + len(van29)

    print(f"ov29 load={OV29:#x} size={len(van29):#x} ram_end={ov_end:#x}")
    print(f"cave slot RAM [{RANGE_LO:#x}, {RANGE_HI:#x}) file [{RANGE_LO - OV29:#x}, {RANGE_HI - OV29:#x})")
    print(f"vanilla @ 0x2351380: {struct.unpack_from('<I', van29, 0x2351380 - OV29)[0]:#010x}")
    print(f"vanilla @ 0x2351384: {struct.unpack_from('<I', van29, 0x2351384 - OV29)[0]:#010x}")

    print("\n=== TASK 1: ALL xrefs into [0x2351380, 0x2351400) ===")
    all_hits: list[tuple] = []
    for name, data, base in [("ov29", van29, OV29), ("arm9", arm9, ARM9), ("ov36", ov36, OV36)]:
        if not data:
            continue
        hits = scan_binary(name, data, base, van29)
        print(f"\n{name} ({base:#x}, len {len(data):#x}): {len(hits)} hit(s)")
        for h in hits:
            kind, addr, off, tgt, extra = h
            extra_s = f" value={extra:#010x}" if extra is not None else ""
            print(f"  {kind:16} from {addr:#010x} (file+{off:#x}) -> {tgt:#010x}{extra_s}")
        all_hits.extend(hits)

    print("\n=== TASK 2: HUD/status regions ldr pools near cave ===")
    scan_hud_ldr_high(van29, 0x022E7000, 0x022F2000, 0x02350000, 0x02354000, "AllocTopScreenStatus region")
    scan_hud_ldr_high(van29, 0x02339000, 0x0233A000, 0x02350000, 0x02354000, "status icon region")

    print("\n=== TASK 3: sentinel / terminator check ===")
    fo = 0x2351384 - OV29
    zs = fo
    while zs > 0 and van29[zs - 1] == 0:
        zs -= 1
    ze = fo
    while ze < len(van29) and van29[ze] == 0:
        ze += 1
    print(f"Zero run through 0x2351384: file [{zs:#x},{ze:#x}) len={ze - zs} bytes")
    print(f"Note: 0x2351380 holds {struct.unpack_from('<I', van29, 0x2351380 - OV29)[0]:#x} (not zero)")

    print("\nPointer rodata block after fn @ 0x022E3D90 (possible tail slot table):")
    for a in range(0x022E3D94, 0x022E3DD8, 4):
        w = struct.unpack_from("<I", van29, a - OV29)[0]
        in_range = " *** IN CAVE RANGE" if RANGE_LO <= w < RANGE_HI else ""
        print(f"  {a:#010x}: {w:#010x}{in_range}")

    table_pat = struct.pack("<I", 0x022E3D94)
    for name, data, base in [("ov29", van29, OV29), ("arm9", arm9, ARM9)]:
        idx = data.find(table_pat)
        if idx >= 0:
            print(f"Table base 0x022E3D94 stored as word at {name} {base + idx:#010x}")

    print("\nWords equal to ov29 RAM end (overlay sentinel candidates):")
    for off in range(0, len(van29) - 3, 4):
        w = struct.unpack_from("<I", van29, off)[0]
        if ov_end - 0x100 <= w <= ov_end + 0x100:
            print(f"  {OV29 + off:#010x} = {w:#010x} (delta from end: {w - ov_end:+d})")

    print(f"\nTOTAL unique xrefs into cave range: {len(all_hits)}")


if __name__ == "__main__":
    main()
