#!/usr/bin/env python3
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent.parent
rom = NintendoDSRom((ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds").read_bytes())
entry = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19]
ov = rom.files[entry.fileID]
load = entry.ramAddress
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

print("=== C150-C1C0 ===")
for ins in cs.disasm(ov[0x238C150 - load : 0x238C1C0 - load], 0x238C150):
    print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

for pc in range(0x238C150, 0x238C1C0, 4):
    w = struct.unpack_from("<I", ov, pc - load)[0]
    if (w & 0xFF000000) == 0xE5000000 or (w & 0xFFF00000) == 0xE5900000:
        imm = w & 0xFFF
        pool = pc + 8 + imm
        if pool - load + 4 <= len(ov):
            val = struct.unpack_from("<I", ov, pool - load)[0]
            print(f"  pool @ {pc:#x} -> {pool:#x} = {val:#x}")
