"""Trace dungeon bag item name display path."""
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
import pmdsky_debug_py.na as na

ROM = Path(
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges.nds"
)
rom = NintendoDSRom(ROM.read_bytes())
ovt = loadOverlayTable(rom.arm9OverlayTable, lambda i, n: b"")
ov29 = rom.files[ovt[29].fileID]
ov11 = rom.files[ovt[11].fileID]
ov10 = rom.files[ovt[10].fileID]
L29, L11, L10 = na.overlay29.loadaddress, na.overlay11.loadaddress, na.overlay10.loadaddress
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def bl_targets(data, base, start, size):
    out = []
    for ins in cs.disasm(data[start - base : start - base + size], start):
        if ins.mnemonic != "bl":
            continue
        tgt = int(ins.op_str.split("#")[-1], 16)
        out.append((ins.address, tgt))
    return out


print("=== OpenMenu (234DDF4) bl targets (first 0x800) ===")
for addr, tgt in bl_targets(ov29, L29, 0x234DDF4, 0x800):
    note = ""
    if tgt == 0x22BD474:
        note = " OpenInvWrapper"
    elif tgt == 0x22BCA80:
        note = " CreateInventoryMenu"
    elif tgt == 0x22BDE50:
        note = " OpenInvById"
    print(f"  {addr:08X} -> {tgt:08X}{note}")

print("\n=== 23016A8 (pre-bag gate) ===")
for ins in cs.disasm(ov29[0x23016A8 - L29 : 0x23016A8 - L29 + 0x80], 0x23016A8):
    print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

NAME_FUNCS = {
    0x0200E864: "GetItemName",
    0x0200D310: "BuildItemName",
    0x0200E884: "GetItemNameFormatted",
}
print("\n=== ov11 bl to ARM9 name functions ===")
for off in range(0, len(ov11) - 4, 4):
    pc = L11 + off
    w = int.from_bytes(ov11[off : off + 4], "little")
    if (w >> 24) & 0xFF != 0xEB:
        continue
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    tgt = pc + 8 + imm * 4
    if tgt in NAME_FUNCS:
        print(f"  {pc:08X} -> {NAME_FUNCS[tgt]}")

# Resolve callback at r4+6 in ov11 BD474 caller: r4 from global after 200EDFC
print("\n=== 200EDFC symbol ===")
print(" ", na.arm9.functions.__dict__.get("GetSomething", ""))
for name, sym in vars(na.arm9.functions).items():
    if hasattr(sym, "addresses") and 0x200EDFC in sym.addresses:
        print(f"  {name}: {sym.description[:120]}")

# Find ov11 functions that look like name callback: bl GetItemName, r0=buf r1=idx
print("\n=== ov11 functions calling GetItemName (scan bl + context) ===")
get_item = 0x0200E864
hits = []
for off in range(0, len(ov11) - 4, 4):
    pc = L11 + off
    w = int.from_bytes(ov11[off : off + 4], "little")
    if (w >> 24) & 0xFF != 0xEB:
        continue
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    if pc + 8 + imm * 4 != get_item:
        continue
    # find function start (scan back for push {.., lr})
    fn_start = pc
    for back in range(off, max(0, off - 0x200), -4):
        w2 = int.from_bytes(ov11[back : back + 4], "little")
        if w2 & 0xFFFF0000 == 0xE92D0000 and (w2 & 0x4000):
            fn_start = L11 + back
            break
    hits.append(fn_start)

for fn in sorted(set(hits)):
    print(f"\n--- candidate callback @ {fn:08X} ---")
    for ins in cs.disasm(ov10 if fn >> 24 == 0x22 and fn < 0x22C0000 else ov11,
                         L10 if fn >> 24 == 0x22 and fn < 0x22C0000 else L11,
                         fn, 0x60):
        pass
    base = L11
    data = ov11
    if fn >= L10 and fn < L10 + len(ov10):
        base = L10
        data = ov10
    for ins in cs.disasm(data[fn - base : fn - base + 0x80], fn):
        print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

# Check what offset +6 in dungeon struct contains - find vtable/init
print("\n=== ov11 parent fn of BD474 call (305300 area) ===")
for ins in cs.disasm(ov11[0x2305300 - L11 : 0x2305300 - L11 + 0x40], 0x2305300):
    print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")
