"""Resident species aliases for town/resources; allocate with live-cache guards."""
from __future__ import annotations
import hashlib,shutil,struct,subprocess,tempfile
from pathlib import Path
from .mega_evolve_runtime import branch,word
from .state import CaveAllocation,HookRecord
BASE=0x02000000
SIZE=0x400
NAME_SITES=(0x020523A4,0x020523E4,0x0205245C,0x0205268C,0x020526D0)
ORIGIN_SITES={0:(0x02052774,0x020537B8,0x020537D4),
              10:(0x022BF044,0x022BF0B0,0x022BF11C,0x022BFA64),
              29:(0x022FC150,0x022FC258,0x0231A3E8)}
LEARN_SITES=(0x02013888,0x020138F8,0x02013944)


def install(rom,module_dir,state,phase=4,runtime_symbols=None):
    from true_patches.mega_evolve.phase4 import load
    forms=load();arm9=bytearray(rom.arm9);overlays=rom.loadArm9Overlays()
    from .mega_evolve_resident_slot import allocate
    size=0x4F0 if phase>=5 else SIZE
    slot=allocate(arm9,state,size)
    compiler=shutil.which('arm-none-eabi-gcc')
    if not compiler:raise RuntimeError('phase4 needs arm-none-eabi-gcc')
    prefix=str(Path(compiler).with_name('arm-none-eabi-'));suffix='.exe' if compiler.endswith('.exe') else ''
    with tempfile.TemporaryDirectory(prefix='mega_forms_') as temp:
        work=Path(temp);cave=slot.load_address
        (work/'phase4_resident_generated.h').write_text(
            f"#define FIRST {forms['first_species']}\n#define TOTAL {forms['total_species']}\n"
            f'#define SWAP_TRAMPOLINE 0x{cave:X}\n'+
            (f"#define PHASE5 1\n#define SPRITE_FIRST 819\n#define LOAD_NEW_SPRITE 0x{runtime_symbols['ME_LoadNewSprite']:X}\n"
             f"#define REPLACE_NEW_SPRITE 0x{runtime_symbols['ME_ReplaceNewSprite']:X}\n" if phase>=5 else ''),encoding='ascii')
        linker=work/'form.ld'
        linker.write_text(f'SECTIONS {{ . = 0x{cave+16:X}; .text : {{ *(.text*) *(.rodata*) }} '
                          '/DISCARD/ : { *(.ARM.exidx*) *(.comment) *(.ARM.attributes) } }',encoding='ascii')
        elf=work/'form.elf'
        p=subprocess.run([compiler,'-mcpu=arm946e-s','-marm','-Os','-ffreestanding','-fno-builtin',
                          '-fno-unwind-tables','-fno-asynchronous-unwind-tables','-nostdlib',
                          '-Wall','-Wextra','-Werror','-I',str(work),
                          str(module_dir/'runtime/phase4_resident.c'),str(module_dir/'runtime/phase4_resident.S'),
                          '-Wl,-T,'+str(linker),'-o',str(elf)],capture_output=True,text=True)
        if p.returncode:raise RuntimeError(p.stdout+p.stderr)
        output=work/'form.bin'
        subprocess.run([prefix+'objcopy'+suffix,'-O','binary',str(elf),str(output)],check=True,capture_output=True)
        blob=output.read_bytes();symbols={}
        if len(blob)>size-16:raise RuntimeError('phase4 resident allocation exceeded')
        for line in subprocess.check_output([prefix+'nm'+suffix,'--defined-only',str(elf)],text=True).splitlines():
            a,k,n=line.split()
            if n.startswith('ME_'):symbols[n]=int(a,16)
    off=slot.file_offset
    arm9[off:off+size]=bytes(size)
    struct.pack_into('<3I',arm9,off,0xE92D4078,0xE24DD004,branch(cave+8,0x022F75DC))
    arm9[off+16:off+16+len(blob)]=blob
    edits=[];hooks=[]
    def patch(binary,site,expected,symbol):
        data,base=(arm9,BASE) if binary==0 else (overlays[binary].data,overlays[binary].ramAddress)
        if word(data,site,base)!=expected:raise RuntimeError(f'phase4 consumer guard {binary}:{site:#x}')
        is_entry=site in (0x0205476C,0x022F7388,0x022F75D4,
                          0x020204EC,0x0201F5C0,0x0205281C,0x0201D484,0x0201D684,0x0201D590)
        value=branch(site,symbols[symbol],not is_entry)
        struct.pack_into('<I',data,site-base,value)
        edits.append(dict(binary=binary,site=site,after=value,before=expected))
        hooks.append(HookRecord(symbol,site,'b' if is_entry else 'bl',symbol,'explicit_origin'))
    for site in NAME_SITES:patch(0,site,branch(site,0x0208FEA4,True),'ME_OriginDivide')
    for binary,sites in ORIGIN_SITES.items():
        for site in sites:patch(binary,site,branch(site,0x0208FEA4,True),'ME_OriginDivide')
    for site in LEARN_SITES:patch(0,site,0xE1A04000,'ME_LearnOrigin')
    patch(0,0x0204D8CC,0xE1DA70F0,'ME_PortraitOrigin')
    patch(0,0x0205476C,0xE92D4008,'ME_ValidSpecies')
    patch(29,0x022F7388,0xE59F2010,'ME_SpriteCacheIndex')
    patch(29,0x022F74E0,0xE1A06000,'ME_LoadAsset')
    patch(29,0x022F7414,0xE1A07000,'ME_StoreAsset')
    patch(29,0x022F7770,0xE1A05000,'ME_DeleteAsset')
    patch(29,0x022F75D4,0xE92D4078,'ME_SwapAsset')
    if phase>=5:
        patch(0,0x020204EC,0xE5D02000,'ME_ResidentSpriteSizeHook')
        patch(0,0x0201F5C0,0xE59FC000,'ME_ResidentSpriteDecodeHook')
        patch(0,0x0205281C,0xE59F2014,'ME_ResidentSpriteBytesHook')
        patch(0,0x0201D484,0xE92D43F8,'ME_ResidentSpritePackHook')
        patch(0,0x0201D684,0xE92D41F0,'ME_ResidentSpriteSwapHook')
        patch(0,0x0201D590,0xE92D43F8,'ME_ResidentSpriteExternalHook')
    rom.arm9=bytes(arm9)
    for binary in ORIGIN_SITES:
        if binary:rom.files[overlays[binary].fileID]=bytes(overlays[binary].data)
    return dict(cave=CaveAllocation('arm9',off,size,cave),hooks=hooks,symbols=symbols,edits=edits,
                sha256=hashlib.sha256(arm9[off:off+size]).hexdigest())


def verify(rom,info):
    cave=info['cave']
    if hashlib.sha256(rom.arm9[cave.file_offset:cave.file_offset+cave.size]).hexdigest()!=info['sha256']:
        raise AssertionError('phase4 resident bytes changed')
    overlays=rom.loadArm9Overlays()
    for e in info['edits']:
        data,base=(rom.arm9,BASE) if e['binary']==0 else (overlays[e['binary']].data,overlays[e['binary']].ramAddress)
        if word(data,e['site'],base)!=e['after']:raise AssertionError('phase4 consumer changed')
