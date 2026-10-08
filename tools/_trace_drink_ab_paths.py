#!/usr/bin/env python3
"""Trace vanilla drink stat menu states 0x20 -> 0x21 -> 0x25."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent


def branch_target(insn_addr: int, word: int) -> int | None:
    if (word >> 24) != 0xEA:
        return None
    off = word & 0xFFFFFF
    if off & 0x800000:
        off -= 0x01000000
    return insn_addr + 8 + off * 4


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"))
    load = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19].ramAddress
    ov = rom.files[19]
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    print("=== Main bar state dispatch @ A4C0 ===")
    for ins in cs.disasm(ov[0x238A4B0 - load : 0x238A4D0 - load], 0x238A4B0):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

    base = 0x238A4C8
    for st in range(0x1E, 0x28):
        entry = base + st * 4
        word = struct.unpack_from("<I", ov, entry - load)[0]
        tgt = branch_target(entry, word)
        mark = " <<<" if tgt in (0x238B4A4, 0x238B4F8) else ""
        print(f"  state 0x{st:02X} -> {tgt:#010x}{mark}")

    print("\n=== Path A B4A4 (state 0x20 handler) ===")
    for ins in cs.disasm(ov[0x238B4A4 - load : 0x238B4F8 - load], 0x238B4A4):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

    print("\n=== Path B B4F8 (state 0x21 handler) ===")
    for ins in cs.disasm(ov[0x238B4F8 - load : 0x238B524 - load], 0x238B4F8):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
