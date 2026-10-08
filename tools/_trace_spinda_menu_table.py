#!/usr/bin/env python3
"""Trace which menu table B518 CreateSimpleMenu actually uses."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_files_from_rom_with_extension, get_ppmdu_config_for_rom
from skytemple_files.data.str.handler import StrHandler

ROOT = Path(__file__).resolve().parent.parent


def pc_ldr_imm12(insn_addr: int, word: int) -> int:
    imm12 = word & 0xFFF
    return (insn_addr + 8 + imm12) & 0xFFFFFFFF


def show_table(ov: bytes, load: int, ptr: int, strings, label: str) -> None:
    print(f"\n{label} @{ptr:#010x}:")
    if ptr < load or ptr >= load + len(ov):
        print("  OUT OF RANGE")
        return
    for i in range(8):
        off = ptr - load + i * 8
        sid, _, act, _ = struct.unpack_from("<4H", ov, off)
        if sid == 0:
            print(f"  [{i}] terminator act={act:#x}")
            break
        text = strings.strings[sid][:50] if sid < len(strings.strings) else "?"
        print(f"  [{i}] str={sid} act={act} -> {text!r}")


def main() -> None:
    p = ROOT / "Export Rom" / "Room_Charge_V3_Test" / "_shell559+spinda_menu.nds"
    rom = NintendoDSRom(p.read_bytes())
    config = get_ppmdu_config_for_rom(rom)
    strings = None
    for fn in get_files_from_rom_with_extension(rom, "str"):
        if fn.endswith("text_e.str"):
            strings = StrHandler.deserialize(
                rom.getFileByName(fn), string_encoding=config.string_encoding
            )
            break
    assert strings is not None

    entry = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19]
    ov = rom.files[entry.fileID]
    load = entry.ramAddress
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    print(f"ov19 size {len(ov)} load {load:#x}")

    # B518 region
    for ins in cs.disasm(ov[0x238B4F8 - load : 0x238B524 - load], 0x238B4F8):
        mark = " <<<" if ins.address == 0x238B518 else ""
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")

    b504 = struct.unpack_from("<I", ov, 0x238B504 - load)[0]
    pool = pc_ldr_imm12(0x238B504, b504)
    r1_ptr = struct.unpack_from("<I", ov, pool - load)[0]
    print(f"\nB504 pool @{pool:#x} -> r1 menu ptr {r1_ptr:#x}")

    b474 = struct.unpack_from("<I", ov, 0x238B474 - load)[0]
    print(f"B474 -> {b474:#x}")

    for ptr, name in [
        (r1_ptr, "B518 r1 table"),
        (b474, "B474 table"),
        (0x0238E380, "E380 fixed"),
        (0x0238E290, "E290 vanilla"),
    ]:
        show_table(ov, load, ptr, strings, name)

    # rodata pools region
    print("\n=== rodata C480-C510 ===")
    for addr in range(0x238C480, 0x238C510, 4):
        w = struct.unpack_from("<I", ov, addr - load)[0]
        print(f"  {addr:#x}: {w:#010x}")


if __name__ == "__main__":
    main()
