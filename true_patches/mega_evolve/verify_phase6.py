"""Execute the Spring runtime and native menu/conversion boundaries in RAM."""
import hashlib,json,struct
from unittest.mock import patch
from .verify_phase1 import SOURCE,MODULE
from .phase6 import load
from .phase4 import load as forms
from true_patches.luminous_evolution.verify import Machine,ROSTER,STATE,OUT,INDEX
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.mega_evolve_runtime import apply_phase1,verify_phase1
from patch_engine.mega_evolve_phase5_data import prepare
from patch_engine.mega_evolve_phase3_data import installed_translations
from patch_engine.korean_codec import parse_str_file,decode_english,translation_issues

class SpringMachine(Machine):
    def __init__(self,rom,record):
        super().__init__(rom,record.data[0]['spring']['symbols'])
        self.u.mem_write(0x021A0000,rom.getFileByName('BALANCE/monster.md'))
        self.write32(0x020B09B4,0x021A0008)
        info=record.data[0];body=0x02140000
        self.u.mem_write(0x023A7080,bytes(rom.loadArm9Overlays()[36].data))
        payload=rom.getFileByName(info['runtime_file'])
        blob=bytearray(payload[info['runtime_image_offset']:])
        for off in info['runtime_relocations']:
            value=struct.unpack_from('<I',blob,off)[0];struct.pack_into('<I',blob,off,value-0x01000000+body)
        self.u.mem_write(body,bytes(blob));self.write32(info['bootstrap_symbols']['base'],body)
        self.u.mem_write(0x02353538,bytes(4))
        self.run('ME_Spring_Prepare')

def fixture():
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=dict(load_module_manifest(MODULE),phase=6)
    a=json.loads((MODULE/'data/phase5_assets.json').read_text(encoding='utf8'))['assets'][0]
    c=json.loads((MODULE/'data/phase5_conversion.json').read_text(encoding='utf8'))['assets'][0]
    def sprite_fixture(r,m):return prepare(r,m,dict(assets=[a],mapping=[dict(species=1155,asset=0)],missing=[]),dict(converted=1,total=1,assets=[c]))
    with patch('patch_engine.mega_evolve_phase5_data.prepare',sprite_fixture):
        record=apply_phase1(rom,MODULE,manifest,None,{'spring_test':True})
    verify_phase1(rom,MODULE,manifest,record,{'spring_test':True})
    return rom,record,manifest

def native_ui(m,source,level,action,target,message,branch_index=None):
    for address in (0x0202F0B0,0x0202F3A4,0x0202F2C4,0x0203C9E4,0x0203C940,
                    0x02017CB4,0x02017C50,0x02056880,0x0202F650,0x0202B4F0,
                    0x0203C8E0,0x0203A5A8,0x0203AA20,0x0200224C,0x02056410):m.stub(address,lambda:0)
    m.stub(0x0200F26C,lambda:-1);m.stub(0x0238CB98,lambda:0)
    m.stub(0x0238CC64,lambda:m.write32(STATE+0x3C,ROSTER+m.reg(0)*0x44))
    def update():
        old=m.stubs.pop(0x0238A140)
        try:m.run(0x0238C1F8)
        finally:m.stub(0x0238A140,old)
    def pick():
        m.select(0);m.write32(STATE+0xD8,1);m.write32(STATE+0x70,11);update()
        assert int.from_bytes(m.u.mem_read(STATE+0x70,4),'little')==14
    def choose(value):m.stub(0x0202B57C,lambda:value);update()
    def select_target():
        for _ in range(12):
            update()
            if int.from_bytes(m.u.mem_read(STATE+0x70,4),'little')!=24:break
        if branch_index is not None:
            m.stub(0x0202BA20,lambda:4)
            m.native_state(39)
            m.stub(0x0202BCDC,lambda:0);m.stub(0x0202BD10,lambda:branch_index)
            m.stub(0x0202BC44,lambda:0);update()
            assert int.from_bytes(m.u.mem_read(STATE+0x40,4),'little')==branch_index
        slot=int.from_bytes(m.u.mem_read(STATE+0x40,4),'little')
        assert m.read16(STATE+0xC+slot*2)==target
    original=m.record(0,source,level);pick();assert action in [a for _,a in m.menus[-1]]
    choose(action)
    select_target()
    m.native_state(19);choose(7)
    assert bytes(m.u.mem_read(ROSTER,68))==original
    pick();choose(action)
    select_target()
    m.native_state(19);choose(6)
    m.stub(0x02056070,lambda:(_ for _ in ()).throw(AssertionError('Nickname changed')))
    m.native_state(31)
    changed=bytearray(m.u.mem_read(ROSTER,68));assert struct.unpack_from('<H',changed,4)[0]==target
    struct.pack_into('<H',changed,4,source)
    assert bytes(changed)==original and m.messages[-1]==message

def main():
    original_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom,record,manifest=fixture();m=SpringMachine(rom,record);data=load()
    original=NintendoDSRom(SOURCE.read_bytes())
    old16=bytes(original.loadArm9Overlays()[16].data)
    new16=bytes(rom.loadArm9Overlays()[16].data)
    # Preserve the prerequisite runtime, plus every original script file.
    assert new16[0x2BC8:len(old16)]==old16[0x2BC8:]
    def scripts(folder,prefix=''):
        for name in folder.files:
            if prefix.startswith('SCRIPT/'):yield prefix+name
        for name,child in folder.folders:yield from scripts(child,prefix+name+'/')
    for path in scripts(original.filenames):assert original.getFileByName(path)==rom.getFileByName(path)
    texts=[decode_english(x) for x in parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))]
    translations=installed_translations(texts)
    for r in data['strings']:
        assert translations[str(r['index'])]=={'en':r['en'],'ko':r['ko']}
        assert not translation_issues(r['en'],r['ko'])
    by_source={}
    for r in data['routes']:by_source.setdefault(r['source'],[]).append(r)
    for source,edges in by_source.items():
        wanted=edges[0]['target_stage']
        if wanted==0:continue
        levels=(79,80,100) if wanted==1 else (1,79,80)
        for level in levels:
            old=m.record(0,source,level);m.select(0);m.run('ME_Spring_Submenu')
            action=3
            allowed=level>=80 if wanted==1 else True
            assert (action in [a for _,a in m.menus[-1]])==allowed,(source,level)
            assert not any(a in (12,13) for _,a in m.menus[-1])
            assert m.run('ME_Spring_Action',12)==0 and m.run('ME_Spring_Action',13)==0
            if not allowed:continue
            m.run('ME_Spring_Possibilities',ROSTER,STATE+2)
            assert [m.read16(STATE+12+i*2) for i in range(len(edges))]==[r['target'] for r in edges]
            assert m.run('ME_Spring_Convert',INDEX,source)==0
            assert bytes(m.u.mem_read(ROSTER,68))==old
            for edge in edges:
                m.record(0,source,level)
                assert m.run('ME_Spring_Convert',INDEX,edge['target'])==1
                changed=bytearray(m.u.mem_read(ROSTER,68));struct.pack_into('<H',changed,4,source)
                assert bytes(changed)==old
                m.run('ME_Spring_RecordEvolution');assert m.evolution_count==0
        m.u.mem_write(ROSTER,bytes(68))
    print('PASS all Mega/Awakening routes: level79/80, both genders/branches, no shiny gate, no record bonuses',flush=True)
    # Every expanded Mega/Shiny returns exactly one permanent stage, with
    # nickname/XP/doping and the native two history bytes retained.
    for row in forms()['rows']:
        if not row['stage']:continue
        old=m.record(0,row['species'],80);m.u.mem_write(ROSTER+6,b'\x14\x28');old=bytes(m.u.mem_read(ROSTER,68))
        m.select(0);m.run('ME_Spring_Submenu');assert m.run('ME_Spring_Action',10)==1
        target=m.read16(STATE+12)
        expected=row['parent']
        if row['species'] in data['compatibility_only_mega_ids']:
            expected=next(r['source'] for r in data['routes'] if r['target']==row['shiny'] and r['source']<1155)
            expected={555:414,556:415,552:525,551:526,536:529}[expected]
        assert target==expected
        assert m.run('ME_Spring_Convert',INDEX,target)==1
        changed=bytearray(m.u.mem_read(ROSTER,68));struct.pack_into('<H',changed,4,row['species'])
        assert bytes(changed)==old
        if row['stage']==2:
            m.select(0);m.run('ME_Spring_Submenu')
            assert 3 in [a for _,a in m.menus[-1]]
            m.run('ME_Spring_Possibilities',ROSTER,STATE+2)
            assert m.read16(STATE+12)==row['species']
    for parent,new in ((233,2269),(833,2270),(261,2271),(861,2272)):
        for level in (19,20):
            m.record(0,parent,level);m.run('ME_Spring_Possibilities',ROSTER,OUT)
            assert m.read16(OUT+8)==(new if level>=20 else 0)
        old=m.record(0,parent,20);m.select(0);m.run('ME_Spring_Submenu')
        assert m.run('ME_Spring_Convert',INDEX,new)==1
        changed=bytearray(m.u.mem_read(ROSTER,68));struct.pack_into('<H',changed,4,parent)
        assert changed[:6]+changed[8:]==old[:6]+old[8:] and changed[6]==20
    m.record(0,318,20);m.select(0);m.run('ME_Spring_Submenu')
    assert m.run('ME_Spring_Convert',INDEX,319)==1 and len(m.spawned)==1
    assert struct.unpack_from('<H',m.spawned[-1],4)[0]==320
    assert m.read16(ROSTER+4)==319 and m.u.mem_read(ROSTER+6,1)==b'\x14'
    for source in (1,2):
        m.record(0,source,50);m.select(0);m.run('ME_Spring_Submenu')
        assert 3 in [a for _,a in m.menus[-1]]
    # Legacy form changes remain, while Origin no longer bypasses level80.
    m.record(0,418,50);m.select(0);m.run('ME_Spring_Submenu')
    assert m.run('ME_Spring_Action',11)==1
    assert [m.read16(STATE+12+i*2) for i in range(3)]==[419,420,421]
    m.record(0,529,79);m.select(0);m.run('ME_Spring_Submenu')
    assert not any(a in (3,11,12,13) for _,a in m.menus[-1])
    for legacy in (555,556,552,551,536):
        m.record(0,legacy,1);m.select(0);m.run('ME_Spring_Submenu')
        assert 3 in [a for _,a in m.menus[-1]] and not any(a in (12,13) for _,a in m.menus[-1])
    # Labels disambiguate X/Y without renaming the permanent species.
    source=next(s for s,edges in by_source.items() if len(edges)>1 and edges[0]['target_stage']==1)
    m.record(0,source,80);m.select(0);m.run('ME_Spring_Submenu');m.run('ME_Spring_Possibilities',ROSTER,STATE+2)
    labels=[]
    for i,r in enumerate(by_source[source]):
        m.write32(STATE+0x50+i*4,i);m.run('ME_Spring_TargetLabel',OUT,i)
        assert m.string_requests[-1]==r['label'];labels.append(r['label'])
    assert len(set(labels))==len(labels)
    # Cancel then re-enter must reset mode. First story visit exposes no Mega.
    old_count=m.evolution_count
    m.record(0,1,50);m.select(0);m.run('ME_Spring_Submenu');m.run('ME_Spring_RecordEvolution')
    assert m.evolution_count==old_count+1
    m.flags[5]=0;m.run('ME_Spring_Prepare');m.record(0,source,100);m.select(0);m.run('ME_Spring_Submenu')
    assert not any(a in (10,11,12,13) for _,a in m.menus[-1])
    m.flags[5]=1;m.run('ME_Spring_Prepare')
    # Exercise actual native selection, No/Yes and animation mutation callsites.
    one=next(r for r in data['routes'] if r['target_stage']==1 and len(by_source[r['source']])==1)
    ids={r['key']:r['index']+1 for r in data['strings']}
    native_ui(m,one['source'],80,3,one['target'],ids['mega_success'])
    shiny=next(r for r in data['routes'] if r['source']==one['target'])
    native_ui(m,shiny['source'],1,3,shiny['target'],ids['shiny_success'])
    branching=next((s,edges) for s,edges in by_source.items() if len(edges)>1 and edges[0]['target_stage']==1)
    native_ui(m,branching[0],80,3,branching[1][1]['target'],ids['mega_success'],branch_index=1)
    print('PASS native Spring menu/select/No/Yes/animation, devolution, labels, story gating and legacy forms',flush=True)
    ov=rom.loadArm9Overlays()[16];saved=rom.files[ov.fileID]
    altered=bytearray(saved);altered[-1]^=1;rom.files[ov.fileID]=altered
    try:verify_phase1(rom,MODULE,manifest,record,{'spring_test':True})
    except AssertionError:pass
    else:raise AssertionError('Spring runtime corruption accepted')
    rom.files[ov.fileID]=saved
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==original_hash
    report=dict(schema=1,routes=len(data['routes']),expanded_devolution_rows=1114,
                spring_runtime_bytes=record.data[0]['spring']['runtime_bytes'],
                evolve_action=3,separate_mega_actions=False,native_branch_selection=True,
                scope='Actual ARM Spring policy and native menu/record writer; window, item inventory, roster spawn and script services modeled. No NDS/save output.')
    (MODULE/'data/phase6_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('PASS phase6:',report)

if __name__=='__main__':main()
