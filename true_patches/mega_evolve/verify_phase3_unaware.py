"""Final native calculation stages, after other modifiers, with Unaware."""
import hashlib,struct
from .verify_phase3_native_immunity import World
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,STACK
from .phase3 import load
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest();rom=NintendoDSRom(SOURCE.read_bytes())
    manifest=dict(load_module_manifest(MODULE),phase=3);record=apply_phase1(rom,MODULE,manifest,None,{'unaware_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'unaware_test':True})
    w=World(rom,record);ids={a['key']:a['id'] for a in load()['abilities']};cases=0
    for owner in (0,1):
        for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
            w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
            for i in range(2):w.profile(i,(0,0))
            p=[(0,0)]*3
            if mode!='none':p[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids['천진'],0)
            w.profile(owner,*p)
            if mode=='suppressed':w.suppressed.add(ENTITIES[owner])
            if mode=='acid':w.u.mem_write(MONSTERS[owner]+0xd8,b'\x04')
            if mode=='mold':w.profile(0,(ids['틀깨기'],0))
            active=mode.startswith('slot')
            w.u.mem_write(STACK+0x38,struct.pack('<4I',768,512,0,14))
            w.segment(0x023c9e58,{0x023c9e5c},{UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R9:ENTITIES[1]})
            assert w.u.reg_read(UC_ARM_REG_R1)==(10 if active and owner==1 else 14)
            assert struct.unpack('<I',bytes(w.u.mem_read(STACK+0x3c,4)))[0]==(256 if active and owner==1 else 512)
            w.segment(0x023c9e78,{0x023c9e7c},{UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R9:ENTITIES[1],UC_ARM_REG_R4:6})
            assert w.u.reg_read(UC_ARM_REG_R4)==(10 if active and owner==0 else 6)
            assert struct.unpack('<I',bytes(w.u.mem_read(STACK+0x38,4)))[0]==(256 if active and owner==0 else 768)
            w.segment(0x023c9f64,{0x023c9f68},{UC_ARM_REG_R7:ENTITIES[0],UC_ARM_REG_R6:ENTITIES[1],UC_ARM_REG_R9:14,UC_ARM_REG_R10:6})
            assert w.u.reg_read(UC_ARM_REG_R9)==(10 if active and owner==1 else 14)
            assert w.u.reg_read(UC_ARM_REG_R10)==(10 if active and owner==0 else 6)
            # Stored ranks never change during any of these lookups.
            assert struct.unpack('<6H',bytes(w.u.mem_read(MONSTERS[0]+0x24,12)))==(10,)*6
            cases+=7
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} final Unaware stage/scalar cases: attack/defense and accuracy/evasion neutral10, 256/256 cached scalar, both sides, slots/suppression/Mold Breaker, original stored values unchanged. Native lookup boundaries execute; no ROM/save output.')
if __name__=='__main__':main()
