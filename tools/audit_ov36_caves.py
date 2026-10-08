#!/usr/bin/env python3
"""Audit ov36 cave chain: reservations vs actual non-zero code extents."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

from ndspy.rom import NintendoDSRom

OV36_LOAD = 0x023A7080


def last_nonzero(data: bytes, start: int, end: int) -> int | None:
    for off in range(end - 1, start - 1, -1):
        if data[off] != 0:
            return off
    return None


def main() -> None:
    rom_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Export Rom/_full_stack_ov36.nds")
    state_path = rom_path.with_suffix(".state.json")
    rom = NintendoDSRom(rom_path.read_bytes())
    state = json.loads(state_path.read_text())
    ov36 = rom.loadArm9Overlays()[36].data

    caves: list[dict] = []
    for mod in state["applied"]:
        for cave in mod.get("caves", []):
            if cave["overlay"] != "ov36":
                continue
            fo = cave["file_offset"]
            size = cave["size"]
            last = last_nonzero(ov36, fo, fo + size)
            used = (last - fo + 1) if last is not None else 0
            caves.append(
                {
                    "module": mod["id"],
                    "file_start": fo,
                    "file_end": fo + size,
                    "size": size,
                    "used": used,
                    "load": cave["load_address"],
                    "overflow": used > size,
                }
            )

    caves.sort(key=lambda c: c["file_start"])
    print(f"ov36 audit: {rom_path.name}")
    print(f"hole chain file [0x1A578 .. 0x2D300)\n")
    prev_end = None
    for c in caves:
        gap = c["file_start"] - prev_end if prev_end is not None else c["file_start"] - 0x1A578
        flag = " OVERFLOW" if c["overflow"] else ""
        spill = ""
        if c["used"] > 0 and not c["overflow"]:
            tail = c["file_start"] + c["used"]
            next_start = next((x["file_start"] for x in caves if x["file_start"] > c["file_start"]), len(ov36))
            if tail > c["file_start"] + c["size"]:
                spill = f" SPILL>{c['file_end']:#x}"
            elif tail + 16 > c["file_end"]:
                spill = f" tight(+{c['file_end'] - tail}B free)"
        print(
            f"{c['module']:18} [{c['file_start']:#7x}..{c['file_end']:#x}) "
            f"used {c['used']:#5x}/{c['size']:#x}  gap={gap:#x}{flag}{spill}"
        )
        if prev_end is not None and c["file_start"] < prev_end:
            print(f"  *** RESERVATION OVERLAP with prior cave ending {prev_end:#x}")
        prev_end = c["file_end"]

    print("\n--- scan for non-zero between cave gaps ---")
    for i in range(len(caves) - 1):
        a, b = caves[i], caves[i + 1]
        gap_s, gap_e = a["file_end"], b["file_start"]
        if gap_s >= gap_e:
            continue
        last = last_nonzero(ov36, gap_s, gap_e)
        if last is not None:
            print(f"  non-zero in gap [{gap_s:#x}..{gap_e:#x}): last @ {last:#x}")

    print("\n--- scan 64B past each cave end (spill into next) ---")
    for i, c in enumerate(caves):
        scan_end = caves[i + 1]["file_start"] if i + 1 < len(caves) else c["file_end"] + 64
        spill_start = c["file_start"] + c["size"]
        last = last_nonzero(ov36, spill_start, min(scan_end, len(ov36)))
        if last is not None:
            print(
                f"  {c['module']}: bytes past reservation end {spill_start:#x} "
                f"through {last:#x} (+{last - spill_start + 1}B)"
            )


if __name__ == "__main__":
    main()
