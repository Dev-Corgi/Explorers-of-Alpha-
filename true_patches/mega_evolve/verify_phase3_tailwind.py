"""Native speed-move/increase ABI with source-tagged Tailwind counter lifetime."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,STACK
from .phase3 import load
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):super().reset();self.native=[];self.allow_speed=True
    def service(self,u,address,size,data):
        if address==0x02314814:
            # Execute real entry/wrapper and DoMoveBoostSpeed1/IncreaseSpeedStage;
            # only native IncreaseSpeed's status checks/timer assignment modeled.
            a,b,c,d=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            sp=u.reg_read(UC_ARM_REG_SP)
            fifth=struct.unpack('<I',bytes(u.mem_read(sp+32,4)))[0]
            self.native.append((a,b,c,d,fifth))
            if self.allow_speed and b in ENTITIES:
                m=MONSTERS[ENTITIES.index(b)]
                timers=bytearray(u.mem_read(m+0x114,5))
                for _ in range(c):
                    try:index=timers.index(0)
                    except ValueError:break
                    timers[index]=3
                u.mem_write(m+0x114,bytes(timers))
            regs=[UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_LR]
            for i,r in enumerate(regs):u.reg_write(r,struct.unpack('<I',bytes(u.mem_read(sp+i*4,4)))[0])
            u.reg_write(UC_ARM_REG_SP,sp+32);self.ret(77);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'tailwind_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'tailwind_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record)
    def reset():
        w.reset()
        for i in range(20):w.profile(i,(0,0))
        w.profile(1,(ids['바람타기'],0))
    def speed_move(id=444):
        assert w.call('',ENTITIES[0],ENTITIES[1],w.move(id),66,start=0x02327928)==1
        assert w.u.reg_read(UC_ARM_REG_SP)==STACK
        assert w.native[-1]==(ENTITIES[0],ENTITIES[1],1,0,1)
    reset();speed_move();assert len(w.stats)==1
    speed_move();assert len(w.stats)==1 # Refresh does not re-award.
    w.call('ME_TurnTick',ENTITIES[1]);assert len(w.stats)==1
    w.u.mem_write(MONSTERS[1]+0x114,bytes(5));w.call('ME_TurnTick',ENTITIES[1])
    speed_move();assert len(w.stats)==2
    # Clear/expiry followed by other speed source reusing the exact same slot
    # and timer value must not keep stale Tailwind ownership.
    reset();speed_move();w.u.mem_write(MONSTERS[1]+0x114,bytes(5));speed_move(12)
    assert len(w.stats)==1;speed_move();assert len(w.stats)==2
    # Already-active Agility is not an already-active Tailwind.
    reset();speed_move(12);assert not w.stats;speed_move();assert len(w.stats)==1
    # No timer changes (failed/full native buff) cannot grant a bonus.
    for mode in ('failed','full','suppressed','absent'):
        reset()
        if mode=='failed':w.allow_speed=False
        if mode=='full':w.u.mem_write(MONSTERS[1]+0x114,b'\x03'*5)
        if mode=='suppressed':w.suppressed.add(ENTITIES[1])
        if mode=='absent':w.profile(1,(0,0))
        speed_move();assert not w.stats
    # Nested move-source contexts restore; ordinary speed changes keep native
    # arguments/return and don't become Tailwind merely because a parent is one.
    reset();parent=w.call('ME_EnterSpeedMove',w.move(444));child=w.call('ME_EnterSpeedMove',w.move(12))
    w.u.mem_write(STACK,struct.pack('<I',99))
    assert w.call('',ENTITIES[0],ENTITIES[1],2,4,start=0x02314810)==77 and not w.stats
    assert w.native[-1][-1]==99
    w.call('ME_LeaveSpeedMove',child);assert w.call('',ENTITIES[0],ENTITIES[1],1,4,start=0x02314810)==77
    assert len(w.stats)==1;w.call('ME_LeaveSpeedMove',parent)
    # New floor starts new ownership; stat profile survives through source data.
    reset();speed_move();w.u.mem_write(MONSTERS[1]+0x114,bytes(5))
    from .verify_phase1 import DUNGEON
    w.u.mem_write(DUNGEON+0x749,b'\x02');w.profile(1,(ids['바람타기'],0));speed_move();assert len(w.stats)==2
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS Tailwind ARM: speed-move/source nesting, native argument/stack/return preservation, timer ownership/refresh/expiry/slot reuse, first-application Wind Rider, suppression/failure/floor reset. Native timer writer modeled; no ROM/save output.')

if __name__=='__main__':main()
