"""Run the existing Alpha coefficient owner with extended native queries.
Threat detection and messages are modeled; the original coefficient arithmetic,
Full-HP comparison, held-item test and native query ABI execute.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3_native_immunity import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,BUFFER
from .phase3 import load
from .phase3_moves import load as move_data
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):super().reset();self.threat=1;self.threat_calls=[]
    def service(self,u,address,size,data):
        if address in (0x0234b350,0x0234b084):self.ret();return
        if address==0x022fb10c:
            self.threat_calls.append([u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)])
            self.ret(self.threat);return
        if address==0x02013840:
            self.ret(self.ranges[struct.unpack('<H',bytes(u.mem_read(u.reg_read(UC_ARM_REG_R0)+4,2)))[0]]<<4);return
        if address==0x023360fc:
            x,y=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
            ptr=next((e for e in ENTITIES[:3] if struct.unpack('<2h',bytes(u.mem_read(e+4,4)))==(x,y)),0)
            u.mem_write(BUFFER+0x280,bytes(20));u.mem_write(BUFFER+0x28c,struct.pack('<I',ptr));self.ret(BUFFER+0x280);return
        super().service(u,address,size,data)
    def coefficient(self,move=20):
        self.segment(0x023af81c,{0x023b0430},{UC_ARM_REG_R3:100,UC_ARM_REG_R7:100,UC_ARM_REG_R4:ENTITIES[1],
            UC_ARM_REG_R9:ENTITIES[0],UC_ARM_REG_R8:self.move(move)})
        return self.u.reg_read(UC_ARM_REG_R7)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'native_coefficient_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'native_coefficient_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    w.ranges={r['id']:r['range'] for r in move_data()['target_rules']}
    def setup(name,holder,mode='slot3'):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0))
        w.position(0,10,10);w.position(1,11,10)
        profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        w.profile(holder,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[holder])
        if mode=='acid':w.u.mem_write(MONSTERS[holder]+0xd8,b'\x04')
        if mode=='mold':w.profile(0,(ids['틀깨기'],0))
    for name,holder,amount in (('통찰',0,120),('위험예지',0,150),('멀티스케일',1,50),('시간벌기',1,80)):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            setup(name,holder,mode)
            if name=='통찰':w.u.mem_write(MONSTERS[1]+0x62,b'\x01')
            assert w.coefficient()==(amount if mode.startswith('slot') else 100),(name,mode,w.coefficient())
            cases+=1
    setup('통찰',0);assert w.coefficient()==100;cases+=1
    setup('위험예지',0);w.threat=0;assert w.coefficient()==100;cases+=1
    assert w.threat_calls==[[ENTITIES[0],ENTITIES[1],1]]
    for hp,maxhp,bonus,expected in ((99,100,0,100),(110,100,10,50),(100,100,10,100)):
        setup('멀티스케일',1);w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<hhhh',hp,maxhp,0,bonus))
        assert w.coefficient()==expected;cases+=1
    setup('멀티스케일',1,'mold');assert w.coefficient()==100;cases+=1
    for name,weather in (('쓱쓱',4),('엽록소',1),('곡예',0)):
        setup(name,0);w.weather(weather);assert w.coefficient()==100;cases+=1
    setup('곡예',0);assert w.call('ME_GetSpeed',ENTITIES[0],100,0,0)==200
    assert w.call('ME_GetStoredSpeed',ENTITIES[0])==10
    w.u.mem_write(MONSTERS[0]+0x62,b'\x01');assert w.call('ME_GetSpeed',ENTITIES[0],100,0,0)==100;cases+=3
    for name,move in (('옹골찬턱',198),('예리함',18),('메가런처',42),('단단한발톱',20)):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
            setup(name,0,mode);assert w.coefficient(move)==(120 if mode.startswith('slot') else 100),(name,mode,w.coefficient(move));cases+=1
    remote=next(r['id'] for r in move_data()['target_rules'] if r['range']==4 and r['category']==0)
    setup('애널라이즈',0);assert w.coefficient(remote)==120;assert w.coefficient(20)==100;cases+=2
    for type_ in (9,13,17,1):
        setup('모래의힘',0);w.weather(2);w.u.mem_write(0x023af5e0,struct.pack('<I',type_))
        assert w.coefficient()==(120 if type_!=1 else 100);cases+=1
    setup('프렌드가드',0);w.position(0,12,10);assert w.coefficient()==80;cases+=1
    w.position(0,15,10);assert w.coefficient()==100;cases+=1
    # The native caller stores a coefficient in r3 across a two-argument query.
    setup('멀티스케일',1)
    for address in (0x02301d10,0x02301d78):
        assert w.call('',ENTITIES[1],12,start=address,registers={UC_ARM_REG_R3:0x12345678})==1
        assert w.u.reg_read(UC_ARM_REG_R3)==0x12345678;cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} native coefficient cases: Frisk x1.2, Anticipation x1.5, native Multiscale full HP/Mold Breaker, Stall x0.8, slots/suppression, removed movement-speed damage penalties, r3-preserving query ABI. Threat/UI modeled; no ROM/save output.')

if __name__=='__main__':main()
