import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from skytemple_files.data.str.handler import StrHandler
from skytemple_files.common.util import get_ppmdu_config_for_rom, get_files_from_rom_with_extension

rom=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
van=NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
table=loadOverlayTable(rom.arm9OverlayTable, lambda i,n:b"")
addr=0x0237C91C
for i,e in enumerate(table):
    if e and e.ramAddress <= addr < e.ramAddress+e.ramSize:
        print(f"table in ov{i} ram={e.ramAddress:#x}")
        off=addr-e.ramAddress
        data=rom.loadArm9Overlays()[i].data
        print("entries action 0..50 and 0x2a:")
        for action in list(range(0,51))+[0x26,0x28,0x29,0x2a,0x2b]:
            o=off+action*8
            if o+8<=len(data):
                a,b=struct.unpack_from("<HH", data, o)
                # formula: string = field + 0x87 + 0x900 = field + 0x987
                sid=(a+0x987)&0xFFFF
                print(f"  act {action:3} ({action:#x}): field0={a:5} => str~{sid}")

# What are strings 2622, 2623 and which field maps to them?
# sid = a + 0x987 => a = sid - 0x987
for sid in [2622,2623,19101]:
    field=(sid-0x987)&0xFFFF
    print(f"string {sid} would need field0={field} ({field:#x})")

config=get_ppmdu_config_for_rom(rom)
for fn in get_files_from_rom_with_extension(rom,"str"):
    if fn.endswith("text_e.str"):
        strings=StrHandler.deserialize(rom.getFileByName(fn), string_encoding=config.string_encoding)
        for sid in [2622,2623,19100,19101,19102]:
            print(f"str[{sid}]={strings.strings[sid]!r}")
