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


def scan_region(name: str, data: bytes, load: int) -> None:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    hits = []
    for off in range(0, len(data) - 4, 4):
        addr = load + off
        w = struct.unpack_from("<I", data, off)[0]
        if (w & 0xFF000000) != 0xEB000000:
            continue
        if bl_target(addr, w) != DRAW:
            continue
        chunk = data[max(0, off - 40) : off + 4]
        base = addr - min(40, off)
        x = y = None
        for ins in cs.disasm(chunk, base):
            if ins.address >= addr:
                break
            if ins.mnemonic == "mov" and ins.op_str.startswith("r1, #"):
                x = ins.op_str.split("#")[1]
            if ins.mnemonic == "mov" and ins.op_str.startswith("r2, #"):
                y = ins.op_str.split("#")[1]
        if y in ("0x16", "22"):
            hits.append((addr, x, y))
    if hits:
        print(f"{name} (load {load:#x}):")
        for a, x, y in hits:
            print(f"  DrawText @ {a:#010x}  x=#{x}  y=#{y}")


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")
    print("=== DrawTextInWindow with y=0x16 (BL HUD line in ov11) ===\n")
    scan_region("arm9", rom.arm9, 0x02000000)
    for i in [10, 11, 29, 31]:
        scan_region(f"overlay{i}", rom.files[table[i].fileID], table[i].ramAddress)

    print("\n=== ov29 @ 0x234F814 (CheckAlphaBL caller near OthersMenuLoop) ===")
    ov29 = rom.files[table[29].fileID]
    L = 0x022DC240
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in cs.disasm(ov29[0x234F7C0 - L : 0x234F880 - L], 0x234F7C0):
        w = struct.unpack_from("<I", ov29, ins.address - L)[0]
        ex = ""
        if ins.mnemonic == "bl":
            ex = f" -> {bl_target(ins.address, w):#x}"
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{ex}")


if __name__ == "__main__":
    main()
