"""Low-HP escape selection with modeled tile/movement native services."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,BUFFER
from .phase3 import load
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):
        self.tiles={};self.moves=[];self.allow_move=True
        super().reset()
    def service(self,u,address,size,data):
        a,b,c,d=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        if address==0x02336164:
            flags,object_=self.tiles.get((a,b),(0,0));occupied=0
            for e,m in zip(ENTITIES,MONSTERS):
                if struct.unpack('<H',bytes(u.mem_read(m+0x10,2)))[0] and struct.unpack('<hh',bytes(u.mem_read(e+4,4)))==(a,b):occupied=e
            tile=bytearray(20);struct.pack_into('<H',tile,0,flags)
            struct.pack_into('<II',tile,12,occupied,object_)
            u.mem_write(BUFFER+0x100,bytes(tile));self.ret(BUFFER+0x100)
        elif address==0x022f85f0:
            self.moves.append((a,b,c,d))
            if self.allow_move:u.mem_write(a+4,struct.pack('<hh',b,c))
            self.ret()
        else:super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'escape_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'escape_test':True})
    ids={r['key']:r['id'] for r in load()['abilities']};w=World(rom,record)
    holder,actor=ENTITIES[0],ENTITIES[3]
    def reset():
        w.reset()
        for i in range(20):
            w.profile(i,(0,0));w.u.mem_write(MONSTERS[i]+0x10,struct.pack('<H',100 if i<4 else 0))
        w.profile(0,(ids['도주'],0));w.u.mem_write(MONSTERS[0]+0x10,struct.pack('<H',25))
        w.u.mem_write(MONSTERS[3]+6,b'\x01')
        w.position(0,10,10);w.position(1,12,10);w.position(2,20,10);w.position(3,9,10)
    reset();w.tiles[(11,9)]=(1,0);w.tiles[(19,9)]=(1,0)
    assert w.call('ME_RunAway',actor,holder,100)==1
    assert w.moves==[(holder,11,9,1)]
    assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[0]+0x10,2)))[0]==25
    assert w.call('ME_RunAway',actor,holder,100)==0 and len(w.moves)==1
    # The nearest ally has no valid adjacent tile; try the next ally.
    reset();w.tiles[(19,9)]=(1,0)
    assert w.call('ME_RunAway',actor,holder,100)==1 and w.moves[-1][1:3]==(19,9)
    # Unsafe terrain, stairs, objects and occupied cells cannot be destinations.
    reset();w.tiles.update({(11,9):(0,0),(12,9):(5,0),(13,9):(1,123),(12,10):(1,0),(19,9):(1,0)})
    assert w.call('ME_RunAway',actor,holder,100)==1 and w.moves[-1][1:3]==(19,9)
    # No ally-adjacent space (or no allies): use a safe tile elsewhere.
    reset();w.tiles[(40,20)]=(1,0)
    assert w.call('ME_RunAway',actor,holder,100)==1 and w.moves[-1][1:3]==(40,20)
    reset();w.u.mem_write(MONSTERS[1]+0x10,b'\0\0');w.u.mem_write(MONSTERS[2]+0x10,b'\0\0')
    w.tiles[(40,20)]=(1,0)
    assert w.call('ME_RunAway',actor,holder,100)==1
    # No destination and a failed native move do not consume the floor charge.
    reset();assert w.call('ME_RunAway',actor,holder,100)==0 and not w.moves
    w.tiles[(11,9)]=(1,0);w.allow_move=False
    assert w.call('ME_RunAway',actor,holder,100)==0
    w.allow_move=True;assert w.call('ME_RunAway',actor,holder,100)==1
    for mode in ('high_hp','fatal','friendly','no_loss','suppressed'):
        reset();w.tiles[(11,9)]=(1,0);previous=100
        if mode=='high_hp':w.u.mem_write(MONSTERS[0]+0x10,struct.pack('<H',26))
        if mode=='fatal':w.u.mem_write(MONSTERS[0]+0x10,b'\0\0')
        if mode=='friendly':w.u.mem_write(MONSTERS[3]+6,b'\0')
        if mode=='no_loss':previous=25
        if mode=='suppressed':w.suppressed.add(holder)
        assert w.call('ME_RunAway',actor,holder,previous)==0 and not w.moves
    reset()
    for caller in (0x022fa9d8,0x02301604,0x023016fc):assert w.call('ME_LegacyAbilityActive',holder,43,caller)==0
    assert w.call('ME_AbilityActive',holder,43)==1 # General query/copy identity survives.
    # Actual hit dispatcher reaches escape; no return/revival/species mutation.
    w.tiles[(11,9)]=(1,0);original_species=bytes(w.u.mem_read(MONSTERS[0]+4,2))
    w.u.mem_write(BUFFER,struct.pack('<I',20))
    from .verify_phase1 import STACK
    w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',actor,holder,100,1)
    assert w.moves[-1][1:3]==(11,9) and bytes(w.u.mem_read(MONSTERS[0]+4,2))==original_species
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase3 escape ARM: quarter-HP enemy hit, closest/next ally/safe-floor fallback,')
    print('  walls/stairs/objects/occupancy exclusions, floor-once and failed-destination safety,')
    print('  suppression/fatal/friendly/no-loss, old AI-only suppression and hit dispatcher. No ROM/save output.')

if __name__=='__main__':main()
