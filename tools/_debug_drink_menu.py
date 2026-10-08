#!/usr/bin/env python3
"""Debug drink stat submenu display path."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROOT / "Export Rom/Room_Charge_V3_Test/_shell559+spinda_menu.nds"))
    load = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19].ramAddress
    ov = rom.files[19]
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    pc = 0x238B4C8 + 8
    lit = pc - 0x30
    val = struct.unpack_from("<I", ov, lit - load)[0]
    print(f"Preprocess script/literal @ {lit:#x} = {val:#010x}")

    pc2 = 0x238B504 + 8
    lit2 = pc2 + 0xF7C
    print(f"B504 literal @ {lit2:#x} = {struct.unpack_from('<I', ov, lit2 - load)[0]:#010x}")

    ptr = struct.unpack_from("<I", ov, 0x238B474 - load)[0]
    print(f"B474 menu ptr -> {ptr:#x}")

    # B4F4 corruption check
    for addr in (0x238B4F0, 0x238B4F4, 0x238B4F8):
        w = struct.unpack_from("<I", ov, addr - load)[0]
        ins = next(cs.disasm(ov[addr - load : addr - load + 4], addr))
        print(f"{addr:#x}: word={w:#010x}  {ins.mnemonic} {ins.op_str}")

    arm9 = rom.arm9
    print("\n=== 2046D50 (menu from table) ===")
    for ins in cs.disasm(arm9[0x2046D50 - 0x2000000 : 0x2046D50 - 0x2000000 + 0x80], 0x2046D50):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
