"""Disassemble f_consume_pp set at 0x2321808 and finish alternate CanUse."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom

ROM = Path(r"c:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
LOAD = 0x022DC240


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROM))
    ov29 = bytes(rom.files[29])
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    print("==== Finish alternate CanUse @ 0x2324BE8 ====")
    for insn in md.disasm(bytes(ov29[0x2324BE8 - LOAD : 0x2324D8C - LOAD]), 0x2324BE8):
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}")

    print("\n==== context 0x2321780.. for orr #8 consume flag ====")
    for insn in md.disasm(bytes(ov29[0x2321780 - LOAD : 0x2321900 - LOAD]), 0x2321780):
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}")

    # Who calls 0x2324BE8?
    print("\n==== callers of 0x2324BE8 ====")
    target = 0x02324BE8
    for off in range(0, len(ov29) - 4, 4):
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w & 0x0F000000) != 0x0B000000:
            continue
        pc = LOAD + off
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm |= ~0xFFFFFF
        tgt = (pc + 8 + (imm << 2)) & 0xFFFFFFFF
        if tgt == target:
            print(f"  {pc:#x}")

    # Does room_charge_pending ExecuteMonsterAction run before CanMonsterUseMove?
    # Check turn-start force path at 0x22ff59c (IsChargingTwoTurnMove) vs our hook
    print("\n==== ExecuteMonsterAction start / RoomCharge hook ====")
    for insn in md.disasm(bytes(ov29[0x22FE4BC - LOAD : 0x22FE4BC - LOAD + 0x80]), 0x22FE4BC):
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}")

    # Look at where f_consume_pp gets set in successful use path - search
    # for strh to [rx,#2] with orr #8 nearby in 0x23214-0x2322d
    print("\n==== wider window around 0x2321808 ====")
    for insn in md.disasm(bytes(ov29[0x2321700 - LOAD : 0x2321A80 - LOAD]), 0x2321700):
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}")


if __name__ == "__main__":
    main()
