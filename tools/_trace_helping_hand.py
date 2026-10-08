#!/usr/bin/env python3
"""Trace BoostOffensiveStat calls near Helping Hand helpers."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
VANILLA = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
BASE = 0x022DC240
TARGET = 0x0231399C


def main() -> None:
    rom = NintendoDSRom(VANILLA.read_bytes())
    ov = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[29].fileID]

    ranges = [
        (0x0231657C, 0x02316680),
        (0x02326550, 0x023265A0),
        (0x023143E8, 0x02314480),
        (0x0232CD00, 0x0232CE00),
    ]
    for start, end in ranges:
        for addr in range(start, end, 4):
            w = struct.unpack_from("<I", ov, addr - BASE)[0]
            if (w >> 24) != 0xEB:
                continue
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            if addr + 8 + (imm << 2) != TARGET:
                continue
            print(f"BoostOffensiveStat call @ {addr:#010x} (range {start:#x}-{end:#x})")
            for i in range(-5, 2):
                a = addr + i * 4
                ww = struct.unpack_from("<I", ov, a - BASE)[0]
                mark = ">>" if i == 0 else "  "
                print(f"{mark} {a:#010x}: {ww:08x}")
            print()


if __name__ == "__main__":
    main()
