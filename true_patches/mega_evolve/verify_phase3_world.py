"""ARM world-event boundary checks, with native continuations modeled."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,STACK
from .phase3 import load
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1,OV29,word
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):
        self.chances=[];self.continuations=[]
        super().reset()
    def service(self,u,address,size,data):
        if address==0x022eab20:
            self.chances.append(u.reg_read(UC_ARM_REG_R0))
        if address in (0x022ee2f4,0x022ee1dc):
            self.continuations.append((address,u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_SP)))
            self.ret();return
        if address==0x0231fde4:
            # The wrapper replays the original push{r3-r11,lr}; the native
            # continuation must receive the complete original frame/parameters.
            sp=u.reg_read(UC_ARM_REG_SP)
            self.continuations.append((address,[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)],sp))
            saved=struct.unpack('<10I',bytes(u.mem_read(sp,40)))
            u.reg_write(UC_ARM_REG_SP,sp+40);u.reg_write(UC_ARM_REG_LR,saved[-1]);self.ret(77);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    original=NintendoDSRom(SOURCE.read_bytes());rom=NintendoDSRom(SOURCE.read_bytes())
    manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'world_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'world_test':True})
    # Direct ApplyTrapEffect entry remains untouched by floor-trap avoidance.
    for site in range(0x022ef154,0x022ef174,4):
        assert word(original.loadArm9Overlays()[29].data,site,OV29)==word(rom.loadArm9Overlays()[29].data,site,OV29)
    ids={row['key']:row['id'] for row in load()['abilities']};w=World(rom,record)
    actor,target=ENTITIES[:2]
    w.profile(0,(ids['라이트메탈'],0));w.profile(1,(0,0))
    registers={UC_ARM_REG_R5:actor,UC_ARM_REG_R9:0x02280100,UC_ARM_REG_R11:0}
    for probability,exit in ((1,0x022ee2f4),(0,0x022ee1dc)):
        w.probability=probability;w.call('',start=0x022ee1d8,registers=registers)
        assert w.continuations[-1][0]==exit and w.continuations[-1][2]==STACK
        assert w.chances[-1]==50
    count=len(w.chances);registers[UC_ARM_REG_R11]=1
    w.probability=1;w.call('',start=0x022ee1d8,registers=registers)
    assert w.continuations[-1]==(0x022ee1dc,0x02280100,STACK) and len(w.chances)==count
    registers[UC_ARM_REG_R11]=0;w.suppressed.add(actor)
    w.call('',start=0x022ee1d8,registers=registers)
    assert w.continuations[-1][0]==0x022ee1dc and len(w.chances)==count
    w.suppressed.clear();w.profile(0,(0,0))
    w.call('',start=0x022ee1d8,registers=registers)
    assert w.continuations[-1][0]==0x022ee1dc and len(w.chances)==count
    # Heavy Metal blocks only the target's forced movement and supports native
    # suppression/Mold Breaker checks. Ordinary continuation keeps arguments.
    w.profile(1,(ids['헤비메탈'],0));count=len(w.continuations)
    assert w.call('',actor,target,6,start=0x0231fde0)==0
    assert len(w.continuations)==count and w.u.reg_read(UC_ARM_REG_SP)==STACK
    w.profile(0,(ids['틀깨기'],0))
    assert w.call('',actor,target,6,start=0x0231fde0)==77
    assert w.continuations[-1][1]==[actor,target,6] and w.continuations[-1][2]==STACK-40
    w.profile(0,(0,0));w.suppressed.add(target)
    assert w.call('',actor,target,2,start=0x0231fde0)==77
    w.suppressed.clear();w.profile(1,(0,0))
    assert w.call('',actor,target,2,start=0x0231fde0)==77
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase3 world ARM: floor-trap 50% avoidance, forced/direct activation exclusion,')
    print('  direct trap entry unchanged; Heavy Metal blow-away, suppression/Mold Breaker, native ABI.')
    print('Other forced-movement/world consumers remain under audit. No ROM/save output.')

if __name__=='__main__':main()
