"""Inspect UseMove / charge path for f_consume_pp (#8) and CanMonsterUseMove gating."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom

ROM = Path(r"c:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
LOAD = 0x022DC240
IS_CHARGING = 0x023245A4
USE_MOVE = 0x0232145C
CAN = 0x02324B24
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

    # Function containing Hook1 starts ~0x2322374
    print("==== UseMove-ish body 0x2322374.. (charge/PP marks) ====")
    start = 0x02322374
    off = start - LOAD
    for insn in md.disasm(bytes(ov29[off : off + 0x900]), start):
        extra = ""
        if insn.mnemonic == "bl":
            # parse target
            w = struct.unpack_from("<I", ov29, insn.address - LOAD)[0]
            tgt = bl_target(insn.address, w)
            names = {
                IS_CHARGING: "IsChargingTwoTurnMove",
                CAN: "CanMonsterUseMove",
                EXE: "ExecuteMoveEffect",
                0x02324D8C: "UpdateMovePp",
                0x0232145C: "UseMove",
            }
            if tgt in names:
                extra = f"  ; {names[tgt]}"
            elif 0x022DC240 <= tgt < 0x022DC240 + len(ov29):
                extra = f"  ; ->{tgt:#x}"
        # highlight orr #8 / bic #8 / tst #8 on halfwords
        if "#8" in insn.op_str or "#0x8" in insn.op_str:
            extra += "  ** FLAG8 **"
        if "#0x10" in insn.op_str or "#16" in insn.op_str:
            extra += "  ** FLAG10 **"
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}{extra}")
        if insn.address > 0x02322C00 and insn.mnemonic == "pop":
            break

    print("\n==== around IsChargingTwoTurnMove @ 0x2322360 ====")
    start = 0x02322280
    off = start - LOAD
    for insn in md.disasm(bytes(ov29[off : off + 0x200]), start):
        extra = ""
        if insn.mnemonic == "bl":
            w = struct.unpack_from("<I", ov29, insn.address - LOAD)[0]
            tgt = bl_target(insn.address, w)
            if tgt == IS_CHARGING:
                extra = "  ; IsChargingTwoTurnMove"
            elif tgt == CAN:
                extra = "  ; CanMonsterUseMove"
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}{extra}")

    # Also look at room_charge_pending TryForce path: does it go through PlayerUseMove?
    # ExecuteMonsterAction forces SetActionUseMove* then later PlayerUseMove/AiUseMove.
    print("\n==== CanMonsterUseMove callers near force-action / turn start ====")
    for addr in [0x022FEF04, 0x022FF0B4, 0x022FF59C]:
        print(f"\n-- context {addr:#x} --")
        start = addr - 0x40
        off = start - LOAD
        for insn in md.disasm(bytes(ov29[off : off + 0xA0]), start):
            mark = " <<<" if insn.address == addr else ""
            print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}{mark}")


if __name__ == "__main__":
    main()
