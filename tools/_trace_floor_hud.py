#!/usr/bin/env python3
"""Trace ov29 floor HUD draw @ 0x22F0B10 and callers."""
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


def bl_target(addr: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return addr + 8 + (imm << 2)


def find_bl_callers(data: bytes, load: int, target: int) -> list[int]:
    out = []
    for off in range(0, len(data) - 4, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if (w & 0xFF000000) != 0xEB000000:
            continue
        if bl_target(load + off, w) == target:
            out.append(load + off)
    return out


def dump(data: bytes, start: int, size: int = 0x180) -> None:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    draw = 0x02026214
    for ins in cs.disasm(data[start - LOAD : start - LOAD + size], start):
        w = struct.unpack_from("<I", data, ins.address - LOAD)[0]
        extra = ""
        if ins.mnemonic == "bl":
            tgt = bl_target(ins.address, w)
            extra = f"  ; -> {tgt:#010x}"
            if tgt == draw:
                extra += " DrawText"
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{extra}")


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    ov29 = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")[29].fileID]

    for target, label in [
        (0x022F0B10, "Draw helper @ 22F0B10"),
        (0x022F0984, "Caller chain @ 22F0984"),
        (0x022EA370, "MessageWait @ 22EA370 area"),
    ]:
        print(f"=== BL callers of {label} ===")
        for addr in find_bl_callers(ov29, LOAD, target):
            print(f"  {addr:#010x}")
        print()

    print("=== ov29 @ 22F0984 (HUD update candidate) ===")
    dump(ov29, 0x022F0984, 0x200)

    print("\n=== ov29 @ 22F0B10 (PreprocessString + DrawText y=0x14) ===")
    dump(ov29, 0x022F0B10, 0x80)

    # search nearby functions with DrawText y=0x16 or second line
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    draw = 0x02026214
    print("\n=== ov29 DrawText in 22F0000-22F2000 with coords ===")
    for off in range(0, len(ov29) - 4, 4):
        addr = LOAD + off
        if not (0x022F0000 <= addr <= 0x022F2000):
            continue
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w & 0xFF000000) != 0xEB000000:
            continue
        if bl_target(addr, w) != draw:
            continue
        chunk = ov29[max(0, off - 28) : off + 4]
        x = y = "?"
        for ins in cs.disasm(chunk, addr - min(28, off)):
            if ins.address >= addr:
                break
            if ins.mnemonic == "mov" and ins.op_str.startswith("r1, #"):
                x = ins.op_str
            if ins.mnemonic == "mov" and ins.op_str.startswith("r2, #"):
                y = ins.op_str
        print(f"  {addr:#010x}  {x}  {y}")


if __name__ == "__main__":
    main()
