#!/usr/bin/env python3
"""Scan ov29 for all GetDungeonMsgArm9 call sites and their message indices."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType

OV29_LOAD = 0x022DC240
GET_DUNGEON_MSG = 0x020258C4


def main() -> None:
    rom = NintendoDSRom((Path(__file__).resolve().parents[1] / "_tmp_rc_only.nds").read_bytes())
    ov = bytes(rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[29].fileID])
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    hits: list[tuple[int, int | None]] = []
    for ins in md.disasm(ov, OV29_LOAD):
        if ins.mnemonic != "bl":
            continue
        tgt = int(ins.op_str.lstrip("#"), 16)
        if tgt != GET_DUNGEON_MSG:
            continue
        # walk back up to 8 insns for ldr r0, [pc]
        idx = None
        back_off = ins.address - OV29_LOAD
        for delta in range(4, 40, 4):
            woff = back_off - delta
            if woff < 0:
                break
            w = struct.unpack_from("<I", ov, woff)[0]
            # ldr r0, [pc, #imm]
            if (w & 0xFFFF0000) == 0xE59F0000 and (w & 0xF) == 0:
                pc = OV29_LOAD + woff + 8
                imm = w & 0xFFF
                pool = pc + imm + ((OV29_LOAD + woff) & 2)
                poff = pool - OV29_LOAD
                if 0 <= poff + 4 <= len(ov):
                    idx = struct.unpack_from("<I", ov, poff)[0]
                    break
        hits.append((ins.address, idx))

    print(f"Found {len(hits)} GetDungeonMsgArm9 calls in ov29\n")
    for addr, idx in sorted(set(hits)):
        if idx is None:
            print(f"  {addr:#010x}: msg_idx=?")
            continue
        direct = strings.strings[idx] if idx < len(strings.strings) else "?"
        print(f"  {addr:#010x}: msg_idx={idx}  text_e.str[{idx}]={direct!r}")

    print("\n=== readying-related indices ===")
    for addr, idx in sorted(set(hits)):
        if idx is None:
            continue
        if idx in range(3270, 3320):
            print(f"  {addr:#010x}: {idx} -> {strings.strings[idx]!r}")


if __name__ == "__main__":
    main()
