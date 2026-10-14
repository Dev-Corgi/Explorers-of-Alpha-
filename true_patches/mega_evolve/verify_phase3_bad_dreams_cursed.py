"""Existing Bad Dreams cache-byte damage and revised Cursed Body threshold."""
import hashlib,struct
from .verify_phase3_native_coefficients import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON
from .phase3 import load
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):super().reset();self.damage_calls=[];self.roll=0
    def service(self,u,address,size,data):
        if address==0x0230d11c:
            self.damage_calls.append(tuple(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)));self.ret(0);return
        if address in (0x02307bdc,):self.ret(0);return
        if address==0x022e28d4:
            a,b=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
            x,y=struct.unpack('<2h',bytes(u.mem_read(a+4,4)));xx,yy=struct.unpack('<2h',bytes(u.mem_read(b+4,4)))
            self.ret(abs(x-xx)<=1 and abs(y-yy)<=1);return
        if address==0x02054ec8:self.ret(1);return # existing contact eligibility
        if address==0x022eaa98:self.ret(self.roll);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest();rom=NintendoDSRom(SOURCE.read_bytes())
    manifest=dict(load_module_manifest(MODULE),phase=3);record=apply_phase1(rom,MODULE,manifest,None,{'bad_dreams_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'bad_dreams_test':True})
    w=World(rom,record);ids={a['key']:a['id'] for a in load()['abilities']};cases=0
    def setup():
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0));w.position(i,10+i,10)
        w.u.mem_write(MONSTERS[1]+6,b'\x01')
    for value in (0,7,8,64,255):
        for status in ('awake','asleep','comatose'):
            setup();w.profile(0,(ids['나이트메어'],0));w.u.mem_write(MONSTERS[0]+0x1c,bytes([value]))
            if status=='asleep':w.u.mem_write(MONSTERS[1]+0xbd,b'\x01')
            if status=='comatose':w.profile(1,(ids['절대안깸'],0))
            w.call('',ENTITIES[0],start=0x0231b1b8,limit=500000)
            assert len(w.damage_calls)==int(status!='awake')
            if w.damage_calls:assert w.damage_calls[-1][:3]==(ENTITIES[1],value//8,24)
            cases+=1
    for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
        for roll in (0,11,12,14,99):
            setup();p=[(0,0)]*3
            if mode!='none':p[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids['저주받은바디'],0)
            w.profile(1,*p)
            if mode=='suppressed':w.suppressed.add(ENTITIES[1])
            if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
            if mode=='mold':w.profile(0,(ids['틀깨기'],0))
            w.roll=roll
            w.segment(0x023af484,{0x023af4dc},{UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R9:ENTITIES[1],
                UC_ARM_REG_R8:MONSTERS[0],UC_ARM_REG_R6:MONSTERS[1],UC_ARM_REG_R4:0})
            flags=struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[1]+0x192,2)))[0]
            assert bool(flags&0x1000)==(mode.startswith('slot') and roll<12),(mode,roll,hex(flags));cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} Bad Dreams/Cursed Body cases: actual adjacent enemy asleep/virtual sleep cache-byte floor(V/8) damage and native seal flag at rolls0..11 only, slots/suppression/Mold Breaker. Fixed damage/contact eligibility/UI/RNG modeled; no ROM/save output.')
if __name__=='__main__':main()
