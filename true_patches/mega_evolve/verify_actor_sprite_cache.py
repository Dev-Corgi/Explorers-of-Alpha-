"""Exercise native actor refresh for mixed parties, not only cache getters."""
import struct
from pathlib import Path
from ndspy.rom import NintendoDSRom
from .verify_native_integration import NativeWorld
from .verify_phase1 import REPO
from unicorn.arm_const import *


class CacheWorld(NativeWorld):
    def service(self,u,address,size,data):
        if address==0x02008C3C:
            descriptor=u.reg_read(UC_ARM_REG_R0);pointer=u.reg_read(UC_ARM_REG_R1)
            path=bytes(u.mem_read(pointer,80)).split(b'\0')[0].decode()
            blob=bytes(self.rom.getFileByName(path.removeprefix('rom0:/').lstrip('/')))
            target=0x02140000 if path.endswith('runtime.bin') else 0x021A0000
            self.opened.append(path);u.mem_write(target,blob)
            u.mem_write(descriptor,struct.pack('<II',target,len(blob)))
            u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR));return
        return super().service(u,address,size,data)


def main():
    rom=NintendoDSRom((REPO/'PatchTesting/Export Rom/Explorers of Alpha+.nds').read_bytes())
    w=CacheWorld(rom);w.rom=rom;w.opened=[]
    for index in (29,36):
        o=rom.loadArm9Overlays()[index];w.u.mem_write(o.ramAddress,bytes(o.data))
    w.call(0x02052358,0)
    dungeon=0x02200000;entity=0x02250000;monster=0x02260000
    w.u.mem_write(0x02353538,struct.pack('<I',dungeon))
    for species,index in ((490,19),(1625,17),(2065,23),(1627,17)):
        w.call(0x022F740C,species,index)
        # Poison the legacy array position a new ID would incorrectly read.
        if species>=1155:w.u.mem_write(dungeon+0x19914+species*2,b'\x71\x71')
        w.u.mem_write(monster,bytes(0x240));w.u.mem_write(monster+2,struct.pack('<HH',species,species))
        w.u.mem_write(monster+0xD8,b'\x04') # A legitimate status must be preserved.
        w.u.mem_write(entity+0xB4,struct.pack('<I',monster))
        for reg,value in ((UC_ARM_REG_R4,0x02353538),(UC_ARM_REG_R8,entity),
                          (UC_ARM_REG_R9,monster),(UC_ARM_REG_R10,0x19914),
                          (UC_ARM_REG_SP,0x023FE000)):
            w.u.reg_write(reg,value)
        w.u.emu_start(0x022FBB5C,0x022FBB74,count=2000000)
        actual=struct.unpack('<h',w.u.mem_read(entity+0xA8,2))[0]
        assert actual==index,(species,actual,index)
        assert w.u.reg_read(UC_ARM_REG_R0)==entity+0x2C
        assert bytes(w.u.mem_read(monster+0xD8,1))==b'\x04'
        w.call(0x022FDDC0,monster,1)
        assert bytes(w.u.mem_read(monster+0xD8,1))==b'\0'
    print('PASS native actor refresh: mixed cache slots, poisoned old array, drawing argument and legitimate status preserved; native initialization does not add Gastro Acid')
    print('Native bootstrap/file checksum/relocations and actor cache read execute; file I/O is modeled.')


if __name__=='__main__':main()
