"""Actual ARM move lock, attack-stat modifier and temporary one-slot exchange."""
from __future__ import annotations
import hashlib,struct
from .verify_phase3 import World as PreviousWorld
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R4,UC_ARM_REG_R6,UC_ARM_REG_R9
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,BUFFER,STACK
from .phase3 import load
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1

class World(PreviousWorld):
    def service(self,u,address,size,data):
        if address in (0x0232e9c4,0x0232eaac):
            self.redirect_result=(address,u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R4))
            self.ret(1);return
        super().service(u,address,size,data)

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=3)
    record=apply_phase1(rom,MODULE,manifest,None,{'actions_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'actions_test':True})
    ids={row['key']:row['id'] for row in load()['abilities']};w=World(rom,record)
    actor,target=ENTITIES[:2];m=MONSTERS[0]
    w.profile(0,(ids['무아지경'],0));w.profile(1,(0,0))
    w.weather(0)
    helper=record.data[0]['base_stats_helpers']['from_monster']
    assert w.call('',m,0,0,start=helper)==101
    context=w.call('ME_EnterCalculation',actor,target)
    assert w.call('',m,0,0,start=helper)==151
    assert w.call('',m,1,0,start=helper)==101
    assert w.call('',m,0,1,start=helper)==101
    w.profile(1,(ids['천진'],0));assert w.call('',m,0,0,start=helper)==101
    w.profile(0,(ids['무아지경'],0),(ids['틀깨기'],0))
    assert w.call('',m,0,0,start=helper)==151
    w.profile(0,(ids['무아지경'],0))
    w.profile(1,(0,0));nested=w.call('ME_EnterCalculation',target,actor)
    w.call('ME_LeaveCalculation',nested);assert w.call('',m,0,0,start=helper)==151
    w.call('ME_LeaveCalculation',context);assert w.call('',m,0,0,start=helper)==101
    # Native move array begins at m+0x124, move ID+4, PP+6.
    for i,id_ in enumerate((20,21,22,23)):
        move=bytearray(8);move[0]=1;struct.pack_into('<H',move,4,id_);move[6]=5
        w.u.mem_write(m+0x124+i*8,bytes(move))
    move=w.move(21);w.u.mem_write(move+6,b'\x05')
    assert w.call('',actor,move,1,start=0x02324b24)==1
    # A miss/no HP change cannot choose a locked move.
    token=w.call('ME_BeginAction',actor,20)
    w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',actor,target,100,1)
    assert w.call('ME_MoveAllowed',actor,move)==1
    w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',90))
    w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',actor,target,100,1)
    assert w.call('',actor,move,0,start=0x02324b24)==0
    locked=w.move(20);w.u.mem_write(locked+6,b'\x05')
    assert w.call('',actor,locked,1,start=0x02324b24)==1
    w.u.mem_write(m+0x12a,b'\0')
    assert w.call('ME_MoveAllowed',actor,locked)==0
    assert w.call('ME_MoveAllowed',actor,w.move(352))==2
    assert w.call('',actor,w.move(352),1,start=0x02324b24)==1
    assert w.call('',actor,w.move(355),1,start=0x02324b24)==1
    w.suppressed.add(actor);assert w.call('ME_MoveAllowed',actor,w.move(21))==1;w.suppressed.clear()
    w.call('ME_EndAction',token)
    # Skip only the redirect block. The original target and its own immunity
    # remain intact; suppressed Stalwart follows the original native branch.
    w.profile(0,(ids['굳건한신념'],0));w.profile(1,(ids['피뢰침'],0))
    registers={UC_ARM_REG_R4:target,UC_ARM_REG_R6:20,UC_ARM_REG_R9:actor}
    w.call('',start=0x0232e9c0,registers=registers)
    assert w.redirect_result[0]==0x0232eaac and w.redirect_result[2]==target
    assert w.call('',target,50,start=0x02301d10)==1
    w.suppressed.add(actor);w.call('',start=0x0232e9c0,registers=registers)
    assert w.redirect_result==(0x0232e9c4,20,target)
    w.suppressed.clear()
    # Non-target wild species also restore their native permanent bytes on
    # floor transition, rather than adopting the temporarily swapped bytes.
    w.reset();w.u.mem_write(MONSTERS[0]+2,struct.pack('<2H',1,1))
    w.profile(0,(ids['부유'],0));w.profile(1,(ids['떠도는영혼'],0))
    w.position(0,10,10);w.position(1,11,10)
    token=w.call('ME_BeginAction',actor,20)
    assert w.call('ME_WanderingSwap',actor,target)==1
    assert w.ability(0,0)==ids['떠도는영혼']
    w.call('ME_EndAction',token)
    w.u.mem_write(0x02100749,b'\x02')
    assert w.ability(0,0)==ids['부유']
    w.u.mem_write(0x02100749,b'\x02');assert w.call('ME_MoveAllowed',actor,w.move(21))==1
    # One selected slot transfers with grade; all other slots and permanent
    # assignments survive. Protected traits reject the whole exchange.
    w.reset();w.profile(0,(ids['부유'],1),(ids['클리어바디'],0))
    w.profile(1,(ids['일렉트릭스킨'],0),(ids['떠도는영혼'],0),(ids['단순'],1))
    w.position(0,10,10);w.position(1,11,10)
    original=[[w.ability(i,j) for j in range(3)] for i in (0,1)]
    token=w.call('ME_BeginAction',actor,20);w.choice=0
    assert w.call('ME_WanderingSwap',actor,target)==1
    assert [w.ability(0,j) for j in range(3)]==[ids['떠도는영혼'],original[0][1],0]
    assert [w.ability(1,j) for j in range(3)]==[original[1][0],original[0][0],original[1][2]]
    w.call('ME_RestoreAbilities',actor);w.call('ME_RestoreAbilities',target)
    assert w.call('ME_WanderingSwap',actor,target)==0 # Same action, restored trait still cannot repeat.
    for i in (0,1):assert [w.ability(i,j) for j in range(3)]==original[i]
    w.call('ME_EndAction',token)
    for protected in ('기분파','멀티타입','일루전','괴짜','절대안깸','Omniscience'):
        w.profile(0,(ids['부유'],0),(ids[protected],0))
        token=w.call('ME_BeginAction',actor,20)
        assert w.call('ME_WanderingSwap',actor,target)==0
        assert w.ability(1,1)==ids['떠도는영혼']
        w.call('ME_EndAction',token)
    for protected in (179,183,190,206,207,208,229,230,241,243,247,251):
        w.profile(0,(protected,0));token=w.call('ME_BeginAction',actor,20)
        assert w.call('ME_WanderingSwap',actor,target)==0
        w.call('ME_EndAction',token)
    w.profile(0,(ids['부유'],0),(ids['부유'],1));token=w.call('ME_BeginAction',actor,20)
    assert w.call('ME_WanderingSwap',actor,target)==1
    assert w.ability(1,1)==ids['부유']|65536
    assert w.ability(0,0)==ids['부유'] and w.ability(0,1)==ids['떠도는영혼']
    w.call('ME_EndAction',token)
    # Full hit dispatcher applies exchange last; non-contact attacks cannot swap.
    w.profile(0,(ids['부유'],0));w.profile(1,(ids['떠도는영혼'],0));w.category=1
    token=w.call('ME_BeginAction',actor,20)
    w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',90))
    w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',actor,target,100,1)
    assert w.ability(0,0)==ids['부유']
    w.category=0;w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',actor,target,100,1)
    assert w.ability(0,0)==ids['떠도는영혼']
    w.call('ME_EndAction',token)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS phase3 actions ARM: physical stat x1.5/Unaware/nested contexts, native move lock,')
    print('  first successful hit/PP/suppression/floor reset; one-slot grade-aware exchange,')
    print('  protected identities, once ledger, restoration, contact-only dispatch and redirect-only bypass.')
    print('No ROM/save output.')

if __name__=='__main__':main()
