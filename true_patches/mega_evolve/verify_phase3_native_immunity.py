"""Execute existing Ground/sound/critical consumers with extended profiles.

Runs the original immunity branches, Gravity state read and sound classifier.
Only float conversion and messages are modeled; subsequent damage is excluded.
No ROM/save output.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from ndspy.rom import NintendoDSRom
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,STACK,BUFFER,DUNGEON,STOP
from .phase3 import load
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1

SOUND_IDS=(217,112,284,83,34,84,171,424,27,241,25,26,446,530,555)
MODES=('none','slot1','slot2','slot3','suppressed','acid','mold')

class World(PreviousWorld):
    def service(self,u,address,size,data):
        if address==0x02054760:self.ret(2);return  # neutral gender modifier
        if address in (0x0230a9dc,0x02301f80):self.ret(0);return  # no held/IQ critical bonuses
        if address==0x02001c80:
            # Ground immunity converts integer zero to the native float output.
            assert u.reg_read(UC_ARM_REG_R1)==0
            u.mem_write(u.reg_read(UC_ARM_REG_R0),bytes(8));self.ret();return
        if address==0x02318a4c:
            # Magnet Rise is an independent defense, outside this test family.
            self.ret(0);return
        super().service(u,address,size,data)

    def segment(self,start,ends,registers):
        reached=[]
        def boundary(u,address,size,_):
            if address in ends:reached.append(address);u.emu_stop()
        handle=self.u.hook_add(UC_HOOK_CODE,boundary)
        try:
            self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP)
            for register,value in registers.items():self.u.reg_write(register,value)
            self.u.emu_start(start,STOP,count=200000)
            assert len(reached)==1,hex(self.u.reg_read(UC_ARM_REG_PC))
            return reached[0]
        finally:self.u.hook_del(handle)

    def ground(self,type_):
        damage=BUFFER+0x300;multiplier=BUFFER+0x320
        self.u.mem_write(damage,struct.pack('<5I',777,777,777,777,777))
        self.u.mem_write(multiplier,b'\x55'*8)
        self.segment(0x0230b1dc,{0x0230b248},{
            UC_ARM_REG_R7:damage,UC_ARM_REG_R8:type_,UC_ARM_REG_R9:ENTITIES[1],
            UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R11:multiplier})
        return struct.unpack('<I',bytes(self.u.mem_read(damage+8,4)))[0]==0

    def sound(self,move_id):
        self.segment(0x0232f220,{0x0232f270,0x023c1244},{
            UC_ARM_REG_R4:ENTITIES[1],UC_ARM_REG_R8:self.move(move_id),
            UC_ARM_REG_R9:ENTITIES[0],UC_ARM_REG_R11:1})
        return self.u.reg_read(UC_ARM_REG_R11)==0

    def critical(self,roll):
        self.choice=roll
        self.u.mem_write(STACK+0xe8,struct.pack('<I',10))
        summary=BUFFER+0x400;self.u.mem_write(summary,bytes(0x60))
        end=self.segment(0x0230cd50,{0x0230ce14,0x0230ce38},{
            UC_ARM_REG_R5:summary,UC_ARM_REG_R6:MONSTERS[0],UC_ARM_REG_R7:MONSTERS[1],
            UC_ARM_REG_R9:ENTITIES[1],UC_ARM_REG_R10:ENTITIES[0]})
        return end==0x0230ce14

def configure(w,ids,name,mode,holder=1):
    w.reset()
    for i in range(20):w.profile(i,(0,0))
    if mode!='none':
        slot=int(mode[-1])-1 if mode.startswith('slot') else 2
        profile=[(0,0)]*3;profile[slot]=(ids[name],0);w.profile(holder,*profile)
    if mode=='suppressed':w.suppressed.add(ENTITIES[holder])
    if mode=='acid':w.u.mem_write(MONSTERS[holder]+0xd8,b'\x04')
    if mode=='mold':w.profile(0,(ids['틀깨기'],0))

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'native_immunity_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'native_immunity_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};w=World(rom,record);cases=0
    for name in ('부유','방음'):
        for mode in MODES:
            configure(w,ids,name,mode)
            active=mode.startswith('slot')
            if name=='부유':
                for gravity in (0,1):
                    w.u.mem_write(DUNGEON+0x12afc,bytes([gravity]))
                    for type_ in (9,1):
                        assert w.ground(type_)==(active and not gravity and type_==9),(name,mode,gravity,type_)
                        cases+=1
            else:
                for move_id in (*SOUND_IDS,20):
                    assert w.sound(move_id)==(active and move_id in SOUND_IDS),(name,mode,move_id)
                    cases+=1
    for name in ('전투무장','조가비갑옷'):
        for mode in MODES:
            configure(w,ids,name,mode)
            assert w.critical(0)==(not mode.startswith('slot')),(name,mode)
            cases+=1
    # Super Luck belongs to the attacker; Mold Breaker does not suppress the
    # attacker's own ability. Test suppression instead of replacing its profile.
    for mode in MODES[:-1]:
        configure(w,ids,'대운',mode,holder=0)
        for roll in (9,10,19,20):
            assert w.critical(roll)==(roll<(20 if mode.startswith('slot') else 10)),('대운',mode,roll)
            cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} native Ground/sound/critical cases: 5 abilities, all three slots, suppression/Gastro Acid/Mold Breaker for defender immunities, real Gravity and 15 sound IDs, critical immunity and Super Luck threshold x2. Subsequent damage/messages excluded; no ROM/save output.')

if __name__=='__main__':main()
