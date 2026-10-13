"""Grouped native ordinary immunities: execute original status bodies, not mocks.
Only unrelated global defenses, UI, RNG and ancillary services are modeled.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,STACK,STOP,BUFFER
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *
from unicorn import UC_HOOK_MEM_WRITE

CASES=(
    ('면역',0x02312664,0xbf,2),('면역',0x0231293c,0xbf,3),
    ('수의베일',0x02312338,0xbf,1),('유연',0x02314544,0xbf,4),
    ('마이페이스',0x02314f38,0xd0,2),('마그마의무장',0x02312bf8,0xc4,1),
    ('불면',0x023118d8,0xbd,1),('의기양양',0x023118d8,0xbd,1),
)
class World(PreviousWorld):
    def reset(self):
        self.status_targets={v for k,v in self.loader_info['prior_helpers'].items() if k.startswith('STATUS_TARGET_')}
        super().reset()
    def service(self,u,address,size,data):
        if address==0x022e1628:
            u.mem_write(BUFFER+0x200,bytes(20));u.mem_write(BUFFER+0x200,b'\x01\0');self.ret(BUFFER+0x200);return
        # Previous harness models these continuations for wrapper ABI testing.
        # This suite instead executes their actual prerequisite instruction body.
        if address in self.status_targets:return
        if address in (0x023118b4,):self.ret(1);return
        if address in (0x02301940,0x02302430,0x02314d40):self.ret(0);return
        if address in (0x022e2ad8,0x022e3ab4,0x022e4b8c,0x022e4c4c,0x022e6798,
                       0x0234b3a4,0x022e451c,0x02304a48,0x020585b4,0x0230040c,
                       0x022e4388,0x02304a84,0x02314e1c,0x023c5a94,0x022e3e74):self.ret();return
        if address==0x022eab80:self.ret(3);return
        super().service(u,address,size,data)

    def attempt(self,entry,offset):
        # The checked behavior ends at rejection or the actual state write.
        # Subsequent sprites/status-response callbacks need a full dungeon and
        # are outside this reuse test, rather than silently mocking their result.
        self.applied=None;watched=MONSTERS[1]+offset
        def written(u,access,address,size,value,_):
            if address==watched and size==1 and value:
                self.applied=value;u.emu_stop()
        handle=self.u.hook_add(UC_HOOK_MEM_WRITE,written)
        try:
            self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP)
            for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),(ENTITIES[0],ENTITIES[1],3,0)):
                self.u.reg_write(reg,value)
            self.u.emu_start(entry,STOP,count=500000)
            if self.applied is None:assert self.u.reg_read(UC_ARM_REG_PC)==STOP
            return self.applied or 0
        finally:self.u.hook_del(handle)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'native_status_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'native_status_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record)
    for name,entry,offset,status in CASES:
        for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
            w.reset()
            for i in range(20):w.profile(i,(0,0))
            if mode!='none':
                slot=int(mode[-1])-1 if mode.startswith('slot') else 2
                profile=[(0,0)]*3;profile[slot]=(ids[name],0);w.profile(1,*profile)
            if mode=='suppressed':w.suppressed.add(ENTITIES[1])
            if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
            if mode=='mold':w.profile(0,(ids['틀깨기'],0))
            w.u.mem_write(STACK,bytes(32))
            try:value=w.attempt(entry,offset)
            except Exception as e:raise AssertionError((name,mode,hex(w.u.reg_read(UC_ARM_REG_PC)))) from e
            assert value==(0 if mode.startswith('slot') else status),(name,mode,hex(entry),value,status)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS grouped native rejection/state-write paths: 7 ordinary abilities / 8 status paths, slots1/2/3, no-trait controls, item/Gastro Acid suppression and Mold Breaker. Post-status visuals/responses excluded; no ROM/save output.')

if __name__=='__main__':main()
