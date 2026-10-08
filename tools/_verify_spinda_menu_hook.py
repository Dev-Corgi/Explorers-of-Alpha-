#!/usr/bin/env python3
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
p = ROOT / "Export Rom" / "Room_Charge_V3_Test" / "_shell559+spinda_menu.nds"
rom = NintendoDSRom(p.read_bytes())
t = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19]
ov = rom.files[t.fileID]
load = t.ramAddress
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

for addr, name in [(0x238ABC0, "ABC0"), (0x238B518, "B518"), (0x238B4A4, "B4A4")]:
    w = struct.unpack_from("<I", ov, addr - load)[0]
    print(f"{name} @{addr:#x}: {w:#010x} (top {w >> 24:#x})")

print("\ninner33 @ B4A4:")
for ins in cs.disasm(ov[0x238B4F8 - load : 0x238B524 - load], 0x238B4F8):
    mark = " <<<" if ins.address == 0x238B518 else ""
    print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")

b474 = struct.unpack_from("<I", ov, 0x238B474 - load)[0]
print(f"\nB474 -> {b474:#x}")
off = b474 - load
for i in range(6):
    sid, _, act, _ = struct.unpack_from("<4H", ov, off + i * 8)
    print(f"  table str={sid} act={act}")
