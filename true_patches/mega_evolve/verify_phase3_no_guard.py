"""No Guard native hit-check boundary, preserving damage/type immunities and
the original miss handler when neither side has an applicable ability.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,STACK
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'no_guard_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'no_guard_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    for holder in (0,1):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
            for accuracy in (0,1):
                w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
                for i in range(2):w.profile(i,(0,0))
                profile=[(0,0)]*3
                if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids['노가드'],0)
                w.profile(holder,*profile)
                if mode=='suppressed':w.suppressed.add(ENTITIES[holder])
                if mode=='acid':w.u.mem_write(MONSTERS[holder]+0xd8,b'\x04')
                if mode=='mold':
                    if holder==1:w.profile(0,(ids['틀깨기'],0))
                    else:w.profile(0,(ids['노가드'],0),(ids['틀깨기'],0))
                forced=mode.startswith('slot') or mode=='mold' and holder==0
                move=w.move(20);values=(11,22,33,44,55);w.u.mem_write(STACK,struct.pack('<5I',*values))
                result=w.call('',ENTITIES[0],ENTITIES[1],move,accuracy,start=0x02323c48)
                assert result==(1 if forced else 77),(holder,mode,accuracy,result)
                calls=[c for c in w.prior_calls if c[0]=='PRIOR_HIT_CHECK']
                assert len(calls)==int(not forced)
                if calls:assert calls==[('PRIOR_HIT_CHECK',[ENTITIES[0],ENTITIES[1],move,accuracy],values)]
                cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} native No Guard hit-check cases: attacker/defender three slots, both accuracy passes, suppression/acid/Mold Breaker, original handler/stack passthrough. Separate damage/type-immunity handlers retained; no ROM/save output.')

if __name__=='__main__':main()
