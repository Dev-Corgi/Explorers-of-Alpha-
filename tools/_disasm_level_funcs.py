import re
from pathlib import Path
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
LOAD = 0x02000000

t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
rev = {}
for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
    nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
    if nums:
        rev[nums[0]] = m.group(1)

import struct

def bl_target(pc,w):
    imm=w&0xFFFFFF
    if imm&0x800000: imm-=0x01000000
    return pc+8+(imm<<2)

def dump(off, size=0x200):
    name = rev.get(off, "?")
    print(f"\n=== 0x{off:X} ({name}) ===")
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in md.disasm(ARM9[off:off+size], LOAD+off):
        note=""
        if ins.mnemonic=="bl":
            w=struct.unpack_from('<I', ARM9, ins.address-LOAD)[0]
            tgt=bl_target(ins.address,w)-LOAD
            if tgt in rev: note=f" ; {rev[tgt]}"
        print(f"0x{ins.address-LOAD:06X}: {ins.mnemonic:7} {ins.op_str}{note}")

for off in [0x51318, 0x530D4, 0x5349C, 0x58138, 0x57AEC]:
    dump(off, 0x280 if off==0x57AEC else 0x200)

# callers of 0x530d4 and 0x5349c and 0x58138
for target in [0x530D4, 0x5349C, 0x58138]:
    callers=[]
    for i in range(0,len(ARM9)-3,4):
        w=struct.unpack_from('<I',ARM9,i)[0]
        if w>>24!=0xEB: continue
        if bl_target(LOAD+i,w)==LOAD+target:
            callers.append(i)
    print(f"\ncallers of 0x{target:X} ({rev.get(target,'?')}): {len(callers)}")
    print([hex(c) for c in callers[:15]])
