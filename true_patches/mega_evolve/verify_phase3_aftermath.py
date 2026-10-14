"""Existing Aftermath chance/recursion/explosion boundary, including Innards Out.
Native defender predicate executes; RNG and explosion terminal modeled.
"""
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
    def reset(self):super().reset();self.chances=[];self.explosions=[]
    def service(self,u,address,size,data):
        if address==0x022eab20:self.chances.append(u.reg_read(UC_ARM_REG_R0));self.ret(self.probability);return
        if address==0x02320788:
            args=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            self.explosions.append((args,struct.unpack('<2I',bytes(u.mem_read(u.reg_read(UC_ARM_REG_SP),8)))))
            self.ret();return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'aftermath_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'aftermath_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    # The native probability and no-recursion damage source are existing data.
    ov29=rom.loadArm9Overlays()[29];prob=struct.unpack_from('<I',ov29.data,0x0230aa84-ov29.ramAddress)[0]
    source=struct.unpack_from('<I',ov29.data,0x0230aa88-ov29.ramAddress)[0]
    # Probability resides in overlay10's immutable game tables.
    ov10=rom.loadArm9Overlays()[10];w.u.mem_write(ov10.ramAddress,bytes(ov10.data))
    assert struct.unpack('<h',bytes(w.u.mem_read(prob,2)))[0]==50
    for name in ('유폭','내용물분출'):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
            for chance in (0,1):
                w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
                for i in range(2):w.profile(i,(0,0))
                profile=[(0,0)]*3
                if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
                w.profile(1,*profile)
                if mode=='suppressed':w.suppressed.add(ENTITIES[1])
                if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
                if mode=='mold':w.profile(0,(ids['틀깨기'],0))
                w.probability=chance;result=w.call('',ENTITIES[0],ENTITIES[1],20,start=0x0230aa0c)
                active=mode.startswith('slot')
                assert result==int(active and chance),(name,mode,chance,result)
                assert w.chances==([50] if active else []) and len(w.explosions)==int(active and chance)
                if w.explosions:assert w.explosions==[([ENTITIES[0],ENTITIES[1],ENTITIES[1]+4,1],(0,source))]
                cases+=1
        w.reset();w.profile(1,(ids[name],0));w.probability=1
        assert w.call('',ENTITIES[0],ENTITIES[1],source,start=0x0230aa0c)==0 and not w.explosions;cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} native Aftermath/Innards Out cases: original 50% chance, three slots, suppression/acid/Mold Breaker, native explosion args and recursion-source exclusion. RNG/explosion terminal modeled; no ROM/save output.')

if __name__=='__main__':main()
