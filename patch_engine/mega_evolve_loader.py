"""Uncompressed ARM runtime file, validated relocations and a small ov36 loader.

No fixed execution RAM address, overlay enlargement or table ID compression.
The native default allocator owns the execution block; release follows the
existing DungeonFree callback, after the payload has returned to bootstrap code.
"""
from __future__ import annotations
import hashlib,struct,subprocess,tempfile
from pathlib import Path
from .mega_evolve_runtime import build_runtime,allocate_runtime,OV36,OV29,word
from .state import CaveAllocation
LINK_BASE=0x01000000
PATH='MEGA/runtime.bin'
MAX_IMAGE=0x40000

def checksum(data):
    value=2166136261
    for byte in data:value=((value^byte)*16777619)&0xffffffff
    return value

def relocation_offsets(elf):
    """Allow only internal ABS32 and location-independent ARM branch/REL32.
    Reject unsupported relocations rather than guessing or patching byte values.
    """
    b=elf.read_bytes();off=struct.unpack_from('<I',b,32)[0]
    stride,count=struct.unpack_from('<HH',b,46)
    rows=[struct.unpack_from('<10I',b,off+i*stride) for i in range(count)]
    result=[]
    for row in rows:
        if row[1]!=9:continue
        target=rows[row[7]]
        if not target[2]&2:continue
        symtab=rows[row[6]]
        for pos in range(row[4],row[4]+row[5],row[9]):
            address,info=struct.unpack_from('<II',b,pos)
            kind=info&255;sym=struct.unpack_from('<IIIBBH',b,symtab[4]+(info>>8)*symtab[9])
            internal=sym[5] not in (0,0xfff1)
            if kind==2:
                if sym[5]==0:raise RuntimeError('mega_evolve undefined absolute relocation')
                if internal:result.append(address-LINK_BASE)
            elif kind in (3,28,29,1):
                if not internal:raise RuntimeError(f'mega_evolve nonrelocatable external branch {address:#x}')
            elif kind!=0:raise RuntimeError(f'mega_evolve unsupported ARM relocation {kind}')
    if len(set(result))!=len(result):raise RuntimeError('mega_evolve duplicate relocation')
    return sorted(result)

def install_file(rom,payload):
    from ndspy.fnt import Folder
    folder=rom.filenames.subfolder('MEGA')
    if folder is not None or rom.filenames.idOf(PATH) is not None:
        raise RuntimeError('mega_evolve runtime namespace already occupied')
    # Append a new directory/file; existing FAT IDs, overlays and paths stay stable.
    rom.filenames.folders.append(('MEGA',Folder(files=['runtime.bin'],firstID=len(rom.files))))
    rom.files.append(payload)

def link_runtime(module,ov29,ov36,state,entity_speed,from_monster):
    from .mega_evolve_phase3_runtime import native_defines,elf_sections
    import shutil
    compiler=shutil.which('arm-none-eabi-gcc')
    if not compiler:raise RuntimeError('mega_evolve needs arm-none-eabi-gcc')
    prefix=str(Path(compiler).with_name('arm-none-eabi-'))
    suffix='.exe' if compiler.lower().endswith('.exe') else ''
    defines=native_defines(ov29)
    with tempfile.TemporaryDirectory(prefix='mega_evolve_loader_') as temp:
        work=Path(temp)
        blob,body_symbols=build_runtime(module,work,LINK_BASE,entity_speed,from_monster,3,
            word(ov29,0x02328790,OV29),defines,emit_relocations=True)
        size=(body_symbols['MERuntimeEnd']-LINK_BASE+31)&~31
        if size>MAX_IMAGE:raise RuntimeError(f'mega_evolve execution image exceeds explicit RAM budget: {size}')
        blob=blob.ljust(size,b'\0')
        relocs=relocation_offsets(work/'phase1.elf')
        if any(offset<0 or offset%4 or offset+4>size for offset in relocs):
            raise RuntimeError('mega_evolve relocation outside execution image')
        image_offset=(32+len(relocs)*8+31)&~31
        # GCC may bias an internal anchor beyond its section, then use a
        # negative load offset. Preserve that addend; validate the exact linked
        # word rather than assuming every pointer literal lies inside the image.
        pairs=[v for offset in relocs for v in (offset,struct.unpack_from('<I',blob,offset)[0])]
        tail=struct.pack('<'+'I'*len(pairs),*pairs).ljust(image_offset-32,b'\0')+blob
        digest=checksum(tail);length=32+len(tail)
        payload=struct.pack('<8I',0x4d454752,1,size,image_offset,len(relocs),length,digest,0)+tail
        offsets={k:v-LINK_BASE for k,v in body_symbols.items()}
        exports=sorted(k for k in offsets if k.startswith('ME_'))
        # Bootstrap code is independent of payload size; retain conservative alignment.
        slot,out=allocate_runtime(ov36,state,0x2000)
        (work/'loader_generated.h').write_text('\n'.join(f'#define {k} {v}u' for k,v in {
            'ME_FILE_SIZE':length,'ME_IMAGE_SIZE':size,'ME_IMAGE_OFFSET':image_offset,
            'ME_RELOC_COUNT':len(relocs),'ME_CHECKSUM':digest,'ME_LINK_BASE':LINK_BASE}.items()),encoding='ascii')
        asm=['.syntax unified','.arm','.text']
        for name in exports:
            asm+=['.balign 16',f'.global {name}',f'{name}:']
            if name=='ME_FreeHook':
                asm+=['push {r4,lr}','bl .Lfree_dispatch','mov r4,r0','bl ME_LoaderRelease',
                      'mov r0,r4','pop {r4,pc}','.Lfree_dispatch:']
            asm += ['push {r12}',f'ldr r12,={offsets[name]}','b .Ldispatch','.ltorg']
        asm+=['.balign 16','.Ldispatch:','push {r0-r11,lr}','mrs r4,cpsr','push {r4,r5}',
              'mov r0,r12','bl ME_LoaderResolve','str r0,[sp,#4]','ldr r4,[sp]',
              'msr cpsr_f,r4','add sp,sp,#8','pop {r0-r11,lr}','pop {r12}','ldr pc,[sp,#-60]']
        (work/'loader.S').write_text('\n'.join(asm)+'\n',encoding='ascii')
        script=f'SECTIONS {{ . = {slot.load_address}; .text : {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} .bss : {{ *(.bss*) }} BootstrapEnd = .; /DISCARD/ : {{ *(.ARM.exidx*) *(.comment) *(.ARM.attributes) }} }}'
        (work/'loader.ld').write_text(script,encoding='ascii')
        run=subprocess.run([compiler,'-mcpu=arm946e-s','-marm','-Os','-ffreestanding','-fno-builtin',
            '-fno-unwind-tables','-fno-asynchronous-unwind-tables','-nostdlib','-Wall','-Wextra','-Werror',
            '-I',str(work),str(module/'runtime/loader.c'),str(work/'loader.S'),
            '-Wl,-T,'+str(work/'loader.ld'),'-o',str(work/'loader.elf')],capture_output=True,text=True)
        if run.returncode:raise RuntimeError(run.stdout+run.stderr)
        symbols={}
        for line in subprocess.check_output([prefix+'nm'+suffix,'--defined-only',str(work/'loader.elf')],text=True).splitlines():
            fields=line.split()
            if len(fields)==3:symbols[fields[2]]=int(fields[0],16)
        if symbols['BootstrapEnd']>slot.load_address+slot.size:raise RuntimeError('mega_evolve bootstrap exceeds allocation')
        for s in elf_sections(work/'loader.elf'):
            if s['flags']&2 and s['size']:
                off=s['address']-OV36;out[off:off+s['size']]=s['data']
        bss=[{'offset':s['address']-LINK_BASE,'size':s['size']} for s in elf_sections(work/'phase1.elf') if s['type']==8 and s['flags']&2 and s['size']]
    info={'prior_helpers':defines,'runtime_file':PATH,'runtime_sha256':hashlib.sha256(payload).hexdigest(),
          'runtime_size':size,'runtime_file_size':length,'runtime_image_offset':image_offset,
          'runtime_relocations':relocs,'runtime_symbol_offsets':offsets,'runtime_bss':bss,
          'bootstrap_symbols':symbols,'loading':'uncompressed_default_heap',
          'runtime_ram_budget':MAX_IMAGE}
    return [CaveAllocation('ov36',slot.file_offset,slot.size,slot.load_address)],out,symbols,info,payload
