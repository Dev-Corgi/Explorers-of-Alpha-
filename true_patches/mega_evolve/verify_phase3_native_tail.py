"""Live native normal damage/stage/recovery consumers, no ROM output."""
import hashlib,struct
from .verify_phase3_native_coefficients import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,BUFFER,STACK
from .phase3 import load
from .phase3_moves import load as moves
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def multiplier(self,start,end,type_,holder=1):
        out=BUFFER+0x400;self.u.mem_write(out,struct.pack('<II',0,100<<16))
        self.segment(start,{end},{UC_ARM_REG_R7:BUFFER+0x480,UC_ARM_REG_R8:type_,UC_ARM_REG_R9:ENTITIES[1],
            UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R11:out})
        return self.call('',out,start=0x02001cb0)
    def sound_tail(self,move):
        context=self.call('ME_EnterCalculation',ENTITIES[0],ENTITIES[1])
        self.u.mem_write(BUFFER+0x400,struct.pack('<5I',100,0,0,0,0));self.u.mem_write(STACK+0xf4,struct.pack('<I',move))
        self.u.mem_write(STACK+0xc,struct.pack('<I',1))
        self.segment(0x0230d03c,{self.symbols['ME_DamageTailHook']},{UC_ARM_REG_R8:BUFFER+0x400,
            UC_ARM_REG_R9:ENTITIES[1],UC_ARM_REG_R10:ENTITIES[0]})
        result=struct.unpack('<I',bytes(self.u.mem_read(BUFFER+0x400,4)))[0]
        self.call('ME_LeaveCalculation',context);return result

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest();rom=NintendoDSRom(SOURCE.read_bytes())
    manifest=dict(load_module_manifest(MODULE),phase=3);record=apply_phase1(rom,MODULE,manifest,None,{'native_tail_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'native_tail_test':True})
    w=World(rom,record);ids={a['key']:a['id'] for a in load()['abilities']};cases=0
    w.ranges={r['id']:r['range'] for r in moves()['target_rules']}
    def setup(name,holder,mode='slot3'):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0));w.position(i,10+i,10)
        w.u.mem_write(MONSTERS[1]+6,b'\x01');p=[(0,0)]*3
        if mode!='none':p[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        w.profile(holder,*p)
        if mode=='suppressed':w.suppressed.add(ENTITIES[holder])
        if mode=='acid':w.u.mem_write(MONSTERS[holder]+0xd8,b'\x04')
        if mode=='mold':w.profile(0,(ids['틀깨기'],0))
    for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
        for name,start,end in (('두꺼운지방',0x0230b104,0x0230b14c),('내열',0x0230b198,0x0230b1dc)):
            setup(name,1,mode);active=mode.startswith('slot')
            got=w.multiplier(start,end,2);assert got==(50 if active else 100),(name,mode,got)
            if name=='두꺼운지방':assert w.multiplier(start,end,6)==(50 if active else 100)
            else:assert w.damage(6)==(50 if active else 100)
            assert w.multiplier(start,end,1)==100;cases+=3
        setup('퍼코트',1,mode);assert w.coefficient()==(50 if mode.startswith('slot') else 100);cases+=1
        setup('펑크록',1,mode);got=w.sound_tail(217);assert got==(50 if mode.startswith('slot') else 100),('Punk Rock',mode,got);cases+=1
    setup('펑크록',0);assert w.sound_tail(217)==120 and w.sound_tail(20)==100;cases+=2
    setup('적응력',0);got=w.multiplier(0x0230b584,0x0230b5cc,1)
    assert got in (169,170),('Adaptability native x1.7',got);cases+=1
    setup('멀티타입',0);w.u.mem_write(MONSTERS[0]+2,struct.pack('<H',537));w.profile(0,(ids['멀티타입'],0))
    assert w.coefficient()==120;cases+=1
    for name,weather,start,end in (('젖은접시',4,0x02311174,0x0231119c),('아이스바디',5,0x023111c8,0x023111f4)):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            setup(name,0,mode);w.weather(weather)
            w.segment(start,{end},{UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R4:100,UC_ARM_REG_R1:3})
            got=w.u.reg_read(UC_ARM_REG_R4);assert got==(50 if mode.startswith('slot') else 100),(name,mode,got,w.call('ME_ApparentWeather',ENTITIES[0]))
            w.weather(0);w.segment(start,{end},{UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R4:100,UC_ARM_REG_R1:3});assert w.u.reg_read(UC_ARM_REG_R4)==100;cases+=2
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        setup('정의의마음',1,mode);w.u.mem_write(BUFFER+0x400,bytes(20));w.u.mem_write(BUFFER+0x40c,b'\x10')
        w.u.mem_write(STACK,bytes(8))
        w.segment(0x023c0428,{0x023c0468,0x023093d8},{UC_ARM_REG_R8:ENTITIES[0],UC_ARM_REG_R7:ENTITIES[1],UC_ARM_REG_R6:BUFFER+0x400})
        assert len(w.stats)==int(mode.startswith('slot'))
        if w.stats:assert w.stats[-1][3:5]==(0,3)
        setup('괴력집게',1,mode)
        assert w.call('ME_AttackDropTrait',ENTITIES[0],ENTITIES[1])==int(mode.startswith('slot'))
        assert w.call('ME_AttackDropTrait',ENTITIES[1],ENTITIES[1])==0;cases+=3
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} live normal tail cases: Thick Fat/Heatproof x0.5, Fur Coat physical x0.5, Punk Rock sound attack/defense, Multitype original Arceus x1.2, native rain/snow recovery active gate, Justified +3, Hyper Cutter self-drop exception. Native fixed multiply; cache/writer services modeled; no ROM/save output.')
if __name__=='__main__':main()
