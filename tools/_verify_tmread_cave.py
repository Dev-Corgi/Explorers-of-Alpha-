#!/usr/bin/env python3
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from pathlib import Path

ROM = Path(
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_orbcharges_orbcount_tmread_zmove_step11_names.nds"
)
BASE29 = 0x022DC240
BASE31 = 0x02382820

rom = NintendoDSRom(ROM.read_bytes())
table = loadOverlayTable(rom.arm9OverlayTable, lambda *_: b"")
ov29 = rom.files[table[29].fileID]
ov31 = rom.files[table[31].fileID]
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def disasm_ov29(addr: int, n: int = 64) -> None:
    off = addr - BASE29
    for ins in cs.disasm(ov29[off : off + n], addr):
        print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


menu_off = 0x02384C54 - BASE31
menu_w = int.from_bytes(ov31[menu_off : menu_off + 4], "little")
if (menu_w >> 24) == 0xEA:
    imm24 = menu_w & 0xFFFFFF
    if imm24 & 0x800000:
        imm24 -= 0x1000000
    menu_target = 0x02384C54 + 8 + imm24 * 4
else:
    menu_target = None

confirm_off = 0x02384DFC - BASE31
confirm_w = int.from_bytes(ov31[confirm_off : confirm_off + 4], "little")
imm = confirm_w & 0xFFFFFF
if imm & 0x800000:
    imm -= 0x1000000
confirm_target = 0x02384DFC + 8 + imm * 4

print(f"ov31 menu b -> 0x{menu_target:08X}" if menu_target else "menu hook bad")
print(f"ov31 confirm bl -> 0x{confirm_target:08X}")

print("\n=== cave 30870-30930 ===")
disasm_ov29(0x02330870, 0xC0)

print("\n=== charge table @ 30900 (first 8 words) ===")
off = 0x02330900 - BASE29
for i in range(8):
    w = int.from_bytes(ov29[off + i * 4 : off + i * 4 + 4], "little")
    print(f"  [{i}] 0x{w:08X}")

print("\n=== cmp r1,#41 (confirm hook) locations ===")
for addr in range(0x02330478, 0x02330B20, 4):
    off = addr - BASE29
    w = int.from_bytes(ov29[off : off + 4], "little")
    if w == 0xE3510029:
        print(f"  0x{addr:08X}")

print("\n=== LoadEntityStatus (ldr r0,[r5]; cmp r0,#0) ===")
for addr in range(0x02330800, 0x023308B0, 4):
    off = addr - BASE29
    w = int.from_bytes(ov29[off : off + 4], "little")
    w2 = int.from_bytes(ov29[off + 4 : off + 8], "little")
    if w == 0xE5950000 and w2 == 0xE3500000:
        print(f"  0x{addr:08X}")

# Cave budget
cave_start = 0x02330478
helper = 0x02330894
budget = helper - cave_start
print(f"\nCave budget to helper: {budget} bytes (0x{budget:X})")

# Find last non-zero before helper from linear stream
last = cave_start
for addr in range(cave_start, helper, 4):
    off = addr - BASE29
    w = int.from_bytes(ov29[off : off + 4], "little")
    if w != 0:
        last = addr + 4
print(f"Last used byte before helper org: ~0x{last:08X} ({last - cave_start} bytes used)")
