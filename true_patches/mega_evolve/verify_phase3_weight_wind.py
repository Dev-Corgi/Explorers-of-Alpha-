"""Actual weight-move native path and post-redirection wind guard ABI."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,BUFFER,STACK
from .phase3 import load
from .phase3_moves import load as move_data,validate_rom
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *
from unicorn import UC_HOOK_CODE

class World(PreviousWorld):
    def reset(self):super().reset();self.weight_calls=[];self.continued=[]
    def service(self,u,address,size,data):
        if address==0x02332b20:
            args=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            item=struct.unpack('<I',bytes(u.mem_read(u.reg_read(UC_ARM_REG_SP),4)))[0]
            self.weight_calls.append((args,item));self.ret(1);return
        if address in (0x0232eab0,0x02332818):self.continued.append((address,u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_SP)));self.ret();return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());validate_rom(rom)
    manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'weight_wind_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'weight_wind_test':True})
    data=load();ids={a['key']:a['id'] for a in data['abilities']};w=World(rom,record)
    md=rom.getFileByName('BALANCE/monster.md');md_address=0x022a0000
    pointer=struct.unpack_from('<I',rom.arm9,0x52914)[0]
    def reset():
        w.reset()
        for i in range(20):w.profile(i,(0,0))
        w.u.mem_write(md_address,md);w.u.mem_write(pointer,struct.pack('<I',md_address+8))
    # GetWeightMultiplier executes its actual MD table read; only DealDamage is
    # modeled, allowing the full Low Kick/Grass Knot caller and native args.
    for move_id in (92,458):
        for mode in ('none','light','heavy','both','suppressed','mold'):
            reset()
            if mode in ('light','suppressed','mold','both'):w.profile(1,(ids['라이트메탈'],0))
            if mode=='heavy':w.profile(1,(ids['헤비메탈'],0))
            if mode=='both':w.profile(1,(ids['라이트메탈'],0),(ids['헤비메탈'],0))
            if mode=='suppressed':w.suppressed.add(ENTITIES[1])
            if mode=='mold':w.profile(0,(ids['틀깨기'],0))
            species=struct.unpack('<H',bytes(w.u.mem_read(MONSTERS[1]+4,2)))[0]
            multiplier=struct.unpack_from('<H',md,8+species*0x44+0x28)[0]
            expected=multiplier//2 if mode=='light' else multiplier*2 if mode=='heavy' else multiplier
            move=w.move(move_id)
            assert w.call('',ENTITIES[0],ENTITIES[1],move,66,start=0x023277b8)==1
            assert w.weight_calls==[([ENTITIES[0],ENTITIES[1],move,expected],66)]
            assert w.u.reg_read(UC_ARM_REG_SP)==STACK
            # Lookup outside weight move still has the original species value.
            assert w.call('',species,start=0x020528fc)==multiplier
    reset();w.profile(1,(ids['헤비메탈'],0));assert w.call('ME_WeightForMove',ENTITIES[0],ENTITIES[1],40000)==65535
    # Hurl has a separate native immunity boundary from TryBlowAway.
    for mode in ('none','slot1','slot2','slot3','suppressed','acid','mold'):
        reset();profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids['헤비메탈'],0)
        w.profile(1,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[1])
        if mode=='acid':w.u.mem_write(MONSTERS[1]+0xd8,b'\x04')
        if mode=='mold':w.profile(0,(ids['틀깨기'],0))
        reached=[]
        def boundary(u,address,size,_):
            if address in (0x0231ee68,0x0231ee8c):reached.append(address);u.emu_stop()
        handle=w.u.hook_add(UC_HOOK_CODE,boundary)
        try:
            w.u.reg_write(UC_ARM_REG_SP,STACK);w.u.reg_write(UC_ARM_REG_R0,ENTITIES[0]);w.u.reg_write(UC_ARM_REG_R1,ENTITIES[1])
            w.u.emu_start(0x0231edfc,0x023ff000,count=200000)
            assert reached==[0x0231ee68 if mode.startswith('slot') else 0x0231ee8c],(mode,reached)
        finally:w.u.hook_del(handle)
    # Every audited damaging wind ID blocks; non-damaging wind keeps native effect.
    reset();w.profile(1,(ids['바람타기'],0))
    for row in move_data()['wind_moves']:
        token=w.call('ME_BeginAction',ENTITIES[0],row['id']);old=len(w.stats)
        assert w.call('ME_WindBlocked',ENTITIES[0],ENTITIES[1],w.move(row['id']))==int(row['category']!=2)
        if row['category']!=2:
            assert len(w.stats)==old+1
            assert w.call('ME_WindBlocked',ENTITIES[0],ENTITIES[1],w.move(row['id']))==1
            assert len(w.stats)==old+1
        else:assert len(w.stats)==old
        w.call('ME_EndAction',token)
    for mode in ('mold','suppressed','no_trait','ordinary'):
        reset();w.profile(1,(ids['바람타기'],0))
        if mode=='mold':w.profile(0,(ids['틀깨기'],0))
        if mode=='suppressed':w.suppressed.add(ENTITIES[1])
        if mode=='no_trait':w.profile(1,(0,0))
        assert w.call('ME_WindBlocked',ENTITIES[0],ENTITIES[1],w.move(20 if mode=='ordinary' else 57))==0
        assert not w.stats
    # Real post-redirection hook takes the resolved target r4, not earlier r6.
    reset();w.profile(1,(ids['바람타기'],0));token=w.call('ME_BeginAction',ENTITIES[0],57)
    regs={UC_ARM_REG_R4:ENTITIES[1],UC_ARM_REG_R6:ENTITIES[2],UC_ARM_REG_R8:w.move(57),UC_ARM_REG_R9:ENTITIES[0]}
    w.call('',123,456,789,42,start=0x0232eaac,registers=regs)
    assert w.continued[-1]==(0x02332818,123,STACK) and w.stats[-1][2]==ENTITIES[1]
    w.call('ME_EndAction',token)
    reset();w.profile(1,(ids['바람타기'],0));regs[UC_ARM_REG_R8]=w.move(20)
    w.call('',123,456,789,42,start=0x0232eaac,registers=regs)
    assert w.continued[-1]==(0x0232eab0,ENTITIES[1],STACK)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase3 weight/wind ARM: real MD weight lookup and two move paths, composed modifiers/suppression/Mold Breaker, all audited wind IDs, once/action and post-redirection target ABI. Tailwind lifetime is checked in verify_phase3_tailwind. No ROM/save output.')

if __name__=='__main__':main()
