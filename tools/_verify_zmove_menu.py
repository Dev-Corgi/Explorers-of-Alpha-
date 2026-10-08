#!/usr/bin/env python3
import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_files_from_rom_with_extension
from skytemple_files.data.str.handler import StrHandler

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_orbcharges_orbcount_tmread_zmove_menu.nds"
)
BASE = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_orbcharges_orbcount_tmread.nds"
)

OV29 = 0x022DC240
OV31 = 0x02382820


def load_ov(rom: NintendoDSRom, ov_id: int) -> bytes:
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return bytes(rom.files[table[ov_id].fileID])


def word(blob: bytes, addr: int, base: int) -> int:
    off = addr - base
    return struct.unpack_from("<I", blob, off)[0]


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    base_rom = NintendoDSRom(BASE.read_bytes())
    ov29 = load_ov(rom, 29)
    ov31 = load_ov(rom, 31)
    ov29_base = load_ov(base_rom, 29)

    checks = [
        ("ov29 EB2DC GetSubMenu hook", ov29, 0x022EB2DC, OV29, lambda w: (w >> 24) == 0xEA),
        ("ov29 FEDB8 tmread restore", ov29, 0x022FEDB8, OV29, lambda w: (w >> 24) == 0xEA),
        ("ov31 859C0 menu hook", ov31, 0x023859C0, OV31, lambda w: (w >> 24) == 0xEA),
        ("ov29 30B20 cave nonzero", ov29, 0x02330B20, OV29, lambda w: w != 0),
    ]
    for name, blob, addr, base, fn in checks:
        w = word(blob, addr, base)
        status = "OK" if fn(w) else "FAIL"
        print(f"{status} {name}: {w:#010x}")

    w_in = word(ov29_base, 0x022FEDB8, OV29)
    w_out = word(ov29, 0x022FEDB8, OV29)
    print(f"tmread FEDB8 unchanged vs input: {w_in == w_out} ({w_in:#010x})")

    for filename in get_files_from_rom_with_extension(rom, "str"):
        if not filename.endswith("text_e.str"):
            continue
        strings = StrHandler.deserialize(rom.getFileByName(filename))
        print(f"str[19075] = {strings.strings.get(19075)!r}")
        print(f"str[19076] = {strings.strings.get(19076)!r}")
        print(f"str[19077] = {strings.strings.get(19077)!r}")
        print(f"str[19094] = {strings.strings.get(19094)!r}")


if __name__ == "__main__":
    main()
