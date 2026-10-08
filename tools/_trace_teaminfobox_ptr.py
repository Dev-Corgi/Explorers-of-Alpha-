#!/usr/bin/env python3
import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROM = Path(
    r"c:\Working\SkyTemple\4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    r"-patched_orbs_roomcharge_nodarkness_orbcharges_orbcount_tmread_zmove_step11_names.nds"
)
LOAD = 0x022DC240


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    ov29 = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")[29].fileID]
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    for pool in (0x232245C, 0x232246C, 0x022FEF20):
        val = struct.unpack_from("<I", ov29, pool - LOAD)[0]
        print(f"\n=== pool {pool:#010x} -> {val:#010x} ===")
        for off in range(0, len(ov29) - 4, 4):
            addr = LOAD + off
            ins = next(cs.disasm(ov29[off : off + 4], addr), None)
            if ins is None or ins.mnemonic != "ldr" or "[pc" not in ins.op_str:
                continue
            m = re.search(r"#(0x[0-9a-f]+|\d+)", ins.op_str)
            if not m:
                continue
            la = (addr + 8 + int(m.group(1), 0)) & ~3
            if abs(la - pool) < 8:
                print(f"  {addr:#010x}: {ins.mnemonic} {ins.op_str}")

    addr = 0x02300EA8
    print(f"\n=== ov29 @ {addr:#010x} (ov11 CreateTeamInfoBox caller) ===")
    for ins in cs.disasm(ov29[addr - LOAD : addr - LOAD + 0x60], addr):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
