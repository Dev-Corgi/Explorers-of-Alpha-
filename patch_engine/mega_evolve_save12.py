"""Resident versioned species codec; no ROM/save output or fixed cave address."""
from __future__ import annotations

import hashlib
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from .hook_registry import branch_target
from .mega_evolve_runtime import branch, word
from .state import CaveAllocation, HookRecord

BASE = 0x02000000
SIZE = 0x280


def install(rom, module_dir, state=None):
    arm9 = bytearray(rom.arm9)
    if word(arm9, 0x02059118, BASE) != 0xE92D41F0:
        raise RuntimeError('save12 roster writer prologue changed')
    reader = word(arm9, 0x02059224, BASE)
    if reader >> 24 != 0xEA:
        raise RuntimeError('save12 requires the resident EVS1 reader')
    for site, target in ((0x02059364, 0x020509C0), (0x0205948C, 0x02050A40)):
        if word(arm9, site, BASE) != branch(site, target, True):
            raise RuntimeError(f'save12 species guard failed at {site:#x}')
    quick = rom.loadArm9Overlays()[30]
    quick_guards=[]
    for site in (0x0238331C, 0x02383334, 0x02384EE4, 0x02385140):
        if word(quick.data, site, quick.ramAddress)!=0xE3A02002:
            raise RuntimeError(f'save12 quicksave species byte width changed at {site:#x}')
        quick_guards.append(dict(site=site,word=0xE3A02002))
    for site,target in ((0x02385C54,0x02385C80),(0x02385CA4,0x02385CD0)):
        expected=branch(site,target)
        if word(quick.data,site,quick.ramAddress)!=expected:
            raise RuntimeError('save12 native quicksave byte codec changed')
        quick_guards.append(dict(site=site,word=expected))
    # Share only audited trampoline padding, never zero-filled live caches.
    from .mega_evolve_resident_slot import allocate
    slot=allocate(arm9,state,SIZE)
    cave = slot.load_address
    compiler = shutil.which('arm-none-eabi-gcc')
    if not compiler:
        raise RuntimeError('save12 needs arm-none-eabi-gcc')
    prefix = str(Path(compiler).with_name('arm-none-eabi-'))
    suffix = '.exe' if compiler.lower().endswith('.exe') else ''
    with tempfile.TemporaryDirectory(prefix='mega_save12_') as directory:
        work = Path(directory)
        (work/'save12_generated.h').write_text(
            f'#define SAVE12_STATE 0x{cave+SIZE-16:X}\n'
            f'#define SAVE12_WRITE_ROSTER 0x{cave:X}\n'
            f'#define SAVE12_READ_ROSTER 0x{branch_target(0x02059224,reader):X}\n',
            encoding='ascii')
        linker = work/'save12.ld'
        linker.write_text(f'SECTIONS {{ . = 0x{cave+16:X}; '
                          '.text : { *(.text*) *(.rodata*) } '
                          '/DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } }',
                          encoding='ascii')
        elf = work/'save12.elf'
        subprocess.run([compiler, '-mcpu=arm946e-s', '-marm', '-Os', '-ffreestanding',
                        '-fno-builtin', '-fno-unwind-tables', '-fno-asynchronous-unwind-tables',
                        '-nostdlib', '-Wall', '-Wextra', '-Werror', '-I', str(work),
                        str(module_dir/'runtime/save12.c'), '-Wl,-T,'+str(linker),
                        '-o', str(elf)], check=True, capture_output=True, text=True)
        binary = work/'save12.bin'
        subprocess.run([prefix+'objcopy'+suffix, '-O', 'binary', str(elf), str(binary)],
                       check=True, capture_output=True)
        payload = binary.read_bytes()
        if len(payload) > SIZE-32:
            raise RuntimeError('save12 exceeds resident allocation')
        symbols = {}
        for line in subprocess.check_output([prefix+'nm'+suffix, '--defined-only', str(elf)], text=True).splitlines():
            fields = line.split()
            if len(fields)==3 and fields[2].startswith('ME_Save12'):
                symbols[fields[2]] = int(fields[0], 16)
    off = slot.file_offset
    arm9[off:off+SIZE] = bytes(SIZE)
    struct.pack_into('<II', arm9, off, 0xE92D41F0, branch(cave+4, 0x0205911C))
    arm9[off+16:off+16+len(payload)] = payload
    edits = []
    hooks = []
    for site, name, link in ((0x02059118, 'ME_Save12WriteRoster', False),
                             (0x02059224, 'ME_Save12ReadRoster', False),
                             (0x02059364, 'ME_Save12WriteSpecies', True),
                             (0x0205948C, 'ME_Save12ReadSpecies', True)):
        before = word(arm9, site, BASE)
        after = branch(site, symbols[name], link)
        struct.pack_into('<I', arm9, site-BASE, after)
        edits.append(dict(site=site, before=before, after=after))
        hooks.append(HookRecord(name, site, 'bl' if link else 'b', name, 'preserve_EVS1'))
    rom.arm9 = bytes(arm9)
    return dict(cave=CaveAllocation('arm9', off, SIZE, cave), hooks=hooks,
                symbols=symbols, state=cave+SIZE-16, edits=edits,
                sha256=hashlib.sha256(arm9[off:off+SIZE]).hexdigest(),
                old_bits=202510, new_bits=203069, marker_offset=0x7F58,
                quick_species_bits=16,quick_guards=quick_guards)


def verify(rom, info):
    cave = info['cave']
    if hashlib.sha256(rom.arm9[cave.file_offset:cave.file_offset+cave.size]).hexdigest()!=info['sha256']:
        raise AssertionError('save12 resident bytes changed')
    for edit in info['edits']:
        if word(rom.arm9, edit['site'], BASE)!=edit['after']:
            raise AssertionError('save12 hook changed')
    quick=rom.loadArm9Overlays()[30]
    for guard in info['quick_guards']:
        if word(quick.data,guard['site'],quick.ramAddress)!=guard['word']:
            raise AssertionError('save12 quicksave width/byte codec changed')
