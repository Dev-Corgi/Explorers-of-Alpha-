import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from skytemple_files.data.str.handler import StrHandler
from skytemple_files.common.util import get_ppmdu_config_for_rom, get_files_from_rom_with_extension

rom = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
config = get_ppmdu_config_for_rom(rom)
hits=[]
for fn in get_files_from_rom_with_extension(rom, "str"):
    if not fn.endswith("text_e.str"):
        continue
    strings = StrHandler.deserialize(rom.getFileByName(fn), string_encoding=config.string_encoding)
    for i,s in enumerate(strings.strings):
        if s and "Shift" in s:
            hits.append((i,s.replace("\n","\\n")[:120]))
print(f"hits={len(hits)}")
for i,s in hits[:40]:
    print(f"  {i}: {s}")
