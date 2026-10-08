#!/usr/bin/env python3
"""Simulate StringFromId / text_e.str pointer lookup (1-based ID)."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType


def string_from_id(raw: bytes, string_id: int) -> str:
    if string_id < 1:
        return "<invalid>"
    i = string_id - 1
    ptr_off = i * 4
    if ptr_off + 8 > len(raw):
        return "<oor>"
    start, end = struct.unpack_from("<II", raw, ptr_off)
    if end <= start or end > len(raw):
        return f"<bad ptr {start:#x}-{end:#x}>"
    return raw[start:end].decode("cp1252", errors="replace")


def main() -> None:
    rom = NintendoDSRom((Path(__file__).resolve().parents[1] / "_tmp_rc_only.nds").read_bytes())
    raw = bytes(rom.getFileByName("MESSAGE/text_e.str"))
    strings = FileType.STR.deserialize(raw)

    ids = [3276, 3280, 3281, 3282, 3306, 3307, 4587]
    print("StringFromId simulation (text_e.str pointer table, 1-based ID):\n")
    for sid in ids:
        sim = string_from_id(raw, sid)
        des = strings.strings[sid] if sid < len(strings.strings) else "?"
        match = "OK" if sim.split("\x00")[0] == des else "MISMATCH"
        print(f"  ID {sid}: {sim!r}  [{match}]")


if __name__ == "__main__":
    main()
