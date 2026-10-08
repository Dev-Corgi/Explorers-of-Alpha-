#!/usr/bin/env python3
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

rom = NintendoDSRom.fromFile("Explorers of Alpha_berryboost.nds")
load = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19].ramAddress
ov = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19].fileID]
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

print("Table @ 0x238DCD8:")
for off in range(0, 0x20, 4):
    addr = 0x238DCD8 + off
    w = struct.unpack_from("<I", ov, addr - load)[0]
    print(f"  +{off:02X} {addr:08X}: {w:08X}")

# Find ldr rX, [pc, #imm] where target is exactly 0x238DCE8 (the fn ptr slot)
for ins in cs.disasm(ov, load):
    if ins.mnemonic != "ldr" or "[pc" not in ins.op_str:
        continue
    pc = (ins.address + 8) & ~3
    for imm in range(-0x2000, 0x2000, 4):
        tgt = (pc + imm) & 0xFFFFFFFF
        if tgt == 0x238DCE8:
            print(f"loads fn ptr slot: {ins.address:08X} {ins.mnemonic} {ins.op_str}")
        if tgt == 0x238DCD8:
            print(f"loads table base: {ins.address:08X} {ins.mnemonic} {ins.op_str}")

# Trace a few ins after loading table base - look for +0x10 and blx
for start in [0x238C678, 0x238C3E0, 0x238D2EC]:
    print(f"\n=== from {start:08X} ===")
    for ins in cs.disasm(ov[start - load : start - load + 0x40], start):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")
