"""Ordinary numeric stat rules and reactive boosts, using linked ARM code.
Native physical/special stored-stat writers are modeled, including their ABI.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'numeric_stats_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'numeric_stats_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    def setup(name=None,mode='slot3',extras=()):
        w.reset()
        # This family needs only source/target. Keep the other dungeon slots
        # empty instead of repeatedly allocating eighteen irrelevant profiles.
        w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0))
        w.u.mem_write(MONSTERS[0]+6,b'\x01') # enemy source
        profile=[(0,0)]*3
        if name and mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        for i,extra in enumerate(extras):profile[i]=(ids[extra],0)
        w.profile(1,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[1])
        if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
        if mode=='mold':w.profile(0,(ids['틀깨기'],0))
    def stored(stat):
        return w.call('ME_GetStoredSpeed',ENTITIES[1]) if stat==4 else struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[1]+(0x2c if stat==5 else 0x2e),2)))[0]
    def set_stored(stat,value):
        if stat==4:w.call('ME_SetStoredSpeed',ENTITIES[1],value)
        else:w.u.mem_write(MONSTERS[1]+(0x2c if stat==5 else 0x2e),struct.pack('<H',value))
    def change(stat,delta,self_source=False):
        return w.call('ME_ChangeStat',ENTITIES[1] if self_source else ENTITIES[0],ENTITIES[1],stat,delta)
    modes=('none','slot1','slot2','slot3','suppressed','acid','mold')
    for name in ('클리어바디','하얀연기','단순','심술꾸러기','날카로운눈'):
        for mode in modes:
            for stat in (4,5,6):
                setup(name,mode);active=mode.startswith('slot')
                delta=1 if active and name=='심술꾸러기' else -2 if active and name=='단순' else -1
                if active and (name in ('클리어바디','하얀연기') or name=='날카로운눈' and stat==5):delta=0
                assert change(stat,-1)==int(delta!=0),(name,mode,stat)
                assert stored(stat)==10+delta,(name,mode,stat,stored(stat))
                cases+=1
    for name,index in (('오기',0),('승기',1)):
        for mode in modes:
            for stat in (4,5,6):
                setup(name,mode);change(stat,-1)
                reactive=mode.startswith('slot') or mode=='mold'
                assert len(w.stats)==int(reactive),(name,mode,stat,w.stats)
                if reactive:assert w.stats[0][:5]==(0x0231399c,ENTITIES[1],ENTITIES[1],index,2)
                cases+=1
    for stat in (4,5,6):
        for name,expected in (('단순',12),('심술꾸러기',9)):
            setup(name);change(stat,1);assert stored(stat)==expected;cases+=1
            setup(name);change(stat,1,True);assert stored(stat)==expected;cases+=1
        setup('단순',extras=('심술꾸러기',));change(stat,-1);assert stored(stat)==12;cases+=1
        for name in ('클리어바디','하얀연기'):
            setup(name);assert change(stat,-1,True)==1 and stored(stat)==9;cases+=1
        for floor in (4,16):
            setup('오기',extras=('승기',));set_stored(stat,floor)
            assert change(stat,-1 if floor==4 else 1)==0 and not w.stats;cases+=1
        setup('오기',extras=('승기','클리어바디'));assert change(stat,-1)==0 and not w.stats;cases+=1
        setup('오기',extras=('승기','심술꾸러기'));change(stat,-1);assert stored(stat)==11 and not w.stats;cases+=1
        setup('오기',extras=('승기',));change(stat,-1,True);assert not w.stats;cases+=1
        setup('오기',extras=('승기',));w.u.mem_write(MONSTERS[0]+6,b'\x00');change(stat,-1);assert not w.stats;cases+=1
        setup('오기',extras=('승기',));change(stat,-1);assert len(w.stats)==2;cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} ordinary numeric Speed/Accuracy/Evasion cases: three slots, suppression/acid/Mold Breaker, protection/self drops, Simple/Contrary, actual-drop-only Defiant/Competitive, caps and allied sources. Native reactive stat writers modeled; no ROM/save output.')

if __name__=='__main__':main()
