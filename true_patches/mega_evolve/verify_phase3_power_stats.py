"""Pure/Huge Power physical stat service and old core boost removal in ARM.
The established native base-stat provider is modeled; entry wrapper executes.
"""
from __future__ import annotations
import hashlib
from .verify_phase3 import World
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'power_stats_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'power_stats_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    helper=record.data[0]['base_stats_helpers']['from_monster']
    def setup(name,mode='slot3'):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0))
        profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        w.profile(0,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[0])
        if mode=='acid':w.u.mem_write(MONSTERS[0]+0xd8,b'\x04')
    for name in ('순수한힘','천하장사'):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            setup(name,mode)
            assert w.call('',MONSTERS[0],0,0,start=helper)==101
            context=w.call('ME_EnterCalculation',ENTITIES[0],ENTITIES[1])
            assert w.call('',MONSTERS[0],0,0,start=helper)==(121 if mode.startswith('slot') else 101),(name,mode)
            assert w.call('',MONSTERS[0],1,0,start=helper)==101 and w.call('',MONSTERS[0],0,1,start=helper)==101
            w.call('ME_LeaveCalculation',context);cases+=4
    setup('순수한힘');w.profile(0,(ids['순수한힘'],0),(ids['천하장사'],0))
    context=w.call('ME_EnterCalculation',ENTITIES[0],ENTITIES[1]);assert w.call('',MONSTERS[0],0,0,start=helper)==145;cases+=1
    w.profile(1,(ids['천진'],0));assert w.call('',MONSTERS[0],0,0,start=helper)==101;cases+=1
    w.profile(0,(ids['순수한힘'],0),(ids['틀깨기'],0));assert w.call('',MONSTERS[0],0,0,start=helper)==121;cases+=1
    w.call('ME_LeaveCalculation',context)
    setup('순수한힘')
    assert w.call('ME_LegacyAbilityActive',ENTITIES[0],34,0x0230c6c4)==0
    assert w.call('ME_LegacyAbilityActive',ENTITIES[0],34,0x0230c6d8)==0
    assert w.call('ME_LegacyAbilityActive',ENTITIES[0],34,0)==1;cases+=3
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} Pure/Huge Power cases: physical attack x1.2, three slots/suppression/acid, special/defense/outside-damage exclusion, distinct traits compose, Unaware/Mold Breaker, exact old-boost query removal. Base-stat provider modeled; no ROM/save output.')

if __name__=='__main__':main()
