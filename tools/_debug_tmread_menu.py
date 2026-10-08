#!/usr/bin/env python3
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from pathlib import Path

ROM = Path(
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges_orbcount_tmread.nds"
)
OV31 = 0x02382820
ADD = 0x022EB81C

rom = NintendoDSRom(ROM.read_bytes())
ov31 = bytes(rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[31].fileID])
ov29 = bytes(rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[29].fileID])
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

print("Hook @ 84C54:", hex(struct.unpack_from("<I", ov31, 0x02384C54 - OV31)[0]))
print("Cave:", ov29[0x02330478 - 0x022DC240 : 0x02330478 - 0x022DC240 + 8].hex())

print("\n=== AddDungeonSubMenuOption calls 84400-84D00 ===")
for off in range(0x02384400 - OV31, 0x02384D00 - OV31, 4):
    pc = OV31 + off
    w = struct.unpack_from("<I", ov31, off)[0]
    if (w >> 24) != 0xEB:
        continue
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 1 << 24
    if pc + 8 + imm * 4 != ADD:
        continue
    tags = []
    for ins in cs.disasm(ov31[off - 0x80 : off + 4], pc - 0x80):
        if ins.address >= pc:
            break
        if "ebb98" in ins.op_str:
            tags.append("GetMenuContext")
        if ins.mnemonic == "cmp" and "#0x75b" in ins.op_str.lower():
            tags.append("dungeon75b")
        if ins.mnemonic == "cmp" and ins.op_str.startswith("r0, #"):
            tags.append(f"cmp{ins.op_str.split('#')[1]}")
        if "200caf0" in ins.op_str:
            tags.append("GetItemCategory")
    aid = None
    for ins in reversed(list(cs.disasm(ov31[off - 0x30 : off], pc - 0x30))):
        if ins.mnemonic == "mov" and ins.op_str.startswith("r0, #"):
            aid = int(ins.op_str.split("#")[1], 0)
            break
    print(f"  {pc:08X} action {aid:3d}  {tags}")

# Map action IDs to names
ACTION_NAMES = {
    8: "Throw", 9: "Use", 11: "Info", 12: "Give", 15: "Place",
    16: "GetItemAction", 39: "?", 54: "?", 60: "?", 61: "?",
}
print("\n=== Expected user menu mapping ===")
for a, n in sorted(ACTION_NAMES.items()):
    print(f"  {a}: {n}")

# Check if 84C50 block is in same function as Use block - find Place (15)
print("\n=== Place(15) add sites ===")
for off in range(len(ov31) - 4):
    pc = OV31 + off
    w = struct.unpack_from("<I", ov31, off)[0]
    if (w >> 24) != 0xEB:
        continue
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 1 << 24
    if pc + 8 + imm * 4 != ADD:
        continue
    for ins in reversed(list(cs.disasm(ov31[off - 0x20 : off], pc - 0x20))):
        if ins.mnemonic == "mov" and ins.op_str == "r0, #0xf":
            print(f"  Place @ {pc:08X}")

# SortSubMenu - does it reorder? User sees Use Give Place Throw Info Exit
# Read would be added before Sort - so order after sort matters
