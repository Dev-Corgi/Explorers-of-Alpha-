"""Run actual native roster/bit codecs with the resident 12-bit wrappers.

Flash I/O is not exercised here. EVS1 write/copy and read restoration are
retained; UI roster post-load setup is modeled. No NDS/save files are written.
"""
from __future__ import annotations
import hashlib
import struct
from .verify_phase1 import SOURCE, MODULE
from ndspy.rom import NintendoDSRom
from patch_engine.mega_evolve_save12 import install, verify
from patch_engine.mega_evolve_runtime import branch
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

ROSTER=0x02100000
BUFFER=0x02200000
STACK=0x023FE000
STOP=0x023FF000


class World:
    def __init__(self, rom):
        self.u=Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.u.mem_map(0x02000000, 0x400000)
        self.u.mem_write(0x02000000, bytes(rom.arm9))
        self.u.mem_write(0x020B0A48, struct.pack('<I', ROSTER))
        self.streams=[]
        self.flash=bytearray(0x19000)
        self.heap=0x022C0000
        self.io=[]
        self.u.hook_add(UC_HOOK_CODE,self.service)

    def service(self,u,address,size,data):
        if address not in (0x02001170,0x02001188,0x0204A9C8,0x0204A8E0,0x020509BC,0x0205523C):
            return
        a,b,c=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
        result=None
        if address==0x02001170:
            result=self.heap;self.heap=(self.heap+a+15)&~15
            assert self.heap<0x02380000
            u.mem_write(result,bytes(a))
        elif address==0x02001188:result=0
        elif address==0x0204A9C8:
            self.flash[a*256:a*256+c]=u.mem_read(b,c)
            self.io.append(('write',a,c));result=0
        elif address==0x0204A8E0:
            u.mem_write(b,bytes(self.flash[a*256:a*256+c]))
            self.io.append(('read',a,c));result=0
        if result is not None:
            u.reg_write(UC_ARM_REG_R0,result)
            u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR));return
        if address==0x020509BC:
            self.streams.append(struct.unpack('<4I',u.mem_read(u.reg_read(UC_ARM_REG_R0),16)))
        if address==0x0205523C: # Native post-load roster/UI setup, after decoding.
            u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))

    def call(self,address,a,b=0,c=0):
        for reg,value in ((UC_ARM_REG_R0,a),(UC_ARM_REG_R1,b),(UC_ARM_REG_R2,c),
                          (UC_ARM_REG_SP,STACK),(UC_ARM_REG_LR,STOP)):
            self.u.reg_write(reg,value)
        self.u.emu_start(address,STOP,count=20000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP
        assert self.u.reg_read(UC_ARM_REG_SP)==STACK
        return self.u.reg_read(UC_ARM_REG_R0)

    def addresses(self):
        return [ROSTER+i*0x44 for i in range(555)]+[ROSTER+0x9898+i*0x44 for i in range(4)]

    def fill(self,ids):
        for i,(address,species) in enumerate(zip(self.addresses(),ids)):
            row=bytearray(0x44)
            row[0]=1;row[1]=i%100;row[2:4]=bytes((i%256,(i*3)%256))
            struct.pack_into('<H',row,4,species)
            row[6]=80;row[7]=i%100
            struct.pack_into('<HH',row,8,700,200)
            row[12:16]=bytes((31,47,63,79))
            row[58:68]=b'ABCDEFGHIJ'
            self.u.mem_write(address,bytes(row))

    def ids(self):
        return [struct.unpack('<H',self.u.mem_read(a+4,2))[0] for a in self.addresses()]


def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes())
    info=install(rom,MODULE);verify(rom,info)
    w=World(rom)
    ids=[(0,3,600,1137,1154,1155,2047,2048,2268,4095)[i%10] for i in range(559)]
    w.fill(ids)
    # Neighbouring sections and the EVS1 tail are outside the serializer.
    w.u.mem_write(BUFFER+0x7F6B,b'NEXT_SECTION')
    w.u.mem_write(BUFFER+0xB700,b'EVS1_TAIL')
    result=w.call(0x02059118,BUFFER,0x7F6B)
    assert w.streams[-1][3]==203069 and result==203069%8
    assert bytes(w.u.mem_read(BUFFER+0x7F58,16))==struct.pack('<4I',0x3231454D,1,12,559)
    assert bytes(w.u.mem_read(BUFFER+0x7F6B,12))==b'NEXT_SECTION'
    assert bytes(w.u.mem_read(BUFFER+0xB700,9))==b'EVS1_TAIL'
    assert (203069+7)//8 < 0x7F58
    w.fill([0]*559)
    assert w.call(0x02059224,BUFFER,0x7F6B)==result
    assert w.ids()==ids and w.streams[-1][3]==203069
    for a in w.addresses():
        assert bytes(w.u.mem_read(a+12,4))==bytes((31,47,63,79))
        assert bytes(w.u.mem_read(a+58,10))==b'ABCDEFGHIJ'
    assert bytes(w.u.mem_read(info['state'],8))==bytes(8)
    # Previous saves have no marker and retain the actual 11-bit native layout.
    old=NintendoDSRom(SOURCE.read_bytes());legacy=World(old)
    old_ids=[i%1155 for i in range(559)]
    legacy.fill(old_ids)
    old_result=legacy.call(0x02059118,BUFFER,0x7F6B)
    assert legacy.streams[-1][3]==202510
    w.u.mem_write(BUFFER,bytes(legacy.u.mem_read(BUFFER,0x7F6B)))
    assert w.call(0x02059224,BUFFER,0x7F6B)==old_result
    assert w.ids()==old_ids and w.streams[-1][3]==202510
    # Unknown future schema fails before any roster record is decoded.
    w.u.mem_write(BUFFER+0x7F58,struct.pack('<4I',0x3231454D,2,12,559))
    snapshot=bytes(w.u.mem_read(ROSTER,0x99A8))
    assert w.call(0x02059224,BUFFER,0x7F6B)==0xFFFFFFFF
    assert bytes(w.u.mem_read(ROSTER,0x99A8))==snapshot
    # Scope does not leak into standalone monster serializers.
    w.u.mem_write(BUFFER,bytes(0x100))
    w.call(0x02050990,BUFFER+0x200,BUFFER,0x100)
    w.u.mem_write(BUFFER+0x300,struct.pack('<H',4095))
    w.call(info['symbols']['ME_Save12WriteSpecies'],BUFFER+0x200,BUFFER+0x300,11)
    assert struct.unpack('<I',w.u.mem_read(BUFFER+0x20C,4))[0]==11
    # Execute the existing EVS1 main/checksum/tail wrappers, with flash storage
    # modeled in memory. Both redundant slots retain their exact old sizes.
    main=BUFFER+0x10000;position=BUFFER+0xC000
    w.u.mem_write(main,bytes(0xB65C));w.fill(ids)
    w.call(0x02059118,main+0x464,0x7F6B)
    for page in (0,200):
        w.heap=0x022C0000
        w.u.mem_write(position,struct.pack('<I',page))
        assert w.call(0x02048E74,position,main,0xB65C)==0
        assert w.io[-1]==('write',page,0xC644)
        assert w.flash[page*256+0x83BC:page*256+0x83CC]==struct.pack('<4I',0x3231454D,1,12,559)
        assert w.flash[page*256+0x35:page*256+0x38]==b'EV\x01'
        assert struct.unpack_from('<I',w.flash,page*256+0xB704)[0]==0x31535645
        assert w.flash[page*256+0xC644:(page+200)*256]==bytes(0x1BC)
        w.fill([0]*559);w.u.mem_write(main,bytes(0xB65C))
        w.u.mem_write(position,struct.pack('<I',page))
        assert w.call(0x02048ED0,position,main,0xB65C)==0
        w.call(0x02059224,main+0x464,0x7F6B)
        assert w.ids()==ids
    # Main checksum covers the version marker; malformed data never reaches
    # the roster decoder through the real read wrapper.
    w.flash[0x83BC]^=1
    w.heap=0x022C0000;w.u.mem_write(position,bytes(4))
    assert w.call(0x02048ED0,position,main,0xB65C)!=0
    # Quicksave already copies both original and apparent species as two
    # bytes. Execute their native write/read fragments and byte codecs.
    quick=rom.loadArm9Overlays()[30]
    w.u.mem_write(quick.ramAddress,bytes(quick.data))
    for original,apparent in ((1155,3),(2048,1155),(2268,2048),(4095,2268)):
        stream=BUFFER+0x200;monster=BUFFER+0x300
        w.u.mem_write(monster,struct.pack('<3H',0,original,apparent))
        w.call(0x02385C3C,stream,BUFFER,16)
        w.u.reg_write(UC_ARM_REG_R6,monster);w.u.reg_write(UC_ARM_REG_R8,stream)
        w.u.reg_write(UC_ARM_REG_SP,STACK)
        w.u.emu_start(0x0238330C,0x0238333C,count=1000)
        assert bytes(w.u.mem_read(BUFFER,4))==struct.pack('<2H',apparent,original)
        w.call(0x02385C8C,stream,BUFFER,16)
        w.u.reg_write(UC_ARM_REG_R10,stream);w.u.reg_write(UC_ARM_REG_SP,STACK)
        w.u.emu_start(0x02384EDC,0x02384EF8,count=1000)
        assert struct.unpack('<H',w.u.mem_read(STACK+0x1A,2))[0]==apparent
        w.u.emu_start(0x02385138,0x0238514C,count=1000)
        assert w.u.reg_read(UC_ARM_REG_R0)==original
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS save12 ARM: all 559 records, IDs through4095, old11/new12 layouts,')
    print('  neighbouring sections/tail, stat/name fields, future-schema rejection, ABI and scope.')
    print('  real EVS1 main/tail checksums, redundant slots and corrupt-main rejection (modeled flash).')
    print('  native quicksave original/apparent species fragments retain both16-bit IDs.')
    print('Complete dungeon quicksave/gameplay remain separate integration checks. No ROM/save output.')


if __name__=='__main__':main()
