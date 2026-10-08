"""Disassemble UpdateMovePp and check two-turn / charge interactions with PP."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom

ROM = Path(r"c:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
LOAD = 0x022DC240
UPDATE_PP = 0x02324D8C
SHOULD = 0x0231A7A0
IS_CHARGING = 0x023245A4  # IsChargingTwoTurnMove from prior research
IS_CHARGING_ANY = 0x02324664  # guess - look up
CAN = 0x02324B24


def bl_target(pc: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm |= ~0xFFFFFF
    return (pc + 8 + (imm << 2)) & 0xFFFFFFFF


def disasm_fn(ov29: bytes, start: int, size: int = 0x120) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    off = start - LOAD
    for insn in md.disasm(bytes(ov29[off : off + size]), start):
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}")
        if insn.mnemonic == "bx" and "lr" in insn.op_str:
            # continue a bit past first bx lr if early return
            if insn.address > start + 0x20:
                # don't stop on early bxeq lr style — only plain bx lr after substantial body
                pass


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROM))
    ov29 = bytes(rom.files[29])
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    print("==== UpdateMovePp full ====")
    disasm_fn(ov29, UPDATE_PP, 0xC0)

    print("\n==== ShouldUsePp full ====")
    disasm_fn(ov29, SHOULD, 0x100)

    print("\n==== CanMonsterUseMove (PP check area) ====")
    disasm_fn(ov29, CAN, 0x100)

    # Find IsChargingTwoTurnMove / IsChargingAnyTwoTurnMove from pmdsky addresses
    # NA IsChargingTwoTurnMove: from yml
    # Read from symbols file if needed — use known 0x23245A4 from transcript
    for name, addr in [
        ("IsChargingTwoTurnMove", 0x023245A4),
        ("IsChargingAnyTwoTurnMove", 0x02324664),
    ]:
        print(f"\n==== BLs to {name} ====")
        hits = []
        for off in range(0, len(ov29) - 4, 4):
            w = struct.unpack_from("<I", ov29, off)[0]
            if (w & 0x0F000000) == 0x0B000000 and bl_target(LOAD + off, w) == addr:
                hits.append(LOAD + off)
        print(f"  {len(hits)} callers: {[hex(h) for h in hits[:30]]}")

    # In UseMove (0x232145C) — find UpdateMovePp? None expected.
    # Instead look at PlayerUseMove / AiUseMove wrappers that call UseMove then UpdateMovePp.
    # Disasm from ShouldUsePp callers context: 0x22f5f70 and 0x231a8f8
    for addr in [0x022F5F00, 0x0231A880]:
        print(f"\n==== context @ {addr:#x} (ShouldUsePp / UseMove wrapper) ====")
        off = addr - LOAD
        for insn in md.disasm(bytes(ov29[off : off + 0x140]), addr):
            print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}")

    # Does UpdateMovePp or its callers check two-turn status?
    # Scan UpdateMovePp body for BL targets
    print("\n==== BL targets inside UpdateMovePp ====")
    off = UPDATE_PP - LOAD
    for i in range(0, 0xC0, 4):
        w = struct.unpack_from("<I", ov29, off + i)[0]
        if (w & 0x0F000000) == 0x0B000000:
            pc = UPDATE_PP + i
            print(f"  {pc:#x} -> {bl_target(pc, w):#x}")

    print("\n==== BL targets inside ShouldUsePp ====")
    off = SHOULD - LOAD
    for i in range(0, 0x100, 4):
        w = struct.unpack_from("<I", ov29, off + i)[0]
        if (w & 0x0F000000) == 0x0B000000:
            pc = SHOULD + i
            print(f"  {pc:#x} -> {bl_target(pc, w):#x}")


if __name__ == "__main__":
    main()
