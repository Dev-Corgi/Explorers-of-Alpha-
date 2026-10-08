#!/usr/bin/env python3
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent.parent
for label, path in [
    ("vanilla", ROOT / "don't touch here (legacy)" / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"),
    ("patched", ROOT / "Export Rom" / "Room_Charge_V3_Test" / "_shell559+spinda_menu.nds"),
]:
    if not path.is_file():
        continue
    rom = NintendoDSRom(path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov = rom.files[table[19].fileID]
    load = table[19].ramAddress
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    print(f"\n======== {label} ov19 size {len(ov)} ========")
    for start, end, title in [
        (0x238AB40, 0x238ABE0, "ABC0 region"),
        (0x238AD90, 0x238AE30, "inner action handler"),
        (0x238B450, 0x238B520, "B474 inner16"),
    ]:
        print(f"\n--- {title} ---")
        for ins in cs.disasm(ov[start - load : end - load], start):
            mark = " <<<" if ins.address in (0x238ABC0, 0x238ABC4, 0x238B474) else ""
            print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")
    b474 = struct.unpack_from("<I", ov, 0x238B474 - load)[0]
    print(f"\nB474 -> {b474:#010x}")
    if b474 >= load and b474 < load + len(ov):
        for i in range(7):
            off = b474 - load + i * 8
            sid, _, act, _ = struct.unpack_from("<4H", ov, off)
            print(f"  table+{i*8}: str={sid} act={act}")
            if sid == 0:
                break
