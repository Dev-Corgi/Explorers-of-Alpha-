#!/usr/bin/env python3
"""Trace summary page stat labels -> PrintSummaryStats format pools."""
from __future__ import annotations

import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.str.handler import StrHandler

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROOT / "Explorers of Alpha_berryboost.nds"))
    config = get_ppmdu_config_for_rom(rom)
    strings = StrHandler.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"), string_encoding=config.string_encoding
    )
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    arm9 = rom.arm9

    print("=== PrintSummaryStats string pool @ D408+ ===")
    for addr in range(0x0203D408, 0x0203D430, 2):
        sid = struct.unpack_from("<H", arm9, addr - 0x02000000)[0]
        text = strings.strings[sid] if sid < len(strings.strings) else "?"
        print(f"  pool {addr:#010x} str {sid}: {text!r}")

    print("\n=== FormatString call sites in PrintSummaryStats ===")
    fmt_sites: list[tuple[int, int | None]] = []
    for ins in cs.disasm(arm9[0x0203CFCC - 0x02000000 : 0x0203D400 - 0x02000000], 0x0203CFCC):
        if ins.mnemonic != "bl" or ins.op_str != "#0x20223f0":
            continue
        # walk back for ldrh from pool
        sid = None
        for prev in cs.disasm(arm9[ins.address - 0x02000000 - 0x20 : ins.address - 0x02000000], ins.address - 0x20):
            if prev.mnemonic == "ldrh" and "[pc" in prev.op_str:
                pc = (prev.address + 8) & ~3
                for imm in range(-0x400, 0x400, 4):
                    pool = (pc + imm) & 0xFFFFFFFF
                    if 0x0203D400 <= pool < 0x0203D430:
                        sid = struct.unpack_from("<H", arm9, pool - 0x02000000)[0]
                        break
            if prev.mnemonic == "bl" and prev.op_str == "#0x20258c4" and sid is None:
                pass
        fmt_sites.append((ins.address, sid))
        label = strings.strings[sid][:60] if sid is not None and sid < len(strings.strings) else "?"
        print(f"  {ins.address:#010x} FormatString  str={sid}  {label!r}")

    print(f"\nTotal FormatString calls: {len(fmt_sites)}")


if __name__ == "__main__":
    main()
