"""Trace CanMonsterUseMove fail path in 0x2322374 — does ExecuteMoveEffect still run?"""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom

ROM = Path(r"c:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
LOAD = 0x022DC240
EXE = 0x0232E864


def bl_target(pc: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm |= ~0xFFFFFF
    return (pc + 8 + (imm << 2)) & 0xFFFFFFFF


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROM))
    ov29 = bytes(rom.files[29])
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    # From fail branch 0x23224c4 to either ExecuteMoveEffect or return
    print("==== from CanUse fail join 0x23224C4 through Hook1 ====")
    for insn in md.disasm(bytes(ov29[0x23224C4 - LOAD : 0x2322B80 - LOAD]), 0x23224C4):
        extra = ""
        if insn.mnemonic == "bl":
            w = struct.unpack_from("<I", ov29, insn.address - LOAD)[0]
            tgt = bl_target(insn.address, w)
            if tgt == EXE:
                extra = "  ; ExecuteMoveEffect"
            elif tgt == 0x02324B24:
                extra = "  ; CanMonsterUseMove"
            elif tgt == 0x02324BE8:
                extra = "  ; CanUseNoPpCheck"
            elif tgt == 0x023245A4:
                extra = "  ; IsChargingTwoTurnMove"
        # highlight sb checks
        if "sb" in insn.op_str and insn.mnemonic in ("cmp", "cmpne", "cmpeq"):
            extra += "  ** sb **"
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}{extra}")

    # Symbol name guess: look for pmdsky near CanMonsterUseMove
    print("\nDone")


if __name__ == "__main__":
    main()
