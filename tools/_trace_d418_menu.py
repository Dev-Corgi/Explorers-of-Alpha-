#!/usr/bin/env python3
"""Trace which menu table 238D418 uses for drink stat submenu."""
from __future__ import annotations

import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROM = ROOT / "don't touch here (legacy)" / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"


def show_menu(ov: bytes, load: int, ptr: int, label: str) -> None:
    print(f"\n{label} @{ptr:#010x}:")
    if ptr < load or ptr - load + 64 > len(ov):
        print("  out of range")
        return
    for i in range(8):
        off = ptr - load + i * 8
        sid, _p, act, _p2 = struct.unpack_from("<4H", ov, off)
        if sid == 0 and act == 0xFFFF:
            print(f"  [{i}] terminator")
            break
        print(f"  [{i}] str={sid} act={act}")


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov = rom.files[table[19].fileID]
    load = table[19].ramAddress
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    entry = 0x0238D418
    print("=== 238D418 entry ===")
    for ins in cs.disasm(ov[entry - load : entry - load + 0x80], entry):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

    print("\n=== callers of 238D418 ===")
    for ins in cs.disasm(ov, load):
        if ins.mnemonic == "bl" and "238d418" in ins.op_str.lower():
            print(f"  {ins.address:08X}")

    for name, addr in [
        ("B474 ptr", 0x0238B474),
        ("E290", 0x0238E290),
        ("E380", 0x0238E380),
    ]:
        if name == "B474 ptr":
            ptr = struct.unpack_from("<I", ov, addr - load)[0]
            print(f"\nB474 -> {ptr:#010x}")
            show_menu(ov, load, ptr, "B474 target")
        else:
            show_menu(ov, load, addr, name)

    # pool refs near D2EC (another stat menu path?)
    pc = 0x0238D2EC
    imm = struct.unpack_from("<I", ov, pc - load)[0] & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    pool = pc + 8 + imm * 4
    val = struct.unpack_from("<I", ov, pool - load)[0]
    print(f"\nD2EC ldr pool @{pool:#010x} = {val:#010x}")
    show_menu(ov, load, val, "D2EC menu")


if __name__ == "__main__":
    main()
