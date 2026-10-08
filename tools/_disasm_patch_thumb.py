from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs
from pathlib import Path
import re, struct

ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py").read_text(encoding='utf-8',errors='ignore')
LOAD=0x02000000

rev={}
for m in re.finditer(r'(\w+)\s*=\s*Symbol\((.*?)\)\n\n', PMDSKY, re.S):
    nums=[int(x,16) for x in re.findall(r'0x([0-9A-Fa-f]+)', m.group(2))]
    if nums: rev[nums[0]]=m.group(1)

def blt(pc,w):
    imm=w&0xFFFFFF
    if imm&0x800000: imm-=0x01000000
    return pc+8+(imm<<2)

for start,name in [(0x3B81CC,'3B81CC'),(0x3B81DC,'IsLevelReset hook'),(0x3B81F0,'57868 hook'),(0x3B8200,'3B8200')]:
    print(f'\n=== {name} @ 0x{start:X} ARM ===')
    md=Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in md.disasm(ARM9[start:start+0x100], LOAD+start):
        note=''
        if ins.mnemonic=='bl':
            w=struct.unpack_from('<I',ARM9,ins.address-LOAD)[0]
            t=blt(ins.address,w)-LOAD
            if t in rev: note=f' ; {rev[t]}'
        print(f'0x{ins.address-LOAD:X}: {ins.mnemonic} {ins.op_str}{note}')
    print(f'=== {name} THUMB ===')
    s=start&~1
    md=Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for ins in md.disasm(ARM9[s:s+0x100], LOAD+s):
        print(f'0x{ins.address-LOAD:X}: {ins.mnemonic} {ins.op_str}')
