import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from skytemple_files.data.str.handler import StrHandler
from skytemple_files.common.util import get_ppmdu_config_for_rom, get_files_from_rom_with_extension

rom=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
config=get_ppmdu_config_for_rom(rom)
for fn in get_files_from_rom_with_extension(rom,"str"):
    if fn.endswith("text_e.str"):
        s=StrHandler.deserialize(rom.getFileByName(fn), string_encoding=config.string_encoding)
        for i in range(2450, 2470):
            print(f"{i}: {s.strings[i]!r}")
        print("---")
        for i in [19100,19101,19102,19120,2622,2623,2481]:
            print(f"{i}: {s.strings[i]!r}")
        # action 0x14 -> 0x14+0x987
        print(f"act14 str {0x14+0x987}: {s.strings[0x14+0x987]!r}")
        print(f"act0x2a default str {0x2a+0x987}: {s.strings[0x2a+0x987]!r}")
