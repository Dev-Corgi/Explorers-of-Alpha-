"""Native Guts physical numerator/denominator and revised Dry Skin rules."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3_native_immunity import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,STACK
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def service(self,u,address,size,data):
        if address in (0x023023c0,0x0234b350,0x022e6130):self.ret();return
        super().service(u,address,size,data)
    def guts(self):
        self.u.mem_write(STACK+0xf4,struct.pack('<I',20))
        self.segment(0x0230c63c,{0x0230c6b8},{UC_ARM_REG_R4:100,UC_ARM_REG_R9:ENTITIES[1],
            UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R11:1})
        return self.u.reg_read(UC_ARM_REG_R4),self.u.reg_read(UC_ARM_REG_R11)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'guts_dry_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'guts_dry_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    def setup(name,holder,mode):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0))
        profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        w.profile(holder,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[holder])
        if mode=='acid':w.u.mem_write(MONSTERS[holder]+0xd8,b'\x04')
        if mode=='mold':w.profile(0,(ids['틀깨기'],0))
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        for status,category in ((0,0),(2,0),(3,0),(1,0),(2,1)):
            setup('근성',0,mode);w.category=category;w.u.mem_write(MONSTERS[0]+0xbf,bytes([status]))
            assert w.guts()==((300,2) if mode.startswith('slot') and status and not category else (100,1)),(mode,status,category,w.guts())
            cases+=1
    for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
        for weather in (0,1,4):
            setup('건조피부',1,mode);w.weather(weather)
            assert w.damage(2)==(120 if mode.startswith('slot') and weather==1 else 100),(mode,weather)
            assert w.damage(1)==100;cases+=2
    setup('건조피부',0,'slot3')
    for caller in (0x0230b50c,0x02310310):assert w.call('ME_LegacyAbilityActive',ENTITIES[0],85,caller)==0;cases+=1
    for caller in (0x0230935c,0x023111a8,0):assert w.call('ME_LegacyAbilityActive',ENTITIES[0],85,caller)==1;cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} Guts/Dry Skin cases: real physical-category/negative-status gate, Guts exact ratio x3/2, Dry Skin sunny-only fire x1.2, old fire/sun-chip queries removed while water/rain queries retained, slots/suppression/Mold Breaker. Cache/UI/base category modeled; no ROM/save output.')

if __name__=='__main__':main()
