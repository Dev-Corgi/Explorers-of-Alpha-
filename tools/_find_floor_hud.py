#!/usr/bin/env python3
"""Find dungeon floor HUD (1F, Lv, HP, BL) draw path in ROM."""
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
LOAD29 = 0x022DC240
DRAW_TEXT = 0x02026214
SNPRINTF_A = 0x020235B8
SNPRINTF_B = 0x0208955C
GET_PERF = 0x0204CA94


def bl_target(addr: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return addr + 8 + (imm << 2)


def scan_bl(data: bytes, load: int, target: int) -> list[int]:
    out = []
    for off in range(0, len(data) - 4, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if (w & 0xFF000000) != 0xEB000000:
            continue
        if bl_target(load + off, w) == target:
            out.append(load + off)
    return out


def coords_before_draw(data: bytes, load: int, addr: int) -> tuple[str, str]:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    off = addr - load
    chunk = data[max(0, off - 36) : off + 4]
    x = y = "?"
    for ins in cs.disasm(chunk, addr - min(36, off)):
        if ins.address >= addr:
            break
        if ins.mnemonic == "mov" and ins.op_str.startswith("r1, #"):
            x = ins.op_str
        if ins.mnemonic == "mov" and ins.op_str.startswith("r2, #"):
            y = ins.op_str
    return x, y


def disasm_window(data: bytes, load: int, start: int, size: int = 0x200) -> None:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in cs.disasm(data[start - load : start - load + size], start):
        off = ins.address - load
        w = struct.unpack_from("<I", data, off)[0] if 0 <= off < len(data) else 0
        extra = ""
        if ins.mnemonic == "bl":
            tgt = bl_target(ins.address, w)
            extra = f"  ; -> {tgt:#010x}"
            if tgt == DRAW_TEXT:
                extra += " DrawText"
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{extra}")


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")
    ov11 = rom.files[table[11].fileID]
    ov29 = rom.files[table[29].fileID]

    print("=== ov11 UpdateTeamInfoBox (Alpha floor HUD candidate) ===")
    print("DrawText sites in walking HUD function:\n")
    for addr in scan_bl(ov11, LOAD29, DRAW_TEXT):
        if 0x022FEF00 <= addr <= 0x022FF200:
            x, y = coords_before_draw(ov11, LOAD29, addr)
            print(f"  {addr:#010x}  {x}  {y}")

    print("\n=== ov29: ALL DrawText (any y) in 0x22FE000-0x22FF200 RAM range ===")
    print("(same RAM slot as ov11 TeamInfoBox when dungeon loaded)\n")
    for addr in scan_bl(ov29, LOAD29, DRAW_TEXT):
        if 0x022FE000 <= addr <= 0x022FF200:
            x, y = coords_before_draw(ov29, LOAD29, addr)
            print(f"  {addr:#010x}  {x}  {y}")

    print("\n=== ov29: search mov r2,#4 + DrawText (HP line in ov11 is y=4) ===")
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for off in range(0, len(ov29) - 4, 4):
        ins = next(cs.disasm(ov29[off : off + 4], LOAD29 + off), None)
        if ins is None or ins.op_str != "r2, #4":
            continue
        # next few ins - find bl DrawText
        for ins2 in cs.disasm(ov29[off : off + 24], LOAD29 + off):
            if ins2.mnemonic != "bl":
                continue
            w = struct.unpack_from("<I", ov29, ins2.address - LOAD29)[0]
            if bl_target(ins2.address, w) == DRAW_TEXT:
                x, _ = coords_before_draw(ov29, LOAD29, ins2.address)
                print(f"  DrawText@{ins2.address:#010x}  {x}  r2,#4  (near {LOAD29+off:#x})")
                break

    print("\n=== ov29 callers of GetPerformanceFlagWithChecks (ov11 uses r0=#0x16 before BL label) ===")
    for addr in scan_bl(ov29, LOAD29, GET_PERF):
        chunk = ov29[addr - LOAD29 - 16 : addr - LOAD29 + 4]
        for ins in cs.disasm(chunk, addr - 16):
            if ins.address >= addr:
                break
            if ins.mnemonic == "mov" and "#0x16" in ins.op_str:
                print(f"  {addr:#010x}  preceded by {ins.mnemonic} {ins.op_str}")
                break
        else:
            print(f"  {addr:#010x}")

    print("\n=== ov11 UpdateTeamInfoBox BL+HP region disasm ===")
    disasm_window(ov11, LOAD29, 0x022FEFDC, 0x120)


if __name__ == "__main__":
    main()
