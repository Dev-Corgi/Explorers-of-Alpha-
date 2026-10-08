#!/usr/bin/env python3
"""Find dungeon message index -> text_e.str mapping used by GetDungeonMsgArm9."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType

ARM9_BASE = 0x02000000
GET_MSG_FILE_BASE_POOL = 0x020258B0  # literal pool for GetMsgFile


def read_arm9_pools(arm9: bytes, addr: int) -> int:
    return struct.unpack_from("<I", arm9, addr - ARM9_BASE)[0]


def parse_msg_file(data: bytes, index: int, strings) -> tuple[int, str] | None:
    """Parse standard PMD2 message pack entry (1-based index)."""
    if index < 1:
        return None
    i = index - 1
    if i * 8 + 8 > len(data):
        return None
    start, end = struct.unpack_from("<II", data, i * 8)
    if end <= start or end > len(data):
        return None
    payload = data[start:end]
    # payload may be raw string bytes or u16 str index
    if len(payload) == 2:
        sid = struct.unpack_from("<H", payload)[0]
        if sid < len(strings.strings):
            return sid, strings.strings[sid]
    try:
        txt = payload.decode("cp1252")
        return -1, txt
    except Exception:
        return None


def scan_file(path: str, data: bytes, strings, indices: list[int]) -> None:
    hits = 0
    for idx in indices:
        r = parse_msg_file(data, idx, strings)
        if r:
            sid, txt = r
            print(f"  {path} msg[{idx}] -> str {sid}: {txt!r}")
            hits += 1
    if hits:
        print(f"  => {hits} hits in {path} ({len(data)} bytes)")


def main() -> None:
    rom_path = Path(__file__).resolve().parents[1] / "_tmp_rc_only.nds"
    rom = NintendoDSRom(rom_path.read_bytes())
    arm9 = bytes(rom.arm9)
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))

    indices = [3276, 3280, 3281, 3282, 3306, 3307]

    print("Expected mappings:")
    for idx in indices:
        print(f"  text_e.str[{idx}] = {strings.strings[idx]!r}")

    # GetMsgFile pools
    base = read_arm9_pools(arm9, 0x020258B0)
    state = read_arm9_pools(arm9, 0x020258B4)
    print(f"\nGetMsgFile base={base:#x} state={state:#x}")

    # collect all rom files
    files: list[tuple[str, bytes]] = []

    def walk(folder, prefix=""):
        for name, sub in folder.folders:
            walk(sub, prefix + name + "/")
        for name in folder.files:
            fid = folder.files.index(name)
            # ndspy folder.files is list of names; need file id from rom
            pass

    # brute: iterate rom.files with names from a path list
    def collect(folder, prefix=""):
        for name, sub in folder.folders:
            collect(sub, prefix + name + "/")
        for fname in folder.files:
            path = prefix + fname
            try:
                files.append((path, bytes(rom.getFileByName(path))))
            except Exception:
                pass

    collect(rom.filenames)

    print(f"\nScanning {len(files)} ROM files for msg pack entries...")
    for path, data in files:
        if len(data) < 3307 * 8:
            continue
        scan_file(path, data, strings, indices)

    # Also scan arm9/overlay for u16 remap tables
    print("\nScan arm9 for u16[idx] -> str_id with valid strings at key indices:")
    for off in range(0, len(arm9) - 3310 * 2, 2):
        ok = True
        mapping = {}
        for idx in (3282, 3306, 3307):
            sid = struct.unpack_from("<H", arm9, off + idx * 2)[0]
            if sid >= len(strings.strings):
                ok = False
                break
            mapping[idx] = sid
        if not ok:
            continue
        if mapping[3282] == 3281 and mapping[3306] == 3306:
            base = ARM9_BASE + off
            print(f"  candidate @ {base:#x}")
            for idx in indices:
                sid = struct.unpack_from("<H", arm9, off + idx * 2)[0]
                print(f"    [{idx}] -> str {sid}: {strings.strings[sid]!r}")


if __name__ == "__main__":
    main()
