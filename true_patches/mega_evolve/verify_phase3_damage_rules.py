"""Shared new final damage rules and resolved-target guard ARM checks.
Category/range catalogues come from the validated ROM; native damage/UI are
outside this suite. The target hook runs its actual ABI and continuation.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3_weight_wind import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,BUFFER,STACK
from .phase3 import load
from .phase3_moves import load as move_data,validate_rom
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):super().reset();self.chance_calls=[]
    def service(self,u,address,size,data):
        if address==0x020151c8:
            self.ret(self.categories[u.reg_read(UC_ARM_REG_R0)]);return
        if address==0x022eab20:
            self.chance_calls.append(u.reg_read(UC_ARM_REG_R0));self.ret(self.probability);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());validate_rom(rom)
    manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'damage_rules_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'damage_rules_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};catalogue=move_data();w=World(rom,record)
    w.categories={r['id']:r['category'] for r in catalogue['target_rules']}
    choose=lambda category,range_:next(r['id'] for r in catalogue['target_rules'] if r['category']==category and r['range']==range_ and r['id']>0)
    physical=choose(0,0);remote=choose(0,4);special=choose(1,0);support=choose(2,0)
    cases=0
    def reset(name=None,holder=0,mode='slot3',friendly=False):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+12,bytes(17*4))
        for i in range(3):w.profile(i,(0,0));w.position(i,10+i,10)
        w.position(2,11,11)
        w.u.mem_write(MONSTERS[1]+6,bytes([0 if friendly else 1]))
        profile=[(0,0)]*3
        if name and mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        w.profile(holder,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[holder])
        if mode=='acid':w.u.mem_write(MONSTERS[holder]+0xd8,b'\x04')
        if mode=='mold':w.profile(0,(ids['틀깨기'],0))
    def damage(type_,move=physical):return w.damage(type_,move)
    for name,type_ in (('강철술사',17),('용의턱',15),('트랜지스터',5),('불꽃의갈기',2)):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            reset(name,mode=mode)
            assert damage(type_)==(120 if mode.startswith('slot') else 100),(name,mode)
            assert damage(1)==100 and damage(type_,support)==100;cases+=3
    for name,type_ in (('드래곤스킨',15),('스카이스킨',10),('페어리스킨',18),('프리즈스킨',6),('일렉트릭스킨',5),('노말스킨',1)):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            reset(name,mode=mode);token=w.call('ME_BeginAction',ENTITIES[0],physical)
            source_type=2 if name=='노말스킨' else 1
            assert w.call('ME_ConvertType',ENTITIES[0],source_type,w.move(physical))==(type_ if mode.startswith('slot') else source_type)
            assert damage(type_)==(120 if mode.startswith('slot') else 100)
            w.call('ME_EndAction',token);cases+=2
    reset('노말스킨');token=w.call('ME_BeginAction',ENTITIES[0],355)
    for move in (355,405):
        assert w.call('ME_ConvertType',ENTITIES[0],2,w.move(move))==2;cases+=1
    w.call('ME_EndAction',token)
    for name,status,move in (('독폭주',2,physical),('독폭주',3,physical),('열폭주',1,special)):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            reset(name,mode=mode);w.u.mem_write(MONSTERS[0]+0xbf,bytes([status]))
            assert damage(1,move)==(150 if mode.startswith('slot') else 100),(name,mode)
            assert damage(1,special if move==physical else physical)==100;cases+=2
    for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
        reset('파동의방호',1,mode)
        assert damage(1)==(50 if mode.startswith('slot') else 100)
        assert damage(1,remote)==100 and damage(1,special)==100
        w.position(1,14,10);assert damage(1)==100;cases+=4
    reset('파동의방호',1);assert w.damage(1,physical,value=1)==1;cases+=1
    reset('내열',1);assert w.damage(6,physical,value=1)==1;cases+=1
    reset('텔레파시',1,friendly=True);assert w.damage(1,physical,value=1)==0;cases+=1
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        reset('파워스폿',2,mode,friendly=True)
        assert damage(1)==(120 if mode.startswith('slot') else 100)
        w.position(2,15,10);assert damage(1)==100;cases+=2
    reset('파워스폿',2,friendly=True);w.profile(1,(ids['파워스폿'],0));assert damage(1)==120;cases+=1
    reset('파워스폿');assert damage(1)==100;cases+=1
    for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
        reset('텔레파시',1,mode,friendly=True)
        for move in (physical,special,support):
            assert w.call('ME_TargetBlocked',ENTITIES[0],ENTITIES[1],w.move(move))==int(mode.startswith('slot') and move!=support)
            cases+=1
        w.u.mem_write(MONSTERS[1]+6,b'\x01');assert w.call('ME_TargetBlocked',ENTITIES[0],ENTITIES[1],w.move(physical))==0;cases+=1
    for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
        reset('미라클스킨',1,mode)
        assert w.call('ME_TargetBlocked',ENTITIES[0],ENTITIES[1],w.move(support))==int(mode.startswith('slot'))
        assert w.chance_calls==([25] if mode.startswith('slot') else [])
        assert w.call('ME_TargetBlocked',ENTITIES[0],ENTITIES[1],w.move(physical))==0;cases+=2
    reset('미라클스킨',1);w.probability=0;assert w.call('ME_TargetBlocked',ENTITIES[0],ENTITIES[1],w.move(support))==0;cases+=1
    reset('미라클스킨',1)
    for move in catalogue['global_status_moves']:
        assert w.call('ME_TargetBlocked',ENTITIES[0],ENTITIES[1],w.move(move))==0
        cases+=1
    assert not w.chance_calls
    reset('미라클스킨',1,friendly=True);assert w.call('ME_TargetBlocked',ENTITIES[0],ENTITIES[1],w.move(support))==0;cases+=1
    assert w.call('ME_TargetBlocked',ENTITIES[1],ENTITIES[1],w.move(support))==0;cases+=1
    # The actual guard must jump past the entire handler (additional effects),
    # using resolved r4 rather than stale pre-redirection r6.
    reset('텔레파시',1,friendly=True)
    regs={UC_ARM_REG_R4:ENTITIES[1],UC_ARM_REG_R6:ENTITIES[2],UC_ARM_REG_R8:w.move(physical),UC_ARM_REG_R9:ENTITIES[0]}
    w.call('',123,456,789,42,start=0x0232eaac,registers=regs)
    assert w.continued[-1]==(0x02332818,123,STACK);cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} shared damage/target guard cases: type and status boosters, native-range Aura Guard, nonstacking adjacent Power Spot, full Telepathy handler skip, Miracle Skin 25% and weather/self/ally exclusions, slots/suppression/Mold Breaker. No ROM/save output.')

if __name__=='__main__':main()
