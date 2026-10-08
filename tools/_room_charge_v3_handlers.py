#!/usr/bin/env python3
import struct
from collections import defaultdict
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.data_cd.handler import DataCDHandler

TARGET = [
    82, 101, 112, 113, 118, 131, 149, 150, 168, 219, 230, 238, 256, 270, 278, 296,
    361, 362, 437, 460, 484, 521, 523, 538, 554,
]
GENERIC = 0


def first_overlay_bl(code: bytes) -> int | None:
    for off in range(0, len(code) - 3, 4):
        w = struct.unpack_from("<I", code, off)[0]
        if (w >> 24) != 0xEB:
            continue
        pc = 0x02330134 + off + 8
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        tgt = pc + (imm << 2)
        if 0x022DC240 <= tgt <= 0x02360000:
            return tgt
    return None


def main() -> None:
    rom_path = Path(__file__).resolve().parents[1] / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
    rom = NintendoDSRom(rom_path.read_bytes())
    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/waza_cd.bin"))
    config = get_ppmdu_config_for_rom(rom)
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))
    names = strings.strings[
        config.string_index_data.string_blocks["Move Names"].begin :
        config.string_index_data.string_blocks["Move Names"].end + 1
    ]
    handlers: dict[int, int | None] = {}
    for mid in TARGET:
        code = cd.get_effect_code(cd.get_item_effect_id(mid))
        handlers[mid] = first_overlay_bl(code)

    for mid in TARGET:
        tgt = handlers[mid]
        rel = hex(tgt) if tgt else "GENERIC"
        print(f"{mid:3d} {names[mid]:18s} {rel}")

    groups: dict[int | None, list[int]] = defaultdict(list)
    for mid, tgt in handlers.items():
        groups[tgt].append(mid)
    print("\n# handler groups")
    for tgt in sorted(groups, key=lambda x: (x is None, x or 0)):
        label = "GenericRoomRelease" if tgt is None else hex(tgt)
        print(label, groups[tgt])


if __name__ == "__main__":
    main()
