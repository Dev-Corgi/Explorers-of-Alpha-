import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

rom = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
arm9 = bytes(rom.arm9)
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

def bt(site, w):
    imm = w & 0xFFFFFF
    if imm & 0x800000: imm -= 0x1000000
    return site + 8 + imm*4

# Second jump table at 0x20041DC for gid 0..
base2 = 0x20041DC
print("=== second LoadOverlay switch targets (actual overlay load) ===")
for gid in range(0x1E, 0x25):
    site = base2 + gid*4
    w = struct.unpack_from("<I", arm9, site-0x02000000)[0]
    dest = bt(site, w)
    print(f"gid {gid:#x} -> {dest:#x}")
    # disasm dest briefly
    for ins in list(cs.disasm(arm9[dest-0x02000000:dest-0x02000000+0x40], dest))[:12]:
        print(f"    {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# Also check ExtraSpace NitroMain path - search arm9 for overlay 36 file load
print("\n=== search arm9 for references to ov36 load addr 0x23A7080 ===")
target = 0x023A7080
hits = []
for off in range(0, len(arm9)-4, 4):
    if struct.unpack_from("<I", arm9, off)[0] == target:
        hits.append(0x02000000+off)
print("literal hits", [hex(h) for h in hits[:20]], "count", len(hits))

# Search for mov r0,#0x24 near ExtraSpace
print("\n=== mov r0,#0x24 sites in arm9 with context ===")
for off in range(0, len(arm9)-4, 4):
    if struct.unpack_from("<I", arm9, off)[0] != 0xE3A00024:
        continue
    addr = 0x02000000+off
    print(f"\n--- {addr:#x} ---")
    start = max(0, off-0x20)
    for ins in cs.disasm(arm9[start:off+0x30], 0x02000000+start):
        mark = ">>>" if ins.address==addr else "   "
        print(f"{mark} {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
