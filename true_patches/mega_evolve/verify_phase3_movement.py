"""Walking window and successful-hit consumption through ARM actor wrappers."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,STACK
from .phase3 import load
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):
        self.destination=None
        super().reset()
    def service(self,u,address,size,data):
        if address==0x022fe4c0:
            e=u.reg_read(UC_ARM_REG_R0);sp=u.reg_read(UC_ARM_REG_SP)
            assert sp==STACK-24-32
            if self.destination:u.mem_write(e+4,struct.pack('<hh',*self.destination))
            regs=(UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_LR)
            values=struct.unpack('<8I',bytes(u.mem_read(sp,32)))
            for r,v in zip(regs,values):u.reg_write(r,v)
            u.reg_write(UC_ARM_REG_SP,sp+32);self.ret(37);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'movement_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'movement_test':True})
    ids={r['key']:r['id'] for r in load()['abilities']};w=World(rom,record)
    attacker,target=ENTITIES[:2]
    for i in range(20):w.profile(i,(0,0))
    w.profile(0,(ids['잠복'],0));w.u.mem_write(MONSTERS[1]+6,b'\x01')
    w.position(0,10,10);w.position(1,11,10)
    def action(kind,destination):
        w.u.mem_write(MONSTERS[1]+0x4a,struct.pack('<H',kind));w.destination=destination
        assert w.call('',target,start=0x022fe4bc)==37
        assert w.u.reg_read(UC_ARM_REG_SP)==STACK
    assert w.damage(1)==100
    action(2,(12,10))
    for _ in range(3):assert w.damage(1)==120
    # A failed hit leaves the window available. Actual damage consumes only
    # this holder/target movement epoch, without altering stored stat ranks.
    token=w.call('ME_BeginAction',attacker,20)
    w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',attacker,target,100,1)
    assert w.damage(1)==120
    w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',90))
    w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',attacker,target,100,1)
    assert w.damage(1)==100
    assert w.call('ME_GetStoredSpeed',attacker)==10
    w.call('ME_EndAction',token)
    action(2,(13,10));assert w.damage(1)==120
    w.suppressed.add(attacker);assert w.damage(1)==100;w.suppressed.clear()
    assert w.damage(1)==120
    w.category=2;assert w.damage(1)==100;w.category=0
    action(1,None);assert w.damage(1)==100 # Next pass/action also expires the window.
    action(2,None);assert w.damage(1)==100 # Blocked walk did not move.
    action(8,(20,10));assert w.damage(1)==100 # Warp/item action is not a walk.
    action(2,(21,10));assert w.damage(1)==120
    w.u.mem_write(MONSTERS[1]+6,b'\0');assert w.damage(1)==100 # Friendly target is excluded.
    w.u.mem_write(MONSTERS[1]+6,b'\x01')
    w.u.mem_write(0x02100749,b'\x02');w.profile(0,(ids['잠복'],0));assert w.damage(1)==100
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase3 movement ARM: actual actor-wrapper ABI, successful-walk window,')
    print('  first successful holder/target hit, miss/calculation safety, next action expiry,')
    print('  blocked/non-walk/friendly exclusions, suppression and floor reset. No ROM/save output.')

if __name__=='__main__':main()
