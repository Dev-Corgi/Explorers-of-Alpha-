"""Read-only ROM/DraStic snapshot diagnostics; never rebuild a ROM.

Run as a module. Supports the observed version-15 DSS wrapper and expanded
5,690,006-byte Complete snapshots; rejects other layouts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools/.korean_jit_test_deps'))

from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_MEM_WRITE, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

RAM_OFFSET = 328231
ITCM_OFFSET = RAM_OFFSET + 0x400000
ITCM = 0x01FF8000
ITCM_FILE = 0xB3380
ITCM_SIZE = 0x4000
SHIFT = ITCM + 0xD8


def words(data, offset, count=1):
    return struct.unpack_from('<' + 'I' * count, data, offset)


def read_snapshot(path):
    original = path.read_bytes()
    raw = original
    if original.startswith(b'DraStic-SaveState---------------'):
        if len(original) < 68 or words(original, 32)[0] != 15:
            raise ValueError('Unsupported DSS header version')
        if words(original, 64)[0] != len(original) - 68:
            raise ValueError('DSS compressed length mismatch')
        decoder = zlib.decompressobj()
        raw = decoder.decompress(original[68:], 5690007)
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('Incomplete, oversized or trailing DSS compressed data')
    if len(raw) != 5690006:
        raise ValueError(f'{path}: unsupported expanded state size {len(raw)}')
    return original, raw


def unpack_sprite(entry):
    if entry[:4] == b'SIR0':
        return entry
    if entry[:4] != b'MEW5':
        raise ValueError('Unsupported added sprite format')
    from skytemple_rust.st_pkdpx import Pkdpx
    total, count = words(entry, 4, 2)
    if not 0 < total <= 0x200000 or not 0 < count <= 64:
        raise ValueError('Invalid MEW5 dimensions')
    parts = []
    offset = 12
    for _ in range(count):
        size = words(entry, offset)[0]
        offset += 4
        if size < 20 or offset + size > len(entry):
            raise ValueError('Invalid MEW5 chunk')
        parts.append(Pkdpx(entry[offset:offset + size]).decompress())
        offset += (size + 3) & ~3
    raw = b''.join(parts)
    if len(raw) != total or raw[:4] != b'SIR0':
        raise ValueError('Invalid decoded WAN')
    return raw


def relocate_sprite(ram, raw, address):
    """Run the snapshot's native SIR0 initializer at the actual buffer address."""
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x02000000, 0x400000)
    u.mem_write(0x02000000, ram)
    u.mem_write(address, raw)
    descriptor, stack, stop = 0x023FC000, 0x023FE000, 0x023FF000

    def watch(cpu, access, target, size, value, unused):
        assert (address <= target and target + size <= address + len(raw)
                or descriptor <= target and target + size <= descriptor + 8
                or stack - 0x1000 <= target and target + size <= stack), hex(target)

    u.hook_add(UC_HOOK_MEM_WRITE, watch)
    u.reg_write(UC_ARM_REG_R0, descriptor)
    u.reg_write(UC_ARM_REG_R1, address)
    u.reg_write(UC_ARM_REG_SP, stack)
    u.reg_write(UC_ARM_REG_LR, stop)
    u.emu_start(0x0201F58C, stop, count=1000000)
    assert u.reg_read(UC_ARM_REG_PC) == stop
    assert u.reg_read(UC_ARM_REG_SP) == stack
    return bytes(u.mem_read(address, len(raw)))


def replay_cache(ram, itcm, packs, species):
    """Replay recorded dungeon cache delete/load/refresh with native allocation.

    Only pack I/O and allocator lock/unlock are replaced. No scheduler, IRQ,
    hardware rendering, map transition or full gameplay is simulated.
    """
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x02000000, 0x400000)
    u.mem_write(0x02000000, ram)
    for base in (0, ITCM):
        u.mem_map(base, 0x8000)
        u.mem_write(base, itcm)
    events, writes = [], []

    def service(cpu, address, size, unused):
        a, b, c = [cpu.reg_read(reg) for reg in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
        if address in (0x02001170, 0x02001188):
            events.append(dict(operation='alloc' if address == 0x02001170 else 'free',
                               argument=a, flags=b if address == 0x02001170 else None))
            return  # Execute the real allocator/free implementation.
        if address in (0x0200C33C, 0x0200C35C):
            blob = bytes(packs[a][b])
            if address == 0x0200C33C:
                cpu.reg_write(UC_ARM_REG_R0, len(blob))
            else:
                cpu.mem_write(c, blob)
        cpu.reg_write(UC_ARM_REG_PC, cpu.reg_read(UC_ARM_REG_LR))

    for address in (0x02001170, 0x02001188, 0x0200C33C, 0x0200C35C,
                    0x02002CB4, 0x02002E98):
        u.hook_add(UC_HOOK_CODE, service, begin=address, end=address)

    def watch(cpu, access, address, size, value, unused):
        if address < 0x02000000:
            writes.append(dict(pc=hex(cpu.reg_read(UC_ARM_REG_PC)), address=hex(address),
                               size=size, value=hex(value)))

    u.hook_add(UC_HOOK_MEM_WRITE, watch)

    def call(address, argument=0):
        u.reg_write(UC_ARM_REG_R0, argument)
        u.reg_write(UC_ARM_REG_SP, 0x023FE000)
        u.reg_write(UC_ARM_REG_LR, 0x023FF000)
        u.emu_start(address, 0x023FF000, count=10000000)
        assert u.reg_read(UC_ARM_REG_PC) == 0x023FF000
        assert u.reg_read(UC_ARM_REG_SP) == 0x023FE000
        return u.reg_read(UC_ARM_REG_R0)

    slots = []
    for item in dict.fromkeys(species):
        call(0x022F7768, item)
        call(0x022F74D4, item)
        slot = call(0x022F7388, item)
        assert 0 < slot < 96
        slots.append(dict(species=item, slot=slot))
    call(0x022FBB1C)
    return dict(reloaded=slots, low_memory_writes=writes, native_allocation_events=events,
                scope='Native recorded dungeon allocation/cache/actor refresh; pack I/O and locks modeled.')


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


def snapshot(path, rom, current_sizes, packs=None, replay=False):
    source, raw = read_snapshot(path)
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

    mismatches, resources = [], []
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
        if current is not None and packs is not None and current == length:
            address = read(manager + slot * 56 + 0x34)[0]
            decoded = unpack_sprite(bytes(packs[pack][index]))
            expected = relocate_sprite(ram, decoded, address)
            live = ram[address - 0x02000000:address - 0x02000000 + length]
            resources.append(dict(slot=slot, pack=pack, index=index, bytes=length,
                                  native_relocated_bytes_match=live == expected))

    md_address = read(0x020B09B4)[0]
    md = rom.getFileByName('UTILITY/monster.md')
    md_offset = md_address - 8 - 0x02000000
    md_matches = ram[md_offset:md_offset + len(md)] == md
    actors, new_species = [], []
    dungeon = read(0x02353538)[0]
    if dungeon:
        for i in range(20):
            entity = read(dungeon + 0x12B78 + i * 4)[0]
            if not entity:
                continue
            monster = read(entity + 0xB4)[0]
            species = struct.unpack_from('<h', ram, monster - 0x02000000 + 4)[0]
            slot = struct.unpack_from('<h', ram, entity - 0x02000000 + 0xA8)[0]
            anim_slot = struct.unpack_from('<H', ram, entity - 0x02000000 + 0x2C + 0x70)[0]
            sprite = struct.unpack_from('<H', ram, md_address - 0x02000000 + species * 68 + 16)[0]
            pack, index = struct.unpack_from('<HH', ram, manager - 0x02000000 + slot * 56 + 0x22)
            actors.append(dict(entity=hex(entity), species=species, slot=slot,
                               animation_slot=anim_slot, pack=pack, index=index,
                               sprite_matches_md=pack == 0 and index == sprite and slot == anim_slot))
            if species >= 1155:
                new_species.append(species)

    payload = rom.getFileByName('MEGA/runtime.bin')
    location = ram.find(payload[:32])
    runtime = dict(current_file_header_found=location >= 0)
    if location >= 0:
        _, _, size, image, count, _, _, _ = words(payload, 0, 8)
        expected = bytearray(payload[image:image + size])
        address = 0x02000000 + location + image
        for i in range(count):
            offset, value = words(payload, 32 + i * 8, 2)
            struct.pack_into('<I', expected, offset, (value - 0x01000000 + address) & 0xFFFFFFFF)
        # The initialized image ends in zero-filled BSS. Compare the prefix
        # through the last nonzero file word, without mislabeling live BSS as
        # corruption. This is an observed prefix bound, not an ELF section map.
        prefix = (max(i for i, byte in enumerate(payload[image:]) if byte) + 4) & ~3
        runtime.update(address=hex(address), compared_prefix_bytes=prefix,
                       relocated_prefix_matches=ram[location + image:location + image + prefix] == expected[:prefix])

    result = upload(ram, itcm, b'\xD4\x21')
    report = dict(path=str(path), sha256=hashlib.sha256(source).hexdigest(),
                expanded_sha256=hashlib.sha256(raw).hexdigest(),
                shift_word=hex(words(itcm, 0xD8)[0]),
                itcm_differences=[hex(ITCM + i) for i in range(0, ITCM_SIZE, 4)
                                  if itcm[i:i + 4] != original[i:i + 4]],
                native_upload_D421=result.hex(), arenas=arenas,
                resources_differ_from_current_rom=mismatches,
                native_resource_comparisons=resources, md_matches_current_rom=md_matches,
                actors=actors, runtime=runtime)
    if replay:
        if not dungeon or not packs or not runtime.get('relocated_prefix_matches') or not md_matches or mismatches:
            raise ValueError('Cache replay requires a compatible current dungeon snapshot')
        report['cache_replay'] = replay_cache(ram, itcm, packs, new_species)
    assert path.read_bytes() == source
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=REPO / 'PatchTesting/Export Rom/Explorers of Alpha+_kor.nds')
    parser.add_argument('--state', type=Path, action='append', default=[])
    parser.add_argument('--report', type=Path)
    parser.add_argument('--replay-cache', action='store_true',
                        help='Replay native cache delete/reload/actor refresh on copied dungeon RAM')
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
    current_sizes, packs = {}, []
    for pack, name in enumerate(('monster', 'm_attack', 'm_ground')):
        entries = FileType.BIN_PACK.deserialize(rom.getFileByName(f'MONSTER/{name}.bin'))
        packs.append(entries)
        for index in range(819, len(entries)):
            entry = bytes(entries[index])
            magic = words(entry, 0)[0]
            if magic == 0x3557454D:  # MEW5 carries its decompressed size.
                current_sizes[pack, index] = words(entry, 4)[0]
            elif magic == 0x30524953:
                current_sizes[pack, index] = len(entry)
            else:
                raise ValueError(f'Unsupported added sprite header: {pack}/{index}')
    states = [snapshot(p, rom, current_sizes, packs, args.replay_cache) for p in args.state]
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
