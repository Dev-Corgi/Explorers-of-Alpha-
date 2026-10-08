import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from skytemple_files.data.str.handler import StrHandler
from skytemple_files.common.util import get_ppmdu_config_for_rom, get_files_from_rom_with_extension

rom=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
ovs=rom.loadArm9Overlays()
addr=0x0237C91C
for i,ov in ovs.items() if hasattr(ovs,"items") else enumerate(ovs):
    if ov is None: continue
    ram=getattr(ov,"ramAddress",None) or getattr(ov,"ramAddress",None)
    # ndspy Overlay
    try:
        ram=ov.ramAddress; size=ov.ramSize; data=ov.data
    except: continue
    if ram <= addr < ram+size:
        print(f"in ov{i} ram={ram:#x} size={size:#x}")
        off=addr-ram
        for action in list(range(0,55)):
            o=off+action*8
            a,b=struct.unpack_from("<HH", data, o)
            sid=(a+0x987)&0xffff
            mark=""
            if a in (2622-0x987, 2623-0x987) or sid in (2622,2623,19101):
                mark=" <<<"
            if action in (0x14,0x1a,0x26,0x28,0x29,0x2a,0x2b,20,38,40,41,42) or mark:
                print(f"  act {action:3} ({action:#04x}): f0={a:5} => ~str {sid}{mark}")

config=get_ppmdu_config_for_rom(rom)
for fn in get_files_from_rom_with_extension(rom,"str"):
    if fn.endswith("text_e.str"):
        strings=StrHandler.deserialize(rom.getFileByName(fn), string_encoding=config.string_encoding)
        print("↑Shift", strings.strings[2622])
        print("↓Shift", strings.strings[2623])
        # find which action field equals 2622-0x987
        need=2622-0x987
        print(f"field for ↑Shift = {need}")
