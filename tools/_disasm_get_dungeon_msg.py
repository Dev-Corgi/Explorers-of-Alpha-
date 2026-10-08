#!/usr/bin/env python3
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

ARM9_BASE = 0x02000000
GET_DUNGEON_MSG = 0x020258C4


def main() -> None:
    rom = NintendoDSRom((Path(__file__).resolve().parents[1] / "_tmp_rc_only.nds").read_bytes())
    arm9 = bytes(rom.arm9)
    off = GET_DUNGEON_MSG - ARM9_BASE
    code = arm9[off : off + 0x200]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = True
    print(f"Disasm GetDungeonMsgArm9 @ {GET_DUNGEON_MSG:#x}\n")
    for ins in md.disasm(code, GET_DUNGEON_MSG):
        extra = ""
        if ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            # resolve literal pool
            # find next pool after this insn
            pass
        if ins.mnemonic in ("ldr", "ldrh", "ldrb") and "#" in ins.op_str:
            pass
        print(f"  {ins.address:#010x}: {ins.mnemonic:6s} {ins.op_str}")
        if ins.address > GET_DUNGEON_MSG + 0x120:
            break

    # scan for ldr r?, [r?, r?, lsl #2] style pointer table access
    print("\nLiteral pools after function:")
    for ins in md.disasm(code, GET_DUNGEON_MSG):
        if ins.mnemonic == "ldr" and "pc" in ins.op_str:
            # PC-relative load: compute pool address
            # ins.address + 8 + imm
            woff = ins.address - GET_DUNGEON_MSG
            w = struct.unpack_from("<I", code, woff)[0]
            imm12 = w & 0xFFF
            u = (ins.address + 8 + imm12) & 0xFFFFFFFF
            if u >= GET_DUNGEON_MSG and u < GET_DUNGEON_MSG + 0x200:
                poff = u - GET_DUNGEON_MSG
                if poff + 4 <= len(code):
                    val = struct.unpack_from("<I", code, poff)[0]
                    print(f"  pool @ {u:#x} = {val} ({val:#x})")
                    if ARM9_BASE <= val < ARM9_BASE + len(arm9):
                        # dump 8 u16 at val
                        toff = val - ARM9_BASE
                        vals = [struct.unpack_from('<H', arm9, toff + i*2)[0] for i in range(8)]
                        print(f"    u16@table: {vals}")


if __name__ == "__main__":
    main()
