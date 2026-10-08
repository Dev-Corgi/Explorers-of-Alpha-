import struct
from pathlib import Path
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable

def scan(path):
    rom = NintendoDSRom(Path(path).read_bytes())
    ov29 = bytes(rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda i,n: b'')[29].fileID])
    ov31 = bytes(rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda i,n: b'')[31].fileID])
    arm9 = bytes(rom.arm9)
    B29,B31=0x022DC240,0x02382820
    sites = [
        ('ov31 84614', ov31, 0x02384614-B31),
        ('ov31 84C54', ov31, 0x02384C54-B31),
        ('ov31 84DFC', ov31, 0x02384DFC-B31),
        ('ov29 EB2DC', ov29, 0x022EB2DC-B29),
        ('ov29 FE72C', ov29, 0x022FE72C-B29),
        ('ov29 FEDB8', ov29, 0x022FEDB8-B29),
        ('arm9 D40C', arm9, 0x0200D40C-0x02000000),
    ]
    print('===', Path(path).name, '===')
    for label,blob,off in sites:
        w = struct.unpack_from('<I', blob, off)[0]
        print(' ', label, hex(w))

for p in [
    '4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges_orbcount_tmread.nds',
    'Explorers of Alpha.nds',
]:
    scan(p)
