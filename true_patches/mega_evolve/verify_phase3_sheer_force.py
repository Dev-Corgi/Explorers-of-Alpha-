"""Native Sheer Force move-ID catalogue, exact final x1.2 and secondary gates.
Original user-target/user-action RNG bodies execute; RNG terminal modeled.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,BUFFER
from .phase3 import load
from .phase3_moves import load as move_data,validate_rom
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):super().reset();self.chances=[]
    def service(self,u,address,size,data):
        if address==0x022ec7e8:self.ret(0);return # normal live dungeon, not end-of-dungeon guard
        if address in (0x022eab20,0x022eab50):self.chances.append(u.reg_read(UC_ARM_REG_R0));self.ret(1);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());validate_rom(rom)
    manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'sheer_force_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'sheer_force_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};catalogue=move_data();w=World(rom,record);cases=0
    damage_ids={r['id'] for r in catalogue['target_rules'] if r['category']!=2}
    eligible=next(i for i in catalogue['sheer_force_moves'] if i in damage_ids)
    plain=next(i for i in damage_ids if i not in catalogue['sheer_force_moves'] and i not in (355,405,559))
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        for move_id in (eligible,plain):
            w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
            for i in range(2):w.profile(i,(0,0))
            w.u.mem_write(MONSTERS[1]+0x162,b'\x01')
            profile=[(0,0)]*3
            if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids['우격다짐'],0)
            w.profile(0,*profile)
            if mode=='suppressed':w.suppressed.add(ENTITIES[0])
            if mode=='acid':w.u.mem_write(MONSTERS[0]+0xd8,b'\x04')
            move=w.move(move_id);frame=w.call('ME_EnterEffect',ENTITIES[0],move)
            active=mode.startswith('slot') and move_id==eligible
            assert w.damage(1,move_id)==(120 if active else 100),(mode,move_id)
            # Actual secondary chance functions, not just active-ability booleans.
            assert w.call('',ENTITIES[0],ENTITIES[1],20,start=0x02324934)==int(not active),(mode,move_id,active,w.chances)
            assert w.call('',ENTITIES[0],20,start=0x02324a20)==int(not active)
            assert w.chances==([] if active else [20,20])
            # Old pointer comparison/add0x30 has been removed at the live call.
            assert w.call('ME_SheerForceObserveHook',ENTITIES[0],move,999,256)==ENTITIES[0]
            assert w.u.reg_read(UC_ARM_REG_R4)==256 and w.u.reg_read(UC_ARM_REG_R1)==move
            w.call('ME_LeaveEffect',frame);cases+=4
    # All native eligible IDs are matched by value; pointer locations are irrelevant.
    w.reset();w.profile(0,(ids['우격다짐'],0));w.profile(1,(0,0))
    w.u.mem_write(MONSTERS[1]+0x162,b'\x01')
    for id_ in catalogue['sheer_force_moves']:
        w.category=0
        assert w.damage(1,id_)==120,id_
        cases+=1
    # A nested/called damage move updates secondary eligibility without changing
    # the original parent move identity or leaking to the next effect frame.
    frame=w.call('ME_EnterEffect',ENTITIES[0],w.move(plain))
    w.damage(1,eligible);assert w.call('',ENTITIES[0],ENTITIES[1],20,start=0x02324934)==0;cases+=1
    w.call('ME_LeaveEffect',frame)
    frame=w.call('ME_EnterEffect',ENTITIES[0],w.move(plain))
    assert w.call('',ENTITIES[0],ENTITIES[1],20,start=0x02324934)==1;cases+=1
    w.call('ME_LeaveEffect',frame)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} Sheer Force cases: all 128 native move IDs, slots/suppression, exact damage x1.2, real secondary chance gates, original coefficient/register contract, called-move tracking and context cleanup. RNG terminal modeled; no ROM/save output.')

if __name__=='__main__':main()
