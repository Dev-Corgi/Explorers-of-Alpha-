#!/usr/bin/env python3
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROOT / "Vanilla Rom/Explorers of Alpha_Vanilla.nds"))
    load = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19].ramAddress
    ov = rom.files[19]

    for sid in (0x45BE, 0x45BF, 0x45C0):
        pat = struct.pack("<H", sid)
        hits = [load + off for off in range(len(ov) - 2) if ov[off : off + 2] == pat]
        print(f"script id {sid:#06x}: {len(hits)} hits", [hex(h) for h in hits[:8]])

    pc = 0x238B3D4 + 8
    lit = pc + 0xBC
    word = struct.unpack_from("<I", ov, lit - load)[0]
    print(f"0x1F sp+6d4 literal @ {lit:#x} = {word:#x}")

    base = 0x238E290 - load
    print("vanilla E290 table:")
    for i in range(7):
        hw = struct.unpack_from("<H", ov, base + i * 8)[0]
        wd = struct.unpack_from("<I", ov, base + i * 8 + 4)[0]
        print(f"  {i}: code={hw} action={wd}")


if __name__ == "__main__":
    main()
