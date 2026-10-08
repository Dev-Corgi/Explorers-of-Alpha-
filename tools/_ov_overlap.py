import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

rom = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
table = loadOverlayTable(rom.arm9OverlayTable, lambda i, n: b"")
print(f"{'id':>4} {'ram':>12} {'size':>10} {'end':>12} {'fileID':>6}")
for i in range(len(table)):
    e = table[i]
    if e is None: continue
    ram = e.ramAddress
    size = e.ramSize
    # highlight overlaps with ov29/ov31/ov36
    flags = []
    if ram == 0x022DC240: flags.append("OV29_ADDR")
    if ram == 0x02382820: flags.append("OV31_ADDR")
    if ram == 0x023A7080: flags.append("OV36_ADDR")
    if 0x022DC240 <= ram < 0x022DC240 + 0x80000 and i not in (29,):
        if ram < 0x02382820:
            flags.append("in_ov29_region")
    mark = " ".join(flags)
    if i in range(28, 40) or mark:
        print(f"{i:4d} {ram:#012x} {size:#010x} {ram+size:#012x} {e.fileID:6d} {mark}")

print("\n=== GROUP slot sharing: gid 0x22 loads file 31, gid 0x24 loads file 33 ===")
for i in (31, 33, 34, 35, 36):
    e = table[i]
    print(f"ov{i}: ram={e.ramAddress:#x} size={e.ramSize:#x} end={e.ramAddress+e.ramSize:#x}")

# Check if ov33 overlaps ov29 or ov36
e29, e33, e36, e31 = table[29], table[33], table[36], table[31]
print(f"\nov29 [{e29.ramAddress:#x}..{e29.ramAddress+e29.ramSize:#x})")
print(f"ov31 [{e31.ramAddress:#x}..{e31.ramAddress+e31.ramSize:#x})")
print(f"ov33 [{e33.ramAddress:#x}..{e33.ramAddress+e33.ramSize:#x})")
print(f"ov36 [{e36.ramAddress:#x}..{e36.ramAddress+e36.ramSize:#x})")

def overlap(a,b):
    as_,ae = a.ramAddress, a.ramAddress+a.ramSize
    bs_,be = b.ramAddress, b.ramAddress+b.ramSize
    return max(as_,bs_) < min(ae,be)
print("ov33 overlaps ov29?", overlap(e33,e29))
print("ov33 overlaps ov31?", overlap(e33,e31))
print("ov33 overlaps ov36?", overlap(e33,e36))
print("ov31 overlaps ov36?", overlap(e31,e36))
print("ov34 overlaps ov29?", overlap(table[34], e29))
