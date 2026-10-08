#!/usr/bin/env python3
from pathlib import Path
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
VANILLA = ROOT / "don't touch here (legacy)" / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
OUT = ROOT / "true_patches" / "spinda_ev_v2" / "data" / "arm9_boot_tail.bin"
START = 0x94AE8
END = 0x9F904

rom = NintendoDSRom(VANILLA.read_bytes())
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(rom.arm9[START:END])
print(f"wrote {OUT} ({END - START} bytes)")
