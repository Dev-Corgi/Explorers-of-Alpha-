"""Real STAB/Filter paths and ARM fx64_16 math in the finished ROM.

Ability availability, exclusive-item STAB and pack file IO are controlled;
the multipliers, factor pointers, native multiply and conversion are not modeled.
"""
import hashlib,json,struct
from .verify_actor_sprite_cache import CacheWorld
from .verify_phase1 import REPO
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

STACK,STOP,OUT,FACTOR=0x023FE000,0x023FF000,0x02280000,0x02280100
ATTACKER,TARGET=0x02250000,0x02250200
MONSTER=0x02260000


class FactorWorld(CacheWorld):
    def __init__(self,rom):
        self.rom=rom;self.opened=[];self.abilities=set();self.filter_active=False;self.multiplies=0
        super().__init__(rom)
        for i in (29,36):
            ov=rom.loadArm9Overlays()[i];self.u.mem_write(ov.ramAddress,bytes(ov.data))
        self.u.mem_write(ATTACKER,struct.pack('<I',1))
        self.u.mem_write(ATTACKER+0xb4,struct.pack('<I',MONSTER))
        self.u.mem_write(MONSTER+0x5e,b'\x01\x00')
        # The native same-type feedback structure is an independent global.
        instruction=struct.unpack('<I',self.u.mem_read(0x0230b584,4))[0]
        literal=0x0230b584+8+(instruction&4095)
        pointer=struct.unpack('<I',self.u.mem_read(literal,4))[0]
        self.u.mem_write(pointer,struct.pack('<I',0x02100000))

    def ret(self,value):
        self.u.reg_write(UC_ARM_REG_R0,int(value)&0xffffffff)
        self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))

    def service(self,u,address,size,data):
        if address==0x02001df4:self.multiplies+=1
        if address in (0x02301d78,0x02301d10):
            self.ret(u.reg_read(UC_ARM_REG_R1) in self.abilities);return
        if address==0x023d44e4:self.ret(0);return
        if address==0x022f96cc:
            assert u.reg_read(UC_ARM_REG_R2)==110
            self.ret(self.filter_active);return
        return super().service(u,address,size,data)

    def invoke(self,start,end=STOP,**registers):
        self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP)
        for name,value in registers.items():self.u.reg_write(globals()['UC_ARM_REG_'+name.upper()],value)
        self.u.emu_start(start,end,count=10000000)
        assert self.u.reg_read(UC_ARM_REG_PC)==end,hex(self.u.reg_read(UC_ARM_REG_PC))
        assert self.u.reg_read(UC_ARM_REG_SP)==STACK
        return self.u.reg_read(UC_ARM_REG_R0)

    def set_amount(self,amount):
        # Obtain input layout from the engine itself, rather than assuming it.
        self.invoke(0x02001c80,r0=OUT,r1=amount)

    def value(self):
        upper,lower=struct.unpack('<II',self.u.mem_read(OUT,8))
        bits=(upper<<32)|lower
        if upper&0x80000000:bits-=1<<64
        return bits/(1<<16)

    def rounded(self):return self.invoke(0x02001cb0,r0=OUT)

    def stab(self,amount,abilities,type_=1):
        self.abilities=set(abilities);self.set_amount(amount);self.multiplies=0
        self.invoke(0x0230b570,0x0230b5cc,r7=OUT+0x200,r8=type_,r9=TARGET,r10=ATTACKER,r11=OUT)
        return self.value(),self.rounded(),self.multiplies


def main():
    path=REPO/'PatchTesting/Export Rom/Explorers of Alpha+.nds'
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    rom=NintendoDSRom(path.read_bytes())
    korean_path=path.with_name('Explorers of Alpha+_kor.nds')
    korean_blob=korean_path.read_bytes();korean=NintendoDSRom(korean_blob)
    assert korean.getFileByName('MEGA/runtime.bin')==rom.getFileByName('MEGA/runtime.bin')
    ov29,ko29=rom.loadArm9Overlays()[29],korean.loadArm9Overlays()[29]
    ov36,ko36=rom.loadArm9Overlays()[36],korean.loadArm9Overlays()[36]
    offset=0x0230b570-ov29.ramAddress
    assert bytes(ov29.data[offset:offset+0x5c])==bytes(ko29.data[offset:offset+0x5c])
    for site,length in ((0x0230b59c,40),(0x0230b5a8,8)):
        instruction=struct.unpack_from('<I',ov29.data,site-ov29.ramAddress)[0]
        start=branch_target(site,instruction);offset=start-ov36.ramAddress
        assert 0<=offset<len(ov36.data)-length
        assert bytes(ov36.data[offset:offset+length])==bytes(ko36.data[offset:offset+length])
    assert bytes(rom.arm9[0x1c80:0x2068])==bytes(korean.arm9[0x1c80:0x2068])
    world=FactorWorld(rom);cases=0
    world.invoke(0x0230b5a8,0x0230b5ac)
    offset=world.u.reg_read(UC_ARM_REG_R2)-ov36.ramAddress
    assert bytes(ov36.data[offset:offset+8])==bytes(ko36.data[offset:offset+8])
    for amount in (1,10,100,1000,32767):
        for traits in ((),(24,),(99,),(24,99)):
            for type_ in (1,2):
                actual,rounded,calls=world.stab(amount,traits,type_)
                factor=(0x1b333/(1<<16) if traits else 1.5) if type_==1 else 1
                assert abs(actual-amount*factor)<1/(1<<16),(amount,traits,type_,actual)
                assert rounded==int(amount*factor+.5),(amount,traits,type_,rounded)
                assert calls==int(type_==1),'STAB multiplied more than once'
                cases+=1
        for active,coefficient in ((False,0xc000),(True,0xcccc)):
            world.filter_active=active;world.set_amount(amount);world.multiplies=0
            world.invoke(0x0230b070,0x0230b080,r9=TARGET,r10=ATTACKER,r11=OUT)
            assert abs(world.value()-amount*coefficient/(1<<16))<1/(1<<16)
            assert world.rounded()==int(amount*coefficient/(1<<16)+.5)
            assert world.multiplies==1
            cases+=1
    # The previous encoding must fail the same actual arithmetic: a negative
    # control prevents replacing the engine with the old erroneous Q16.48 mock.
    world.set_amount(100);world.u.mem_write(FACTOR,struct.pack('<II',0x33333333,0x1b333))
    world.invoke(0x02001df4,r0=OUT,r1=OUT,r2=FACTOR)
    previous=world.value();assert previous>1e9,previous
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    report=dict(schema=1,cases=cases,rom_sha256=before,korean_rom_sha256=hashlib.sha256(korean_blob).hexdigest(),
                korean_factor_code_identical=True,old_encoding_native_intermediate=previous,
                adaptability_100=170,ordinary_stab_100=150,non_stab_100=100,filter_100=80,
                scope='Actual ARM type gate, STAB query wrapper, Filter pointer helper, fx64_16 multiply/conversion. Ability availability, exclusive items and file IO controlled; no gameplay claim.')
    (REPO/'true_patches/mega_evolve/data/phase3_fixed_factors_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS native fixed-point regression:',report)


if __name__=='__main__':main()
