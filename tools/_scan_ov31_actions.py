#!/usr/bin/env python3
from pathlib import Path
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

OV31 = 0x02382820
ADD = 0x022EB81C
ROM = Path(
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges.nds"
)
NAMES = {
    8: "THROW(8)", 9: "USE(9)", 10: "EQUIP(10)", 11: "INFO(11)", 12: "GIVE(12)",
    16: "PICKUP(16 via GetItemAction)", 0x27: "39", 0x36: "54", 0x37: "55",
    0x38: "56", 0x3A: "58", 0x3C: "60", 0x3D: "61", 0x3E: "62", 0x41: "65",
}

def blt(pc, w):
    if (w >> 24) != 0xEB:
        return None
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 1 << 24
    return pc + 8 + imm * 4

rom = NintendoDSRom(ROM.read_bytes())
ov31 = bytes(rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda i, n: b"")[31].fileID])
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

print("=== TM bag submenu block 844FC-84C60 ===")
for off in range(0x023844FC - OV31, 0x02384C60 - OV31 - 4, 4):
    pc = OV31 + off
    if blt(pc, struct.unpack_from("<I", ov31, off)[0]) != ADD:
        continue
    ctx = list(cs.disasm(ov31[off - 0x40 : off + 4], pc - 0x40))
    aid = None
    tags = []
    for ins in ctx:
        if ins.address >= pc:
            break
        if "22ebb98" in ins.op_str:
            tags.append("ctx")
        if "200caf0" in ins.op_str:
            tags.append("cat")
        if "22eb5d8" in ins.op_str:
            tags.append("GetItemAction")
        if ins.mnemonic == "cmp" and "#0x80" in ins.op_str:
            tags.append("ctx==0x80")
        if ins.mnemonic == "cmp" and "#0x33" in ins.op_str:
            tags.append("ctx<0x33")
    for ins in reversed(ctx):
        if ins.address >= pc:
            continue
        if ins.mnemonic == "mov" and ins.op_str.startswith("r0, #"):
            aid = int(ins.op_str.split("#")[1], 0)
            break
    label = NAMES.get(aid, str(aid))
    print(f"  {pc:08X}: action {aid:3d} ({label})  tags={tags}")

ids = set()
for off in range(0, len(ov31) - 4, 4):
    pc = OV31 + off
    if blt(pc, struct.unpack_from("<I", ov31, off)[0]) != ADD:
        continue
    for ins in reversed(list(cs.disasm(ov31[max(0, off - 0x24) : off], pc - 0x24))):
        if ins.mnemonic == "mov" and ins.op_str.startswith("r0, #"):
            ids.add(int(ins.op_str.split("#")[1], 0))
            break
print("\nAll hardcoded action IDs in ov31:", sorted(ids))
