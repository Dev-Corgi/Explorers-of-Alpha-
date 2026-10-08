"""Trace CreateTeamSelectionMenu callers and town X->Team flow."""
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable

ROM = "Explorers of Alpha_berryboost.nds"
CREATE_TEAM_SEL = 0x2030F44
DRAW_TEAM_STATS = 0x22C09E8
INIT_TEAM_STATS = 0x22E8130
HANDLE_TEAM_STATS_GROUND = 0x2313ADC

rom = NintendoDSRom.fromFile(ROM)
arm9 = bytes(rom.arm9)
table = loadOverlayTable(rom.arm9OverlayTable, lambda _id, _name: b"")
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def find_bl_to(data, base, target, label):
    hits = []
    for ins in cs.disasm(data, base):
        if ins.mnemonic != "bl":
            continue
        op = ins.op_str.lstrip("#")
        try:
            t = int(op, 16)
        except ValueError:
            continue
        if t == target:
            hits.append(ins.address)
    if hits:
        print(f"\n=== BL {label} ({target:#x}) ===")
        for a in hits:
            region = "arm9" if base == 0x2000000 else f"ov@{base:#x}"
            print(f"  {region} {a:#010x}")


find_bl_to(arm9, 0x2000000, CREATE_TEAM_SEL, "CreateTeamSelectionMenu")
find_bl_to(arm9, 0x2000000, DRAW_TEAM_STATS, "DrawTeamStats")
find_bl_to(arm9, 0x2000000, INIT_TEAM_STATS, "InitializeTeamStats")
find_bl_to(arm9, 0x2000000, HANDLE_TEAM_STATS_GROUND, "HandleTeamStatsGround")

for ov_id, ov in table.items():
    if ov.fileID >= len(rom.files):
        continue
    data = bytes(rom.files[ov.fileID])
    if not data:
        continue
    base = ov.ramAddress
    for target, label in [
        (CREATE_TEAM_SEL, "CreateTeamSelectionMenu"),
        (DRAW_TEAM_STATS, "DrawTeamStats"),
        (INIT_TEAM_STATS, "InitializeTeamStats"),
        (HANDLE_TEAM_STATS_GROUND, "HandleTeamStatsGround"),
    ]:
        hits = []
        for ins in cs.disasm(data, base):
            if ins.mnemonic != "bl":
                continue
            op = ins.op_str.lstrip("#")
            try:
                t = int(op, 16)
            except ValueError:
                continue
            if t == target:
                hits.append(ins.address)
        if hits:
            print(f"\n=== BL {label} from overlay{ov_id:02d} ===")
            for a in hits:
                print(f"  {a:#010x}")


def disasm_region(data, base, start, size, depth=0):
    s = start - base
    print(f"\n--- disasm {start:#x} ---")
    for ins in cs.disasm(data[s : s + size], start):
        mark = ""
        if ins.mnemonic == "bl":
            if "2030f44" in ins.op_str.lower():
                mark = "  << CreateTeamSelectionMenu"
            elif "22c09e8" in ins.op_str.lower():
                mark = "  << DrawTeamStats"
            elif "22e8130" in ins.op_str.lower():
                mark = "  << InitializeTeamStats"
        print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")


ov11 = bytes(rom.files[table[11].fileID])
base11 = table[11].ramAddress

for addr in [0x23048AC, 0x2301174, 0x2304AE0, 0x2304BC4, 0x22E8130, 0x2313ADC]:
    if addr >= base11 and addr < base11 + len(ov11):
        disasm_region(ov11, base11, addr, 0xA0)

# CreateTopGroundMenu menu table literals
import struct
for pc in [0x2300DB8, 0x2300DC4, 0x2300DC8]:
    off = pc - base11 + 8
    val = struct.unpack_from("<I", ov11, off)[0]
    print(f"literal @{pc:#x} -> {val:#x}")

# dump menu struct if literal points into ov11
for name, pc in [("menuA", 0x2300DB8), ("menuB", 0x2300DC4)]:
    off = pc - base11 + 8
    ptr = struct.unpack_from("<I", ov11, off)[0]
    if base11 <= ptr < base11 + len(ov11):
        po = ptr - base11
        print(f"\n{name} table @{ptr:#x}:")
        for i in range(8):
            w = struct.unpack_from("<HH", ov11, po + i * 8)[0]
            act = struct.unpack_from("<H", ov11, po + i * 8 + 4)[0]
            if w == 0:
                break
            print(f"  str {w:#06x}  action/type {act}")
