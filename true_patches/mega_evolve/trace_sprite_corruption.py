"""Read-only ROM/expanded DraStic snapshot diagnostics; never rebuild a ROM.

Run as a module. Snapshot offsets apply only to the previously expanded
5,690,006-byte Complete snapshots, not arbitrary compressed emulator states.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools/.korean_jit_test_deps'))

from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

RAM_OFFSET = 328231
ITCM_OFFSET = RAM_OFFSET + 0x400000
ITCM = 0x01FF8000
ITCM_FILE = 0xB3380
ITCM_SIZE = 0x4000
SHIFT = ITCM + 0xD8


def words(data, offset, count=1):
    return struct.unpack_from('<' + 'I' * count, data, offset)


def is_shift_alias(address, size):
    # ARM9 ITCM is mirrored below main RAM. A watch on 01FF80D8 alone
    # misses a null-pointer write to 000000D8, for example.
    return any(0 <= a < 0x02000000 and (a & 0x7FFF) in range(0xD8, 0xDC)
               for a in range(address, address + size))


def upload(arm9, itcm, source):
    """Execute native type-2 upload dispatcher and the actual ITCM routine.

    Only input/output/descriptor/stack storage is synthetic. No allocator,
    Mega runtime, WAN decoder, replacement pixel code or hardware is modeled.
    """
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x02000000, 0x400000)
    u.mem_map(ITCM, 0x8000)
    u.mem_write(0x02000000, bytes(arm9))
    u.mem_write(ITCM, itcm)
    src, dst, descriptor = 0x02200000, 0x02201000, 0x02202000
    stack, stop = 0x023FE000, 0x023FF000
    assert len(source) % 2 == 0
    u.mem_write(src, source)
    u.mem_write(dst - 4, b'SAFE' + bytes(len(source) * 2) + b'SAFE')
    u.mem_write(descriptor, struct.pack('<IIIHBB', len(source) * 2, src, dst, 0, 2, 0))
    writes = []

    def watch(cpu, access, address, size, value, unused):
        if is_shift_alias(address, size):
            writes.append(dict(pc=cpu.reg_read(UC_ARM_REG_PC), address=address,
                               size=size, value=value))

    u.hook_add(UC_HOOK_MEM_WRITE, watch)
    u.reg_write(UC_ARM_REG_R0, descriptor)
    u.reg_write(UC_ARM_REG_SP, stack)
    u.reg_write(UC_ARM_REG_LR, stop)
    u.emu_start(0x0201AB0C, stop, count=100000)
    assert u.reg_read(UC_ARM_REG_PC) == stop
    assert u.reg_read(UC_ARM_REG_SP) == stack
    assert bytes(u.mem_read(dst - 4, 4)) == b'SAFE'
    assert bytes(u.mem_read(dst + len(source) * 2, 4)) == b'SAFE'
    assert not writes, writes
    return bytes(u.mem_read(dst, len(source) * 2))


def snapshot(path, rom, current_sizes):
    raw = path.read_bytes()
    if len(raw) != 5690006:
        raise ValueError(f'{path}: unsupported expanded state size {len(raw)}')
    ram = raw[RAM_OFFSET:ITCM_OFFSET]
    itcm = raw[ITCM_OFFSET:ITCM_OFFSET + ITCM_SIZE]
    original = rom.arm9[ITCM_FILE:ITCM_FILE + ITCM_SIZE]
    # Check two code anchors before interpreting offsets or pointers.
    if itcm[:32] != original[:32] or itcm[0x130:0x150] != original[0x130:0x150]:
        raise ValueError(f'{path}: ITCM layout/ROM mismatch')

    def read(address, count=1):
        if address < 0x02000000 or address + count * 4 > 0x02400000:
            raise ValueError(f'{path}: RAM pointer outside main RAM: {address:#x}')
        return words(ram, address - 0x02000000, count)

    arenas = []
    n = read(0x020B3380)[0]
    if not 1 <= n <= 8:
        raise ValueError(f'{path}: invalid arena count {n}')
    for pointer in read(0x020B33A0, n):
        header = read(pointer, 7)
        assert 0 <= header[3] <= header[4] <= 256
        blocks = [read(header[2] + i * 24, 6) for i in range(header[3])]
        # FindAvailableMemBlock tests *allocator flags* at +4, not content
        # flags at +0; allocated objects also have bit 0 clear at +0.
        available = [b[4] for b in blocks if not b[1] & 1]
        arenas.append(dict(address=hex(pointer), free_bytes=sum(available),
                           largest_free_block=max(available, default=0),
                           blocks=header[3], max_blocks=header[4]))

    mismatches = []
    manager = read(0x020AFC68)[0]
    capacity = struct.unpack_from('<h', ram, manager - 0x02000000 + 0x1508)[0]
    assert capacity == 96
    for slot in range(1, capacity):
        row = manager - 0x02000000 + slot * 56
        pack, index = struct.unpack_from('<HH', ram, row + 0x22)
        if ram[row + 0x21] != 2 or not read(manager + slot * 56 + 0x34)[0]:
            continue
        current = current_sizes.get((pack, index))
        length = words(ram, row + 0x28)[0]
        if current is not None and current != length:
            mismatches.append(dict(slot=slot, pack=pack, index=index,
                                   snapshot_bytes=length, current_bytes=current))

    result = upload(ram, itcm, b'\xD4\x21')
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(),
                shift_word=hex(words(itcm, 0xD8)[0]),
                itcm_differences=[hex(ITCM + i) for i in range(0, ITCM_SIZE, 4)
                                  if itcm[i:i + 4] != original[i:i + 4]],
                native_upload_D421=result.hex(), arenas=arenas,
                resources_differ_from_current_rom=mismatches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=REPO / 'PatchTesting/Export Rom/Explorers of Alpha+_kor.nds')
    parser.add_argument('--state', type=Path, action='append', default=[])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    rom_bytes = args.rom.read_bytes()
    rom = NintendoDSRom(rom_bytes)
    original = bytes(rom.arm9[ITCM_FILE:ITCM_FILE + ITCM_SIZE])
    assert words(original, 0xD8)[0] == 0xE1A04204
    source = bytes(range(256))
    expected = bytes(v for byte in source for v in (byte & 15, byte >> 4))
    assert upload(rom.arm9, original, source) == expected
    damaged = bytearray(original)
    struct.pack_into('<I', damaged, 0xD8, 4)
    actual = upload(rom.arm9, bytes(damaged), source)
    assert actual == bytes(v for i, byte in enumerate(source)
                           for v in ((byte, 0) if i % 2 == 0 else (byte & 15, byte >> 4)))
    assert upload(rom.arm9, original, b'\xD4\x21') == b'\x04\x0D\x01\x02'
    assert is_shift_alias(0xD8, 4) and is_shift_alias(SHIFT, 4)
    assert is_shift_alias(0x80D8, 4) and not is_shift_alias(0x020000D8, 4)

    from skytemple_files.common.types.file_types import FileType
    current_sizes = {}
    for pack, name in enumerate(('monster', 'm_attack', 'm_ground')):
        entries = FileType.BIN_PACK.deserialize(rom.getFileByName(f'MONSTER/{name}.bin'))
        for index in range(819, len(entries)):
            entry = bytes(entries[index])
            magic = words(entry, 0)[0]
            if magic == 0x3557454D:  # MEW5 carries its decompressed size.
                current_sizes[pack, index] = words(entry, 4)[0]
            elif magic == 0x30524953:
                current_sizes[pack, index] = len(entry)
            else:
                raise ValueError(f'Unsupported added sprite header: {pack}/{index}')
    states = [snapshot(p, rom, current_sizes) for p in args.state]
    report = dict(rom=str(args.rom), rom_sha256=hashlib.sha256(rom_bytes).hexdigest(),
                  native_upload_256_inputs='pass',
                  corrupted_shift_256_inputs='reproduced', snapshots=states,
                  limitation='Snapshots cannot identify a historical writer or prove current gameplay is fixed.')
    if args.report:
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    assert args.rom.read_bytes() == rom_bytes
    print('PASS native pixel reproduction and snapshot audit; ROM/states unchanged. No gameplay certification.')


if __name__ == '__main__':
    main()
