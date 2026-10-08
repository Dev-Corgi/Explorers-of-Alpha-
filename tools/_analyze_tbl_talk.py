#!/usr/bin/env python3
from pathlib import Path
import struct
from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType

rom = NintendoDSRom((Path(__file__).resolve().parents[1] / "_tmp_rc_only.nds").read_bytes())
strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))
tlk = rom.getFileByName("MESSAGE/tbl_talk.tlk")
print("tlk size", len(tlk))

for i in range(4575, 4600):
    s = strings.strings[i]
    if "TALK_MESSAGE" in s:
        print(i, repr(s))

# brute hdr + index scales
for hdr in range(0, 128, 2):
    for scale in (2, 4):
        off3307 = hdr + 3307 * scale
        if off3307 + 2 > len(tlk):
            continue
        v = struct.unpack_from("<H", tlk, off3307)[0]
        if v == 4587:
            print(f"tlk maps 3307->4587 with hdr={hdr} scale={scale}")
            for idx in (3281, 3282, 3306, 3307):
                o = hdr + idx * scale
                sid = struct.unpack_from("<H", tlk, o)[0]
                txt = strings.strings[sid] if sid < len(strings.strings) else "?"
                print(f"  tlk[{idx}] -> {sid}: {txt!r}")
