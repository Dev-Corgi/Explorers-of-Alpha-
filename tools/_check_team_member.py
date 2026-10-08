import re
from pathlib import Path
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
LOAD = 0x02000000

t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
m = re.search(r"CheckTeamMemberIdx\s*=\s*Symbol\((.*?)\)\n\n", t, re.S)
nums = [int(x,16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(1))]
off, ram = nums[0], nums[1]
print("CheckTeamMemberIdx", hex(off), hex(ram))
print(re.search(r'"([^"]*)"\s*,\s*"([^"]*)"', m.group(1)).group(2))

print("\n=== Disasm ===")
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
for ins in md.disasm(ARM9[off:off+0x100], LOAD+off):
    print(f"0x{ins.address-LOAD:X}: {ins.mnemonic} {ins.op_str}")

# ARM bl callers
import struct

def bl_tgt(pc,w):
    imm=w&0xFFFFFF
    if imm&0x800000: imm-=0x01000000
    return pc+8+(imm<<2)

callers=[]
for i in range(0,len(ARM9)-3,4):
    w=struct.unpack_from('<I',ARM9,i)[0]
    if w>>24!=0xEB: continue
    if bl_tgt(LOAD+i,w)==ram:
        callers.append(i)
print('\ncallers', len(callers))
for c in callers[:15]:
    print(f'  0x{c:X}')
