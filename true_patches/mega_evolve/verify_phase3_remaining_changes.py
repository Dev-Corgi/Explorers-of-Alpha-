"""Changed normal room auras, wake healing and successful drain boundary.
Native stat/cache, messages and reflected fixed damage are external models.
"""
import hashlib,struct
from ndspy.rom import NintendoDSRom
from .verify_phase3_native_immunity import World as PreviousWorld
from unicorn.arm_const import *
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,BUFFER,STACK
from .phase3 import load
from .phase3_moves import load as moves
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1

class World(PreviousWorld):
    def service(self,u,address,size,data):
        if address in (0x0234b350,0x022e2ad8,0x022e3ab4,0x02304a48):self.ret(0);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'remaining_changes_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'remaining_changes_test':True})
    w=World(rom,record);ids={a['key']:a['id'] for a in load()['abilities']};cases=0
    def setup(name,mode='slot3'):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+12,bytes(17*4))
        for i in range(3):w.profile(i,(0,0));w.position(i,10+i,10);w.u.mem_write(ENTITIES[i]+0x25,b'\x01')
        w.u.mem_write(MONSTERS[1]+6,b'\x01');w.u.mem_write(MONSTERS[2]+6,b'\x01')
        p=[(0,0)]*3
        if mode!='none':p[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids[name],0)
        w.profile(2,*p)
        if mode=='suppressed':w.suppressed.add(ENTITIES[2])
        if mode=='acid':w.u.mem_write(MONSTERS[2]+0xd8,b'\x04')
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        setup('위협',mode)
        w.u.mem_write(STACK+0x30,struct.pack('<I',0))
        # Repeat with the physical category stack slot explicitly initialized.
        w.segment(0x0230c820,{0x0230c84c},{UC_ARM_REG_R10:ENTITIES[0],UC_ARM_REG_R9:ENTITIES[1],UC_ARM_REG_R4:100,UC_ARM_REG_R11:100})
        active=mode.startswith('slot');assert w.u.reg_read(UC_ARM_REG_R4)==(400 if active else 100)
        assert w.u.reg_read(UC_ARM_REG_R11)==(500 if active else 100)
        w.u.mem_write(ENTITIES[2]+0x25,b'\x02');assert not w.call('ME_IntimidateAura',ENTITIES[0]);cases+=2
        setup('자력',mode);w.u.mem_write(MONSTERS[0]+0x5e,b'\x11');w.position(2,11,10)
        assert w.call('ME_Magnetized',ENTITIES[0])==int(active)
        assert w.call('ME_MagnetDefenseStage',ENTITIES[2],ENTITIES[0],10,0)==(9 if active else 10)
        w.u.mem_write(MONSTERS[0]+0x4a,struct.pack('<H',2));w.call('ME_BlockMagnetWalk',ENTITIES[0])
        assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[0]+0x4a,2)))[0]==(1 if active else 2)
        w.position(2,15,10);assert not w.call('ME_Magnetized',ENTITIES[0]);cases+=4
        setup('일찍기상',mode);w.u.mem_write(MONSTERS[2]+0x10,struct.pack('<H',20))
        w.u.mem_write(MONSTERS[2]+0xbd,b'\x01');w.u.mem_write(STACK,struct.pack('<I',0))
        w.call('',ENTITIES[2],ENTITIES[2],0,0,start=0x02305fdc)
        assert bytes(w.u.mem_read(MONSTERS[2]+0xbd,1))==b'\0'
        assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[2]+0x10,2)))[0]==(100 if active else 20)
        assert w.u.reg_read(UC_ARM_REG_SP)==STACK;cases+=1
        setup('해감액',mode);w.u.mem_write(BUFFER+0x400,struct.pack('<5I',101,0,0,0,0))
        for move in moves()['drain_moves']:
            w.u.mem_write(BUFFER+0x400,struct.pack('<5I',101,0,0,0,0))
            w.call('ME_LiquidOozeHit',ENTITIES[0],ENTITIES[2],BUFFER+0x400,move)
            assert struct.unpack('<I',bytes(w.u.mem_read(BUFFER+0x400,4)))[0]==(0 if active else 101)
            if active:assert w.thorns[-1][2]==50
            cases+=1
    setup('자력');w.position(2,11,10);w.u.mem_write(MONSTERS[0]+0x5e,b'\x11')
    w.profile(2,(ids['천진'],0),(ids['자력'],0));assert w.call('ME_MagnetDefenseStage',ENTITIES[2],ENTITIES[0],10,0)==10;cases+=1
    setup('일찍기상');w.u.mem_write(MONSTERS[2]+0x10,struct.pack('<H',20))
    w.call('ME_WokeUp',ENTITIES[2],0);assert struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[2]+0x10,2)))[0]==20;cases+=1
    setup('해감액');w.u.mem_write(BUFFER+0x400,struct.pack('<5I',101,0,0,0,0))
    w.segment(w.symbols['ME_LiquidOozeHook'],{0x02332da0},{UC_ARM_REG_R5:w.move(moves()['drain_moves'][0]),
        UC_ARM_REG_R6:BUFFER+0x400,UC_ARM_REG_R7:ENTITIES[2],UC_ARM_REG_R8:ENTITIES[0],UC_ARM_REG_LR:0x02332da0})
    assert struct.unpack('<I',bytes(w.u.mem_read(BUFFER+0x400,4)))[0]==0 and w.thorns[-1][2]==50;cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} changed normal effect cases: room Intimidate physical ratio, adjacent Steel Magnet Pull calculation/walk, actual native wake and full HP, drain amount immunity/half reflection after hit; external messages/stat/cache/fixed damage modeled. No ROM/save output.')
if __name__=='__main__':main()
