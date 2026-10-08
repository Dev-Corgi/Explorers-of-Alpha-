#!/usr/bin/env python3
"""Trace stat drink submenu dispatch and string ID tables."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent


def pool_from_ldr(ov: bytes, load: int, pc: int) -> tuple[int, int]:
    w = struct.unpack_from("<I", ov, pc - load)[0]
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    addr = pc + 8 + imm * 4
    val = struct.unpack_from("<I", ov, addr - load)[0]
    return addr, val


def show_halfword_table(ov: bytes, load: int, ptr: int, count: int = 12) -> None:
    print(f"  halfword table @{ptr:#010x}:")
    if ptr < load or ptr >= load + len(ov):
        print("    OUT OF RANGE")
        return
    for i in range(count):
        off = ptr - load + i * 2
        hw = struct.unpack_from("<H", ov, off)[0]
        print(f"    [{i}] {hw} ({hw:#x})")


def main() -> None:
    rom = NintendoDSRom((ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds").read_bytes())
    entry = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19]
    ov = rom.files[entry.fileID]
    load = entry.ramAddress
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    print("=== B640-B6A0 stat menu ===")
    for ins in cs.disasm(ov[0x238B640 - load : 0x238B6A0 - load], 0x238B640):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

    for pc in (0x0238B64C, 0x0238B650, 0x0238B658):
        pool, val = pool_from_ldr(ov, load, pc)
        print(f"\nldr @ {pc:#x} -> pool {pool:#x} = {val:#010x}")
        if val >= load and val < load + len(ov):
            show_halfword_table(ov, load, val)
        elif val < 0x10000:
            show_halfword_table(ov, load, load + val)

    b474 = struct.unpack_from("<I", ov, 0x0238B474 - load)[0]
    print(f"\nB474 -> {b474:#010x}")
    for i in range(8):
        off = b474 - load + i * 8
        sid, _, act, _ = struct.unpack_from("<4H", ov, off)
        if sid == 0:
            print(f"  term act={act:#x}")
            break
        print(f"  [{i}] str={sid} act={act}")

    print("\n=== A700 team menu (uses B474?) ===")
    for ins in cs.disasm(ov[0x238A700 - load : 0x238A740 - load], 0x238A700):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")
    pool, val = pool_from_ldr(ov, load, 0x0238A700)
    print(f"A700 pool {pool:#x} = {val:#x}")


if __name__ == "__main__":
    main()
