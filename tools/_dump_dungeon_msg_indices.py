#!/usr/bin/env python3
"""Dump text_e.str at battle/dungeon message indices and scan DoMoveSolarBeam."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom

ARM9_BASE = 0x02000000
GET_DUNGEON_MSG = 0x020258C4
OV29_LOAD = 0x022DC240
DO_MOVE_SOLAR_BEAM = 0x02328C74


def find_rom() -> Path:
    root = Path(__file__).resolve().parents[1]
    candidates = list(root.glob("**/*.nds"))
    for p in candidates:
        if "vanilla" in p.name.lower() or p.name == "_tmp_rc_only.nds":
            return p
    if candidates:
        return candidates[0]
    raise SystemExit("No .nds found")


def dump_strings(rom: NintendoDSRom) -> None:
    config = get_ppmdu_config_for_rom(rom)
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))
    print(f"total strings: {len(strings.strings)}")
    print("\n=== string blocks (battle/dungeon/talk) ===")
    for name, block in sorted(config.string_index_data.string_blocks.items()):
        if any(k in name.lower() for k in ("battle", "dungeon", "talk", "message", "script")):
            print(f"  {name}: {block.begin}..{block.end}")

    idxs = list(range(3275, 3315)) + [4580, 4587]
    print("\n=== text_e.str around 3281/3306 ===")
    for i in idxs:
        if i < len(strings.strings):
            s = strings.strings[i].replace("\n", "\\n")
            print(f"  {i}: {s!r}")

    # search for readying strings
    print("\n=== strings containing 'readying' ===")
    for i, s in enumerate(strings.strings):
        if "readying" in s.lower():
            print(f"  {i}: {s!r}")


def scan_solar_beam(rom: NintendoDSRom) -> None:
    ov29 = rom.loadArm9Overlays([29])[29].data
    off = DO_MOVE_SOLAR_BEAM - OV29_LOAD
    chunk = ov29[off : off + 0x120]
    print(f"\n=== DoMoveSolarBeam @ {DO_MOVE_SOLAR_BEAM:#x} (file+{off:#x}) ===")
    # find ldr = immediates and bl targets
    for i in range(0, len(chunk) - 3, 4):
        w = struct.unpack_from("<I", chunk, i)[0]
        addr = DO_MOVE_SOLAR_BEAM + i
        if (w & 0xFFFF0000) == 0xE59F0000:  # ldr r0, [pc, #imm]
            pc = addr + 8
            lit_off = (w & 0xFFF) + ((addr & 2) + 4)
            lit_addr = pc + lit_off
            lit_file = lit_addr - OV29_LOAD
            if 0 <= lit_file + 4 <= len(ov29):
                val = struct.unpack_from("<I", ov29, lit_file)[0]
                print(f"  {addr:#010x}: ldr pool -> {val} ({val:#x})")
        if (w >> 24) == 0xEB:
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            tgt = addr + 8 + (imm << 2)
            if tgt == GET_DUNGEON_MSG:
                print(f"  {addr:#010x}: bl GetDungeonMsgArm9")


def disasm_get_dungeon_msg(rom: NintendoDSRom) -> None:
    arm9 = rom.arm9Code
    off = GET_DUNGEON_MSG - ARM9_BASE
    chunk = arm9[off : off + 0x80]
    print(f"\n=== GetDungeonMsgArm9 entry @ {GET_DUNGEON_MSG:#x} ===")
    for i in range(0, min(len(chunk), 0x40), 4):
        w = struct.unpack_from("<I", chunk, i)[0]
        print(f"  {GET_DUNGEON_MSG + i:#010x}: {w:08x}")


def main() -> None:
    rom_path = find_rom()
    print(f"ROM: {rom_path}")
    rom = NintendoDSRom(rom_path.read_bytes())
    dump_strings(rom)
    scan_solar_beam(rom)
    disasm_get_dungeon_msg(rom)


if __name__ == "__main__":
    main()
