#!/usr/bin/env python3
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

rom = NintendoDSRom.fromFile("Explorers of Alpha_berryboost.nds")
load = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19].ramAddress
ov = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19].fileID]
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

print("=== ldr [..,#0x10] in bar overlay ===")
for ins in cs.disasm(ov, load):
    if not ins.mnemonic.startswith("ldr"):
        continue
    op = ins.op_str.replace(" ", "").lower()
    if "#0x10]" in op or "#16]" in op:
        if 0x238A000 <= ins.address <= 0x238E000:
            print(f"{ins.address:08X}: {ins.mnemonic} {ins.op_str}")

print("\n=== pc-relative load of word at 0x238DCE8, show next ins ===")
seen = set()
for ins in cs.disasm(ov, load):
    if ins.mnemonic != "ldr":
        continue
    pc = (ins.address + 8) & ~3
    for imm in range(-0x1000, 0x1000, 4):
        if (pc + imm) & 0xFFFFFFFF != 0x238DCE8:
            continue
        if ins.address in seen:
            break
        seen.add(ins.address)
        off = ins.address - load
        print(f"\n{ins.address:08X}: {ins.mnemonic} {ins.op_str}")
        for ins2 in cs.disasm(ov[off : off + 24], ins.address):
            if ins2.address == ins.address:
                continue
            print(f"  {ins2.address:08X}: {ins2.mnemonic} {ins2.op_str}")
        break
