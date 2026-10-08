#!/usr/bin/env python3
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

OV29_LOAD = 0x022DC240
TRY_BEGIN = 0x02318BBC
DO_MOVE_SOLAR = 0x02328C74
GET_DUNGEON_MSG = 0x020258C4


def disasm(rom: NintendoDSRom, addr: int, size: int = 0x180) -> None:
    if addr >= OV29_LOAD:
        ov = bytes(rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[29].fileID])
        code = ov[addr - OV29_LOAD : addr - OV29_LOAD + size]
    else:
        code = bytes(rom.arm9)[addr - 0x02000000 : addr - 0x02000000 + size]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    print(f"\n=== {addr:#x} ===")
    for ins in md.disasm(code, addr):
        mark = ""
        if ins.mnemonic == "bl":
            tgt = int(ins.op_str.lstrip("#"), 16) if ins.op_str.startswith("#") else None
            if tgt == GET_DUNGEON_MSG:
                mark = "  <-- GetDungeonMsgArm9"
        print(f"  {ins.address:#010x}: {ins.mnemonic:6s} {ins.op_str}{mark}")
        if ins.address >= addr + 0x100:
            break


def main() -> None:
    rom = NintendoDSRom((Path(__file__).resolve().parents[1] / "_tmp_rc_only.nds").read_bytes())
    disasm(rom, DO_MOVE_SOLAR, 0x120)
    disasm(rom, TRY_BEGIN, 0x180)


if __name__ == "__main__":
    main()
