"""Virtual sleeping belongs to move targeting, never global action gating."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS
from .phase3 import load
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1,OV29,word,branch

class World(PreviousWorld):
    def service(self,u,address,size,data):
        if address==0x022eab80:self.ret(2);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'sleep_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'sleep_test':True})
    ids={r['key']:r['id'] for r in load()['abilities']};w=World(rom,record)
    e=ENTITIES[0];m=MONSTERS[0]
    w.profile(0,(ids['절대안깸'],0))
    assert w.call('ME_SleepTarget',e)==1
    assert w.call('',e,start=0x023007a8)==0 # Actual global sleep predicate remains false.
    w.suppressed.add(e)
    assert w.call('ME_SleepTarget',e)==0
    w.u.mem_write(m+0xbd,b'\x01');assert w.call('ME_SleepTarget',e)==1
    w.suppressed.clear();w.u.mem_write(m+0xbd,b'\0')
    w.u.mem_write(m+0x10,struct.pack('<H',40))
    assert w.call('',e,e,0,0,start=0x0232a414)==1
    assert bytes(w.u.mem_read(m+0xbd,1))==b'\0'
    assert struct.unpack('<H',bytes(w.u.mem_read(m+0x10,2)))[0]==40
    # Both player and enemy Rest branches reach the guarded Napping entry.
    w.u.mem_write(m+6,b'\x01');w.probability=1
    w.call('',e,e,0,0,start=0x0232a414)
    assert bytes(w.u.mem_read(m+0xbd,1))==b'\0'
    overlays=rom.loadArm9Overlays()
    assert word(overlays[29].data,0x0232bcf0,OV29)==branch(0x0232bcf0,record.data[0]['symbols']['ME_SleepTarget'],True)
    original=NintendoDSRom(SOURCE.read_bytes()).loadArm9Overlays()[29].data
    assert overlays[29].data[0x023007a8-OV29:0x023007dc-OV29]==original[0x023007a8-OV29:0x023007dc-OV29]
    for site in (0x0231b2b4,0x023265c0,0x02325cd8,0x023344d4,0x023344fc):
        assert word(overlays[29].data,site,OV29)==branch(site,record.data[0]['symbols']['ME_SleepTarget'],True)
    # Snore's real handler gates on virtual sleep; stop at native damage entry,
    # before ancillary effect/UI processing needs a complete dungeon.
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3
    from .verify_phase1 import STACK,STOP
    reached=[]
    # The direct branch boundary is before its native DealDamage call.
    def boundary(u,address,size,_):
        if address in (0x023265cc,0x02326624):reached.append(address);u.emu_stop()
    handle=w.u.hook_add(UC_HOOK_CODE,boundary)
    try:
        w.u.reg_write(UC_ARM_REG_SP,STACK);w.u.reg_write(UC_ARM_REG_LR,STOP)
        for reg,val in ((UC_ARM_REG_R0,e),(UC_ARM_REG_R1,ENTITIES[1]),(UC_ARM_REG_R2,w.move(25)),(UC_ARM_REG_R3,0)):w.u.reg_write(reg,val)
        w.u.emu_start(0x023265a4,STOP,count=200000)
        assert reached==[0x023265cc] and bytes(w.u.mem_read(m+0xbd,1))==b'\0'
    finally:w.u.hook_del(handle)
    count=len(w.prior_calls);w.call('',ENTITIES[1],e,5,start=0x02311c4c)
    assert len(w.prior_calls)==count and bytes(w.u.mem_read(m+0xbd,1))==b'\0'
    w.profile(0,(0,0));w.u.mem_write(m+0xbd,b'\0');assert w.call('ME_SleepTarget',e)==0
    for status in (1,3,5):
        w.u.mem_write(m+0xbd,bytes([status]));assert w.call('ME_SleepTarget',e)==1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase3 sleep ARM: targeted virtual sleep/suppression/native sleeping,')
    print('  actual player/enemy Rest blocked without HP/sleep mutation; global action predicate unchanged.')
    print('  Native Snore gate/Bad Dreams/status checks use virtual sleep; Rest/Nightmare real sleep blocked. No ROM/save output.')

if __name__=='__main__':main()
