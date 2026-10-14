"""Read-only bounded native disassembly for the persisted phase3 ABI audit."""
import sys
from ndspy.rom import NintendoDSRom
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from .verify_phase1 import SOURCE

def main():
    rom=NintendoDSRom(SOURCE.read_bytes()); overlays=rom.loadArm9Overlays()
    decoder=Cs(CS_ARCH_ARM,CS_MODE_ARM);decoder.skipdata=True
    if len(sys.argv)>1 and sys.argv[1]=='--loads':
        ids=set(int(v) for v in sys.argv[2:])
        for base,raw in ((0x022dc240,overlays[29].data),(0x023a7080,overlays[36].data)):
            for i in decoder.disasm(bytes(raw),base):
                if i.mnemonic.startswith('mov') and '#' in i.op_str:
                    try:relevant=int(i.op_str.split('#')[1],0) in ids
                    except ValueError:continue
                    if relevant and i.op_str.startswith(('r1,','r2,')):
                        for j in decoder.disasm(bytes(raw[i.address-base:i.address-base+24]),i.address):
                            print(f'{j.address:08x} {j.bytes.hex()} {j.mnemonic} {j.op_str}')
        return
    if len(sys.argv)>1 and sys.argv[1]=='--queries':
        ids=set(int(v) for v in sys.argv[2:]);targets={0x02301d10,0x02301d78,0x0230a940,0x02311b94,0x02332a0c}
        for base,raw in ((0x022dc240,overlays[29].data),(0x023a7080,overlays[36].data)):
            window=[]
            for i in decoder.disasm(bytes(raw),base):
                window.append(i);window=window[-8:]
                if i.mnemonic=='bl' and i.op_str.startswith('#') and int(i.op_str[1:],16) in targets:
                    relevant=any(j.mnemonic=='mov' and j.op_str.startswith(('r1, #','r2, #')) and int(j.op_str.split('#')[1],0) in ids for j in window[:-1])
                    if relevant:
                        for j in window:print(f'{j.address:08x} {j.bytes.hex()} {j.mnemonic} {j.op_str}')
        return
    for spec in sys.argv[1:]:
        lo,hi=[int(x,16) for x in spec.split(':')]
        if lo<0x02000000: raw=rom.arm9[0xb3380:0xbb380];base=0x01ff8000
        elif lo<0x022dc240: raw=rom.arm9;base=0x02000000
        elif lo<0x023a7080: raw=overlays[29].data;base=0x022dc240
        else: raw=overlays[36].data;base=0x023a7080
        for i in decoder.disasm(bytes(raw[lo-base:hi-base]),lo):
            print(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}')
if __name__=='__main__':main()
