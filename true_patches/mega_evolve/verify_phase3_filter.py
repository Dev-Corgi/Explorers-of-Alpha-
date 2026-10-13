"""Actual shared Filter/Omniscience matchup branch, with fixed-point multiply
modeled from the native factor pointer. No final damage/battle certification.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3_native_immunity import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,BUFFER
from .phase3 import load
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def service(self,u,address,size,data):
        if address==0x02001df4:
            out,left,right=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            a,b=[struct.unpack('<Q',bytes(u.mem_read(p,8)))[0] for p in (left,right)]
            u.mem_write(out,struct.pack('<Q',(a*b)>>48));self.ret();return
        super().service(u,address,size,data)
    def multiplier(self,matchup):
        out=BUFFER+0x300;damage=BUFFER+0x320
        self.u.mem_write(out,struct.pack('<Q',100<<48));self.u.mem_write(damage,bytes(20))
        self.u.mem_write(damage+8,struct.pack('<I',matchup))
        self.segment(0x0230b02c,{0x0230b080},{UC_ARM_REG_R7:damage,UC_ARM_REG_R9:ENTITIES[1],
            UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R11:out})
        return struct.unpack('<Q',bytes(self.u.mem_read(out,8)))[0]>>48

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'filter_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'filter_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    for name,factor in (('필터',80),('하드록',80),('Omniscience',75)):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
            w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
            for i in range(2):w.profile(i,(0,0))
            profile=[(0,0)]*3
            if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
            w.profile(1,*profile)
            if mode=='suppressed':w.suppressed.add(ENTITIES[1])
            if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
            if mode=='mold':w.profile(0,(ids['틀깨기'],0))
            for matchup in (2,3):
                assert w.multiplier(matchup)==(factor if mode.startswith('slot') and matchup==3 else 100),(name,mode,matchup)
                cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} native shared multiplier cases: Filter/Hard Rock x0.8 on super-effective matchup only, original Omniscience-only x0.75 retained, slots/suppression/acid/Mold Breaker. Fixed-point multiply modeled from native constants; no ROM/save output.')

if __name__=='__main__':main()
