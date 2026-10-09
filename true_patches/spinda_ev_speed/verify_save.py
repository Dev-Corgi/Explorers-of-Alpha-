"""Execute the freestanding ARM save codec, using a simulated backup device.

No ROM is built or written. The stock ARM9 read/checksum code is executed;
only hardware I/O, allocations and monster-stream payloads are stubbed.
"""
from __future__ import annotations
import re
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.script.ssb.handler import SsbHandler
from patch_engine.spinda_save_runtime import build_runtime, patch_import_prompt

MAIN=0xB65C; TAIL=0xB700; TAIL_SIZE=3908; COUNT=555
OFFSETS=(10,12,13,14,15,11)
TEAM=0x02100000; ENTITY=0x02200000; INFO=ENTITY+0x1000
CAVE=0x02094D94; STATE=CAVE+0x1D00; STOP=0x020F0000


def sum_words(data):
    return sum(struct.unpack_from('<I',data,i)[0] for i in range(4,len(data)&~3,4)) & 0xFFFFFFFF


class Machine:
    def __init__(self, rom, binary, labels, flash=None):
        self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
        self.u.mem_map(0x02000000,0x400000)
        self.u.mem_write(0x02000000,bytes(rom.arm9))
        self.u.mem_write(CAVE+0x1000,binary)
        self.u.mem_write(STATE,bytes(3904))
        self.u.mem_write(0x020B0A48,struct.pack('<I',TEAM))
        self.flash=flash if flash is not None else bytearray(0x20000)
        self.labels={name:int(address,16) for name,address in re.findall(r'definelabel (\w+), 0x(\w+)',labels)}
        self.heap=0x02180000; self.serialized={}; self.restored={}; self.copy_capture=None
        for off,word,target in [(0x800,0xE92D4038,0x02048ED4),(0x810,0xE92D4070,0x02048E78)]:
            pc=CAVE+off+4
            branch=0xEA000000 | (((target-pc-8)>>2)&0xFFFFFF)
            self.u.mem_write(CAVE+off,struct.pack('<II',word,branch))
        self.u.hook_add(UC_HOOK_CODE,self.api)

    def ret(self,value=0):
        self.u.reg_write(UC_ARM_REG_R0,value)
        self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))

    def api(self,u,address,size,_):
        a,b,c=(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2))
        if address==0x02001170:
            p=self.heap; self.heap+=(a+7)&~7; self.ret(p)
        elif address==0x02001188: self.ret()
        elif address==0x020555A8: self.ret(TEAM+a*0x44 if a<COUNT else 0)
        elif address==0x0205638C: self.ret(TEAM+0x936C+a*0x68 if a<4 else 0)
        elif address==0x0204A8E0:
            u.mem_write(b,bytes(self.flash[a*256:a*256+c])); self.ret(0)
        elif address==0x0204A9C8:
            self.flash[a*256:a*256+c]=u.mem_read(b,c); self.ret(0)
        elif address==CAVE+0x820:
            self.copy_capture=bytes(u.mem_read(b,0x44)); self.ret()
        elif address==CAVE+0x830:
            for i,record in self.restored.items(): u.mem_write(TEAM+i*0x44,record)
            self.ret(123)

    def call(self,name,*args):
        self.u.reg_write(UC_ARM_REG_SP,STOP-0x100)
        self.u.reg_write(UC_ARM_REG_LR,STOP)
        for r,v in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):self.u.reg_write(r,v)
        self.u.emu_start(self.labels[name],STOP,count=3000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==STOP, name+' did not return'
        return self.u.reg_read(UC_ARM_REG_R0)

    def ground(self,i,values=None):
        p=TEAM+i*0x44
        if values is not None:
            rec=bytearray(0x44);rec[0]=1;rec[1]=40;struct.pack_into('<h',rec,4,25)
            for off,v in zip(OFFSETS,values):rec[off]=v
            self.u.mem_write(p,bytes(rec))
        return [self.u.mem_read(p+off,1)[0] for off in OFFSETS]

    def member(self,slot,i):
        t=TEAM+0x936C+slot*0x68
        self.u.mem_write(t,bytes(0x68));self.u.mem_write(t,b'\1')
        self.u.mem_write(t+8,struct.pack('<h',i))
        if i>=0:
            values=self.ground(i)
            self.u.mem_write(t+16,bytes([values[0],values[5],*values[1:5]]))
        return t

    def entity(self,slot):
        t=TEAM+0x936C+slot*0x68
        self.u.mem_write(ENTITY,struct.pack('<I',1))
        self.u.mem_write(ENTITY+0xB4,struct.pack('<I',INFO))
        self.u.mem_write(INFO+12,struct.pack('<h',slot))
        self.u.mem_write(INFO+26,bytes(self.u.mem_read(t+18,4)))

    def gain(self,slot,delta,nested=False):
        self.entity(slot);t=TEAM+0x936C+slot*0x68
        self.call('EvSave_Begin',ENTITY)
        if nested:self.call('EvSave_Begin',ENTITY)
        for j,v in enumerate(delta):
            p=t+16 if j==0 else t+17 if j==5 else INFO+25+j
            old=self.u.mem_read(p,1)[0];self.u.mem_write(p,bytes([min(255,old+v)]))
        if nested:self.call('EvSave_End')
        self.call('EvSave_End')


def verify_script(rom):
    config=get_ppmdu_config_for_rom(rom)
    old=SsbHandler.deserialize(rom.getFileByName('SCRIPT/COMMON/unionall.ssb'),static_data=config)
    indices=patch_import_prompt(rom,config)
    new=SsbHandler.deserialize(rom.getFileByName('SCRIPT/COMMON/unionall.ssb'),static_data=config)
    assert indices==[240,241,242]
    extra=new.routine_ops[68][12].offset-old.routine_ops[68][0].offset
    threshold=old.routine_ops[68][0].offset
    for i,ops in enumerate(old.routine_ops):
        newops=new.routine_ops[i][12:] if i==68 else new.routine_ops[i]
        assert len(ops)==len(newops)
        for a,b in zip(ops,newops):
            assert a.op_code.id==b.op_code.id
            expected=list(a.params)
            for arg in a.op_code.arguments:
                if arg.name=='jump_address' and expected[arg.id]>=threshold:expected[arg.id]+=extra
            assert expected==list(b.params), (i,a.offset)
    assert patch_import_prompt(rom,config)==[]


def main():
    rom=NintendoDSRom.fromFile(str(ROOT/'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'))
    verify_script(rom)
    with tempfile.TemporaryDirectory(prefix='spinda_save_verify_') as tmp:
        binary,labels=build_runtime(Path(__file__).parent,Path(tmp),CAVE,0x023E0000)
        code=binary.read_bytes()
    m=Machine(rom,code,labels)
    permanent=[5,10,11,12,13,10]
    m.ground(10,permanent);m.member(0,10)
    m.gain(0,[4,3,2,1,5,7],nested=True)
    combined=[a+b for a,b in zip(permanent,[4,3,2,1,5,7])]
    assert m.ground(10)==combined
    # Leader/slot changes do not move the roster-indexed temporary record.
    m.member(0,12);m.ground(12,[0]*6);m.member(2,10)
    m.gain(2,[1]*6)
    combined=[v+1 for v in combined]
    assert m.ground(10)==combined
    original=bytes(m.u.mem_read(TEAM+10*0x44,0x44))
    m.call('EvSave_CopyMonster',0x02210000,TEAM+10*0x44)
    saved=m.copy_capture
    assert [saved[o] for o in OFFSETS]==permanent[:5]+[0]
    assert bytes(m.u.mem_read(TEAM+10*0x44,0x44))==original
    # 0..255 Speed preservation, including values destroyed by old 10-bit HP.
    for i,speed in enumerate([0,1,2,3,4,10,63,64,127,128,254,255]):m.ground(100+i,[0,1,2,3,4,speed])
    main_buffer=0x02210000;position=main_buffer+MAIN+0x100
    main=bytearray(MAIN);main[0x38+0x3EB]=0xFF
    m.u.mem_write(main_buffer,bytes(main));m.u.mem_write(position,struct.pack('<I',0))
    assert m.call('EvSave_Write',position,main_buffer,MAIN)==0
    assert m.flash[0x35:0x38]==b'EV\1'
    assert m.flash[0x38+0x3EB]==0xFF
    assert struct.unpack_from('<I',m.flash)[0]==sum_words(m.flash[:MAIN])
    assert struct.unpack_from('<I',m.flash,TAIL)[0]==sum_words(m.flash[TAIL:TAIL+TAIL_SIZE])
    # Separate backup slot; tail must stop before the next slot/quicksave.
    m.u.mem_write(position,struct.pack('<I',200))
    assert m.call('EvSave_Write',position,main_buffer,MAIN)==0
    assert m.flash[199*256:200*256]==bytes(256)
    assert m.flash[399*256:400*256]==bytes(256)
    n=Machine(rom,code,labels,m.flash)
    n.restored={10:saved}
    for i in range(12):
        rec=bytearray(0x44);rec[0]=1;rec[12:16]=bytes([1,2,3,4]);n.restored[100+i]=bytes(rec)
    n.u.mem_write(position,struct.pack('<I',0))
    assert n.call('EvSave_Read',position,main_buffer,MAIN)==0
    assert n.call('EvSave_ReadMonsters',main_buffer+0x464,0x7F6B)==123
    assert n.ground(10)==combined
    assert [n.ground(100+i)[5] for i in range(12)]==[0,1,2,3,4,10,63,64,127,128,254,255]
    # Quicksave restoration may overwrite active copies after the main load.
    t=n.member(2,10);n.entity(2)
    n.u.mem_write(0x02353538,struct.pack('<I',0x02230000))
    n.u.mem_write(0x02230000+0x12B28+8,struct.pack('<I',ENTITY))
    n.u.mem_write(t+16,bytes(6));n.u.mem_write(INFO+26,bytes(4))
    n.call('EvSave_DungeonImport')
    assert list(n.u.mem_read(t+16,6))==[combined[0],combined[5],*combined[1:5]]
    assert list(n.u.mem_read(INFO+26,4))==combined[1:5]
    n.member(1,10);n.member(1,-1) # Sent home: no active member remains.
    n.call('EvSave_GroupEnd')
    assert n.ground(10)==permanent
    # Corrupt tail fails closed; intact backup remains usable.
    n.flash[TAIL+30]^=1;n.u.mem_write(position,struct.pack('<I',0))
    assert n.call('EvSave_Read',position,main_buffer,MAIN)==2
    n.u.mem_write(position,struct.pack('<I',200))
    assert n.call('EvSave_Read',position,main_buffer,MAIN)==0
    # Both explicit legacy policies, no automatic deletion, no unresolved save.
    old=bytearray(MAIN);struct.pack_into('<I',old,0,sum_words(old));n.flash[:MAIN]=old
    for choice in [1,0]:
        n.u.mem_write(position,struct.pack('<I',0))
        assert n.call('EvSave_Read',position,main_buffer,MAIN)==0
        n.ground(3,[99]*6);n.member(0,3)
        assert n.call('EvSave_LegacyPending')==1
        n.u.mem_write(position,struct.pack('<I',0))
        assert n.call('EvSave_Write',position,main_buffer,MAIN)==2
        n.call('EvSave_Convert',choice)
        assert n.ground(3)==([99]*6 if choice else [0]*6)
        assert n.call('EvSave_LegacyPending')==0
    n.call('EvSave_NewGame')
    assert bytes(n.u.mem_read(STATE,3904))==bytes(3904)
    print('PASS: ARM codec, Speed boundaries, nested gains, leader changes, sent-home cleanup, checksums/backup, legacy choices, script relocation')


if __name__=='__main__':main()
