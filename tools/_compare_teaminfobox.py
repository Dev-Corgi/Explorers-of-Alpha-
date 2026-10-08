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


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")
    ov11 = rom.files[table[11].fileID]
    ov29 = rom.files[table[29].fileID]
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    addr = 0x022FEFA4  # UpdateTeamInfoBox (ov11) — BL HUD @ y=0x16
    off = addr - LOAD
    print("=== RAM 0x22FEFA4 when ov29 is loaded (dungeon) ===")
    print("(ov11 UpdateTeamInfoBox is NOT this code anymore)\n")
    for ins in cs.disasm(ov29[off : off + 0x120], addr):
        w = struct.unpack_from("<I", ov29, ins.address - LOAD)[0]
        extra = ""
        if ins.mnemonic == "bl":
            tgt = bl_target(ins.address, w)
            extra = f"  ; -> {tgt:#010x}"
            if tgt == DRAW:
                extra += " DrawTextInWindow"
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{extra}")
        if ins.address >= 0x022FF0E0:
            break

    print("\n=== ov11 UpdateTeamInfoBox BL draw (reference — only when ov11 loaded) ===")
    for ins in cs.disasm(ov11[off : off + 0x120], addr):
        w = struct.unpack_from("<I", ov11, ins.address - LOAD)[0]
        extra = ""
        if ins.mnemonic == "bl":
            tgt = bl_target(ins.address, w)
            extra = f"  ; -> {tgt:#010x}"
            if tgt == DRAW and ins.address in (0x022FF0A8, 0x022FF0D8):
                extra += "  <<< BL label / BL value"
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{extra}")
        if ins.address >= 0x022FF0E0:
            break

    print("\n=== ov29 DrawTextInWindow call sites (all) ===")
    for off in range(0, len(ov29) - 4, 4):
        a = LOAD + off
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w & 0xFF000000) != 0xEB000000:
            continue
        if bl_target(a, w) != DRAW:
            continue
        chunk = ov29[max(0, off - 32) : off + 4]
        base = a - min(32, off)
        x = y = "?"
        for ins in cs.disasm(chunk, base):
            if ins.address >= a:
                break
            if ins.mnemonic == "mov" and ins.op_str.startswith("r1, #"):
                x = ins.op_str
            if ins.mnemonic == "mov" and ins.op_str.startswith("r2, #"):
                y = ins.op_str
        print(f"  {a:#010x}  {x:12} {y}")

    print("\n=== WRONG TARGET: ov29 menu draw @ 0x234F430 (pmdsky: MenuLoop vtable) ===")
    print("Only runs when dungeon MENU is open, NOT floor HUD.\n")
    for ins in cs.disasm(ov29[0x234F460 - LOAD : 0x234F510 - LOAD], 0x234F460):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
