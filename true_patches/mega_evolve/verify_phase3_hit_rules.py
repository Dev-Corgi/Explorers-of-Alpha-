"""Shared hit-response conditions and action/floor lifetime in ARM runtime.
Native stat writers, fixed damage and RNG are modeled at their established ABI.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,STACK,BUFFER
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'hit_rules_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'hit_rules_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    def setup(name,mode='slot3',friendly=False):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0));w.position(i,10+i,10)
        w.u.mem_write(MONSTERS[1]+6,bytes([0 if friendly else 1]))
        profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        w.profile(1,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[1])
        if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
        # The native hit hook runs inside UseMove's action boundary. Standalone
        # cases need the same boundary for once-per-action traits to trigger.
        w.call('ME_BeginAction',ENTITIES[0],20)
    def hit(previous=100,current=90,type_=1):
        w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',current))
        w.u.mem_write(STACK,struct.pack('<I',20))
        w.call('ME_HitEvent',ENTITIES[0],ENTITIES[1],previous,type_)
    for name in ('깨어진갑옷','지구력','주눅','까칠한피부'):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            setup(name,mode);token=w.call('ME_BeginAction',ENTITIES[0],20)
            for _ in range(3):hit(type_=16)
            active=mode.startswith('slot')
            if name=='깨어진갑옷':
                assert len(w.stats)==int(active)
                if active:assert w.stats[0][:5]==(0x02313814,ENTITIES[1],ENTITIES[1],0,1)
                assert w.call('ME_GetStoredSpeed',ENTITIES[1])==(11 if active else 10)
            if name=='지구력':
                assert len(w.stats)==int(active)
                if active:assert w.stats[0][:5]==(0x02313b08,ENTITIES[1],ENTITIES[1],0,1)
            if name=='주눅':assert w.call('ME_GetStoredSpeed',ENTITIES[1])==(13 if active else 10)
            if name=='까칠한피부':assert len(w.thorns)==int(active)
            w.call('ME_EndAction',token);cases+=1
        setup(name);w.category=2;hit(type_=16);assert not w.stats and not w.thorns and w.call('ME_GetStoredSpeed',ENTITIES[1])==10;cases+=1
    for category in (0,1):
        setup('깨어진갑옷');w.category=category;hit();assert len(w.stats)==int(category==0),(category,w.stats);cases+=1
    for type_ in (12,14,16,1):
        setup('주눅');hit(type_=type_);assert w.call('ME_GetStoredSpeed',ENTITIES[1])==(13 if type_!=1 else 10);cases+=1
    setup('지구력');w.category=1;hit();assert len(w.stats)==1;cases+=1
    setup('지구력');hit(current=100);assert not w.stats;cases+=1
    setup('까칠한피부');w.position(1,15,10);hit();assert not w.thorns;cases+=1
    setup('까칠한피부');w.category=1;hit();assert not w.thorns;cases+=1
    for name in ('지구력','주눅'):
        setup(name)
        for action in range(2):
            token=w.call('ME_BeginAction',ENTITIES[0],20);hit(type_=16);w.call('ME_EndAction',token)
        assert len(w.stats)==2 if name=='지구력' else w.call('ME_GetStoredSpeed',ENTITIES[1])==16
        cases+=1
    for friendly in (False,True):
        setup('발끈',friendly=friendly)
        for _ in range(2):
            token=w.call('ME_BeginAction',ENTITIES[0],20);hit(previous=60,current=50);w.call('ME_EndAction',token)
        assert len(w.stats)==int(not friendly)
        if not friendly:assert w.stats[0][:5]==(0x0231399c,ENTITIES[1],ENTITIES[1],1,1)
        cases+=1
    for previous,current in ((50,40),(70,60),(60,0)):
        setup('발끈');hit(previous,current);assert not w.stats;cases+=1
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        setup('점착',mode);hit();assert w.call('ME_GetStoredSpeed',ENTITIES[0])==(9 if mode.startswith('slot') else 10);cases+=1
    setup('점착');w.probability=0;hit();assert w.call('ME_GetStoredSpeed',ENTITIES[0])==10;cases+=1
    setup('점착');w.position(1,15,10);hit();assert w.call('ME_GetStoredSpeed',ENTITIES[0])==10;cases+=1
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        setup('분노의경혈',mode)
        info=bytearray(20);struct.pack_into('<I',info,0,10);info[12]=1;info[14]=1
        w.u.mem_write(BUFFER+0x400,bytes(info));w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',90))
        w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_ReportHit',ENTITIES[0],ENTITIES[1],100,BUFFER+0x400)
        assert len(w.stats)==(2 if mode.startswith('slot') else 0),(mode,w.stats)
        if w.stats:assert [r[3:5] for r in w.stats]==[(0,3),(1,3)]
        cases+=1
    # HP can be restored by a Reviver before the native hit callback. Its actual
    # positive damage packet still triggers once-per-action responses.
    setup('지구력');info=bytearray(20);struct.pack_into('<I',info,0,10);info[12]=1
    w.u.mem_write(BUFFER+0x400,bytes(info));w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',100))
    w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_ReportHit',ENTITIES[0],ENTITIES[1],100,BUFFER+0x400)
    assert len(w.stats)==1;cases+=1
    setup('지구력');w.u.mem_write(BUFFER+0x400,bytes(20));w.u.mem_write(STACK,struct.pack('<I',20))
    w.call('ME_ReportHit',ENTITIES[0],ENTITIES[1],100,BUFFER+0x400);assert not w.stats;cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} shared hit responses: Weak Armor/Stamina/Rattled/Rough Skin action dedup, status/miss/range/category exclusions, new-action rearm, enemy-only floor-once Berserk and Sticky Hold 12% Speed drop. Native writers/damage/RNG modeled; no ROM/save output.')

if __name__=='__main__':main()
