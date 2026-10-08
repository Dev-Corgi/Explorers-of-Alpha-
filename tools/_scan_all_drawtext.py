#!/usr/bin/env python3
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROM = Path(
    r"c:\Working\SkyTemple\4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    r"-patched_orbs_roomcharge_nodarkness_orbcharges_orbcount_tmread_zmove_step11_names.nds"
)
DRAW = 0x02026214


def bl_target(addr: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return addr + 8 + (imm << 2)


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    for y_want in ("#4", "#0x16", "#0x14", "#2"):
        print(f"=== DrawText with r2={y_want} ===")
        for oid in range(len(table)):
            data = rom.files[table[oid].fileID]
            load = table[oid].ramAddress
            for off in range(0, len(data) - 4, 4):
                w = struct.unpack_from("<I", data, off)[0]
                if (w & 0xFF000000) != 0xEB000000:
                    continue
                addr = load + off
                if bl_target(addr, w) != DRAW:
                    continue
                chunk = data[max(0, off - 28) : off + 4]
                y = None
                x = None
                for ins in cs.disasm(chunk, addr - min(28, off)):
                    if ins.address >= addr:
                        break
                    if ins.mnemonic == "mov" and ins.op_str.startswith("r2, #"):
                        y = ins.op_str
                    if ins.mnemonic == "mov" and ins.op_str.startswith("r1, #"):
                        x = ins.op_str
                if y == f"r2, {y_want}":
                    print(f"  ov{oid:02d} @ {addr:#010x}  {x}  {y}  (load {load:#x})")
        print()


if __name__ == "__main__":
    main()
