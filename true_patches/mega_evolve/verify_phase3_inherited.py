"""Inherited normal effects retain native consumers and extended lookup ABI.
This does not assert that each full battle was emulated. Redirect eligibility
is modeled; its original ITCM ability queries and cache writes execute.
"""
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON
from .phase3 import load
from .native_consumers import build,load_inventory
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def __init__(self,rom,record):
        super().__init__(rom,record)
        self.u.mem_map(0x01ff0000,0x10000)
        self.u.mem_write(0x01ff8000,bytes(rom.arm9[0xb3380:0xbb380]))
    def service(self,u,address,size,data):
        if address==0x01ffbf78:self.ret(1);return # unrelated native redirect eligibility
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest();assert load_inventory()==build()
    inventory=load_inventory();manual={'습기','괴짜','일루전'}
    assert all(a['consumers'] or a['key'] in manual for a in inventory['abilities'] if a['candidate']=='reuse_candidate')
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'inherited_test':True});verify_phase1(rom,MODULE,manifest,record,{'inherited_test':True})
    w=World(rom,record);abilities=load()['abilities'];ids={a['key']:a['id'] for a in abilities};cases=0
    w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4));w.profile(1,(0,0))
    for a in abilities:
        for slot in range(3):
            p=[(0,0)]*3;p[slot]=(a['id'],0);w.profile(0,*p)
            assert w.call('ME_AbilityActive',ENTITIES[0],a['id'])==1
            if a['legacy_effect_id']:
                assert w.call('',ENTITIES[0],a['legacy_effect_id'],start=0x02301d10,registers={UC_ARM_REG_R3:0x12345678})==1
                assert w.u.reg_read(UC_ARM_REG_R3)==0x12345678
            w.suppressed.add(ENTITIES[0]);assert not w.call('ME_AbilityActive',ENTITIES[0],a['id']);w.suppressed.clear()
            cases+=3
    # Native ITCM record updater is a real consumer outside ov29/36. Its branch
    # destinations resolve correctly after the ROM startup copy to 0x01ff8000.
    for name,offset in (('피뢰침',0),('마중물',8)):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4));w.profile(0,(0,0));p=[(0,0)]*3
            if mode!='none':p[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
            w.profile(1,*p);w.u.mem_write(MONSTERS[1]+6,b'\x01')
            if mode=='suppressed':w.suppressed.add(ENTITIES[1])
            if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
            w.call('',ENTITIES[0],ENTITIES[1],start=0x01ffbd20)
            cached=struct.unpack('<I',bytes(w.u.mem_read(DUNGEON+0x198f4+offset,4)))[0]
            assert cached==(ENTITIES[1] if mode.startswith('slot') else 0),(name,mode,hex(cached));cases+=1
    for name,weather,strong in (('가뭄',1,0),('잔비',4,0),('모래날림',2,0),('눈퍼뜨리기',5,0),
                               ('시작의바다',4,1),('끝의대지',1,1),('델타스트림',0,1)):
        for slot in range(3):
            w.reset();w.u.mem_write(DUNGEON+0x12b78+4,bytes(19*4));p=[(0,0)]*3;p[slot]=(ids[name],0);w.profile(0,*p)
            w.call('ME_FloorEntry',ENTITIES[0],limit=500000)
            assert w.call('ME_ApparentWeather',ENTITIES[0])==weather,(name,slot)
            assert w.call('ME_WeatherStrength',ENTITIES[0])==strong;cases+=2
    w.reset();w.u.mem_write(DUNGEON+0x12b78+4,bytes(19*4));w.profile(0,(ids['재생력'],0))
    w.u.mem_write(MONSTERS[0]+0x10,struct.pack('<H',20));w.call('ME_FloorEntry',ENTITIES[0])
    assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[0]+0x10,2)))[0]==100;cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} inherited routing cases: all206 assigned ordinary identities in allthree slots, native legacy-query ABI and suppression, persistent consumer provenance including copied ITCM, Lightning Rod/Storm Drain native cache registration. Unchanged effect bodies inherited; redirect eligibility modeled. No ROM/save output.')
if __name__=='__main__':main()
