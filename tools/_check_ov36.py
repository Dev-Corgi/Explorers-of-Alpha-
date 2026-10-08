#!/usr/bin/env python3
from pathlib import Path
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = [
    ROOT / "don't touch here (legacy)" / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds",
    ROOT / "Export Rom" / "Room_Charge_V3_Test" / "_shell559+spinda_menu.nds",
]


def check(path: Path) -> None:
    if not path.is_file():
        print(f"MISSING {path}")
        return
    rom = NintendoDSRom(path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    print(f"\n=== {path.name} ===")
    print(f"overlay slots: {len(table)}  has 36: {36 < len(table)}")
    if 36 >= len(table):
        return
    entry = table[36]
    data = rom.files[entry.fileID]
    print(f"ov36 RAM {entry.ramAddress:#010x}  ramSize {entry.ramSize:#x}  file {len(data):,} B")


if __name__ == "__main__":
    for p in CANDIDATES:
        check(p)
