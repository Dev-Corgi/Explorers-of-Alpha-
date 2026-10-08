#!/usr/bin/env python3
"""Find ldr rX,[pc]; ldr rY,[rX] where [pc] points at B474 menu ptr slot."""
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
SLOT = 0x0238B474

insns = list(cs.disasm(ov, load))
for i, ins in enumerate(insns):
    if ins.mnemonic != "ldr" or "[pc" not in ins.op_str:
        continue
    pc = (ins.address + 8) & ~3
    for imm in range(-0x2000, 0x2000, 4):
        pool = (pc + imm) & 0xFFFFFFFF
        if pool != SLOT:
            continue
        reg = ins.op_str.split(",")[0].strip()
        if i + 1 >= len(insns):
            break
        nxt = insns[i + 1]
        if nxt.mnemonic == "ldr" and f"[{reg}]" in nxt.op_str:
            print(f"Deref B474 @ {ins.address:#x}: {ins.op_str} ; {nxt.mnemonic} {nxt.op_str}")
            for ctx in insns[max(0, i - 2) : i + 8]:
                print(f"  {ctx.address:08X}: {ctx.mnemonic:8} {ctx.op_str}")
            print()
