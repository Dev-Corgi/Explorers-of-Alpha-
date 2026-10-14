"""Exercise the actual MD loader and updater with a read-only legacy save."""
import hashlib,struct,sys
from pathlib import Path
from ndspy.rom import NintendoDSRom
from skytemple_files.data.data_cd.handler import DataCDHandler
from .verify_save12 import World,BUFFER,ROSTER,STOP
from .verify_phase1 import REPO
from .phase4 import load
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_PC,UC_ARM_REG_LR


class NativeWorld(World):
    def process(self,code):
        self.u.mem_write(0x022E7A48,code)
        # Alpha's process loader flushes instruction caches before executing
        # another effect at this same address; mirror that in Unicorn's JIT.
        self.u.ctl_remove_cache(0x022E7A48,0x022E7A48+max(64,len(code)))
        return self.call(0x022E7A48,0)

    def service(self,u,address,size,data):
        if address==0x02008C3C:
            descriptor=u.reg_read(UC_ARM_REG_R0);pointer=u.reg_read(UC_ARM_REG_R1)
            path=bytes(u.mem_read(pointer,80)).split(b'\0')[0].decode()
            blob=bytes(self.rom.getFileByName(path.removeprefix('rom0:/')))
            self.opened.append(path)
            u.mem_write(0x021A0000,blob)
            u.mem_write(descriptor,struct.pack('<II',0x021A0000,len(blob)))
        elif address not in (0x02052BD4,0x022E82C0):
            return super().service(u,address,size,data)
        u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))


def main():
    rom=NintendoDSRom((REPO/'PatchTesting/Export Rom/Explorers of Alpha+.nds').read_bytes())
    w=NativeWorld(rom);w.rom=rom;w.opened=[]
    w.call(0x02052358,0)
    assert w.opened==['rom0:/UTILITY/monster.md']
    assert struct.unpack('<I',w.u.mem_read(0x021A0004,4))[0]==2273
    md=rom.getFileByName('UTILITY/monster.md')
    metadata=8+2273*68+16+1118*32
    for row in load()['rows']:
        species=row['species']
        assert w.call(0x02052740,species)==struct.unpack_from('<H',md,8+species*68+4)[0]
        assert w.call(0x020526EC,species)==struct.unpack_from('<H',md,8+species*68+16)[0]
        assert w.call(0x0205476C,species)==1
        expected_bytes=struct.unpack_from('<I',md,metadata+16+(species-1155)*8+4)[0]
        assert w.call(0x0205281C,species)==expected_bytes
    cd=DataCDHandler.deserialize(rom.getFileByName('UTILITY/process.bin'))
    gate=bytes(cd.get_effect_code(cd.items_effects[77]))
    complete=bytes(cd.get_effect_code(cd.items_effects[76]))
    state,alpha_version=struct.unpack_from('<2I',gate,32)
    for pending in (0,1):
        for old in (0,255):
            w.u.mem_write(state+8,struct.pack('<II',pending,0))
            w.u.mem_write(alpha_version,bytes([old]))
            assert w.process(gate)==(0 if pending else old)
            w.process(complete)
            assert bytes(w.u.mem_read(state+8,8))==struct.pack('<II',0,1)
            assert bytes(w.u.mem_read(alpha_version,1))==b'\xff'
    if len(sys.argv)>1:
        path=Path(sys.argv[1]);before=hashlib.sha256(path.read_bytes()).hexdigest()
        w.flash=bytearray(path.read_bytes());position=BUFFER+0xC000
        for page in (0,200):
            w.heap=0x022C0000;w.u.mem_write(position,struct.pack('<I',page))
            assert w.call(0x02048ED0,position,BUFFER,0xB65C)==0
            w.call(0x02059224,BUFFER+0x464,0x7F6B)
            assert w.ids()[:2]==[490,736]
            original_ids=w.ids()
            records=bytes(w.u.mem_read(ROSTER,0x99A8))
            assert bytes(w.u.mem_read(state+8,8))==struct.pack('<II',1,0)
            w.u.mem_write(alpha_version,b'\xff')
            assert w.process(gate)==0
            w.process(complete)
            assert bytes(w.u.mem_read(ROSTER,0x99A8))==records
            # Write/read the migrated 12-bit stream in RAM, before any disk I/O.
            w.call(0x02059118,BUFFER+0x464,0x7F6B)
            w.call(0x02059224,BUFFER+0x464,0x7F6B)
            assert w.ids()==original_ids
            assert bytes(w.u.mem_read(state+8,8))==struct.pack('<II',0,1)
            for slot,species in ((0,2065),(1,1421),(2,1625),(3,1626)):
                w.u.mem_write(ROSTER+slot*68+4,struct.pack('<H',species))
            advanced=w.ids()
            w.call(0x02059118,BUFFER+0x464,0x7F6B)
            w.call(0x02059224,BUFFER+0x464,0x7F6B)
            assert w.ids()==advanced
        assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    print('PASS native UTILITY MD loader: all1118 rows dex/sprite/validity; existing Alpha updater gate/completion; legacy save unchanged')
    print('File I/O and process return are modeled; ARM MD consumers, save/checksum codecs and updater code execute. No emulator gameplay claim.')


if __name__=='__main__':main()
