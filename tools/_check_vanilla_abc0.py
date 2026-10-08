#!/usr/bin/env python3
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_files_from_rom_with_extension, get_ppmdu_config_for_rom
from skytemple_files.data.str.handler import StrHandler

ROOT = Path(__file__).resolve().parent.parent
VANILLA = ROOT / "don't touch here (legacy)" / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"


def main() -> None:
    rom = NintendoDSRom(VANILLA.read_bytes())
    config = get_ppmdu_config_for_rom(rom)
    for fn in get_files_from_rom_with_extension(rom, "str"):
        if fn.endswith("text_e.str"):
            strings = StrHandler.deserialize(
                rom.getFileByName(fn), string_encoding=config.string_encoding
            )
            print(f"vanilla text_e.str count: {len(strings.strings)}")
            print(f"id 19300 in range: {19300 < len(strings.strings)}")
            print(f"id 19555 in range: {19555 < len(strings.strings)}")
            break

    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov19 = rom.files[table[19].fileID]
    load = table[19].ramAddress
    print(f"vanilla ov19 size: {len(ov19)} ram {load:#x}")

    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    addr = 0x238ABC0
    off = addr - load
    word = struct.unpack_from("<I", ov19, off)[0]
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    tgt = addr + 8 + imm * 4
    print(f"ABC0 word {word:#010x} -> {tgt:#010x}")

    for ins in cs.disasm(ov19[off - 0x20 : off + 0x10], addr - 0x20):
        mark = " <<<" if ins.address == addr else ""
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")


if __name__ == "__main__":
    main()
