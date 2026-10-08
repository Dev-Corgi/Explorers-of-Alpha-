#!/usr/bin/env python3
"""Dump BL bottom-HUD code paths in overlay29 for review."""
import re
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
DRAW_TEXT = 0x02026214


def bl_target(addr: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return addr + 8 + (imm << 2)


def disasm_range(data: bytes, load: int, start: int, size: int) -> None:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in cs.disasm(data[start - load : start - load + size], start):
        off = ins.address - load
        word = struct.unpack_from("<I", data, off)[0] if 0 <= off < len(data) else 0
        extra = ""
        if ins.mnemonic == "bl":
            tgt = bl_target(ins.address, word)
            extra = f"  ; -> {tgt:#010x}"
            if tgt == DRAW_TEXT:
                extra += " DrawTextInWindow"
        elif ins.mnemonic in ("b", "beq", "bne", "blt", "bgt", "ble", "bge"):
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            extra = f"  ; -> {ins.address + 8 + (imm << 2):#010x}"
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{extra}")


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    ov29 = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[29].fileID]

    print("=== overlay29 BL HUD function @ 0x0234F430 ===")
    print("r0=window id (r5), r1=status struct*, mode byte at [r1]")
    print("mode 1 -> 0x234F460: BL label + PreprocessString belly value + /100")
    disasm_range(ov29, LOAD, 0x0234F430, 0x340)

    print("\n=== hook site @ 0x0234F75C (patched) ===")
    disasm_range(ov29, LOAD, 0x0234F758, 0x10)

    print("\n=== ZMove_DrawZGaugeHud cave @ 0x02330B80 ===")
    disasm_range(ov29, LOAD, 0x02330B80, 0x50)

    print("\n=== vtable pools ===")
    for pool in (0x0234F3F0, 0x02353438):
        ptr = struct.unpack_from("<I", ov29, pool - LOAD)[0]
        print(f"  [{pool:#010x}] -> {ptr:#010x}")

    print("\n=== ldr [pc] loading vtable region ===")
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for off in range(0, len(ov29) - 4, 4):
        addr = LOAD + off
        ins = next(cs.disasm(ov29[off : off + 4], addr), None)
        if ins is None or ins.mnemonic != "ldr" or "[pc" not in ins.op_str:
            continue
        m = re.search(r"#(0x[0-9a-f]+|\d+)", ins.op_str)
        if not m:
            continue
        imm = int(m.group(1), 0)
        literal = (addr + 8) + imm
        if 0x0234F3E0 <= literal <= 0x0234F400:
            val = struct.unpack_from("<I", ov29, literal - LOAD)[0]
            print(f"  {addr:#010x}: {ins.mnemonic} {ins.op_str}  ; [{literal:#010x}]={val:#010x}")

    print("\n=== overlay11 BL DrawText (y=0x16) when ov11 loaded @ 0x022DC240 ===")
    ov11 = rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[11].fileID]
    disasm_range(ov11, LOAD, 0x022FF0A0, 0x50)


if __name__ == "__main__":
    main()
