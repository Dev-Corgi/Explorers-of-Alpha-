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


def dump(data: bytes, start: int, size: int = 0x120) -> None:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in cs.disasm(data[start - LOAD : start - LOAD + size], start):
        w = struct.unpack_from("<I", data, ins.address - LOAD)[0]
        extra = ""
        if ins.mnemonic == "bl":
            tgt = bl_target(ins.address, w)
            extra = f"  ; -> {tgt:#010x}"
            if tgt == DRAW:
                extra += " DrawText"
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{extra}")


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    ov29 = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")[29].fileID]
    ov11 = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")[11].fileID]

    for start, label in [
        (0x022FF674, "ov29 @ 22FF674 (called from dungeon code)"),
        (0x022FF168, "ov29 @ 22FF168 (pmdsky symbol region)"),
        (0x022FEFA4, "ov11 UpdateTeamInfoBox @ 22FEFA4"),
    ]:
        print(f"=== {label} ===")
        data = ov29 if start != 0x022FEFA4 else ov11
        dump(data, start)
        print()

    print("=== DrawText in ov29 RAM 0x22FF000-0x2301000 ===")
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for off in range(0, len(ov29) - 4, 4):
        addr = LOAD + off
        if not (0x022FF000 <= addr <= 0x02301000):
            continue
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w & 0xFF000000) != 0xEB000000:
            continue
        if bl_target(addr, w) != DRAW:
            continue
        chunk = ov29[max(0, off - 24) : off + 4]
        x = y = "?"
        for ins in cs.disasm(chunk, addr - min(24, off)):
            if ins.address >= addr:
                break
            if ins.mnemonic == "mov" and ins.op_str.startswith("r1, #"):
                x = ins.op_str
            if ins.mnemonic == "mov" and ins.op_str.startswith("r2, #"):
                y = ins.op_str
        print(f"  {addr:#010x}  {x}  {y}")


if __name__ == "__main__":
    main()
