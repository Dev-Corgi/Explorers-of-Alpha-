#!/usr/bin/env python3
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
p = ROOT / "don't touch here (legacy)" / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
rom = NintendoDSRom(p.read_bytes())
t = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19]
ov = rom.files[t.fileID]
load = t.ramAddress
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

for ins in cs.disasm(ov[0x238B4A0 - load : 0x238B530 - load], 0x238B4A0):
    print(f"{ins.address:08X}: {ins.mnemonic} {ins.op_str}")

pc = 0x0238B504
w = struct.unpack_from("<I", ov, pc - load)[0]
print(f"\nB504 insn word {w:#010x}")
imm12 = w & 0xFFF
pool = (pc + 8 + imm12) & 0xFFFFFFFF
print(f"pool {pool:#x} file off {pool - load:#x} (ov len {len(ov):#x})")
if pool < load or pool - load + 4 > len(ov):
    print("pool out of ov19 — likely points via B474 chain")
    b474 = struct.unpack_from("<I", ov, 0x0238B474 - load)[0]
    print(f"B474 -> {b474:#x}")
    val = b474
else:
    val = struct.unpack_from("<I", ov, pool - load)[0]
    print(f"pool -> {val:#x}")
for i in range(7):
    sid, _, act, _ = struct.unpack_from("<4H", ov, val - load + i * 8)
    print(f"  str={sid} act={act}")
    if sid == 0:
        break
