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


def bl_target(addr: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return addr + 8 + (imm << 2)


def find_callers(data: bytes, load: int, target: int) -> list[int]:
    out = []
    for off in range(0, len(data) - 4, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if (w & 0xFF000000) != 0xEB000000:
            continue
        if bl_target(load + off, w) == target:
            out.append(load + off)
    return out


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _: b"")
    ov10 = rom.files[table[10].fileID]
    ov11 = rom.files[table[11].fileID]
    ov29 = rom.files[table[29].fileID]
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    # Belly helpers used by ov11 UpdateTeamInfoBox before BL text
    belly_fns = {
        "GetBelly?": 0x02050C74,
        "GetMaxBelly?": 0x02050BB8,
        "CheckAlphaBL?": 0x0204CA94,
    }
    print("=== Callers of belly helpers ===")
    for name, fn in belly_fns.items():
        c29 = find_callers(ov29, LOAD, fn)
        c11 = find_callers(ov11, LOAD, fn)
        print(f"{name} {fn:#x}: ov29={len(c29)} ov11={len(c11)}")
        for a in c29[:8]:
            print(f"  ov29 {a:#x}")

    # Search ov29 for mov r1,#0x28 and mov r2,#0x16 pair (BL HUD coords from ov11)
    print("\n=== ov29: mov r1,#0x28 then mov r2,#0x16 (ov11 BL HUD coords) ===")
    for off in range(0, len(ov29) - 8, 4):
        ins = list(cs.disasm(ov29[off : off + 8], LOAD + off))
        if len(ins) >= 2:
            if ins[0].mnemonic == "mov" and ins[0].op_str == "r1, #0x28":
                if ins[1].mnemonic == "mov" and ins[1].op_str == "r2, #0x16":
                    print(f"  {LOAD + off:#010x}")

    # UpdateTeamStats in ov10
    print("\n=== ov10 UpdateTeamStats @ 0x22C0CE0 ===")
    L10 = table[10].ramAddress
    for ins in cs.disasm(ov10[0x22C0CE0 - L10 : 0x22C0CE0 - L10 + 0x80], 0x22C0CE0):
        w = struct.unpack_from("<I", ov10, ins.address - L10)[0]
        ex = ""
        if ins.mnemonic == "bl":
            ex = f" -> {bl_target(ins.address, w):#x}"
        print(f"{ins.address:08X}: {ins.mnemonic} {ins.op_str}{ex}")

    print("\n=== ov11 UpdateTeamInfoBox BL lines (y=0x16) ===")
    off = 0x22FEFA4 - LOAD
    for ins in cs.disasm(ov11[off : off + 0x140], 0x22FEFA4):
        mark = ""
        if ins.address in (0x022FF0A8, 0x022FF0D8):
            mark = "  << BL HUD"
        w = struct.unpack_from("<I", ov11, ins.address - LOAD)[0]
        ex = ""
        if ins.mnemonic == "bl":
            ex = f" -> {bl_target(ins.address, w):#x}"
        print(f"{ins.address:08X}: {ins.mnemonic} {ins.op_str}{ex}{mark}")
        if ins.address >= 0x022FF0E8:
            break


if __name__ == "__main__":
    main()
