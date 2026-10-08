#!/usr/bin/env python3
"""Trace GetDungeonMsgArm9 dungeon-msg-index -> text_e.str mapping."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom

ARM9_BASE = 0x02000000
GET_DUNGEON_MSG = 0x020258C4


def find_rom() -> Path:
    root = Path(__file__).resolve().parents[1]
    for name in ("_tmp_rc_only.nds",):
        p = root / name
        if p.is_file():
            return p
    nds = list(root.glob("**/*.nds"))
    return nds[0]


def read_u32(data: bytes, addr: int) -> int:
    off = addr - ARM9_BASE
    return struct.unpack_from("<I", data, off)[0]


def read_u16(data: bytes, addr: int) -> int:
    off = addr - ARM9_BASE
    return struct.unpack_from("<H", data, off)[0]


def follow_get_dungeon_msg(arm9: bytes) -> None:
    off = GET_DUNGEON_MSG - ARM9_BASE
    code = arm9[off : off + 0x100]
    print(f"GetDungeonMsgArm9 @ {GET_DUNGEON_MSG:#x}")
    # scan for ldr to tables / mov patterns in first 0x80 bytes
    for i in range(0, 0x80, 4):
        w = struct.unpack_from("<I", code, i)[0]
        addr = GET_DUNGEON_MSG + i
        # ldr rX, [pc, #imm]
        if (w & 0xFFFF0000) == 0xE59F0000:
            rn = (w >> 16) & 0xF
            rd = w & 0xF
            imm = w & 0xFFF
            pc = addr + 8
            lit = pc + imm + (addr & 2)
            if ARM9_BASE <= lit < ARM9_BASE + len(arm9):
                val = read_u32(arm9, lit)
                print(f"  {addr:#010x}: ldr r{rd}, [pc+...] -> pool {lit:#x} = {val} ({val:#x})")
        # ldrh
        if (w & 0xFFFF0FF0) == 0xE1DF0000:
            print(f"  {addr:#010x}: ldrh? {w:08x}")


def scan_table_near(arm9: bytes, table_addr: int, count: int = 20) -> None:
    print(f"\nTable dump @ {table_addr:#x}:")
    for i in range(count):
        val = read_u16(arm9, table_addr + i * 2)
        print(f"  [{i}] msg_idx={table_addr - ARM9_BASE + i*2:#x} u16={val}")


def resolve_msg_index(arm9: bytes, msg_idx: int, strings) -> None:
    """Try common EoS mapping: table of u16 str indices indexed by (msg_idx - base)."""
    # Search arm9 for arrays containing known str indices like 3281, 3306 near msg_idx
    targets = {3281, 3282, 3306, 3307, 4587}
    hits = []
    for off in range(0, len(arm9) - 2, 2):
        v = struct.unpack_from("<H", arm9, off)[0]
        if v in targets:
            hits.append((ARM9_BASE + off, v))
    print(f"\n=== u16 hits for str indices {targets} in arm9 ({len(hits)} total) ===")
    for addr, v in hits[:40]:
        print(f"  {addr:#010x}: {v}")

    # Brute: find contiguous u16 table where entry at offset msg_idx equals expected
    print("\n=== brute table search: entry[msg_idx] == str_idx ===")
    for str_idx in (3281, 3306, 4587):
        for off in range(0, len(arm9) - msg_idx * 2 - 2, 2):
            at = struct.unpack_from("<H", arm9, off + msg_idx * 2)[0]
            if at == str_idx:
                base = ARM9_BASE + off
                print(f"  table_base={base:#x} entry[{msg_idx}]={str_idx}")
                # dump neighbors
                for j in range(max(0, msg_idx - 3), msg_idx + 4):
                    si = struct.unpack_from("<H", arm9, off + j * 2)[0]
                    txt = strings.strings[si] if si < len(strings.strings) else "?"
                    print(f"    [{j}] -> str {si}: {txt!r}")


def main() -> None:
    rom_path = find_rom()
    print(f"ROM: {rom_path}")
    rom = NintendoDSRom(rom_path.read_bytes())
    arm9 = bytes(rom.arm9)
    config = get_ppmdu_config_for_rom(rom)
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))

    follow_get_dungeon_msg(arm9)

    for msg_idx in (3281, 3282, 3306, 3307):
        print(f"\n--- analyze dungeon msg index {msg_idx} ---")
        print(f"  direct text_e.str[{msg_idx}] = {strings.strings[msg_idx]!r}")

    resolve_msg_index(arm9, 3307, strings)
    resolve_msg_index(arm9, 3282, strings)


if __name__ == "__main__":
    main()
