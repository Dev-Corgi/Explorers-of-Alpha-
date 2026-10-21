"""Shop-local, uncompressed Spring runtime integrated after luminous_evolution."""
import hashlib,json,shutil,struct,subprocess,tempfile
from collections import Counter
from pathlib import Path
from ndspy.code import saveOverlayTable
from .state import CaveAllocation,HookRecord
from .cave_allocator import allocate_cave
from .cave_reservations import FileRange,reserved_file_ranges
from .mega_evolve_runtime import branch,word
from .hook_registry import branch_target
from .korean_codec import parse_str_file,build_str_file,decode_english
from true_patches.mega_evolve.phase6 import load
from true_patches.mega_evolve.phase4 import load as forms
LOAD=0x0238A140
SIZE=0x8000

def header(rom,ov,data):
    from skytemple_files.data.md.handler import MdHandler
    from true_patches.luminous_evolution.policy import relationship_tables
    legacy=Path(__file__).resolve().parents[1]/'true_patches/luminous_evolution'
    relationships=json.loads((legacy/'data/forms.json').read_text(encoding='utf-8'))
    md=MdHandler.deserialize(rom.getFileByName('BALANCE/monster.md'))
    previous,groups,targets,secondary=relationship_tables(md.entries[:1155],relationships['groups'],relationships['regression_overrides'])
    total=data['total_species'];previous.extend([0]*(total-len(previous)));stages=[0]*total
    registry=json.loads((legacy.parent/'mega_evolve/data/registry.json').read_text(encoding='utf-8'))
    for t in registry['targets']:
        if t['source_rom_id']==t['special_existing_target'] and t['official_form'] in ('Origin','Primal'):
            stages[t['source_rom_id']]=1;previous[t['source_rom_id']]=t['special_base_source']
    by_key={t['key']:t for t in registry['targets']}
    for row in forms()['rows']:
        stages[row['species']]=row['stage'];previous[row['species']]=row['parent']
        if row['species'] in data['compatibility_only_mega_ids']:
            previous[row['species']]=by_key[row['target']]['special_base_source']
    labels=[0]*600
    for item in json.loads((legacy/'data/texts.json').read_text(encoding='utf-8'))['text_e']:
        if 'species' in item:labels[item['species']]=item['index']+1
    offsets=[];pos=0
    for species in range(total+1):
        while pos<len(data['routes']) and data['routes'][pos]['source']<species:pos+=1
        offsets.append(pos)
    constants={'SPRING_STATE_PTR':word(ov,0x0238B0CC,LOAD),'SUBMENU_WINDOW':word(ov,0x0238B0F8,LOAD),
               'SUBMENU_FLAGS':0x13,'TEAM_COUNT':word(ov,0x0238CC60,LOAD),'MD_COUNT':total,'FORM_FIRST':1155,
               'STR_REGRESSION':19701,'STR_FORM':19702,'STR_REG_CONFIRM':19703,'STR_FORM_CONFIRM':19704,
               'STR_REG_SUCCESS':19705,'STR_FORM_SUCCESS':19706,'STR_FORM_SELECT':19707}
    constants.update({'STR_'+r['key'].upper():r['index']+1 for r in data['strings']})
    out=''.join(f'#define {k} {v}\n' for k,v in constants.items())
    def array(name,values,typ='unsigned short'):
        return f'static const {typ} {name}[]={{'+','.join(map(str,values))+'};\n'
    out+=array('previous_species',previous)+array('mega_stage',stages,'unsigned char')
    out+=array('route_offsets',offsets)+array('form_groups',groups,'unsigned char')
    out+=array('form_secondary',secondary,'unsigned char')+array('form_labels',labels)
    out+='static const unsigned short form_targets[][4]={'+','.join('{'+','.join(map(str,r))+'}' for r in targets)+'};\n'
    out+='typedef struct {unsigned short source,target,level,stage,label;} MERoute;\n'
    out+='static const MERoute mega_routes[]={'+','.join('{'+','.join(map(str,(r['source'],r['target'],r['level'] or 0,r['target_stage'],r['label'])))+'}' for r in data['routes'])+'};\n'
    return out

def install(rom,module,state,record):
    data=load();tables=rom.loadArm9Overlays();ov=tables[16]
    if ov.ramAddress!=LOAD or ov.bssSize:raise RuntimeError('phase6 Spring overlay layout changed')
    source=bytes(ov.data);arm9=bytearray(rom.arm9)
    if tuple(word(source,site,LOAD) for site in (0x0238CCF0,0x0238CCF4,0x0238CCF8,0x0238CCFC,0x0238CD00))!=(
            0xE59F000C,0xE3A01004,0xE5900000,0xE58010D8,0xE12FFF1E):
        raise RuntimeError('phase6 Spring animation completion callback changed')
    # Luminous prerequisite signatures and original resident writer are required.
    if word(arm9,0x02059B0C,0x02000000)!=0xE3A00005 or word(arm9,0x0205A340,0x02000000)!=0xE92D4070:
        raise RuntimeError('phase6 luminous Spring prerequisite missing')
    source_end=LOAD+len(source)
    def prior(site,blob=source,base=LOAD,link=True):
        v=word(blob,site,base)
        if v>>24!=(0xEB if link else 0xEA):raise RuntimeError('phase6 Spring prior hook changed')
        target=branch_target(site,v)
        if not LOAD+0x2BC8<=target<source_end:raise RuntimeError('phase6 prior Spring target outside prerequisite')
        return target
    for site in (0x02039F30,0x02039F74,0x02039FF0):prior(site,arm9,0x02000000)
    counts=Counter()
    for off in range(0,0x2BC8,4):
        v=word(source,LOAD+off,LOAD)
        if v>>24==0xEB:
            target=branch_target(LOAD+off,v)
            if LOAD+0x2BC8<=target<source_end:counts[target]+=1
    messages=[target for target,n in counts.items() if n>=20]
    if len(messages)!=1:raise RuntimeError('phase6 Spring message inventory changed')
    extended=source+bytes(SIZE+16)
    slot=allocate_cave(extended,LOAD,SIZE,alignment=16,preferred_file_offset=(len(source)+15)&~15,
                       forbidden_file_offsets=[FileRange(0,len(source))],reserved_file_offsets=reserved_file_ranges(state,'ov16'))
    if slot.load_address+SIZE>0x023A7080:raise RuntimeError('phase6 Spring extension would overlap ov36')
    compiler=shutil.which('arm-none-eabi-gcc')
    if not compiler:raise RuntimeError('phase6 requires arm-none-eabi-gcc')
    prefix=str(Path(compiler).with_name('arm-none-eabi-'));suffix='.exe' if compiler.endswith('.exe') else ''
    with tempfile.TemporaryDirectory(prefix='mega_spring_') as temp:
        work=Path(temp);(work/'phase6_generated.h').write_text(header(rom,source,data),encoding='ascii')
        (work/'phase6_generated_asm.h').write_text('',encoding='ascii')
        linker=work/'spring.ld';linker.write_text(f'SECTIONS {{ . = 0x{slot.load_address:X}; .text : {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} .bss : {{ *(.bss*) *(COMMON) }} ME_SpringRuntimeEnd = .; /DISCARD/ : {{ *(.comment) *(.ARM.attributes) *(.ARM.exidx*) }} }}',encoding='ascii')
        elf=work/'spring.elf'
        result=subprocess.run([compiler,'-mcpu=arm946e-s','-marm','-Os','-ffreestanding','-fno-builtin','-fno-unwind-tables',
             '-fno-asynchronous-unwind-tables','-nostdlib','-Wall','-Wextra','-Werror','-I',str(work),
             str(module/'runtime/phase6_spring.c'),str(module/'runtime/phase6_spring.S'),'-Wl,-T,'+str(linker),'-o',str(elf)],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        binary=work/'spring.bin';subprocess.run([prefix+'objcopy'+suffix,'-O','binary',str(elf),str(binary)],check=True,capture_output=True)
        symbols={}
        for line in subprocess.check_output([prefix+'nm'+suffix,'--defined-only',str(elf)],text=True).splitlines():
            a,k,n=line.split()
            if n.startswith('ME_Spring'):symbols[n]=int(a,16)
        if symbols['ME_SpringRuntimeEnd']>slot.load_address+SIZE:raise RuntimeError('phase6 Spring allocation exceeded')
        blob=binary.read_bytes()
    patched=bytearray(extended[:slot.file_offset+SIZE]);patched[slot.file_offset:slot.file_offset+len(blob)]=blob
    edits=[]
    site=0x0238CCF0
    value=branch(site,symbols['ME_Spring_AnimationComplete'])
    struct.pack_into('<I',patched,site-LOAD,value)
    edits.append(dict(binary=16,site=site,before=word(source,site,LOAD),after=value))
    record.hooks.append(HookRecord('ME_Spring_AnimationComplete',site,'b',
                                  'ME_Spring_AnimationComplete','spring_animation_lifetime'))
    def patch(site,name,link=True,binary=16):
        b,base=(arm9,0x02000000) if binary==0 else (patched,LOAD)
        old=word(b,site,base);prior(site,bytes(b),base,link)
        new=branch(site,symbols[name],link);struct.pack_into('<I',b,site-base,new)
        edits.append(dict(binary=binary,site=site,before=old,after=new))
        record.hooks.append(HookRecord(name,site,'bl' if link else 'b',name,'spring_progression'))
    for site in (0x02039F30,0x02039F74,0x02039FF0):patch(site,'ME_Spring_Eligibility',binary=0)
    for site,name,link in ((0x0238C148,'ME_SpringInitStub',False),(0x0238A614,'ME_SpringSubmenuA',False),
        (0x0238B614,'ME_SpringSubmenuB',False),(0x0238C57C,'ME_SpringActionStub',False),
        (0x0238CBD0,'ME_Spring_Count',False),(0x0238CB30,'ME_Spring_TargetLabel',False),
        (0x0238C484,'ME_Spring_Possibilities',True),(0x0238ABB4,'ME_Spring_Convert',True),
        (0x0238BBB4,'ME_Spring_Convert',True),(0x0238AB14,'ME_Spring_RecordEvolution',True),
        (0x0238BB14,'ME_Spring_RecordEvolution',True)):patch(site,name,link)
    for off in range(0,0x2BC8,4):
        site=LOAD+off;v=word(source,site,LOAD)
        if v>>24==0xEB and branch_target(site,v)==messages[0]:patch(site,'ME_Spring_Message')
    strings=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    for r in data['strings']:
        i=r['index']
        if i<len(strings) and decode_english(strings[i]).strip():raise RuntimeError('phase6 string index occupied')
        strings.extend([b'']*max(0,i+1-len(strings)));strings[i]=r['en'].encode('ascii')
    rom.setFileByName('MESSAGE/text_e.str',build_str_file(strings));rom.arm9=bytes(arm9)
    ov.data=patched;ov.ramSize=len(patched);ov.compressed=False
    rom.files[ov.fileID]=ov.save(compress=False);rom.arm9OverlayTable=saveOverlayTable(tables)
    cave=CaveAllocation('ov16',slot.file_offset,SIZE,slot.load_address);record.caves.append(cave)
    return dict(cave=cave.to_dict(),symbols=symbols,edits=edits,sha256=hashlib.sha256(patched[slot.file_offset:]).hexdigest(),
                runtime_bytes=symbols['ME_SpringRuntimeEnd']-slot.load_address,strings=data['strings'],source_bytes=len(source))

def verify(rom,info):
    ov=rom.loadArm9Overlays()[16];cave=info['cave']
    blob=bytearray(ov.data[cave['file_offset']:cave['file_offset']+cave['size']])
    addon=info['symbols'].get('ME_SpringCompletionAddon')
    if addon is not None and cave['load_address']<=addon<=cave['load_address']+cave['size']-4:
        blob[addon-cave['load_address']:addon-cave['load_address']+4]=b'\xff'*4
    if hashlib.sha256(blob).hexdigest()!=info['sha256']:
        raise AssertionError('phase6 Spring runtime drift')
    for e in info['edits']:
        b,base=(rom.arm9,0x02000000) if e['binary']==0 else (ov.data,LOAD)
        if word(b,e['site'],base)!=e['after']:raise AssertionError('phase6 Spring hook drift')
    text=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    if any(decode_english(text[r['index']])!=r['en'] for r in info['strings']):raise AssertionError('phase6 Spring strings drift')
