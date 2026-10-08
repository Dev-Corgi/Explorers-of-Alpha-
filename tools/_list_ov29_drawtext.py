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
LOAD = 0x022DC240
DRAW = 0x02026214


def bl_target(addr: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return addr + 8 + (imm << 2)


def find_prologue(data: bytes, load: int, addr: int) -> int:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    off = addr - load
    best = addr
    for back in range(0, min(off, 0x400), 4):
        a = addr - back
        ins = next(cs.disasm(data[a - load : a - load + 4], a), None)
        if ins and ins.mnemonic == "push" and "lr" in ins.op_str and "{" in ins.op_str:
            best = a
    return best


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    ov29 = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")[29].fileID]
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    print("All DrawTextInWindow sites in overlay29:\n")
    for off in range(0, len(ov29) - 4, 4):
        addr = LOAD + off
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w & 0xFF000000) != 0xEB000000:
            continue
        if bl_target(addr, w) != DRAW:
            continue
        fn = find_prologue(ov29, LOAD, addr)
        chunk = ov29[max(0, off - 32) : off + 4]
        base = addr - min(32, off)
        x = y = "?"
        for ins in cs.disasm(chunk, base):
            if ins.address >= addr:
                break
            if ins.mnemonic == "mov" and ins.op_str.startswith("r1, #"):
                x = ins.op_str
            if ins.mnemonic == "mov" and ins.op_str.startswith("r2, #"):
                y = ins.op_str
        tag = ""
        if fn == 0x0234F430:
            tag = " [MENU STATUS fn - NOT floor HUD]"
        if addr == 0x02330BB8:
            tag = " [our Z gauge cave]"
        print(f"  fn~{fn:#010x}  DrawText@{addr:#010x}  {x}  {y}{tag}")


if __name__ == "__main__":
    main()
