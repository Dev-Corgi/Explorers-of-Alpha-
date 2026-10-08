"""Dump exact words at recommended patch sites (patched + vanilla)."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROMS = {
    "base_stats": Path(
        r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed.nds"
    ),
    "vanilla": Path(r"C:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds"),
}
OV29 = 0x022DC240
SITES = [
    0x022F9084,
    0x022F9088,
    0x022F908C,
    0x022F9090,
    0x0230E1A8,
    0x0230E1AC,
    0x0230E1B0,
    0x0230E1B4,
    0x0230E1E8,
    0x0230E1F8,
    0x0230E4B8,
    0x022FE064,
    0x022FE068,
]


def main():
    for tag, path in ROMS.items():
        rom = NintendoDSRom.fromFile(str(path))
        table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
        ov29 = bytes(rom.files[table[29].fileID])
        print(f"== {tag} ==")
        for a in SITES:
            w = struct.unpack_from("<I", ov29, a - OV29)[0]
            print(f"  {a:08X}  {w:08X}")


if __name__ == "__main__":
    main()
