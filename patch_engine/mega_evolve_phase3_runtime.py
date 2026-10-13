"""Link function/data sections into dynamically checked prerequisite padding.
No executable heap loading or fixed code-cave addresses are used.
"""
from __future__ import annotations
import hashlib,shutil,struct,subprocess,tempfile
from pathlib import Path
from .mega_evolve_runtime import OV29,OV36,build_runtime,word
from .cave_allocator import find_zero_run
from .cave_reservations import reserved_file_ranges
from .cave_xref import scan_overlay_xrefs
from .ov36_layout import ov36_forbidden_ranges,allocate_ov36_cave
from .state import CaveAllocation

def elf_sections(path):
    b=path.read_bytes()
    if b[:6]!=b'\x7fELF\x01\x01' or struct.unpack_from('<H',b,18)[0]!=40:
        raise ValueError('mega_evolve expects little-endian ARM ELF32')
    off=struct.unpack_from('<I',b,32)[0]
    stride,count,names=struct.unpack_from('<HHH',b,46)
    rows=[struct.unpack_from('<10I',b,off+i*stride) for i in range(count)]
    s=rows[names];strings=b[s[4]:s[4]+s[5]]
    result=[]
    for row in rows:
        name=strings[row[0]:].split(b'\0',1)[0].decode('ascii')
        result.append({'name':name,'type':row[1],'flags':row[2],'address':row[3],
                       'offset':row[4],'size':row[5],'align':row[8],
                       'data':bytes(row[5]) if row[1]==8 else b[row[4]:row[4]+row[5]]})
    return result

def native_defines(ov29):
    from .hook_registry import branch_target
    values={}
    for name,site in [('USE_MOVE',0x0232145c),('MOVE_TYPE',0x0230227c),
                      ('APPLY_DAMAGE',0x02308fe0),('DUNGEON_FREE',0x022deab0),
                      ('FAINT',0x022f7f34),('CALC_DAMAGE',0x0230bbac)]:
        instruction=word(ov29,site,OV29)
        if instruction>>24!=0xea:raise RuntimeError(f'mega_evolve phase3 prior {name} missing')
        values['PRIOR_'+name]=branch_target(site,instruction)
    from true_patches.mega_evolve.status_hooks import ENTRIES
    for i,(name,site,expected) in enumerate(ENTRIES):
        head=word(ov29,site,OV29)
        observed=head&0xff000000 if expected==0xea000000 else head
        if observed!=expected:raise RuntimeError(f'mega_evolve phase3 {name} status entry changed')
        values[f'STATUS_HEAD_{i}']=head
        values[f'STATUS_TARGET_{i}']=branch_target(site,head) if head>>24==0xea else site+4
    return values

def scatter_link(module_dir,ov29,ov36,state,entity_speed,from_monster):
    defines=native_defines(ov29)
    compiler=shutil.which('arm-none-eabi-gcc')
    if not compiler:raise RuntimeError('mega_evolve needs arm-none-eabi-gcc')
    prefix=str(Path(compiler).with_name('arm-none-eabi-'))
    suffix='.exe' if compiler.lower().endswith('.exe') else ''
    runs=find_zero_run(bytes(ov36),0x4000,16,forbidden=ov36_forbidden_ranges())
    if not runs:raise RuntimeError('mega_evolve phase3 has no large prerequisite padding')
    start,length=max(runs,key=lambda item:item[1])
    pieces=[(start,start+length)]
    blockers=[(r.start,r.end) for r in reserved_file_ranges(state,'ov36')]
    blockers.extend(((r.target_file_offset_for(OV36)//16)*16,
                     (r.target_file_offset_for(OV36)//16)*16+16)
                    for r in scan_overlay_xrefs(bytes(ov36),OV36))
    for a,b in sorted(blockers):
        updated=[]
        for lo,hi in pieces:
            if b<=lo or a>=hi:updated.append((lo,hi));continue
            if lo<a:updated.append((lo,a))
            if b<hi:updated.append((b,hi))
        pieces=updated
    pieces=[((lo+15)&~15,hi&~15) for lo,hi in pieces if ((lo+15)&~15)<(hi&~15)]
    allocations=[];result=bytearray(ov36)
    for lo,hi in pieces:
        if hi-lo<128:continue
        slot,result=allocate_ov36_cave(result,OV36,hi-lo,alignment=16,preferred_file_offset=lo,
            reserved_file_offsets=reserved_file_ranges(state,'ov36'))
        allocations.append(CaveAllocation('ov36',slot.file_offset,slot.size,slot.load_address))
    if not allocations:raise RuntimeError('mega_evolve phase3 padding is entirely reserved/referenced')
    with tempfile.TemporaryDirectory(prefix='mega_evolve_phase3_') as temporary:
        work=Path(temporary)
        build_runtime(module_dir,work,0,entity_speed,from_monster,3,word(ov29,0x02328790,OV29),defines)
        flags=['-mcpu=arm946e-s','-marm','-Os','-ffreestanding','-fno-builtin',
               '-fno-unwind-tables','-fno-asynchronous-unwind-tables','-ffunction-sections',
               '-fdata-sections','-Wall','-Wextra','-Werror','-I',str(work)]
        objects=[];sections=[]
        for name,source in [('runtime_c','phase1.c'),('runtime_s','phase1_hooks.S')]:
            obj=work/(name+'.o');objects.append(obj)
            run=subprocess.run([compiler,*flags,'-c',str(module_dir/'runtime'/source),'-o',str(obj)],capture_output=True,text=True)
            if run.returncode:raise RuntimeError(run.stdout+run.stderr)
            sections.extend(dict(s,object=obj) for s in elf_sections(obj)
                if s['size'] and s['flags']&2 and not s['name'].startswith('.ARM.'))
        cursor=[a.load_address for a in allocations]
        placements=[]
        for s in sorted(sections,key=lambda x:(-x['size'],str(x['object']),x['name'])):
            candidates=[]
            for i,a in enumerate(allocations):
                alignment=max(16,s['align']);address=(cursor[i]+alignment-1)&~(alignment-1)
                if address+s['size']<=a.load_address+a.size:candidates.append((a.load_address+a.size-address-s['size'],i,address))
            if not candidates:raise RuntimeError('mega_evolve phase3 sections exceed safe padding: '+s['name'])
            _,i,address=min(candidates)
            cursor[i]=address+s['size'];placements.append((s,address))
        script=['SECTIONS {']
        for i,(s,address) in enumerate(placements):
            script.append(f'.ME_out{i} 0x{address:X} : {{ "{s["object"].as_posix()}"({s["name"]}) }}')
        script.append('MERuntimeEnd = '+str(max(cursor))+'; /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } }')
        linker=work/'scatter.ld';linker.write_text('\n'.join(script),encoding='ascii')
        elf=work/'scatter.elf'
        run=subprocess.run([compiler,'-mcpu=arm946e-s','-marm','-nostdlib',*[str(p) for p in objects],'-Wl,-T,'+str(linker),'-o',str(elf)],capture_output=True,text=True)
        if run.returncode:raise RuntimeError(run.stdout+run.stderr)
        bss=[]
        for s in elf_sections(elf):
            if not s['name'].startswith('.ME_out'):continue
            off=s['address']-OV36;result[off:off+s['size']]=s['data']
            if s['type']==8:bss.append({'address':s['address'],'size':s['size']})
        symbols={}
        for line in subprocess.check_output([prefix+'nm'+suffix,'--defined-only',str(elf)],text=True).splitlines():
            fields=line.split()
            if len(fields)!=3:continue
            address,kind,name=fields
            if name.startswith('ME_') or name in ('state','MERuntimeEnd'):symbols[name]=int(address,16)
    info={'bss_ranges':bss,'prior_helpers':defines,'sections':len(sections),
          'cave_hashes':[hashlib.sha256(result[a.file_offset:a.file_offset+a.size]).hexdigest() for a in allocations]}
    return allocations,result,symbols,info


def install_hooks(ov29,ov36,symbols,patch):
    """Internal phase3 installation; the public module gate stays phase2.

    Preserve the balance damage tail before dispatching new final multipliers.
    A changed prerequisite stops installation before ROM files are written.
    """
    from .mega_evolve_runtime import branch
    from .hook_registry import branch_target
    guards={0x022ffdf4:0xe92d41f0,0x02311088:0xe92d4ff8,
            0x022fd9d4:0xe92d41f8,0x02309a28:branch(0x02309a28,0x022e81f8,True),
            0x02314e54:branch(0x02314e54,0x02314810,True),
            0x0231b094:branch(0x0231b094,0x0231493c,True),
            0x0231b394:branch(0x0231b394,0x0231493c,True)}
    for site,expected in guards.items():
        if word(ov29,site,OV29)!=expected:
            raise RuntimeError(f'mega_evolve phase3 instruction guard failed at {site:#x}')
    entry=0x0230d03c;owner=word(ov29,entry,OV29)
    if owner>>24!=0xea:raise RuntimeError('mega_evolve balance damage tail missing')
    start=branch_target(entry,owner)
    if bytes(ov36[start-OV36:start-OV36+12])!=struct.pack('<III',0xe92d40ff,0xe5987000,0xe3570000):
        raise RuntimeError('mega_evolve unexpected balance damage tail owner')
    exits=[site for site in range(start,start+0x110,4)
           if word(ov36,site,OV36)==branch(site,0x0230d040)]
    if len(exits)!=1:raise RuntimeError('mega_evolve balance damage tail exit changed')
    # This pair belongs only to Punk Rock's defensive multiplier, after its
    # query. The aura multiplier later in the same owner must stay 4/5.
    for offset,expected in ((0x68,0xe3a01004),(0x70,0xe3a01005)):
        if word(ov36,start+offset,OV36)!=expected:
            raise RuntimeError('mega_evolve Punk Rock owner guard failed')
    patch(36,start+0x68,0xe3a01001,'PunkRockDefenseNumerator')
    patch(36,start+0x70,0xe3a01002,'PunkRockDefenseDenominator')
    patch(36,exits[0],branch(exits[0],symbols['ME_DamageTailHook']),
          'ME_DamageTailHook','ME_DamageTailHook')
    hooks=[(0x0232145c,'ME_ActionHook'),
           (0x0230227c,'ME_TypeHook'),(0x0230bbac,'ME_CalculationHook'),
           (0x022ffdf4,'ME_MovementHook'),(0x022f7f34,'ME_FaintHook'),
           (0x02311088,'ME_TurnHook'),(0x022fd9d4,'ME_InitHook'),
           (0x022deab0,'ME_FreeHook'),(0x02309a28,'ME_HitBoundaryHook')]
    for site,name in hooks:
        patch(29,site,branch(site,symbols[name],site==0x02309a28),name,name)
    for site,name in ((0x02314e54,'ME_QuickFeet'),(0x0231b094,'ME_MotorDrive'),(0x0231b394,'ME_Steadfast')):
        patch(29,site,branch(site,symbols[name],True),name,name)
    from true_patches.mega_evolve.status_hooks import ENTRIES
    for name,site,expected in ENTRIES:
        symbol='ME_Status'+name+'Hook'
        patch(29,site,branch(site,symbols[symbol]),symbol,symbol)
