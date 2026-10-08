import re, struct
from pathlib import Path
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py").read_text(encoding='utf-8',errors='ignore')
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
rev={}
for m in re.finditer(r'(\w+)\s*=\s*Symbol\((.*?)\)\n\n', PMDSKY, re.S):
    nums=[int(x,16) for x in re.findall(r'0x([0-9A-Fa-f]+)', m.group(2))]
    if nums: rev[nums[0]]=m.group(1)

def blt(pc,w):
    imm=w&0xFFFFFF
    if imm&0x800000: imm-=0x01000000
    return pc+8+(imm<<2)

for start in [0x56C20, 0x57AEC, 0x581F0]:
    print(f'\n=== 0x{start:X} ({rev.get(start,"?")}) ===')
    md=Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in md.disasm(ARM9[start:start+0x300], 0x02000000+start):
        note=''
        if ins.mnemonic=='bl':
            w=struct.unpack_from('<I',ARM9,ins.address-0x02000000)[0]
            t=blt(ins.address,w)-0x02000000
            if t in rev: note=' ; '+rev[t]
        print(f'0x{ins.address-0x02000000:X}: {ins.mnemonic} {ins.op_str}{note}')

# callers of GetPartyMembers
gp=0x56C20
print('\n=== callers GetPartyMembers ===')
for i in range(0,len(ARM9)-3,4):
    w=struct.unpack_from('<I',ARM9,i)[0]
    if w>>24!=0xEB: continue
    if blt(0x02000000+i,w)==0x02000000+gp:
        print(hex(i))
