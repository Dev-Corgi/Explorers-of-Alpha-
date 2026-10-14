"""Real native theft tail: six-byte item transfer and team/bag boundaries.
UI, fixed-room gate and bag operations are modeled; theft checks/body execute.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,STACK
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import UC_ARM_REG_R0

class World(PreviousWorld):
    def reset(self):super().reset();self.bag_full=0;self.fixed=0;self.bag_calls=[]
    def service(self,u,address,size,data):
        if address==0x0200edc0:self.ret(self.bag_full);return
        if address==0x022e0880:self.ret(self.fixed);return
        if address in (0x022e2ad8,0x0234b350,0x022f9ea0):self.ret();return
        if address in (0x02346f14,0x0200f558):self.bag_calls.append((address,u.reg_read(UC_ARM_REG_R0)));self.ret();return
        if address==0x0200d81c:u.mem_write(u.reg_read(UC_ARM_REG_R0),bytes(6));self.ret();return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'pickpocket_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'pickpocket_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    item=struct.pack('<BBHH',1|8,0x12,0x3456,80)
    def setup(mode):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0));w.position(i,10+i,10)
        profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids['나쁜손버릇'],0)
        w.profile(1,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[1])
        if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
        w.u.mem_write(MONSTERS[0]+0x62,item);w.u.mem_write(MONSTERS[1]+6,b'\x01')
        w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',90))
    def hit():
        w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',ENTITIES[0],ENTITIES[1],100,1)
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        setup(mode);hit();active=mode.startswith('slot')
        assert bytes(w.u.mem_read(MONSTERS[1]+0x62,6))==(item if active else bytes(6)),mode
        assert bytes(w.u.mem_read(MONSTERS[0]+0x62,6))==(bytes(6) if active else item)
        if active:assert w.bag_calls==[(0x0200f558,MONSTERS[0]+0x62)]
        hit();assert bytes(w.u.mem_read(MONSTERS[1]+0x62,6))==(item if active else bytes(6));cases+=1
    for rule in ('held','empty_source','distant','special','sticky','boss','bag_full','fatal'):
        setup('slot3')
        if rule=='held':w.u.mem_write(MONSTERS[1]+0x62,item)
        if rule=='empty_source':w.u.mem_write(MONSTERS[0]+0x62,bytes(6))
        if rule=='distant':w.position(1,15,10)
        if rule=='special':w.category=1
        if rule=='sticky':w.profile(0,(ids['점착'],0))
        if rule=='boss':w.fixed=1
        if rule=='bag_full':w.u.mem_write(MONSTERS[1]+6,b'\x00');w.bag_full=1
        if rule=='fatal':w.u.mem_write(MONSTERS[1]+0x10,b'\0\0')
        prior=bytes(w.u.mem_read(MONSTERS[1]+0x62,6));hit()
        assert bytes(w.u.mem_read(MONSTERS[1]+0x62,6))==prior,(rule,w.bag_calls);cases+=1
    setup('slot3');w.u.mem_write(MONSTERS[0]+6,b'\x01');w.u.mem_write(MONSTERS[1]+6,b'\x00');hit()
    assert w.bag_calls==[(0x02346f14,MONSTERS[1])];cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} native Pickpocket theft cases: 100% physical-adjacent empty-holder transfer, all six item bytes, slots/suppression/acid, no duplicate theft, held/empty/range/special/Sticky Hold/boss/bag-full/fatal exclusions, correct team bag callbacks. Native UI/bag services modeled; no ROM/save output.')

if __name__=='__main__':main()
