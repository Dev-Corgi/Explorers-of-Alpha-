#!/usr/bin/env python3
"""Set MOVE_PROJECTILE post-CalcDamage multiplier to 1.0 (vanilla 0.5)."""

from __future__ import annotations

import struct
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom

from patch_engine.overlay_caves import get_rom_binary, write_rom_binary

ROOT = Path(__file__).resolve().parents[1]
ROM_PATH = ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack_no_loader.nds"
OV29_LOAD = 0x022DC240
# CalcDamage: after cmp move_id==PROJECTILE, mov r1, #mult then Fx multiply into [r8]
SITE = 0x0230CFA8
MOV_R1_0x80 = 0xE3A01080
MOV_R1_0x100 = 0xE3A01C01


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROM_PATH))
    ov29 = get_rom_binary(rom, "ov29")
    off = SITE - OV29_LOAD
    cur = struct.unpack_from("<I", ov29, off)[0]
    if cur not in (MOV_R1_0x80, MOV_R1_0x100):
        raise RuntimeError(f"unexpected word at {SITE:#x}: {cur:#010x}")
    struct.pack_into("<I", ov29, off, MOV_R1_0x100)
    write_rom_binary(rom, get_ppmdu_config_for_rom(rom), "ov29", bytes(ov29))
    ROM_PATH.write_bytes(rom.save())
    (ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds").write_bytes(
        ROM_PATH.read_bytes()
    )
    print(f"projectile mult @ {SITE:#x}: {cur:#010x} -> {MOV_R1_0x100:#010x} (1.0)")
    print("synced")


if __name__ == "__main__":
    main()
