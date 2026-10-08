#!/usr/bin/env python3
import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
B474 = 0x0238B474
TABLE = 0x0238E380
E340 = 0x0238E340


def main() -> None:
    base = NintendoDSRom.fromFile(str(ROOT / "Explorers of Alpha_berryboost.nds"))
    rom = NintendoDSRom.fromFile(str(ROOT / "Explorers of Alpha_berryboost_ev.nds"))
    tb = loadOverlayTable(base.arm9OverlayTable, lambda _i, _n: b"")[19]
    tp = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19]
    bov, pov = base.files[tb.fileID], rom.files[tp.fileID]
    load = tb.ramAddress

    b474 = struct.unpack_from("<I", pov, B474 - load)[0]
    print(f"B474 -> {b474:#010x} (want {TABLE:#010x})")
    print(f"overlay19 size vanilla={len(bov):#x} patched={len(pov):#x} ramSize={tp.ramSize:#x}")
    print(f"E340 tail unchanged: {pov[E340-load:E340-load+0x40] == bov[E340-load:E340-load+0x40]}")


if __name__ == "__main__":
    main()
