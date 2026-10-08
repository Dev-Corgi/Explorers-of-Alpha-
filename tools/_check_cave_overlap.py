#!/usr/bin/env python3
"""Check whether ov29 caves sit on vanilla padding vs live code."""
from __future__ import annotations

import json
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
VANILLA = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
STATE = ROOT / "Export Rom" / "full_stack.state.json"


def main() -> None:
    rom = NintendoDSRom(VANILLA.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov = rom.files[table[29].fileID]
    base = table[29].ramAddress
    state = json.loads(STATE.read_text())

    print(f"ov29 file size {len(ov):#x} load {base:#x}")
    for mod in state["modules"]:
        for c in mod.get("caves", []):
            if c.get("overlay") != "ov29":
                continue
            fo = c["file_offset"]
            sz = c["size"]
            chunk = ov[fo : fo + sz]
            nz = sum(1 for b in chunk if b != 0)
            la = c.get("load_address", base + fo)
            print(
                f"{mod['id']:16} off={fo:#7x} la={la:#x} size={sz:4} "
                f"nonzero={nz:4}/{sz} head={chunk[:8].hex()}"
            )


if __name__ == "__main__":
    main()
