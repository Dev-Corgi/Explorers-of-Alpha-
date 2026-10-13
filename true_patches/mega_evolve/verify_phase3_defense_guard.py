"""New Big Pecks native decrease entry guard, preserving prior patch ABI."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,STACK
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def service(self,u,address,size,data):
        if address==0x02313814:return # Execute the installed guard, not writer mock.
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'defense_guard_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'defense_guard_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold','contrary'):
        for special,self_source in ((0,False),(1,False),(0,True)):
            w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
            for i in range(2):w.profile(i,(0,0))
            if mode!='none':
                profile=[(0,0)]*3;profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids['부풀린가슴'],0)
                if mode=='contrary':profile[0]=(ids['심술꾸러기'],0)
                w.profile(1,*profile)
            if mode=='suppressed':w.suppressed.add(ENTITIES[1])
            if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
            if mode=='mold':w.profile(0,(ids['틀깨기'],0))
            actor=ENTITIES[1] if self_source else ENTITIES[0]
            values=(11,22,33,44,55);w.u.mem_write(STACK,struct.pack('<5I',*values))
            w.call('',actor,ENTITIES[1],special,2,start=0x02313814,registers={UC_ARM_REG_R12:0x12345678})
            blocked=mode.startswith('slot') and not special and not self_source
            calls=[r for r in w.prior_calls if r[0]=='PRIOR_DEFENSE_DROP']
            assert len(calls)==int(not blocked),(mode,special,self_source,calls)
            if calls:assert calls==[('PRIOR_DEFENSE_DROP',[actor,ENTITIES[1],special,2],values)]
            assert w.u.reg_read(UC_ARM_REG_SP)==STACK and w.u.reg_read(UC_ARM_REG_R12)==0x12345678
            cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} Big Pecks native-entry cases: physical-only opponent guard, self/special/Contrary passthrough, three slots, suppression/acid/Mold Breaker, original registers/stack/prior owner. Native decrease body modeled; no ROM/save output.')

if __name__=='__main__':main()
