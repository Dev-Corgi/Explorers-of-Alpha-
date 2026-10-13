"""ARM event paths: accepted sunshine, floor-once stats, KO and precise cures.
Native weather selection and status cures execute; UI/RNG/stat writers modeled.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):
        super().reset();self.values=[100]*4;self.base_speed=100;self.random=[];self.rolls=[];self.cures=[]
    def service(self,u,address,size,data):
        a,b,c,d=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        if address==self.calc_stat:self.ret(self.values[c-1]);return
        if address==0x022eaa98:
            self.rolls.append(('pick',a));self.ret(self.random.pop(0) if self.random else 0);return
        if address==0x022eab20:
            self.rolls.append(('chance',a));self.ret(self.probability);return
        if address in (0x02305fdc,0x023061a8,0x023063d4,0x02306258):
            if address==0x02305fdc:
                assert c==d==0 and struct.unpack('<I',bytes(u.mem_read(u.reg_read(UC_ARM_REG_SP),4)))[0]==0
            self.cures.append((address,a,b)) # Continue through real native ARM cure.
        if address==0x02305c04:self.ret(1);return
        if address in (0x022e2ad8,0x022e3ab4,0x02304a48,0x022fff4c,0x022e6798,0x0234b3a4):self.ret();return
        super().service(u,address,size,data)
    def apply_weather(self,weather,force=1):
        self.u.mem_write(DUNGEON+0xcd3a,bytes(16))
        self.u.mem_write(DUNGEON+0xcd3a+weather*2,struct.pack('<H',3000))
        return self.call('',0,force,start=0x023354c4)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'event_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'event_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record)
    def reset():
        w.reset()
        for i in range(20):w.profile(i,(0,0));w.position(i,40,25)
    def proto():w.profile(0,(ids['고대활성'],0))
    # Real accepted native weather callback; quiet queries and periodic updates
    # cannot repeatedly increase the stored stage. A forced fresh sun can.
    reset();proto();w.weather(0);w.apply_weather(1)
    assert len(w.stats)==1 and w.stats[0][:5]==(0x0231399c,ENTITIES[0],ENTITIES[0],0,1)
    for _ in range(3):w.call('ME_ApparentWeather',ENTITIES[0]);w.apply_weather(1,0)
    assert len(w.stats)==1
    w.apply_weather(1,1);assert len(w.stats)==2
    w.apply_weather(4);assert len(w.stats)==2
    w.apply_weather(1);assert len(w.stats)==3
    # Suppressed ability and suppressed weather do not award boosts.
    w.suppressed.add(ENTITIES[0]);w.apply_weather(1);assert len(w.stats)==3
    w.suppressed.clear();w.u.mem_write(DUNGEON+0xcd5d,b'\x01')
    w.apply_weather(1);assert len(w.stats)==3
    w.u.mem_write(DUNGEON+0xcd5d,b'\0');w.apply_weather(1);assert len(w.stats)==4
    # Already-sunny entry and a holder which also creates sun each award once.
    reset();proto();w.weather(1);w.call('ME_FloorEntry',ENTITIES[0]);w.call('ME_FloorEntry',ENTITIES[0]);assert len(w.stats)==1
    reset();w.profile(0,(ids['고대활성'],0),(ids['가뭄'],0));w.weather(0)
    w.call('ME_FloorEntry',ENTITIES[0]);assert len(w.stats)==1
    # Highest stat selection uses actual native stat categories and tie priority.
    for winner in range(5):
        reset();proto();w.values=[100]*4;w.base_speed=100
        if winner<4:w.values[winner]=200
        else:w.base_speed=200
        w.weather(1);w.call('ME_FloorEntry',ENTITIES[0])
        if winner==4:assert w.call('ME_GetStoredSpeed',ENTITIES[0])==11 and not w.stats
        else:
            expected=0x02313b08 if winner in (1,3) else 0x0231399c
            assert w.stats[0][0]==expected and w.stats[0][3]==int(winner>=2)
    reset();proto();w.values=[200]*4;w.base_speed=200;w.weather(1);w.call('ME_FloorEntry',ENTITIES[0]);assert w.stats[0][0]==0x0231399c and w.stats[0][3]==0
    # Opponent KOs: Moxie per KO, Soul-Heart and Protosynthesis once per action.
    reset();w.profile(0,(ids['자기과신'],0),(ids['소울하트'],0),(ids['고대활성'],0))
    for i in range(3):w.u.mem_write(ENTITIES[i]+0x25,b'\x01')
    for i in (1,2):w.u.mem_write(MONSTERS[i]+6,b'\x01');w.u.mem_write(MONSTERS[i]+0x10,bytes(2))
    token=w.call('ME_BeginAction',ENTITIES[0],20)
    w.call('ME_FaintEvent',ENTITIES[1],20,ENTITIES[0]);w.call('ME_FaintEvent',ENTITIES[2],20,ENTITIES[0]);w.call('ME_EndAction',token)
    assert len(w.stats)==4 and sum(s[3]==1 for s in w.stats)==1
    # Supersweet Syrup floor-wide foes only; caps, regrant and next floor.
    reset();w.profile(0,(ids['감미로운꿀'],0))
    for i in (1,2):w.u.mem_write(MONSTERS[i]+6,b'\x01')
    w.call('ME_FloorEntry',ENTITIES[0]);assert [struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[i]+0x2e,2)))[0] for i in (0,1,2)]==[10,9,9]
    w.call('ME_RestoreAbilities',ENTITIES[0]);w.call('ME_FloorEntry',ENTITIES[0]);assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[1]+0x2e,2)))[0]==9
    w.u.mem_write(DUNGEON+0x749,b'\x02');w.profile(0,(ids['감미로운꿀'],0));w.call('ME_FloorEntry',ENTITIES[0]);assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[1]+0x2e,2)))[0]==8
    # Slow Start changes numeric Speed exactly once; Moody selects distinct stats.
    reset();w.profile(0,(ids['슬로스타트'],0));w.call('ME_FloorEntry',ENTITIES[0]);w.call('ME_FloorEntry',ENTITIES[0]);assert w.call('ME_GetStoredSpeed',ENTITIES[0])==7
    reset();w.profile(0,(ids['변덕쟁이'],0));w.random=[4,4];w.call('ME_FloorEntry',ENTITIES[0]);assert w.call('ME_GetStoredSpeed',ENTITIES[0])==12
    assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[0]+0x2c,2)))[0]==9
    w.call('ME_FloorEntry',ENTITIES[0]);assert w.rolls==[('pick',7),('pick',6)]
    # Healer selects one eligible adjacent ally and executes actual class cures.
    reset();w.profile(0,(ids['치유의마음'],0));w.position(0,10,10);w.position(1,11,11);w.position(2,11,10)
    w.u.mem_write(MONSTERS[1]+0xbd,b'\x05');w.u.mem_write(MONSTERS[1]+0xbf,b'\x05');w.u.mem_write(MONSTERS[1]+0xd0,b'\x02')
    w.u.mem_write(MONSTERS[2]+0xbf,b'\x02');w.random=[0]
    assert w.call('ME_HealAlly',ENTITIES[0],limit=500000)==1
    assert all(bytes(w.u.mem_read(MONSTERS[1]+offset,1))==b'\0' for offset in (0xbd,0xbf,0xd0))
    assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[1]+0x10,2)))[0]==100 # Napping cure grants no free HP.
    assert bytes(w.u.mem_read(MONSTERS[2]+0xbf,1))==b'\x02'
    assert w.rolls==[('chance',50),('pick',2)] and len(w.cures)==3
    for offset,value in ((0xbd,2),(0xbd,4),(0xd0,5),(0xc4,2)):
        reset();w.profile(0,(ids['치유의마음'],0));w.position(0,10,10);w.position(1,11,10);w.u.mem_write(MONSTERS[1]+offset,bytes([value]))
        assert w.call('ME_HealAlly',ENTITIES[0])==0 and not w.rolls
    for mode in ('distant','enemy','dead','suppressed','failed'):
        reset();w.profile(0,(ids['치유의마음'],0));w.position(0,10,10);w.position(1,11,10);w.u.mem_write(MONSTERS[1]+0xbf,b'\x02')
        if mode=='distant':w.position(1,12,10)
        if mode=='enemy':w.u.mem_write(MONSTERS[1]+6,b'\x01')
        if mode=='dead':w.u.mem_write(MONSTERS[1]+0x10,bytes(2))
        if mode=='suppressed':w.suppressed.add(ENTITIES[0])
        if mode=='failed':w.probability=0
        assert w.call('ME_HealAlly',ENTITIES[0])==0 and not w.cures
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase3 events ARM: accepted native sunlight/quiet updates/suppression, entry-once/highest-stat, KO scope, floor stats and precise native Healer cures. No ROM/save output.')

if __name__=='__main__':main()
