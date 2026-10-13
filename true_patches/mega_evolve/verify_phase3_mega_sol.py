"""Mega Sol personal move weather: native Solar Beam and Morning Sun paths.
World weather is never written. Final damage/recovery/charge services modeled.
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
    def reset(self):super().reset();self.charge_checks=[];self.charges=[];self.damages=[];self.heals=[]
    def service(self,u,address,size,data):
        args=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        if address==0x023245a4:self.charge_checks.append(args);self.ret(0);return
        if address==0x02318bbc:self.charges.append(args);self.ret();return
        if address==0x02318d58:self.ret();return
        if address==0x02332b20:self.damages.append(args);self.ret(1);return
        if address==0x023152e4:self.heals.append(args);self.ret();return
        if address==0x020258c4:self.ret(1);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'mega_sol_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'mega_sol_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    # The original move handlers read their weather-healing and power tables
    # from overlay10's immutable data, outside the overlay29 fixture mapping.
    ov10=rom.loadArm9Overlays()[10];w.u.mem_write(ov10.ramAddress,bytes(ov10.data))
    def setup(mode):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0))
        profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids['메가솔라'],0)
        w.profile(0,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[0])
        if mode=='acid':w.u.mem_write(MONSTERS[0]+0xd8,b'\x04')
        w.weather(4)
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        setup(mode);active=mode.startswith('slot')
        assert w.call('ME_NativeApparentWeather',ENTITIES[0],0x02328c90)==4;cases+=1
        token=w.call('ME_BeginAction',ENTITIES[0],467)
        for caller in (0x0230b5d4,0x0230bf64,0x02324e9c,0x02328c90,0x02325f84):
            assert w.call('ME_NativeApparentWeather',ENTITIES[0],caller)==(1 if active else 4)
            assert w.call('ME_NativeApparentWeather',ENTITIES[1],caller)==4;cases+=2
        for caller in (0x02310178,0x02310180,0x02335594,0):
            assert w.call('ME_NativeApparentWeather',ENTITIES[0],caller)==4;cases+=1
        assert w.call('ME_ApparentWeather',ENTITIES[0])==4;cases+=1
        # Actual native query return-site LR controls charging and recovery.
        w.call('',ENTITIES[0],ENTITIES[1],w.move(163),0,start=0x02328c74)
        assert len(w.charge_checks)==int(not active) and len(w.charges)==int(not active)
        assert len(w.damages)==int(active);cases+=1
        w.call('',ENTITIES[0],ENTITIES[0],w.move(134),0,start=0x02325f74)
        table=struct.unpack_from('<I',rom.loadArm9Overlays()[29].data,0x02325fb0-0x022dc240)[0]
        expected=struct.unpack('<h',bytes(w.u.mem_read(table+2*(1 if active else 4),2)))[0]
        assert expected>0 and w.heals[-1][2]==expected;cases+=1
        assert bytes(w.u.mem_read(DUNGEON+0xcd38,2))==b'\x04\x04';cases+=1
        w.call('ME_EndAction',token)
    setup('slot3');token=w.call('ME_BeginAction',ENTITIES[0],20)
    nested=w.call('ME_BeginAction',ENTITIES[1],20)
    assert w.call('ME_NativeApparentWeather',ENTITIES[0],0x0230b5d4)==4
    w.call('ME_EndAction',nested);assert w.call('ME_NativeApparentWeather',ENTITIES[0],0x0230b5d4)==1;cases+=2
    w.call('ME_EndAction',token)
    previous=w.call('ME_EnterCalculation',ENTITIES[0],ENTITIES[1])
    assert w.call('ME_NativeApparentWeather',ENTITIES[0],0x0230b5d4)==1;cases+=1
    address=w.call('ME_WeatherPower',ENTITIES[0])
    assert struct.unpack('<2I',bytes(w.u.mem_read(address,8)))==(0x33333334,0x13333);cases+=1
    w.call('ME_LeaveCalculation',previous)
    setup('slot3');w.profile(0,(ids['메가솔라'],0),(ids['엽록소'],0))
    assert w.call('ME_GetSpeed',ENTITIES[0],100,0,0)==100;cases+=1
    token=w.call('ME_BeginAction',ENTITIES[0],20)
    assert w.call('ME_GetSpeed',ENTITIES[0],100,0,0)==200;cases+=1
    incoming=w.call('ME_EnterCalculation',ENTITIES[1],ENTITIES[0])
    assert w.call('ME_NativeApparentWeather',ENTITIES[0],0x0230b5d4)==4;cases+=1
    w.call('ME_LeaveCalculation',incoming);w.call('ME_EndAction',token)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} Mega Sol move-weather cases: slots/suppression, actor/target/world/ambient separation, nested actions/calculation context, native Solar Beam charge bypass and Morning Sun weather lookup, ordinary sun power. Native terminal services modeled; no ROM/save output.')

if __name__=='__main__':main()
