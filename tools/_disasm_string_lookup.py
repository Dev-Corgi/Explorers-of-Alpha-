#!/usr/bin/env python3
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom

ARM9_BASE = 0x02000000
GET_STRING = 0x02025788
GET_MSG_FILE = 0x02025888
GET_DUNGEON_MSG = 0x020258C4


def disasm_range(arm9: bytes, start: int, size: int = 0x200) -> None:
    off = start - ARM9_BASE
    code = arm9[off : off + size]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    print(f"\n=== Disasm @ {start:#x} ===")
    for ins in md.disasm(code, start):
        print(f"  {ins.address:#010x}: {ins.mnemonic:6s} {ins.op_str}")
        if ins.address >= start + 0x100:
            break


def read_pools(arm9: bytes, start: int, size: int = 0x200) -> list[tuple[int, int]]:
    off = start - ARM9_BASE
    code = arm9[off : off + size]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    pools = []
    for ins in md.disasm(code, start):
        if ins.mnemonic != "ldr" or "pc" not in ins.op_str:
            continue
        woff = ins.address - start
        w = struct.unpack_from("<I", code, woff)[0]
        imm12 = w & 0xFFF
        pool = (ins.address + 8 + imm12) & 0xFFFFFFFF
        poff = pool - start
        if 0 <= poff + 4 <= len(code):
            val = struct.unpack_from("<I", code, poff)[0]
            pools.append((pool, val))
    return pools


def resolve_string(arm9: bytes, strings, msg_idx: int) -> None:
    """Simulate lookup chain by finding the message index table."""
    # From GetDungeonMsgArm9: bl GetMsgFile then bl GetString( file, idx )
    # Disasm 0x2025788 to find table format
    pass


def find_msg_table(arm9: bytes, strings) -> None:
    """Find u16 table where [3282] maps to useful string and [3306] maps to readying its move."""
    # Known: vanilla solar beam passes 3282, should show "readying Solar Beam" = str 3281
    # So table[3282] should be 3281 ideally
    # Or maybe the index IS the string id for some ranges

    # Search overlay too - maybe table is in overlay
    print("Searching arm9 for u16 table where [3282]==3281...")
    for off in range(0, len(arm9) - 3308 * 2, 2):
        v3282 = struct.unpack_from("<H", arm9, off + 3282 * 2)[0]
        v3306 = struct.unpack_from("<H", arm9, off + 3306 * 2)[0]
        if v3282 == 3281 and v3306 == 3306:
            base = ARM9_BASE + off
            print(f"FOUND table @ {base:#x}")
            for idx in (3276, 3280, 3281, 3282, 3306, 3307):
                si = struct.unpack_from("<H", arm9, off + idx * 2)[0]
                print(f"  [{idx}] -> str {si}: {strings.strings[si]!r}")
            return
    print("Not found in arm9 with simple u16[idx] mapping")


def main() -> None:
    rom = NintendoDSRom((Path(__file__).resolve().parents[1] / "_tmp_rc_only.nds").read_bytes())
    arm9 = bytes(rom.arm9)
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))

    disasm_range(arm9, GET_STRING, 0x120)
    disasm_range(arm9, GET_MSG_FILE, 0x80)
    print("\nPools in GetString:")
    for pool, val in read_pools(arm9, GET_STRING, 0x120):
        print(f"  {pool:#x} -> {val:#x}")
        if ARM9_BASE <= val < ARM9_BASE + len(arm9):
            toff = val - ARM9_BASE
            print(f"    first u16s: {[struct.unpack_from('<H', arm9, toff+i*2)[0] for i in range(16)]}")

    find_msg_table(arm9, strings)

    # Also search in ROM files for message table binary
    for fn in rom.filenames:
        if "msg" in fn.lower() or "message" in fn.lower() or "dialogue" in fn.lower():
            if fn.endswith(".bin") or fn.endswith(".srb") or "MESSAGE" in fn:
                print("file:", fn)


if __name__ == "__main__":
    main()
