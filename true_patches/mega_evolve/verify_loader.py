"""Execute actual ARM heap loader/thunks; model only ROM IO and allocator.
No NDS/save output. Check relocation, flags/register/stack ABI and reload lifetime.
"""
from __future__ import annotations
import copy,hashlib,struct
from .verify_phase3 import World
from .verify_phase1 import SOURCE,MODULE,STACK,STOP,ENTITIES
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class LoaderWorld(World):
    def __init__(self,rom,record):
        self.loads=[];self.probe=None;self.observed=None;self.corrupt=False
        super().__init__(rom,record)
        self.u.mem_write(self.loader_info['bootstrap_symbols']['base'],bytes(4))
        self.u.mem_write(self.loader_info['bootstrap_symbols']['loaded'],bytes(8))
    def service(self,u,address,size,data):
        if address==0x02008c3c:
            a,b,c=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            assert bytes(u.mem_read(b,18)).split(b'\0')[0]==b'/MEGA/runtime.bin'
            assert c==0 and u.reg_read(UC_ARM_REG_SP)%8==0
            pointer=0x02180000+len(self.loads)*0x10000
            payload=bytearray(self.payload)
            if self.corrupt:payload[-1]^=1
            u.mem_write(pointer,bytes(payload));u.mem_write(a,struct.pack('<II',pointer,len(payload)))
            self.loads.append(pointer)
            self.ret();return
        if self.probe and self.loads and address==self.loads[-1]+self.loader_info['runtime_image_offset']+self.probe:
            regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,
                  UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
                  UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12]
            self.observed=([u.reg_read(r) for r in regs],u.reg_read(UC_ARM_REG_SP),u.reg_read(UC_ARM_REG_CPSR)&0xf0000000,
                           bytes(u.mem_read(u.reg_read(UC_ARM_REG_SP),24)))
            self.ret(37);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());files=copy.deepcopy(rom.files)
    names=[rom.filenames.filenameOf(i) for i in range(len(files))]
    table=bytes(rom.arm9OverlayTable)
    manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'loader_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'loader_test':True})
    info=record.data[0];assert rom.arm9OverlayTable==table
    assert all(rom.filenames.filenameOf(i)==name for i,name in enumerate(names))
    assert len(rom.files)==len(files)+1
    assert record.caves[0].size==8192 and info['runtime_size']>25000
    w=LoaderWorld(rom,record);exports=info['bootstrap_symbols']
    # Execute relocation and real C/global access at an allocator-chosen address.
    assert w.call('',ENTITIES[0],start=exports['ME_GetStoredSpeed'],limit=2000000)==10
    assert len(w.loads)==1
    base=w.loads[0]+info['runtime_image_offset']
    original=w.payload[info['runtime_image_offset']:]
    for offset in info['runtime_relocations']:
        assert struct.unpack('<I',bytes(w.u.mem_read(base+offset,4)))[0]==struct.unpack_from('<I',original,offset)[0]-0x01000000+base
    w.call('',ENTITIES[0],12,start=exports['ME_SetStoredSpeed'])
    assert w.call('',ENTITIES[0],start=exports['ME_GetStoredSpeed'])==12 and len(w.loads)==1
    # Preserve every input register, flags, SP and caller stack at tail dispatch.
    regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,
          UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,
          UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12]
    w.probe=info['runtime_symbol_offsets']['ME_ApparentWeatherHook']
    for cold in (False,True):
        if cold:
            w.call('',start=exports['ME_LoaderRelease']);assert w.loads[-1] in w.freed
        values=[0x10101010+i for i in range(13)]
        for r,v in zip(regs,values):w.u.reg_write(r,v)
        stack=struct.pack('<6I',*range(6));w.u.mem_write(STACK,stack)
        w.u.reg_write(UC_ARM_REG_SP,STACK);w.u.reg_write(UC_ARM_REG_LR,STOP)
        cpsr=w.u.reg_read(UC_ARM_REG_CPSR);w.u.reg_write(UC_ARM_REG_CPSR,(cpsr&0x0fffffff)|0xa0000000)
        w.u.emu_start(exports['ME_ApparentWeatherHook'],STOP,count=2000000)
        assert w.observed==(values,STACK,0xa0000000,stack)
        assert w.u.reg_read(UC_ARM_REG_SP)==STACK
    w.probe=None
    # Free calls existing dungeon owner, frees effect heaps, then frees execution
    # block from bootstrap after the last payload instruction has returned.
    pointer=w.loads[-1]
    w.call('',start=exports['ME_FreeHook'],limit=2000000)
    assert pointer in w.freed
    assert struct.unpack('<I',bytes(w.u.mem_read(exports['base'],4)))[0]==0
    assert w.call('',ENTITIES[0],start=exports['ME_GetStoredSpeed'],limit=2000000)==10
    assert w.loads[-1]!=pointer
    # Corrupt payload never publishes a code pointer or dispatches its contents.
    bad=LoaderWorld(rom,record);bad.corrupt=True
    bad.u.reg_write(UC_ARM_REG_SP,STACK);bad.u.reg_write(UC_ARM_REG_LR,STOP)
    bad.u.emu_start(exports['ME_GetStoredSpeed'],STOP,count=1000000)
    assert struct.unpack('<I',bytes(bad.u.mem_read(exports['base'],4)))[0]==0
    corrupted=NintendoDSRom(rom.save());payload=bytearray(corrupted.getFileByName(info['runtime_file']))
    payload[-1]^=1;corrupted.setFileByName(info['runtime_file'],bytes(payload))
    try:verify_phase1(corrupted,MODULE,manifest,record,{'loader_test':True})
    except AssertionError as e:assert 'payload hash' in str(e)
    else:raise AssertionError('corrupt file passed verification')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS execution loader ARM: uncompressed heap image, internal relocation, cold/warm register+flags+stack ABI, cache instructions, free/reload, checksum rejection; FAT IDs/overlay sizes unchanged. No ROM/save output.')

if __name__=='__main__':main()
