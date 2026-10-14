"""Native pinch HP/type gates and revised Iron Fist/Reckless power arithmetic.
Native fixed-point multiplication runs; status-cache/UI services are modeled.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3_native_immunity import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,BUFFER,STACK
from .phase3 import load
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def service(self,u,address,size,data):
        if address==0x023023c0:self.ret(0);return
        if address in (0x0234b350,0x022e6510):self.ret();return
        super().service(u,address,size,data)
    def pinch(self,start,end,type_):
        out=BUFFER+0x300;self.u.mem_write(out,struct.pack('<II',0,100<<16))
        self.segment(start,{end,0x0230b534} if start==0x0230b44c else {end},{UC_ARM_REG_R6:MONSTERS[0],UC_ARM_REG_R8:type_,UC_ARM_REG_R9:ENTITIES[1],
            UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R11:out})
        return self.call('',out,start=0x02001cb0)
    def power(self,move):
        self.u.mem_write(STACK+0x1c,struct.pack('<I',100));self.u.mem_write(STACK+0xf4,struct.pack('<I',move))
        self.segment(0x0230bc1c,{0x0230bc84},{UC_ARM_REG_R10:ENTITIES[0]})
        return struct.unpack('<I',bytes(self.u.mem_read(STACK+0x1c,4)))[0]

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'pinch_power_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'pinch_power_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    def setup(name,mode):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0))
        profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        w.profile(0,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[0])
        if mode=='acid':w.u.mem_write(MONSTERS[0]+0xd8,b'\x04')
    for name,type_,start,end in (('급류',3,0x0230b248,0x0230b2f4),('심록',4,0x0230b2f4,0x0230b3a0),
                                ('벌레의알림',12,0x0230b3a0,0x0230b44c),('맹화',2,0x0230b44c,0x0230b4f8)):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            for hp,bonus in ((25,0),(26,0),(27,10),(28,10)):
                setup(name,mode);w.u.mem_write(MONSTERS[0]+0x10,struct.pack('<4h',hp,100,0,bonus))
                active=mode.startswith('slot') and hp<=(100+bonus)//4
                assert w.pinch(start,end,type_)==(150 if active else 100),(name,mode,hp,bonus)
                assert w.pinch(start,end,1)==100;cases+=2
    # Original ARM classifiers enumerate recoil/punch moves; select IDs by
    # executing them rather than duplicating their implementation in the test.
    for name,classifier in (('이판사판',0x02013e14),('철주먹',0x02014d18)):
        positive=next(i for i in range(1,560) if w.call('',i,start=classifier))
        negative=next(i for i in range(1,560) if not w.call('',i,start=classifier))
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            setup(name,mode)
            assert w.power(positive)==(120 if mode.startswith('slot') else 100),(name,mode,positive)
            assert w.power(negative)==100;cases+=2
    # Tinted Lens consumes the final native type-matchup value, not a guessed type.
    setup('색안경','slot3');w.u.mem_write(BUFFER,struct.pack('<3I',100,0,1))
    w.u.mem_write(STACK,struct.pack('<I',1));w.call('ME_AdjustDamage',ENTITIES[0],ENTITIES[1],BUFFER,1)
    assert struct.unpack('<I',bytes(w.u.mem_read(BUFFER,4)))[0]==120;cases+=1
    assert w.call('ME_LegacyAbilityActive',ENTITIES[0],80,0x0230aff8)==0;cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} native pinch/power cases: four native HP-quarter/type/bonus gates, Iron Fist/Reckless classifiers and exact x1.2 power, conditional flags retained, Tinted Lens resistant-matchup x1.2 and old boost removed. Cache/UI/fixed multiply modeled; no ROM/save output.')

if __name__=='__main__':main()
