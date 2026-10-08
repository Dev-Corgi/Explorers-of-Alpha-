"""Compare CanMonsterUseMove vs charging alternate; find f_consume_pp sets."""
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

    print("==== CanMonsterUseMove @ 0x2324B24 ====")
    for insn in md.disasm(bytes(ov29[0x2324B24 - LOAD : 0x2324BE0 - LOAD]), 0x2324B24):
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}")

    print("\n==== Alternate @ 0x2324BE8 (used when IsChargingTwoTurnMove) ====")
    for insn in md.disasm(bytes(ov29[0x2324BE8 - LOAD : 0x2324D00 - LOAD]), 0x2324BE8):
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}")
        if insn.mnemonic.startswith("pop") or (insn.mnemonic == "bx" and "lr" in insn.op_str):
            if insn.address > 0x2324C40:
                break

    # Search for orr with #8 on halfword stores near move use (0x23214xx - 0x2322dxx)
    print("\n==== orr/bic #8 sites in UseMove region 0x232145C-0x2322E00 ====")
    for addr in range(0x232145C, 0x2322E00, 4):
        w = struct.unpack_from("<I", ov29, addr - LOAD)[0]
        # ARM orr Rd, Rn, #8 = often E38xx008 or similar
        # bic with #8
        for insn in md.disasm(struct.pack("<I", w), addr):
            if insn.mnemonic in ("orr", "bic", "orrseq", "biceq", "orrne", "bicne") and (
                "#8" in insn.op_str or "#0x8" in insn.op_str
            ):
                # show context
                print(f"\n-- {addr:#x} --")
                for i2 in md.disasm(bytes(ov29[addr - 0x10 - LOAD : addr + 0x20 - LOAD]), addr - 0x10):
                    m = " <<<" if i2.address == addr else ""
                    print(f"  {i2.address:08X}: {i2.mnemonic} {i2.op_str}{m}")

    # Specifically 0x22faa04 which was called before seeming PP mark path
    print("\n==== 0x22FAA04 (candidate mark-used / consume) ====")
    for insn in md.disasm(bytes(ov29[0x22FAA04 - LOAD : 0x22FAA04 - LOAD + 0x80]), 0x22FAA04):
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}")
        if insn.mnemonic == "bx" and "lr" in insn.op_str and insn.address > 0x22FAA20:
            break
        if insn.mnemonic.startswith("pop") and insn.address > 0x22FAA20:
            break

    # PlayerUseMove path when CanMonsterUseMove fails (sb==0) - does it still UpdateMovePp?
    # Already know UpdateMovePp runs after UseMove always if entity check passes.
    # Key: does UseMove still set flag #8 when ExecuteMoveEffect is skipped by pending?

    # Search strh after orr #8 more carefully in whole ov29 for pattern used in UpdateMovePp callers
    print("\n==== sites: orr reg,#8 then strh (f_consume_pp pattern) ====")
    for addr in range(LOAD, LOAD + len(ov29) - 12, 4):
        w = struct.unpack_from("<I", ov29, addr - LOAD)[0]
        for insn in md.disasm(struct.pack("<I", w), addr):
            if insn.mnemonic.startswith("orr") and ("#8" in insn.op_str or "#0x8" in insn.op_str):
                # next few insns
                nxt = list(md.disasm(bytes(ov29[addr + 4 - LOAD : addr + 20 - LOAD]), addr + 4))
                if any(n.mnemonic.startswith("strh") for n in nxt[:3]):
                    print(f"  {addr:#x}: {insn.op_str} -> {[n.mnemonic+' '+n.op_str for n in nxt[:3]]}")


if __name__ == "__main__":
    main()
