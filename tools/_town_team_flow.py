"""Town X -> Main menu -> Team flow vs CreateTeamSelectionMenu."""
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
import struct

rom = NintendoDSRom.fromFile("Explorers of Alpha_berryboost.nds")
arm9 = bytes(rom.arm9)
table = loadOverlayTable(rom.arm9OverlayTable, lambda _id, _name: b"")
ov11 = bytes(rom.files[11])
base11 = table[11].ramAddress
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def pool_u32(data, base, insn_addr):
    off = insn_addr - base + 8
    return struct.unpack_from("<I", data, off)[0]


def disasm(data, base, start, size):
    s = start - base
    for ins in cs.disasm(data[s : s + size], start):
        yield ins


print("=== CreateTopGroundMenu menu tables ===")
for pc in [0x2300DB8, 0x2300DC8]:
    ptr = pool_u32(ov11, base11, pc)
    print(f"\ntable ptr {ptr:#x} (from insn {pc:#x})")
    if base11 <= ptr < base11 + len(ov11):
        po = ptr - base11
        for i in range(8):
            sid = struct.unpack_from("<H", ov11, po + i * 8)[0]
            kind = struct.unpack_from("<H", ov11, po + i * 8 + 4)[0]
            if sid == 0:
                break
            print(f"  [{i}] string {sid:#06x}  enable_kind {kind}")

print("\n=== UpdateTopGroundMenu action dispatch (state 5) ===")
print("  action 3 -> 0x2304AE0 (veneer)")
print("  action 4 -> 0x2304BC4 (veneer)")
print("  action 5 -> 0x23048AC")
print("  action 6 -> 0x2301174")

for addr in [0x2304AE0, 0x2304BC4]:
    off = addr - base11
    target = struct.unpack_from("<I", ov11, off + 8)[0]
    print(f"\nveneer {addr:#x} -> {target:#x}")

print("\n=== 0x2301174 (action 6 handler) ===")
for ins in disasm(ov11, base11, 0x2301174, 0x50):
    print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

print("\n=== DrawTeamStats caller @ 0x22DC3D4 ===")
for ins in disasm(ov11, base11, 0x22DC3A0, 0x50):
    mark = ""
    if ins.mnemonic == "bl" and "22c09e8" in ins.op_str.lower():
        mark = "  << DrawTeamStats (team stats top screen)"
    print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")

print("\n=== CreateTeamSelectionMenu callers (arm9) ===")
for pc in [0x203A3CC, 0x203A40C, 0x203A474]:
    print(f"\n  call @ {pc:#x}, context:")
    for ins in disasm(arm9, 0x2000000, pc - 0x40, 0x60):
        mark = " <<<" if ins.address == pc else ""
        print(f"    {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")

# find BL to function containing 0x203A3CC
ENTRY = 0x203A180
print(f"\n=== BL callers of team-menu opener ~{ENTRY:#x} ===")

def bl_hits(data, base, target):
    for i in range(0, len(data) - 4, 4):
        w = struct.unpack_from("<I", data, i)[0]
        if (w & 0xFF000000) != 0xEB000000:
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        pc = base + i
        if pc + 8 + imm * 4 == target:
            yield pc


for pc in bl_hits(arm9, 0x2000000, ENTRY):
    print(f"  arm9 {pc:#x}")
for oid, ov in table.items():
    data = bytes(rom.files[ov.fileID])
    for pc in bl_hits(data, ov.ramAddress, ENTRY):
        print(f"  overlay{oid} {pc:#x}")

# r3 callback passed to CreateTeamSelectionMenu - literal at 0x203A3B8 pool
pool = 0x203A3C0
off = pool - 0x2000000
cb = struct.unpack_from("<I", arm9, off)[0]
print(f"\nCreateTeamSelectionMenu text callback (pool @ {pool:#x}) = {cb:#x}")
if cb == 0x0203A75C:
    print("  -> TeamSelectionMenuGetItem (member name list)")
