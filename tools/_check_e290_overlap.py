#!/usr/bin/env python3
"""Check E290 7-entry patch overlap with overlay19 rodata/code."""
from __future__ import annotations

import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROOT / "Explorers of Alpha_berryboost.nds"))
    rom_ev = NintendoDSRom.fromFile(str(ROOT / "Explorers of Alpha_berryboost_ev.nds"))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov = rom.files[table[19].fileID]
    ov_ev = rom_ev.files[table[19].fileID]
    load = table[19].ramAddress
    end = load + table[19].ramSize
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    print(f"ov19 RAM {load:#010x}..{end:#010x} (size {table[19].ramSize:#x})")
    print(f"E290+0x40 = {0x238E290 + 0x40:#010x} (within ov19: {0x238E290 + 0x40 <= end})")

    for start in (0x238E2C0, 0x238E2D0, 0x238E300, 0x238E340):
        off = start - load
        insns = list(cs.disasm(ov[off : off + 16], start))
        txt = ", ".join(f"{i.mnemonic} {i.op_str}" for i in insns[:4])
        print(f"\n{start:#010x} as ARM?: {txt}")

    print("\n=== Vanilla vs patched E290-E310 ===")
    for addr in range(0x238E290, 0x238E310, 8):
        v = ov[addr - load : addr - load + 8]
        p = ov_ev[addr - load : addr - load + 8]
        if v != p:
            print(f"  CHANGED @{addr:#010x}: vanilla={v.hex()} patched={p.hex()}")

    print("\n=== Pointers into E2A0-E310 (overlay pools) ===")
    for off in range(0, len(ov) - 4, 4):
        w = struct.unpack_from("<I", ov, off)[0]
        if 0x238E2A0 <= w <= 0x238E310:
            print(f"  @{load + off:#010x} -> {w:#010x}")

    print("\n=== na.py symbols in spill zone ===")
    symbols = [
        ("BAR_SUBMENU_ITEMS_2", 0x238E290, 0x30),
        ("SUB2 ingredient (E2A0)", 0x238E2A0, 0x18),
        ("OVERLAY19_RESERVED", 0x238E344, 0x1C),
    ]
    for name, addr, size in symbols:
        print(f"  {name}: {addr:#010x} size {size:#x}")


if __name__ == "__main__":
    main()
