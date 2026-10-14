"""Phase3 integration checks, with separate normal-family execution suites.

Runs linked ARM services and wrappers with modeled external native services;
unchanged ordinary bodies retain prerequisite native behavior.
No ROM, save, workbook or full-stack output is written.
"""
from __future__ import annotations
import copy,hashlib,json,struct
from .verify_phase2 import World as PreviousWorld
from .verify_phase1 import SOURCE,MODULE,ENTITIES,MONSTERS,BUFFER,STACK,DUNGEON,STOP
from .phase3 import load,build,validate
from .phase3_strings import load_strings
from .status_hooks import ENTRIES
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1,OV29,OV36,word
from patch_engine.mega_evolve_phase3_data import prepare_data,installed_translations
from patch_engine.manifest import load_module_manifest
from patch_engine.apply_mega_evolve import load_registry
from patch_engine.apply_korean import load_source,plan_translation
from patch_engine.korean_codec import parse_str_file,decode_english,build_str_file,translation_issues
from ndspy.rom import NintendoDSRom
from skytemple_files.data.md.handler import MdHandler
from unicorn.arm_const import *


class World(PreviousWorld):
    def __init__(self,rom,record):
        # Effect tests use a relocated heap image. Dedicated loader tests execute
        # the real bootstrap, file boundary and cold/warm/reload dispatch paths.
        info=record.data[0];body_base=0x02140000
        record=copy.deepcopy(record)
        record.data[0]['symbols']={k:body_base+v for k,v in info['runtime_symbol_offsets'].items()}
        record.data[0]['bss_ranges']=[{'address':body_base+s['offset'],'size':s['size']} for s in info['runtime_bss']]
        self.body_base=body_base
        self.payload=rom.getFileByName(info['runtime_file'])
        self.loader_info=info
        super().__init__(rom,record)

    def reset(self):
        info=self.loader_info
        blob=bytearray(self.payload[info['runtime_image_offset']:])
        for offset in info['runtime_relocations']:
            value=struct.unpack_from('<I',blob,offset)[0]
            struct.pack_into('<I',blob,offset,value-0x01000000+self.body_base)
        self.u.mem_write(self.body_base,bytes(blob))
        # Patched native callers still go through actual persistent dispatchers.
        self.u.mem_write(info['bootstrap_symbols']['base'],struct.pack('<I',self.body_base))
        self.heap=0x02290000;self.allocations=[];self.freed=[];self.fail_alloc=False
        self.stats=[];self.thorns=[];self.category=0;self.resolved_type=1
        self.prior_calls=[];self.probability=1
        # Scatter layout has code between BSS sections. Never clear state..end.
        for section in self.record.data[0]['bss_ranges']:
            self.u.mem_write(section['address'],bytes(section['size']))
        end=self.symbols['MERuntimeEnd'];self.symbols['MERuntimeEnd']=self.symbols['state']
        try:super().reset()
        finally:self.symbols['MERuntimeEnd']=end
        for m in MONSTERS:self.u.mem_write(m+0x24,struct.pack('<6H',*([10]*6)))

    def service(self,u,address,size,data):
        args=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
        a,b,c,d=args;sp=u.reg_read(UC_ARM_REG_SP)
        if address==0x02001170:
            if self.fail_alloc:self.ret(0);return
            pointer=self.heap;self.heap=(pointer+a+15)&~15
            self.allocations.append((pointer,a));u.mem_write(pointer,b'\xa5'*a);self.ret(pointer)
        elif address==0x02001188:self.freed.append(a);self.ret()
        elif address==0x020151c8:self.ret(self.category)
        elif address==0x022eab20:self.ret(self.probability)
        elif address in (0x0231399c,0x02313b08,0x023135fc,0x02313814):
            # Native stored-stat routine is external to this service test.
            self.stats.append((address,a,b,c,d,struct.unpack('<2I',bytes(u.mem_read(sp,8)))));self.ret()
        elif address==0x0230d240:
            # Execute the actual CalcDamageFixedWrapper first; only its native
            # fixed-damage service is modeled, including all seven stack args.
            values=struct.unpack('<7I',bytes(u.mem_read(sp,28)))
            assert bytes(u.mem_read(values[0],0x14))==bytes(0x14)
            self.thorns.append((a,b,c,d,values[1:]));self.ret()
        elif address in self.record.data[0]['prior_helpers'].values():
            name=next(k for k,v in self.record.data[0]['prior_helpers'].items() if v==address)
            values=struct.unpack('<5I',bytes(u.mem_read(sp,20)))
            self.prior_calls.append((name,args,values))
            if name.startswith('STATUS_TARGET_'):
                status=int(name.rsplit('_',1)[1])
                head=self.record.data[0]['prior_helpers'][f'STATUS_HEAD_{status}']
                if head>>24!=0xea:
                    mask=head&65535
                    registers=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
                               UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
                               UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,
                               UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC]
                    saved=[r for i,r in enumerate(registers) if mask&(1<<i)]
                    original_sp=sp+len(saved)*4
                    self.prior_calls[-1]=(name,args,struct.unpack('<5I',bytes(u.mem_read(original_sp,20))))
                    for i,r in enumerate(saved):u.reg_write(r,struct.unpack('<I',bytes(u.mem_read(sp+4*i,4)))[0])
                    u.reg_write(UC_ARM_REG_SP,original_sp)
            self.ret(self.resolved_type if name=='PRIOR_MOVE_TYPE' else 77)
        elif address in (0x022e81f8,0x0230d040,0x0234b250):self.ret()
        else:super().service(u,address,size,data)

    def move(self,move_id):
        self.u.mem_write(BUFFER+0x40,bytes(8))
        self.u.mem_write(BUFFER+0x44,struct.pack('<H',move_id))
        return BUFFER+0x40

    def damage(self,type_,move=20,value=100):
        self.u.mem_write(BUFFER,bytes(0x20));self.u.mem_write(BUFFER,struct.pack('<I',value))
        self.u.mem_write(STACK,struct.pack('<I',move))
        self.call('ME_AdjustDamage',ENTITIES[0],ENTITIES[1],BUFFER,type_)
        return struct.unpack('<I',bytes(self.u.mem_read(BUFFER,4)))[0]


def reject(call,message):
    try:call()
    except (ValueError,RuntimeError,AssertionError) as error:
        assert message in str(error),str(error)
    else:raise AssertionError('invalid input accepted: '+message)


def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    data=load();assert data==build()
    strings=load_strings();ids={a['key']:a['id'] for a in data['abilities']}
    from .audit_phase3 import build as coverage
    assert json.loads((MODULE/'data/phase3_coverage.json').read_text(encoding='utf-8'))==coverage()
    assert len(data['base_profiles'])==546 and len(ids)==206
    for mutation,message in [('base_profiles','base profiles'),('legacy_effect_id','identity/effect')]:
        broken=copy.deepcopy(data)
        if mutation=='base_profiles':broken[mutation]['6']=[1,2]
        else:broken['abilities'][0][mutation]=251
        reject(lambda:validate(broken),message)
    manifest=dict(load_module_manifest(MODULE),phase=3)
    assert load_registry(MODULE,manifest)[1]['phase3_ordinary_count']==206
    reject(lambda:load_registry(MODULE,dict(manifest,phase=4)),'not implemented')
    rom=NintendoDSRom(SOURCE.read_bytes())
    md_original=rom.getFileByName('BALANCE/monster.md')
    md0=MdHandler.deserialize(md_original)
    files,edits=prepare_data(rom)
    assert rom.getFileByName('BALANCE/monster.md')==md_original
    md1=MdHandler.deserialize(files['BALANCE/monster.md'])
    untouched=set(range(len(md0.entries)))-set(map(int,data['base_profiles']))
    assert 1137 in untouched
    for i in untouched:
        assert vars(md0.entries[i])==vars(md1.entries[i])
    for edit in edits:
        row=md1.entries[edit['species']]
        assert [row.ability_primary,row.ability_secondary]==edit['after']
    text0=[decode_english(x) for x in parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))]
    assert installed_translations(text0)=={}
    text1=[decode_english(x) for x in parse_str_file(files['MESSAGE/text_e.str'])]
    targets={row['index'] for row in strings['entries']}
    assert all(text1[i]==s for i,s in enumerate(text0) if i not in targets)
    assert len(installed_translations(text1))==len(strings['entries'])
    for row in strings['entries']:assert not translation_issues(row['en'],row['ko'])
    legacy=next(row for row in strings['entries'] if not row['new'])
    changed=text1[:];changed[legacy['index']]+=' stale'
    assert str(legacy['index']) not in installed_translations(changed)
    collision=NintendoDSRom(SOURCE.read_bytes());raw=parse_str_file(collision.getFileByName('MESSAGE/text_e.str'))
    raw.extend([b'']*(19801-len(raw)));raw[19800]=b'Unrelated occupied slot'
    collision.setFileByName('MESSAGE/text_e.str',build_str_file(raw))
    reject(lambda:prepare_data(collision),'occupied')
    record=apply_phase1(rom,MODULE,manifest,None,{'internal_phase3_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'internal_phase3_test':True})
    korean=MODULE.parent/'korean'
    plan=plan_translation(rom,load_source(korean,load_module_manifest(korean)))
    for row in strings['entries']:assert plan.text_dec[row['index']].ko==row['ko']
    assert not any(row['where']=='text_e' and row['index'] in targets for row in plan.rejected)
    assert len(record.caves)==1 and record.caves[0].size==0x2000
    assert record.data[0]['runtime_size']>record.caves[0].size
    w=World(rom,record)
    # Every baseline assignment is actually obtained by the linked ARM bank.
    for species,pair in data['base_profiles'].items():
        w.u.mem_write(MONSTERS[0]+2,struct.pack('<2H',int(species),int(species)))
        w.call('ME_ResetMonster',MONSTERS[0])
        assert [w.ability(0,i) for i in range(3)]==[*pair,0]
    w.u.mem_write(MONSTERS[0]+2,struct.pack('<2H',1137,1137));w.call('ME_ResetMonster',MONSTERS[0])
    w.u.mem_write(MONSTERS[0]+0x60,bytes([250,0]))
    assert w.ability(0,0)==ids['Omniscience']
    # Numeric speed is a calculated bonus, with no stored-stage accumulation.
    for key,weather in [('쓱쓱',4),('엽록소',1),('모래헤치기',2),('눈치우기',5)]:
        w.profile(0,(ids[key],0));w.weather(weather);w.call('ME_SetStoredSpeed',ENTITIES[0],10)
        for _ in range(3):assert w.call('ME_GetSpeed',ENTITIES[0],100,0,0)==200
        assert w.call('ME_GetStoredSpeed',ENTITIES[0])==10
        old=w.call('ME_EnterMovement');assert w.call('ME_LegacyAbilityActive',ENTITIES[0],next(a['legacy_effect_id'] for a in data['abilities'] if a['key']==key),0)==0
        w.call('ME_LeaveMovement',old)
    for key,entry,actor in [('속보',0x02314e1c,True),('불굴의마음',0x0231b364,True),('전기엔진',0x0231b060,False)]:
        w.profile(1,(ids[key],0));w.call('ME_SetStoredSpeed',ENTITIES[1],10)
        movement=bytes(w.u.mem_read(MONSTERS[1]+0x110,4))
        if actor:w.call('',ENTITIES[0],ENTITIES[1],start=entry)
        else:w.call('',ENTITIES[1],start=entry)
        assert w.call('ME_GetStoredSpeed',ENTITIES[1])==11
        assert bytes(w.u.mem_read(MONSTERS[1]+0x110,4))==movement
    # Conversion includes actual resolved type, actor/action/ID, and slot priority.
    w.reset();w.profile(0,(ids['일렉트릭스킨'],0));w.profile(1,(0,0))
    token=w.call('ME_BeginAction',ENTITIES[0],20);move=w.move(20)
    assert w.call('ME_ConvertType',ENTITIES[0],1,move)==5
    assert w.damage(5)==120
    assert w.damage(5,21)==100
    assert w.call('ME_ConvertType',ENTITIES[0],4,move)==4
    assert w.damage(4)==100 # Weather Ball resolved to Water is not converted.
    assert w.call('ME_ConvertType',ENTITIES[0],1,move)==5
    nested=w.call('ME_BeginAction',ENTITIES[1],20)
    assert w.damage(5)==100 # The outer conversion cannot leak into another action.
    w.call('ME_EndAction',nested);assert w.damage(5)==120
    w.call('ME_EndAction',token);assert w.damage(5)==100
    w.profile(0,(ids['프리즈스킨'],0),(ids['일렉트릭스킨'],0))
    assert w.call('ME_ConvertType',ENTITIES[0],1,move)==6
    # Real type/action/calculation wrappers preserve parameters and stack args.
    w.profile(0,(ids['일렉트릭스킨'],0));token=w.call('ME_BeginAction',ENTITIES[0],20)
    assert w.call('',ENTITIES[0],move,start=0x0230227c)==5
    assert w.prior_calls[-1][1][:2]==[ENTITIES[0],move]
    w.u.mem_write(STACK,struct.pack('<5I',11,22,33,44,55))
    assert w.call('',ENTITIES[0],ENTITIES[1],5,60,start=0x0230bbac)==77
    assert w.prior_calls[-1][2]==(11,22,33,44,55)
    w.call('ME_EndAction',token)
    # Actual native status entries: block new ordinary immunity families, then
    # tail-call each original implementation with all register/stack arguments.
    w.reset();w.profile(0,(0,0));w.profile(1,(ids['절대안깸'],0))
    for name,site,_ in (*ENTRIES[:7],ENTRIES[12],ENTRIES[13]):
        count=len(w.prior_calls)
        assert w.call('',ENTITIES[0],ENTITIES[1],3,4,start=site)==0
        assert len(w.prior_calls)==count and w.u.reg_read(UC_ARM_REG_SP)==STACK
    w.profile(1,(0,0));w.profile(2,(ids['스위트베일'],0))
    w.u.mem_write(ENTITIES[1]+0x25,b'\x01');w.u.mem_write(ENTITIES[2]+0x25,b'\x01')
    for name,site,_ in (ENTRIES[0],ENTRIES[7],ENTRIES[12],ENTRIES[13]):assert w.call('',ENTITIES[0],ENTITIES[1],3,4,start=site)==0
    w.profile(2,(ids['아로마베일'],0))
    for name,site,_ in ENTRIES[8:12]:assert w.call('',ENTITIES[0],ENTITIES[1],3,4,start=site)==0
    w.u.mem_write(ENTITIES[2]+0x25,b'\x02')
    for status,(name,site,_) in enumerate(ENTRIES):
        w.u.mem_write(STACK,struct.pack('<5I',91,92,93,94,95))
        assert w.call('',ENTITIES[0],ENTITIES[1],3,4,start=site)==77
        assert w.prior_calls[-1][0]==f'STATUS_TARGET_{status}'
        assert w.prior_calls[-1][1]==[ENTITIES[0],ENTITIES[1],3,4]
        assert w.prior_calls[-1][2]==(91,92,93,94,95)
        assert w.u.reg_read(UC_ARM_REG_SP)==STACK
    w.u.mem_write(STACK,struct.pack('<I',99));w.u.mem_write(MONSTERS[0]+0x128,struct.pack('<H',20))
    assert w.call('',ENTITIES[0],0,17,18,start=0x0232145c)==77
    assert w.prior_calls[-1][1]==[ENTITIES[0],0,17,18] and w.prior_calls[-1][2][0]==99
    assert w.call('ME_ClaimEffect',ENTITIES[0],ids['일렉트릭스킨'],1,0)==0
    # The damage tail reads the native frame's attack type and move ID correctly.
    w.profile(0,(ids['일렉트릭스킨'],0));move=w.move(20)
    token=w.call('ME_BeginAction',ENTITIES[0],20);w.call('ME_ConvertType',ENTITIES[0],1,move)
    w.u.mem_write(BUFFER,struct.pack('<I',100));w.u.mem_write(STACK+0xc,struct.pack('<I',5));w.u.mem_write(STACK+0xf4,struct.pack('<I',20))
    w.call('ME_DamageTailHook',registers={UC_ARM_REG_R8:BUFFER,UC_ARM_REG_R9:ENTITIES[1],UC_ARM_REG_R10:ENTITIES[0]})
    assert struct.unpack('<I',bytes(w.u.mem_read(BUFFER,4)))[0]==120
    w.call('ME_EndAction',token)
    # Hit events: once across hits, numeric Speed, fixed-damage ABI, fatal HP.
    w.reset();w.profile(0,(0,0));w.profile(1,(ids['철가시'],0),(ids['컬리헤어'],0),(ids['지구력'],0))
    w.position(0,10,10);w.position(1,11,10)
    w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',0))
    token=w.call('ME_BeginAction',ENTITIES[0],20)
    for _ in range(3):
        w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',ENTITIES[0],ENTITIES[1],100,1)
    assert len(w.thorns)==1 and w.thorns[0][:4]==(ENTITIES[1],ENTITIES[0],12,0)
    assert w.thorns[0][4]==(0,3,563,0,0,0)
    assert w.call('ME_GetStoredSpeed',ENTITIES[0])==9
    w.call('ME_EndAction',token)
    # Allocate/zero/fail/free all owned heaps; no flags leak across dungeons.
    w.reset();w.profile(0,(ids['전기로바꾸기'],0));w.profile(1,(0,0))
    w.u.mem_write(MONSTERS[0]+0x10,struct.pack('<H',90))
    token=w.call('ME_BeginAction',ENTITIES[1],20)
    w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',ENTITIES[1],ENTITIES[0],100,1)
    w.call('ME_EndAction',token)
    token=w.call('ME_BeginAction',ENTITIES[0],20)
    for _ in range(3):assert w.damage(5)==150 # Calculation/miss does not consume Charge.
    w.u.mem_write(MONSTERS[1]+0x10,struct.pack('<H',90))
    w.u.mem_write(STACK,struct.pack('<I',20));w.call('ME_HitEvent',ENTITIES[0],ENTITIES[1],100,5)
    assert w.damage(5)==150 # Remaining targets/hits in this same move keep the bonus.
    w.call('ME_EndAction',token)
    token=w.call('ME_BeginAction',ENTITIES[0],20);assert w.damage(5)==100
    w.call('ME_EndAction',token)
    w.reset();w.fail_alloc=True
    # reset already allocated the bank; first free it, then force an allocation failure.
    w.call('ME_FreeAbilities')
    assert w.call('ME_BeginAction',ENTITIES[0],20)==0
    assert w.call('ME_EndAction',1)==0
    assert w.call('ME_ClaimEffect',ENTITIES[0],ids['철가시'],1,0)==0
    w.call('ME_ResetMonster',MONSTERS[0])
    w.fail_alloc=False;w.call('ME_FreeAbilities');w.profile(0,(ids['일렉트릭스킨'],0))
    w.call('ME_ConvertType',ENTITIES[0],1,w.move(20))
    active_allocations=w.allocations[len(w.freed):]
    w.call('ME_EnterMovement');w.call('ME_EnterCalculation')
    w.call('',start=0x022deab0) # Free is a void native function.
    assert all(pointer in w.freed for pointer,_ in active_allocations)
    assert w.call('ME_EnterMovement')==0 and w.call('ME_EnterCalculation')==0
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS internal phase3: 546 profiles, assigned bilingual text, protected species/slots,')
    print('  heap image/bootstrap/BSS guards, real ARM numeric speed and conversion/action wrappers,')
    print('  resolved-type skin bonus, hit ledger and fixed-damage ABI, allocation failure/free.')
    print('  14 native status-entry wrappers: Comatose/Sweet Veil/Aroma Veil, Rest/Nightmare, native continuation ABI.')
    print('Public phase3 ordinary implementation enabled; family tests/native inheritance are separate from full battle/hardware validation. No ROM/save output.')


if __name__=='__main__':main()
