"""Existing native spawn appearance with three-slot traits and stable profiles.
Reuses bug_fixes' original services and terminal boundary; no copied effect code.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,STACK,STOP
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):super().reset();self.appearance=[];self.candidates=1;self.apparent_species=151;self.fixed=0
    def service(self,u,address,size,data):
        a,b=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
        if address==0x023361d4:self.ret(self.fixed);return
        if address==0x022e7c60:self.ret(self.candidates);return
        if address==0x02054480:self.ret(self.apparent_species);return
        if address==0x022f9408:self.ret(b);return
        if address==0x023c0318:self.appearance.append((a,b));self.ret();return
        if address in (0x022fe350,0x022fe3b8):self.ret(70+u.reg_read(UC_ARM_REG_R2));return
        if address==0x02303b18:u.mem_write(a,struct.pack('<4H',1,2,3,4));self.ret();return
        if address==0x020137e8:u.mem_write(a,struct.pack('<H6x',b));self.ret();return
        super().service(u,address,size,data)
    def spawn(self):
        reached=[]
        def boundary(u,address,size,_):
            if address==0x023bf928:reached.append(address);u.emu_stop()
        handle=self.u.hook_add(UC_HOOK_CODE,boundary)
        try:
            self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_R4,ENTITIES[0])
            self.u.emu_start(0x023bf464,STOP,count=500000)
            assert reached==[0x023bf928],hex(self.u.reg_read(UC_ARM_REG_PC))
        finally:self.u.hook_del(handle)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'appearance_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'appearance_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    def setup(name,mode):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        w.u.mem_write(MONSTERS[0]+2,struct.pack('<2H',132,132))
        for i in range(2):w.profile(i,(0,0))
        profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        w.profile(0,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[0])
        if mode=='acid':w.u.mem_write(MONSTERS[0]+0xd8,b'\x04')
        return profile
    for name in ('일루전','괴짜'):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            profile=setup(name,mode);w.spawn();active=mode.startswith('slot')
            assert w.appearance==([(ENTITIES[0],151)] if active else []),(name,mode,w.appearance)
            assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[0]+2,2)))[0]==132
            if active:
                assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[0]+4,2)))[0]==151
                if name=='일루전':assert struct.unpack('<2H',bytes(w.u.mem_read(MONSTERS[0]+0x24,4)))==(11,11)
                w.call('ME_RestoreAbilities',ENTITIES[0])
                assert [w.ability(0,j) for j in range(3)]==[p[0] for p in profile]
            cases+=1
        for count in (0,1):
            setup(name,'slot3');w.candidates=count;w.apparent_species=132 if count else 151
            w.spawn();assert not w.appearance;cases+=1
    # Changing apparent species never re-seeds the profile from a different MD
    # row. Real original-species changes still invalidate the profile bank.
    profile=setup('일루전','slot3');w.u.mem_write(MONSTERS[0]+4,struct.pack('<H',151))
    assert w.ability(0,2)==ids['일루전'];cases+=1
    w.u.mem_write(MONSTERS[0]+2,struct.pack('<H',1));assert w.ability(0,2)==0;cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} native Illusion/Imposter spawn cases: all slots, suppression/acid, existing fixed-room/candidate gates retained, native appearance/stats, permanent original ID2 versus apparent ID4, profile restore. Native ancillary services modeled; no ROM/save output.')

if __name__=='__main__':main()
