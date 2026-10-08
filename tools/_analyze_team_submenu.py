"""Analyze Spinda Drink team-member submenu structure in overlay19."""
from __future__ import annotations

import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import (
    get_files_from_rom_with_extension,
    get_ppmdu_config_for_rom,
)
from skytemple_files.data.str.handler import StrHandler

ROM = "Explorers of Alpha_berryboost.nds"
MENU_E290 = 0x0238E290

rom = NintendoDSRom.fromFile(ROM)
table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
ov19 = rom.files[table[19].fileID]
base = table[19].ramAddress
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

config = get_ppmdu_config_for_rom(rom)
strings = None
for fn in get_files_from_rom_with_extension(rom, "str"):
    if fn.endswith("text_e.str"):
        strings = StrHandler.deserialize(
            rom.getFileByName(fn), string_encoding=config.string_encoding
        )
        break


def read_pool(insn: int, imm: int) -> tuple[int, int]:
    addr = insn + 8 + imm
    val = struct.unpack_from("<I", ov19, addr - base)[0]
    return addr, val


def show_menu(ptr: int, label: str) -> None:
    off = ptr - base
    print(f"\n{label} @{ptr:#010x}:")
    for i in range(8):
        sid = struct.unpack_from("<H", ov19, off + i * 8)[0]
        act = struct.unpack_from("<H", ov19, off + i * 8 + 4)[0]
        if sid == 0:
            break
        text = strings.strings[sid][:40] if sid < len(strings.strings) else "?"
        print(f"  [{i}] act={act:2d} str={sid:#06x}: {text!r}")


print("=== 238AB40-238ABC0 (menu setup before team pick) ===")
for ins in cs.disasm(ov19[0x238AB40 - base : 0x238ABC0 - base], 0x0238AB40):
    print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

for pc, imm in [(0x0238AB80, 0x8EC), (0x0238C280, 0x27C), (0x0238D2EC, 0x18)]:
    pool, val = read_pool(pc, imm)
    print(f"pool used near {pc:#x} -> @{pool:#x} = {val:#010x}")

show_menu(MENU_E290, "Per-member submenu (vanilla)")

print("\n=== inner 20 action handler (238AD90) ===")
for ins in cs.disasm(ov19[0x0238AD90 - base : 0x0238AE30 - base], 0x0238AD90):
    print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

print("\n=== 238CCEC stat row builder (first case sb=0) ===")
for ins in cs.disasm(ov19[0x0238CD5C - base : 0x0238CD90 - base], 0x0238CD5C):
    print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")
