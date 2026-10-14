"""Real quicksave main/sidecar wrappers, with flash storage modeled in RAM."""
import hashlib,struct
from .verify_phase4_forms import FormWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,BUFFER,DUNGEON
from .phase4 import load
from .phase3 import load as abilities
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from unicorn.arm_const import *


class QuickWorld(FormWorld):
    def __init__(self,rom,record):
        self.flash=bytearray(0x20000);self.io=[]
        super().__init__(rom,record)
    def service(self,u,address,size,data):
        if address in (0x0204A9C8,0x0204A8E0):
            page,pointer,length=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
            offset=page*256;assert offset+length<=len(self.flash)
            if address==0x0204A9C8:self.flash[offset:offset+length]=u.mem_read(pointer,length)
            else:u.mem_write(pointer,bytes(self.flash[offset:offset+length]))
            self.io.append((address,page,length));self.ret(0);return
        super().service(u,address,size,data)


def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=load_module_manifest(MODULE)
    record=apply_phase1(rom,MODULE,manifest,None,{'quick_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'quick_test':True})
    w=QuickWorld(rom,record);raw=rom.getFileByName('BALANCE/monster.md')
    w.u.mem_write(0x021A0000,raw);w.u.mem_write(0x020B09B4,struct.pack('<I',0x021A0008))
    species=load()['rows'][0]['species']
    w.u.mem_write(MONSTERS[0]+2,struct.pack('<HH',species,species))
    w.call('ME_ResetMonster',MONSTERS[0]);w.call('ME_SetStoredSpeed',ENTITIES[0],15)
    original=[w.ability(0,i) for i in range(3)]
    slow=next(a['id'] for a in abilities()['abilities'] if a['key']=='슬로스타트')
    borrowed=[slow,original[1],original[0]|65536]
    w.u.mem_write(BUFFER+0x6000,struct.pack('<3I',*borrowed))
    w.call('ME_SetAbilityProfile',ENTITIES[1],BUFFER+0x6000,3)
    w.call('ME_CopyAbilities',ENTITIES[0],ENTITIES[1])
    w.call('ME_FloorEntry',ENTITIES[0]);w.call('ME_FloorEntry',ENTITIES[1])
    assert w.call('ME_GetStoredSpeed',ENTITIES[0])==12
    assert w.call('ME_SetWeatherSource',ENTITIES[0],2,1,0)==1
    assert w.call('ME_ForcedWeather')==2
    # Existing ordinary main slots and the remaining unused flash tail stay intact.
    w.flash[:0x19000]=b'\xA5'*0x19000;w.flash[0x1FC00:]=b'\x5A'*0x400
    w.u.mem_write(BUFFER,bytes(0x5800))
    assert w.call('',BUFFER,0x5800,start=0x02049248,limit=3000000)==0
    assert w.io[-2:]==[(0x0204A9C8,400,0x5800),(0x0204A9C8,488,0x1400)]
    assert w.flash[:0x19000]==b'\xA5'*0x19000 and w.flash[0x1FC00:]==b'\x5A'*0x400
    # Cold heap/actor recreation. Native original/apparent species come from
    # the stock quicksave; the linked sidecar restores the custom state next.
    w.reset();w.u.mem_write(0x021A0000,raw);w.u.mem_write(0x020B09B4,struct.pack('<I',0x021A0008))
    w.u.mem_write(MONSTERS[0]+2,struct.pack('<HH',species,species))
    assert w.call('',BUFFER,0x5800,start=0x02049628,limit=3000000)==0
    w.call('ME_FloorEntry',ENTITIES[0]);w.call('ME_FloorEntry',ENTITIES[1])
    assert w.call('ME_GetStoredSpeed',ENTITIES[0])==10 # No repeated Slow Start.
    w.call('ME_QuickReady')
    assert w.call('ME_GetStoredSpeed',ENTITIES[0])==12
    assert [w.ability(0,i) for i in range(3)]==borrowed
    w.call('ME_RestoreAbilities',ENTITIES[0]);assert [w.ability(0,i) for i in range(3)]==original
    assert w.call('ME_ForcedWeather')==2
    # Corrupted or stale sidecars fail before restoring any live state.
    w.flash[0x1E800+100]^=1
    assert w.call('',BUFFER,0x5800,start=0x02049628,limit=3000000)==2
    w.flash[0x1E800:0x1FC00]=b'\xFF'*0x1400
    assert w.call('',BUFFER,0x5800,start=0x02049628,limit=3000000)==0
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase4 quicksave: real native main/checksum wrappers and automatic sidecar,')
    print('  cold restoration of numeric Speed, strong weather and all3 temporary/permanent traits,')
    print('  legacy/no-marker saves, corruption rejection, flash boundaries and main-slot preservation.')
    print('Flash I/O modeled in RAM; no NDS/save output.')


if __name__=='__main__':main()
