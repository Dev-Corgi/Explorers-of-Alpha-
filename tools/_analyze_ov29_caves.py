#!/usr/bin/env python3
"""Analyze ov29 safe cave placement vs StartMFunc."""
from __future__ import annotations

from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
OV29_LOAD = 0x022DC240
START_MFUNC_RAM = 0x02330134
END_MFUNC_RAM = 0x023326CC
START_MFUNC_FILE = START_MFUNC_RAM - OV29_LOAD
END_MFUNC_FILE = END_MFUNC_RAM - OV29_LOAD


def find_runs(data: bytes, min_size: int = 64, align: int = 4) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    i = 0
    n = len(data)
    while i < n:
        if data[i] != 0:
            i += 1
            continue
        j = i
        while j < n and data[j] == 0:
            j += 1
        s = (i + align - 1) // align * align
        length = j - s
        if length >= min_size:
            runs.append((s, length))
        i = j
    return runs


def overlaps_start_mfunc(la: int, end_la: int) -> bool:
    return not (end_la <= START_MFUNC_RAM or la >= END_MFUNC_RAM)


def main() -> None:
    vrom = NintendoDSRom((ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds").read_bytes())
    table = loadOverlayTable(vrom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = vrom.files[table[29].fileID]
    print(f"ov29 size={len(ov29):#x} load={OV29_LOAD:#x}")
    print(
        f"StartMFunc file=[{START_MFUNC_FILE:#x}..{END_MFUNC_FILE:#x}) "
        f"ram=[{START_MFUNC_RAM:#x}..{END_MFUNC_RAM:#x}) "
        f"size={END_MFUNC_FILE - START_MFUNC_FILE}"
    )

    runs = find_runs(ov29, 64)
    print("\nZero runs >=64 outside StartMFunc (sorted by length):")
    safe_runs = []
    for s, length in runs:
        la = OV29_LOAD + s
        end_la = la + length
        if overlaps_start_mfunc(la, end_la):
            continue
        safe_runs.append((s, length, la, end_la))
    for s, length, la, end_la in sorted(safe_runs, key=lambda x: -x[1])[:15]:
        zone = "pre" if end_la <= START_MFUNC_RAM else "post"
        print(f"  [{zone}] file=[{s:#x}..{s + length:#x}) len={length} la=[{la:#x}..{end_la:#x})")

    pre_cap = sum(l for s, l in runs if s + l <= START_MFUNC_FILE)
    post_cap = sum(l for s, l in runs if s >= END_MFUNC_FILE)
    print(f"\nPre-StartMFunc zero capacity: {pre_cap} ({pre_cap:#x})")
    print(f"Post-EndMFunc zero capacity: {post_cap} ({post_cap:#x})")

    needs = [("orb_charges_v2", 896), ("berry_boost", 512), ("iq_change", 768),
             ("room_charge_v4", 768), ("tm_read", 2300), ("z_move_v2", 2048)]
    gap = 16
    total = sum(n for _, n in needs) + gap * (len(needs) - 1)
    print(f"\nStack need (with {gap}B gaps): {total} ({total:#x})")

    # simulate chain from largest pre run
    pre_runs = [(s, l) for s, l in runs if s + l <= START_MFUNC_FILE]
    if pre_runs:
        start, _ = max(pre_runs, key=lambda x: x[1])
        cursor = start
        print(f"\nChain from pre run @ {start:#x}:")
        for name, need in needs:
            la = OV29_LOAD + cursor
            print(f"  {name:18} file={cursor:#x} la={la:#x} size={need}")
            cursor = (cursor + need + gap + 3) // 4 * 4
        print(f"  chain ends file={cursor:#x} la={OV29_LOAD + cursor:#x}")
        print(f"  StartMFunc begins at {START_MFUNC_FILE:#x} — margin={START_MFUNC_FILE - cursor}")


if __name__ == "__main__":
    main()
