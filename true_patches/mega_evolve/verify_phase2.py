"""Real linked ARM ability predicates; no ROM or save outputs."""
from __future__ import annotations
import hashlib,json,struct,sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO))
from true_patches.mega_evolve.verify_phase1 import World as BaseWorld,ENTITIES,MONSTERS,BUFFER,SOURCE,MODULE,STOP
from patch_engine.apply_mega_evolve import apply_mega_evolve_module,verify_mega_evolve_module
from patch_engine.manifest import load_module_manifest
from true_patches.mega_evolve.phase2 import load
from ndspy.rom import NintendoDSRom
from unicorn.arm_const import *

class World(BaseWorld):
    def service(self,u,address,size,data):
        a,b=(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1))
        # Execute both native entries, Gas scan and Gastro Acid predicate.
        if address==0x02301D78:return
        if address==0x023467e4:self.ret(a in self.suppressed and b==39)
        elif address==0x02052a04:self.ret(1 if b==0 else 0)
        elif address==0x02052a24:self.ret(3+b)
        elif address==0x022eaa98:self.ret(self.choice)
        elif address in (0x022e2ad8,0x022e6260,0x022fa7dc,0x020258e4,0x022efb04):self.ret()
        else:super().service(u,address,size,data)
    def reset(self):
        super().reset();self.choice=0
        # Cause the runtime's floor identity guard to reset all component banks.
        self.call('ME_GetStoredSpeed',ENTITIES[0])
    def profile(self,i,*pairs):
        values=[p[0]|(p[1]<<16) for p in pairs]
        self.u.mem_write(BUFFER,struct.pack('<'+'I'*len(values),*values))
        assert self.call('ME_SetAbilityProfile',ENTITIES[i],BUFFER,len(values))==1
    def active(self,i,a):return self.call('ME_AbilityActive',ENTITIES[i],a)
    def grade(self,i,a):return self.call('ME_AbilityGrade',ENTITIES[i],a)
    def ability(self,i,j):return self.call('ME_GetAbility',ENTITIES[i],j,0)
    def position(self,i,x,y):self.u.mem_write(ENTITIES[i]+4,struct.pack('<hh',x,y))

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=load_module_manifest(MODULE)
    record=apply_mega_evolve_module('mega_evolve',MODULE,manifest,rom)
    verify_mega_evolve_module(rom,MODULE,manifest,record)
    w=World(rom,record);data=load();ids={e['key']:e['id'] for e in data['entries']}
    from true_patches.mega_evolve.audit_phase2 import build as audit
    assert json.loads((MODULE/'data/phase2_slot_audit.json').read_text(encoding='utf-8'))==audit()
    cb,simple,trace,gas,lev=(ids[k] for k in ('클리어바디','단순','트레이스','화학변화가스','부유'))
    # A third native trait must reach both entry and veneer, including defensive
    # helper callers. Grade remains separate from the legacy effect ID.
    w.profile(0,(cb,0),(simple,1),(lev,1))
    assert w.active(0,55)==1 and w.grade(0,55)==1 and w.grade(0,lev)==1
    for address in (0x02301d10,0x02301d78):
        assert w.call('',ENTITIES[0],55,start=address,registers={UC_ARM_REG_R3:0x12345678})==1
        assert w.u.reg_read(UC_ARM_REG_R3)==0x12345678
    assert w.active(0,0)==0 and w.active(0,255)==0 and w.active(0,65535)==0
    w.profile(0,(55,1));assert w.ability(0,0)==lev|65536
    w.profile(0,(cb,0),(simple,1),(lev,1))
    original=[w.ability(0,j) for j in range(3)]
    # Every assigned identity supports both grades, including new effects which
    # are intentionally implemented later. No implemented-only copy filter.
    for entry in data['entries']:
        w.profile(0,(entry['id'],0),(entry['id'],1),(0,0))
        assert w.grade(0,entry['id'])==1
    w.profile(0,(cb,0),(simple,1),(lev,1))
    for acid in (0,4):
        w.u.mem_write(MONSTERS[0]+0xd8,bytes([acid]))
        assert w.active(0,55)==(acid==0)
    w.u.mem_write(MONSTERS[0]+0xd8,b'\0');w.suppressed.add(ENTITIES[0])
    assert w.active(0,55)==0;w.suppressed.clear()
    # Existing adjacent Gas scan sees a third-slot Gas without recursion. Dead,
    # distant, self and Gastro Acid/item-suppressed sources behave as before.
    w.profile(1,(0,0),(0,0),(gas,0));w.position(0,10,10);w.position(1,11,11)
    assert w.active(0,55)==0 and w.active(1,160)==1
    w.position(1,12,10);assert w.active(0,55)==1
    w.position(1,11,10);w.suppressed.add(ENTITIES[1]);assert w.active(0,55)==1
    w.suppressed.clear();w.u.mem_write(MONSTERS[1]+0xd8,b'\x04');assert w.active(0,55)==1
    w.u.mem_write(MONSTERS[1]+0xd8,b'\0');w.u.mem_write(MONSTERS[1]+0x10,b'\0\0');assert w.active(0,55)==1
    w.profile(1,(0,0));w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',100))
    # Native changes cannot overwrite permanent profile; restoration restores
    # grade and third slot. Skill Swap / Role Play execute actual move bodies.
    w.u.mem_write(MONSTERS[0]+0x60,bytes([3,4]));assert w.active(0,3)==1
    assert w.call('ME_RestoreAbilities',ENTITIES[0])==1
    assert [w.ability(0,j) for j in range(3)]==original
    w.profile(1,(lev,0),(cb,1),(simple,0));second=[w.ability(1,j) for j in range(3)]
    assert w.call('',ENTITIES[0],ENTITIES[1],start=0x02328698)==1
    assert [w.ability(0,j) for j in range(3)]==second
    assert [w.ability(1,j) for j in range(3)]==original
    w.call('ME_RestoreAbilities',ENTITIES[0]);w.call('ME_RestoreAbilities',ENTITIES[1])
    assert w.call('',ENTITIES[0],ENTITIES[1],start=0x0232a188)==1
    assert [w.ability(0,j) for j in range(3)]==second
    w.call('',ENTITIES[0],start=0x022f9194)
    assert [w.ability(0,j) for j in range(3)]==original
    # Trace slot3, duplicate uniqueness, enhancement without candidate pruning.
    fresh=next(e['id'] for e in data['entries'] if not e['legacy_effect_id'])
    w.profile(0,(lev,0),(lev,0),(fresh,0));w.profile(1,(cb,0),(simple,0),(trace,1));w.choice=1
    assert w.call('ME_Trace',ENTITIES[0],ENTITIES[1])==1
    assert w.ability(1,2)==fresh|65536
    w.call('ME_RestoreAbilities',ENTITIES[1])
    w.call('',ENTITIES[0],ENTITIES[1],BUFFER,start=0x022f94f0)
    assert w.ability(1,2)==fresh|65536
    assert w.call('ME_RestoreAbilities',ENTITIES[1])==1
    w.suppressed.add(ENTITIES[1]);assert w.call('ME_Trace',ENTITIES[0],ENTITIES[1])==0;w.suppressed.clear()
    # Unassigned native traits remain copyable/enhanceable too.
    assigned_native={e['legacy_effect_id'] for e in data['entries']}
    legacy=next(i for i in range(1,255) if i not in assigned_native)
    w.profile(0,(legacy,0));assert w.call('ME_Trace',ENTITIES[0],ENTITIES[1])==1
    assert w.ability(1,2)==legacy|65536
    # Once ledger spans hits/targets when target=NULL; target-specific effects
    # are independent. Nested/reflected actions cannot leak claims into parent.
    w.profile(0,(lev,0),(lev,1),(cb,0))
    token=w.call('ME_BeginAction',ENTITIES[0],467);assert token
    assert w.call('ME_ClaimEffect',ENTITIES[0],lev,1,0)==1
    assert w.call('ME_ClaimEffect',ENTITIES[0],55,1,0)==0
    assert w.call('ME_ClaimEffect',ENTITIES[0],lev,1,ENTITIES[1])==1
    nested=w.call('ME_BeginAction',ENTITIES[1],20)
    assert w.call('ME_ClaimEffect',ENTITIES[0],lev,1,0)==1
    assert w.call('ME_EndAction',token)==0
    assert w.call('ME_EndAction',nested)==1
    assert w.call('ME_ClaimEffect',ENTITIES[0],lev,1,0)==0
    assert w.call('ME_EndAction',token)==1
    assert w.call('ME_ClaimEffect',ENTITIES[0],lev,1,0)==0
    # Phase1 services use the new query, including independent Simple/CB grade.
    w.profile(0,(simple,1))
    w.call('ME_SetStoredSpeed',ENTITIES[0],10)
    w.call('ME_ChangeSpeed',ENTITIES[0],ENTITIES[0],-1,0)
    assert w.call('ME_GetStoredSpeed',ENTITIES[0])==9
    w.call('ME_ChangeSpeed',ENTITIES[0],ENTITIES[0],1,0)
    assert w.call('ME_GetStoredSpeed',ENTITIES[0])==11
    w.profile(0,(cb,1));w.call('ME_ChangeSpeed',ENTITIES[0],ENTITIES[0],-1,0)
    assert w.call('ME_GetStoredSpeed',ENTITIES[0])==11
    drought=ids['가뭄'];w.profile(0,(drought,1))
    assert w.call('ME_SetWeatherSource',ENTITIES[0],1,1,drought)==1
    assert w.call('ME_ForcedWeather')==1
    assert w.call('ME_ExportState',BUFFER,1024)==1024
    assert struct.unpack('<H',bytes(w.u.mem_read(BUFFER+4,2)))[0]==2
    assert bytes(w.u.mem_read(BUFFER+96+6,1))==b'\x02'
    assert w.call('ME_ImportState',BUFFER,1024)==1
    w.profile(0,(drought,0));assert w.call('ME_ForcedWeather')==0xffffffff
    assert w.call('ME_SetWeatherSource',ENTITIES[0],1,1,65535)==0
    # Depth overflow is atomic, out-of-order endings cannot pop another action.
    tokens=[w.call('ME_BeginAction',ENTITIES[0],1) for _ in range(4)]
    assert all(tokens) and w.call('ME_BeginAction',ENTITIES[0],1)==0
    for t in reversed(tokens):assert w.call('ME_EndAction',t)==1
    w.profile(0,(lev,1))
    # Invalid profile rejects atomically. Reset/reused entities do not retain
    # traits. Full-stack file remains untouched.
    w.u.mem_write(BUFFER,struct.pack('<III',cb,255,lev))
    snap=[w.ability(0,j) for j in range(3)]
    assert w.call('ME_SetAbilityProfile',ENTITIES[0],BUFFER,3)==0
    assert [w.ability(0,j) for j in range(3)]==snap
    w.u.mem_write(MONSTERS[0]+4,struct.pack('<H',99))
    assert w.ability(0,2)==0
    # Guard every skipped native block before installing any replacement.
    broken=NintendoDSRom(SOURCE.read_bytes());table=broken.loadArm9Overlays()[29]
    raw=bytearray(table.data);struct.pack_into('<I',raw,0x0232a1cc-0x022dc240,0)
    broken.files[table.fileID]=bytes(raw)
    try:apply_mega_evolve_module('mega_evolve',MODULE,manifest,broken)
    except RuntimeError as error:assert 'skipped-block guard' in str(error)
    else:raise AssertionError('unguarded Role Play block accepted')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase2 ARM: 206 identities / both grades, three slots, native queries,')
    print('  Gas/Gastro Acid/items, native Skill Swap/Role Play/Trace/restore, nested once ledger,')
    print('  invalid profiles, entity reuse and cave/instruction/hash guards. No ROM/save outputs.')
if __name__=='__main__':main()
