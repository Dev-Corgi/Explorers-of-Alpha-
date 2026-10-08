#!/usr/bin/env python3
"""Analyze Z-Gauge WRAM / SetupAction flow on patched ROM."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

OV29 = 0x022DC240
ZGAUGE_WRAM = 0x022B6A00
GAUGE_LIT = 0x023311DC
Z_GAUGE_MAX = 100


def bl_target(word: int, pc: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def pc_rel_ldr(word: int, pc: int) -> int | None:
    if (word & 0xFFFF0000) != 0xE59F0000:
        return None
    off = word & 0xFFF
    return pc + 8 + off


def main() -> None:
    rom = NintendoDSRom(Path("Explorers of Alpha_Rom_seeds.nds").read_bytes())
    ov = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[29].fileID]
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    lit = struct.unpack_from("<I", ov, GAUGE_LIT - OV29)[0]
    print(f"Gauge literal @ {GAUGE_LIT:08X} = {lit:08X} (expect {ZGAUGE_WRAM:08X})")

    print("\n=== GetZGauge paths ===")
    for addr in (0x02330B20, 0x02330B48, 0x02330B54):
        print(f"\n--- @ {addr:08X} ---")
        for ins in cs.disasm(ov[addr - OV29 : addr - OV29 + 0x24], addr):
            print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")
            w = struct.unpack_from("<I", ov, ins.address - OV29)[0]
            if ins.mnemonic == "ldr" and "pc" in ins.op_str:
                tgt = pc_rel_ldr(w, ins.address)
                if tgt:
                    val = struct.unpack_from("<I", ov, tgt - OV29)[0] if OV29 <= tgt < OV29 + len(ov) else None
                    print(f"           -> pool {tgt:08X} = {val:#x}" if val else f"           -> pool {tgt:08X}")

    print("\n=== Find ZMove_SetupAction (bl GetZGauge + cmp #100) ===")
    for off in range(0x02330B20 - OV29, 0x02332000 - OV29 - 4, 4):
        addr = OV29 + off
        w = struct.unpack_from("<I", ov, off)[0]
        if w != 0xE3500064:  # cmp r0, #100
            continue
        ctx = ov[off - 16 : off + 8]
        print(f"\ncmp #100 @ {addr:08X}")
        for ins in cs.disasm(ctx, addr - 16):
            if ins.address >= addr - 12:
                print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

    print("\n=== Old cave gauge slot @ 30B44 ===")
    cave = struct.unpack_from("<H", ov, 0x02330B44 - OV29)[0]
    print(f"  ROM image halfword (always 0 in file): {cave}")

    print("\n=== Code still referencing cave address literal ===")
    cave_lit = struct.pack("<I", 0x02330B44)
    hits = [OV29 + i for i in range(len(ov) - 3) if ov[i : i + 4] == cave_lit]
    print(f"  ov29 pool refs to 02330B44: {[hex(h) for h in hits]}")

    print("\n=== WRAM region notes (0x22B6900..0x22B6F20) ===")
    print("  ZGauge @ 6A00; offsetsMenuOnly warns struct @ 6F10")


if __name__ == "__main__":
    main()
