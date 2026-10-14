"""Parental Bond native effect wrapper: two same-action strikes, second quarter,
single PP cost, eligibility and nested context. Native effect terminal modeled.
"""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,DUNGEON,BUFFER,STOP,STACK
from .phase3 import load
from .phase3_moves import load as move_data,validate_rom
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.manifest import load_module_manifest
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(PreviousWorld):
    def reset(self):super().reset();self.effect_calls=[];self.damage_results=[];self.kill_actor=False;self.nested=False;self.inner_results=[]
    def nested_call(self,name,args,stack_value=0):
        regs=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,
              UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,
              UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
        saved=[self.u.reg_read(r) for r in regs];sp=self.u.reg_read(UC_ARM_REG_SP)-0x2000
        try:
            self.u.reg_write(UC_ARM_REG_SP,sp);self.u.reg_write(UC_ARM_REG_LR,STOP);self.u.mem_write(sp,struct.pack('<I',stack_value))
            for reg,val in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):self.u.reg_write(reg,val)
            self.u.emu_start(self.symbols[name],STOP,count=500000)
            assert self.u.reg_read(UC_ARM_REG_PC)==STOP
            return self.u.reg_read(UC_ARM_REG_R0)
        finally:
            for r,v in zip(regs,saved):self.u.reg_write(r,v)
    def actual_adjustment(self,actor,id_):
        out=BUFFER+0x500;self.u.mem_write(out,struct.pack('<I',100)+bytes(28))
        self.nested_call('ME_AdjustDamage',(actor,ENTITIES[1],out,1),id_)
        return struct.unpack('<I',bytes(self.u.mem_read(out,4)))[0]
    def service(self,u,address,size,data):
        if address==self.loader_info['prior_helpers']['PRIOR_EXECUTE_EFFECT']:
            args=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            fifth=struct.unpack('<I',bytes(u.mem_read(u.reg_read(UC_ARM_REG_SP),4)))[0]
            self.effect_calls.append((args,fifth));actor=args[1];move=args[2];id_=struct.unpack('<H',bytes(u.mem_read(move+4,2)))[0]
            u.mem_write(move+6,bytes([max(0,bytes(u.mem_read(move+6,1))[0]-1)]))
            u.mem_write(MONSTERS[0]+0x12a,bytes([max(0,bytes(u.mem_read(MONSTERS[0]+0x12a,1))[0]-1)]))
            self.damage_results.append(self.actual_adjustment(actor,id_))
            if self.nested and len(self.effect_calls)==2:
                child=BUFFER+0x600;u.mem_write(child,struct.pack('<IHBB',1,21,10,0))
                context=self.nested_call('ME_EnterEffect',(actor,child))
                self.inner_results.append(self.actual_adjustment(actor,21))
                self.nested_call('ME_LeaveEffect',(context,))
                self.inner_results.append(self.actual_adjustment(actor,id_))
            if self.kill_actor:u.mem_write(MONSTERS[0]+0x10,b'\0\0')
            self.ret(77);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());validate_rom(rom)
    manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'parental_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'parental_test':True})
    ids={a['key']:a['id'] for a in load()['abilities']};catalogue=move_data();w=World(rom,record);cases=0
    physical={r['id'] for r in catalogue['target_rules'] if r['category']==0}
    eligible=next(i for i in catalogue['parental_moves'] if i in physical)
    def setup(mode,id_=eligible):
        w.reset();w.u.mem_write(DUNGEON+0x12b78+8,bytes(18*4))
        for i in range(2):w.profile(i,(0,0))
        profile=[(0,0)]*3
        if mode!='none':profile[int(mode[-1])-1 if mode.startswith('slot') else 2]=(ids['부자유친'],0)
        w.profile(0,*profile)
        if mode=='suppressed':w.suppressed.add(ENTITIES[0])
        if mode=='acid':w.u.mem_write(MONSTERS[0]+0xd8,b'\x04')
        move=w.move(id_);w.u.mem_write(move+6,b'\x0a');w.u.mem_write(MONSTERS[0]+0x124,struct.pack('<IHBB',1,id_,10,0))
        return move
    def invoke(move):
        args=[BUFFER+0x700,ENTITIES[0],move,123];w.u.mem_write(STACK,struct.pack('<I',456))
        assert w.call('',*args,start=0x0232e864)==77
        assert w.effect_calls==[(args,456)]*len(w.effect_calls)
        assert w.u.reg_read(UC_ARM_REG_SP)==STACK
    for mode in ('none','slot1','slot2','slot3','suppressed','acid'):
        move=setup(mode);invoke(move);active=mode.startswith('slot')
        assert w.damage_results==([100,25] if active else [100]),(mode,w.damage_results)
        assert bytes(w.u.mem_read(move+6,1))==b'\x09' and bytes(w.u.mem_read(MONSTERS[0]+0x12a,1))==b'\x09';cases+=1
    # All catalogue exclusions must retain one native invocation. Sample a
    # status, native multi-hit, charge, fixed and regular/projectile/Z identity.
    rows=catalogue['target_rules'];excluded=[next(r['id'] for r in rows if r['category']==2),355,405,559]
    from patch_engine.korean_codec import parse_str_file,decode_english
    import re
    normalize=lambda s:re.sub('[^a-z0-9]','',s.lower())
    names=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    for label in ('Solar Beam','Night Shade','Double Slap'):
        excluded.append(next(r['id'] for r in rows if normalize(decode_english(names[8173+r['id']]))==normalize(label)))
    for id_ in excluded:
        assert id_ not in catalogue['parental_moves'];move=setup('slot3',id_);invoke(move)
        assert len(w.effect_calls)==1;cases+=1
    move=setup('slot3');w.kill_actor=True;invoke(move);assert w.damage_results==[100];cases+=1
    move=setup('slot3');w.nested=True;invoke(move);assert w.inner_results==[100,25];cases+=1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print(f'PASS {cases} Parental Bond effect-wrapper cases: native arguments/stack/result, second damage quarter, single PP cost, slots/suppression, fixed/charge/multihit/status/regular/projectile/Z exclusions, death and nested-scope restoration. Native terminal effect modeled; no ROM/save output.')

if __name__=='__main__':main()
