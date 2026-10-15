"""Replay the real ground flash callback with shared low/ITCM aliases.

Compiles the actual Spring C/ASM in temporary files. ROM and supplied DSS
files are read-only; no full-stack build, ROM or modified state is produced.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from .trace_sprite_corruption import (REPO, read_snapshot, ITCM_OFFSET, ITCM,
                                      SHIFT, words, upload)
from .phase6 import load
from patch_engine.mega_evolve_phase6 import header
from patch_engine.mega_evolve_runtime import branch
from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_PC)

MODULE = Path(__file__).resolve().parent
# Test-only memory for the compiled image. Production uses allocate_cave.
TEST_IMAGE = 0x02400000
CALLBACK = 0x0238CCF0
STATE_PTR = 0x0238CE40
EFFECT_UPDATE = 0x02316168
LEGACY_CALLBACK = (0xE59F000C, 0xE3A01004, 0xE5900000, 0xE58010D8, 0xE12FFF1E)


def compile_spring(rom):
    compiler = shutil.which('arm-none-eabi-gcc')
    if not compiler:
        raise RuntimeError('arm-none-eabi-gcc required')
    prefix = str(Path(compiler).with_name('arm-none-eabi-'))
    suffix = '.exe' if compiler.lower().endswith('.exe') else ''
    ov = rom.loadArm9Overlays()[16]
    with tempfile.TemporaryDirectory(prefix='spring_lifetime_') as temp:
        work = Path(temp)
        (work / 'phase6_generated.h').write_text(header(rom, bytes(ov.data), load()), encoding='ascii')
        (work / 'phase6_generated_asm.h').write_text('', encoding='ascii')
        (work / 'spring.ld').write_text(
            f'SECTIONS {{ . = {TEST_IMAGE}; .text : {{ *(.text*) *(.rodata*) }} '
            '.data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } '
            '/DISCARD/ : { *(.comment) *(.ARM.attributes) *(.ARM.exidx*) } }', encoding='ascii')
        elf = work / 'spring.elf'
        command = [compiler, '-mcpu=arm946e-s', '-marm', '-Os', '-ffreestanding',
                   '-fno-builtin', '-fno-unwind-tables', '-fno-asynchronous-unwind-tables',
                   '-nostdlib', '-Wall', '-Wextra', '-Werror', '-I', str(work),
                   str(MODULE / 'runtime/phase6_spring.c'), str(MODULE / 'runtime/phase6_spring.S'),
                   '-Wl,-T,' + str(work / 'spring.ld'), '-o', str(elf)]
        subprocess.run(command, check=True, capture_output=True)
        output = work / 'spring.bin'
        subprocess.run([prefix + 'objcopy' + suffix, '-O', 'binary', str(elf), str(output)],
                       check=True, capture_output=True)
        symbols = {}
        for line in subprocess.check_output([prefix + 'nm' + suffix, '--defined-only', str(elf)], text=True).splitlines():
            fields = line.split()
            if len(fields) == 3:
                symbols[fields[2]] = int(fields[0], 16)
        return output.read_bytes(), symbols


def replay(raw, blob, symbols, fixed, live):
    ram = raw[328231:ITCM_OFFSET]
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x02000000, 0x400000)
    u.mem_write(0x02000000, ram)
    # Retain a reproducible original-behavior baseline even after the local
    # output ROM itself has the new entry branch installed.
    u.mem_write(CALLBACK, struct.pack('<6I', *LEGACY_CALLBACK, STATE_PTR))
    # Share backing memory, so a store to 000000D8 changes 01FF80D8 exactly
    # as on the DS. Two unrelated emulated buffers would hide the corruption.
    backing = ctypes.create_string_buffer(0x8000)
    ctypes.memmove(ctypes.addressof(backing), raw[ITCM_OFFSET:ITCM_OFFSET + 0x8000], 0x8000)
    for address in (0, ITCM):
        u.mem_map_ptr(address, 0x8000, 7, ctypes.addressof(backing))
    u.mem_write(SHIFT, struct.pack('<I', 0xE1A04204))
    if fixed:
        u.mem_map(TEST_IMAGE, 0x10000)
        u.mem_write(TEST_IMAGE, blob)
        u.mem_write(CALLBACK, struct.pack('<I', branch(CALLBACK, symbols['ME_Spring_AnimationComplete'])))
    controller, effect = 0x023F0000, 0x023F1000
    u.mem_write(STATE_PTR, struct.pack('<I', controller if live else 0))
    u.mem_write(controller, bytes(0x200))
    u.mem_write(controller + 0xD8, struct.pack('<I', 3))
    # The ground effect has its own phase and frame counter. In phase 3 it
    # calls the shop completion unconditionally when frame 179 becomes 180.
    u.mem_write(effect, bytes(0x40))
    u.mem_write(effect + 0xC, struct.pack('<I', 3))
    u.mem_write(effect + 0x16, struct.pack('<H', 179))
    u.mem_write(controller + 0xE0, bytes(4))  # no new effect request
    writes = []

    def watch(cpu, access, address, size, value, unused):
        if address < 0x02000000:
            writes.append(dict(pc=hex(cpu.reg_read(UC_ARM_REG_PC)), address=hex(address),
                               size=size, value=hex(value)))

    u.hook_add(UC_HOOK_MEM_WRITE, watch)
    u.reg_write(UC_ARM_REG_R0, effect)
    u.reg_write(UC_ARM_REG_SP, 0x023FE000)
    u.reg_write(UC_ARM_REG_LR, 0x023FF000)
    u.emu_start(EFFECT_UPDATE, 0x023FF000, count=1000000)
    assert u.reg_read(UC_ARM_REG_PC) == 0x023FF000
    assert u.reg_read(UC_ARM_REG_SP) == 0x023FE000
    instruction = words(bytes(u.mem_read(SHIFT, 4)), 0)[0]
    state = words(bytes(u.mem_read(controller + 0xD8, 4)), 0)[0]
    if not fixed and not live:
        assert instruction == 4
        assert writes == [dict(pc='0x238ccfc', address='0xd8', size=4, value='0x4')]
    else:
        assert instruction == 0xE1A04204 and not writes
    assert state == (4 if live else 3)
    itcm = bytes(u.mem_read(ITCM, 0x4000))
    pixels = upload(ram, itcm, b'\xD4\x21')
    assert pixels == (b'\xD4\x00\x01\x02' if not fixed and not live else b'\x04\x0D\x01\x02')
    return dict(fixed=fixed, controller_live=live, writes=writes, pixels=pixels.hex())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, help='Optional recorded ground snapshot with ov11/ov16 callback code')
    args = parser.parse_args()
    rom_path = REPO / 'PatchTesting/Export Rom/Explorers of Alpha+_kor.nds'
    rom_bytes = rom_path.read_bytes()
    rom = NintendoDSRom(rom_bytes)
    source = None
    if args.state:
        source, raw = read_snapshot(args.state)
    else:
        raw = bytearray(5690006)
        raw[328231:328231 + len(rom.arm9)] = rom.arm9
        for index in (11, 16):
            ov = rom.loadArm9Overlays()[index]
            offset = 328231 + ov.ramAddress - 0x02000000
            raw[offset:offset + len(ov.data)] = ov.data
        raw[ITCM_OFFSET:ITCM_OFFSET + 0x4000] = rom.arm9[0xB3380:0xB7380]
        raw = bytes(raw)
    ram = raw[328231:ITCM_OFFSET]
    observed = words(ram, CALLBACK - 0x02000000, 6)
    assert observed[1:] == (*LEGACY_CALLBACK[1:], STATE_PTR)
    assert observed[0] == LEGACY_CALLBACK[0] or observed[0] >> 24 == 0xEA
    assert words(ram, 0x023162B4 - 0x02000000)[0] == branch(0x023162B4, CALLBACK, True)
    blob, symbols = compile_spring(rom)
    assert len(blob) < 0x8000
    assert symbols['ME_Spring_AnimationComplete'] < TEST_IMAGE + 0x8000
    for fixed in (False, True):
        for live in (False, True):
            print(replay(raw, blob, symbols, fixed, live))
    assert source is None or args.state.read_bytes() == source
    assert rom_path.read_bytes() == rom_bytes
    print('PASS native frame-180 callback: original NULL write reproduced, fixed late callback safe, live completion preserved.')
    print('Native ground effect/callback/pixel upload execute; only effect phase/counter and controller lifetime are selected in copied RAM.')
    print('ROM/state unchanged:', hashlib.sha256(source if source is not None else rom_bytes).hexdigest())


if __name__ == '__main__':
    main()
