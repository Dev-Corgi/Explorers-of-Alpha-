#!/usr/bin/env python3
"""Verify ZGauge: WRAM storage, results-screen zero via call-site hook."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "Explorers of Alpha2.nds"
OV29_BASE = 0x022DC240
ARM9_BASE = 0x02000000
ZGAUGE_RAM = 0x022B6A00
GET_DUNGEON_RESULT_MSG = 0x0200C4FC
GET_DUNGEON_RESULT_MSG_VANILLA = 0xE92D4078  # push {r3,r4,r5,r6,lr}
CALL_SITE = 0x0200C6F0
ARM9_GAUGE_CAVE = 0x020AF2C0
AF3E0 = 0x020AF3E0
RUN_DUNGEON = 0x022DEF38
DUNGEON_FREE = 0x022DEAB0
DEAL_DAMAGE_BODY = 0x02332B24
APPLY_DAMAGE = 0x02308FE0
HANDLE_FAINT = 0x022F7F30
BRANCH_MASK = 0xFF000000
BL_OPCODE = 0xEB000000
BRANCH_OPCODE = 0xEA000000
PUSH_RUN = 0xE92D4FF8
PUSH_FREE = 0xE92D4008


def bl_target(pc: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def main() -> None:
    rom_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROM
    rom = NintendoDSRom(rom_path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _id, _name: b"")
    ov29 = bytes(rom.files[table[29].fileID])
    arm9 = bytes(rom.arm9)

    assert struct.unpack_from("<I", ov29, RUN_DUNGEON - OV29_BASE)[0] == PUSH_RUN
    assert struct.unpack_from("<I", ov29, DUNGEON_FREE - OV29_BASE)[0] == PUSH_FREE
    assert (
        struct.unpack_from("<I", arm9, GET_DUNGEON_RESULT_MSG - ARM9_BASE)[0]
        == GET_DUNGEON_RESULT_MSG_VANILLA
    ), "GetDungeonResultMsg entry must be vanilla"

    call = struct.unpack_from("<I", arm9, CALL_SITE - ARM9_BASE)[0]
    assert (call & BRANCH_MASK) == BL_OPCODE, f"call site not bl: {call:#010x}"
    assert bl_target(CALL_SITE, call) == ARM9_GAUGE_CAVE

    assert arm9[AF3E0 - ARM9_BASE : AF3E0 - ARM9_BASE + 0x30] == bytes(0x30), "AF3E0 not cleared"

    for label, addr in (
        ("DealDamageBody", DEAL_DAMAGE_BODY),
        ("ApplyDamage", APPLY_DAMAGE),
        ("HandleFaint", HANDLE_FAINT),
    ):
        word = struct.unpack_from("<I", ov29, addr - OV29_BASE)[0]
        assert (word & BRANCH_MASK) == BRANCH_OPCODE, f"{label} not hooked @ {addr:#x}"

    cave = ov29[0x02330B20 - OV29_BASE : 0x02332000 - OV29_BASE]
    assert struct.pack("<I", ZGAUGE_RAM) in cave
    assert struct.unpack_from("<I", ov29, 0x02332000 - OV29_BASE)[0] == 0xE92D4030

    print(f"OK: ZGauge WRAM @ {ZGAUGE_RAM:#x}")
    print(f"OK: call-site bl -> {ARM9_GAUGE_CAVE:#x}; GetDungeonResultMsg vanilla; AF3E0 cleared")


if __name__ == "__main__":
    main()
