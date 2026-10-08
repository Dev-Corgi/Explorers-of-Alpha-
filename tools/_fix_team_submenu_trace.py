#!/usr/bin/env python3
"""Trace Drink team-member submenu path and compare patched ROM."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent


def pool_word(ov: bytes, load: int, insn: int, imm: int) -> tuple[int, int]:
    addr = insn + 8 + imm
    val = struct.unpack_from("<I", ov, addr - load)[0]
    return addr, val


def show_menu(ov: bytes, load: int, ptr: int, label: str) -> None:
    print(f"\n{label} @{ptr:#010x}:")
    if ptr < load or ptr >= load + len(ov):
        print("  (out of overlay range)")
        return
    for i in range(8):
        off = ptr - load + i * 8
        sid, _p, act, _p2 = struct.unpack_from("<4H", ov, off)
        if sid == 0:
            print(f"  terminator act={act:#x}")
            break
        print(f"  [{i}] str={sid} act={act}")


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROOT / "Explorers of Alpha_berryboost.nds"))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov = rom.files[table[19].fileID]
    load = table[19].ramAddress
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    print("=== CreateSimpleMenuFromStringIds (2046BE8) call sites ===")
    for ins in cs.disasm(ov, load):
        if ins.mnemonic == "bl" and ins.op_str == "#0x2046be8":
            print(f"\n@{ins.address:#010x}")
            off = ins.address - load
            for prev in cs.disasm(ov[max(0, off - 0x28) : off + 4], ins.address - 0x28):
                print(f"  {prev.address:08X}: {prev.mnemonic:8} {prev.op_str}")

    pools = [
        ("B474 menu ptr (inner16)", 0x0238B474),
        ("B518 menu r1", *pool_word(ov, load, 0x0238B504, 0xF7C)),
        ("B5C0 menu r1", *pool_word(ov, load, 0x0238B5B0, 0xED8)),
        ("C290 menu r1", *pool_word(ov, load, 0x0238C280, 0x27C)),
        ("D2EC menu r1", *pool_word(ov, load, 0x0238D2EC, 0x18)),
        ("BFF4 menu r1", *pool_word(ov, load, 0x0238BFE8, 0x4EC)),
        ("DCE8 rodata", 0x0238DCE8),
    ]
    for item in pools:
        if len(item) == 2:
            name, addr = item
            val = struct.unpack_from("<I", ov, addr - load)[0]
        else:
            name, addr, val = item
        print(f"{name}: pool @{addr:#x} = {val:#010x}")
        if val >= load and val < load + len(ov):
            show_menu(ov, load, val, name)

    show_menu(ov, load, 0x0238E290, "BAR_SUBMENU_ITEMS_2 (vanilla)")
    show_menu(ov, load, 0x0238DD04, "DD04 cave (vanilla zeros)")

    ev = ROOT / "Explorers of Alpha_berryboost_ev.nds"
    if ev.is_file():
        rom2 = NintendoDSRom.fromFile(str(ev))
        ov2 = rom2.files[table[19].fileID]
        b474 = struct.unpack_from("<I", ov2, 0x0238B474 - load)[0]
        print(f"\nPATCHED ROM B474 -> {b474:#010x}")
        show_menu(ov2, load, 0x0238DD04, "DD04 patched")
        show_menu(ov2, load, 0x0238E290, "E290 patched (should be vanilla)")


if __name__ == "__main__":
    main()
