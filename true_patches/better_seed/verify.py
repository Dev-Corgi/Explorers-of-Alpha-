"""Apply to temporary ROMs; run native seed/explosion tile enumeration in ARM."""
from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))
from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from patch_engine.apply_module import apply_module, verify_module_applied
from patch_engine.build_full_stack import FULL_STACK_MODULES

MODULE = Path(__file__).resolve().parent
DUNGEON, ENTITIES, INFOS, TILES = 0x02100000, 0x02140000, 0x02150000, 0x02180000
SP, RETURN = 0x0273F000, 0x021F0000


def target(data, base, address):
    word = struct.unpack_from('<I', data, address - base)[0]
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return address + 8 + imm * 4


class Machine:
    def __init__(self, rom, prior_seed):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(0x02000000, 0x400000)
        self.uc.mem_map(0x02700000, 0x40000)
        self.uc.mem_write(0x02000000, bytes(rom.arm9))
        for i, ov in rom.loadArm9Overlays().items():
            if i in (10, 29, 36):
                self.uc.mem_write(ov.ramAddress, bytes(ov.data))
        self.prior_seed = prior_seed
        self.uc.hook_add(UC_HOOK_CODE, self.service)

    def word(self, a, v):
        self.uc.mem_write(a, struct.pack('<I', v))

    def entity(self, i):
        return ENTITIES + i * 0xB8

    def info(self, i):
        return INFOS + i * 0x240

    def setup(self, ally=False, near=False, rain=False, damp=False, immune=False):
        self.uc.mem_write(DUNGEON, bytes(0x2CC00))
        self.uc.mem_write(TILES, bytes(56 * 32 * 32))
        self.word(0x02353538, DUNGEON)
        self.damage, self.fixed, self.prior = [], [], []
        self.rain, self.damp, self.immune = rain, damp, immune
        positions = [(10, 8) if near else (2, 2), (10, 10), (9, 10), (12, 10), (13, 10), (10, 11)]
        for i, (x, y) in enumerate(positions):
            e, info = self.entity(i), self.info(i)
            self.word(e, 1)
            self.uc.mem_write(e + 4, struct.pack('<hh', x, y))
            self.word(e + 0xB4, info)
            self.uc.mem_write(info, bytes(0x240))
            self.uc.mem_write(info + 6, bytes([int(i not in (0, 5) and not (i == 1 and ally))]))
            self.uc.mem_write(info + 0x10, struct.pack('<H', 100 + i * 200))
            self.word(DUNGEON + 0x12B78 + i * 4, e)
            self.word(TILES + (y * 56 + x) * 32 + 0xC, e)
        for index in range(56 * 32):
            self.uc.mem_write(TILES + index * 32, b'\x01\x00')

    def service(self, uc, a, _size, _data):
        if a == RETURN:
            uc.emu_stop()
            return
        r0, r1, r2, r3 = (uc.reg_read(reg) for reg in
                           (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        sp = uc.reg_read(UC_ARM_REG_SP)
        if a == 0x02332C4C:
            self.damage.append((r0, r1, r3, struct.unpack('<II', uc.mem_read(sp, 8))))
            value = 40
        elif a == self.prior_seed and a != 0x0230D3A8:
            self.prior.append((r0, r1))
            value = 40
        elif a == 0x0230D3A8:
            self.fixed.append((r0, r1, r2))
            value = 40
        elif a == 0x02336164:  # GetTile
            assert 0 <= r0 < 56 and 0 <= r1 < 32
            value = TILES + (r1 * 56 + r0) * 32
        elif a == 0x02301D78:  # Damp
            value = int(self.damp and r1 == 0x15)
        elif a == 0x022E28D4:  # Alpha's local Damp range check
            value = 1
        elif a == 0x02334D08:
            value = 4 if self.rain else 0
        elif a == 0x02324854:  # Explosion immunity from exclusive items
            value = int(self.immune)
        elif a == 0x022F8830:  # Enemy in front for eating the seed
            value = self.entity(1)
        elif a == 0x020137B8:  # InitMove
            self.uc.mem_write(r0, bytes(8))
            value = 0
        elif a in (0x022E0880, 0x022E5BD8, 0x02306258, 0x022E5560,
                   0x022E55F0, 0x022E2AD8, 0x0234B350, 0x02314D40,
                   0x02301E50, 0x022EC7E8, 0x02339CE8, 0x02336F4C):
            value = 0
        else:
            return
        uc.reg_write(UC_ARM_REG_R0, value)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def run(self, address, args, stack=()):
        self.uc.reg_write(UC_ARM_REG_CPSR, 0x1F)
        self.uc.reg_write(UC_ARM_REG_SP, SP)
        self.uc.reg_write(UC_ARM_REG_LR, RETURN)
        self.uc.mem_write(SP, bytes(0x100))
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            self.uc.reg_write(reg, value)
        for i, value in enumerate(stack):
            self.word(SP + i * 4, value)
        try:
            self.uc.emu_start(address, RETURN, count=50000)
        except Exception as exc:
            raise AssertionError(f'ARM fixture stopped at {self.uc.reg_read(UC_ARM_REG_PC):#x}') from exc
        assert self.uc.reg_read(UC_ARM_REG_PC) == RETURN
        assert self.uc.reg_read(UC_ARM_REG_SP) == SP


def main():
    assert FULL_STACK_MODULES.index('damage_formula') < FULL_STACK_MODULES.index('better_seed')
    inputs = [ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds',
              ROOT / 'PatchTesting/Export Rom/Explorers of Alpha+.nds',
              ROOT / 'PatchTesting/Export Rom/Explorers of Alpha+_kor.nds']
    with tempfile.TemporaryDirectory(prefix='better_seed_verify_') as temp:
        for index, source in enumerate(inputs):
            original = NintendoDSRom(source.read_bytes())
            ov = original.loadArm9Overlays()[29]
            prior = target(bytes(ov.data), ov.ramAddress, 0x0231D004)
            output = Path(temp) / f'patched{index}.nds'
            state = apply_module('better_seed', source, output)
            verify_module_applied(output, MODULE, state)
            rom = NintendoDSRom(output.read_bytes())
            record = state.get_module('better_seed')
            changed = {site + n - ov.ramAddress for site in
                       (0x0231D004, 0x0231D09C, 0x02320BBC) for n in range(4)}
            overlays = rom.loadArm9Overlays()
            for i in (29, 36):
                old = bytes(original.loadArm9Overlays()[i].data)
                new = bytes(overlays[i].data)
                allowed = changed if i == 29 else {
                    offset for cave in record.caves
                    for offset in range(cave.file_offset, cave.file_offset + cave.size)}
                assert len(old) == len(new)
                assert all(a == b or offset in allowed for offset, (a, b) in enumerate(zip(old, new)))
            m = Machine(rom, prior)
            for thrown in (0, 1):
                for near in (False, True):
                    m.setup(near=near)
                    m.run(0x0231CF84, (m.entity(0), m.entity(1), thrown))
                    expected = {m.entity(i) for i in ((0, 1, 2, 3, 5) if near else (1, 2, 3, 5))}
                    assert {d[1] for d in m.damage} == expected, m.damage
                    assert len(m.damage) == len(expected)
                    assert all(d[0] == m.entity(0) and d[2:] == (100, (256, 87)) for d in m.damage)
                    assert not m.fixed and not m.prior
                for option in ('rain', 'damp', 'immune'):
                    m.setup(**{option: True})
                    m.run(0x0231CF84, (m.entity(0), m.entity(1), thrown))
                    assert not m.damage and not m.fixed and not m.prior, option
                m.setup(ally=True)
                m.run(0x0231CF84, (m.entity(0), m.entity(1), thrown))
                assert not m.damage
                assert m.prior or m.fixed
            # Native ordinary explosion must keep fixed / HP-based damage.
            m.setup()
            m.run(0x02320448, (m.entity(0), m.entity(1), m.entity(1) + 4, 2), (0, 623))
            assert not m.damage and m.fixed
            print(f'PASS seed/native explosion cases, module apply/verify: {source.name}')
    print('OK better_seed; no full-stack rebuild')


if __name__ == '__main__':
    main()
