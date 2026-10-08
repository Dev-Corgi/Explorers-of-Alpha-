import struct
from pathlib import Path
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

def bl_target(w, pc):
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)

OV29 = 0x022DC240
ARM9 = 0x02000000
rom = NintendoDSRom(Path("Explorers of Alpha_Rom_seeds.nds").read_bytes())
table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
ov = rom.files[table[29].fileID]
arm9 = rom.arm9

for s, e in [(0x02330B20, 0x02332000), (0x023302B0, 0x02330478)]:
    chunk = ov[s - OV29 : e - OV29]
    nz = sum(1 for b in chunk if b)
    print(f"ov29 {s:08X}-{e:08X}: {nz}/{len(chunk)} nonzero")

w = struct.unpack_from("<I", arm9, 0xC6F0)[0]
print(f"C6F0 bl -> {bl_target(w, 0x0200C6F0):08X}")
print(f"C4FC entry: {struct.unpack_from('<I', arm9, 0xC4FC)[0]:08X}")

w2 = struct.unpack_from("<I", ov, 0x022E7EC4 - OV29)[0]
print(f"AllocTop -> {bl_target(w2, 0x022E7EC4):08X}")

lit = struct.unpack_from("<I", ov, 0x023311DC - OV29)[0]
print(f"gauge lit: {lit:08X}")
