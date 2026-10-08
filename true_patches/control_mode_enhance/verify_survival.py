"""Assemble temporary ARM fixtures and execute survival paths without a ROM build."""
from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))
import yaml
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from patch_engine.apply_asm import _patch_strings
from patch_engine.apply_korean import load_source, plan_translation
from patch_engine.korean_codec import DenseEncoder, parse_str_file, build_str_file

MODULE = Path(__file__).resolve().parent
DUNGEON, TEAM, ENTITY, INFO = 0x020C0000, 0x02170000, 0x02150000, 0x02151000
SP, RETURN = 0x027E2000, 0x021F0000


class Machine:
    def __init__(self, rom, overlay29, overlay36, symbols):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(0x02000000, 0x400000)
        self.uc.mem_map(0x027E0000, 0x4000)
        self.uc.mem_write(0x02000000, bytes(rom.arm9))
        self.uc.mem_write(0x022DC240, overlay29)
        self.uc.mem_write(0x023A7080, overlay36)
        self.symbols = symbols
        self.logs = []
        self.calls = []
        self.stop = RETURN
        self.stopped = False
        self.recruit_result = 1
        self.spawn_pp_bonus = 0
        self.spawn_retained_leader = None
        self.uc.hook_add(UC_HOOK_CODE, self.code)

    def address(self, name):
        return self.symbols[name.lower()]

    def word(self, address, value=None):
        if value is not None:
            self.uc.mem_write(address, struct.pack('<I', value & 0xFFFFFFFF))
        return struct.unpack('<I', self.uc.mem_read(address, 4))[0]

    def byte(self, address, value=None):
        if value is not None:
            self.uc.mem_write(address, bytes([value]))
        return self.uc.mem_read(address, 1)[0]

    def half(self, address, value=None):
        if value is not None:
            self.uc.mem_write(address, struct.pack('<H', value))
        return struct.unpack('<H', self.uc.mem_read(address, 2))[0]

    def entity(self, index):
        return ENTITY + index * 0xB8

    def info(self, index):
        return INFO + index * 0x240

    def member(self, index):
        return TEAM + index * 0x80

    def return_from_stub(self, value=0):
        self.uc.reg_write(UC_ARM_REG_R0, value)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def code(self, uc, address, size, _):
        if address == self.stop:
            self.stopped = True
            uc.emu_stop()
            return
        r0, r1 = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        if address == 0x0205638C:
            assert r0 < 4, f'out-of-range roster lookup: {r0:#x}'
            self.return_from_stub(self.member(r0))
        elif address == 0x02056228:
            self.return_from_stub(int(r0 & 0x80000000 != 0 or (r0 & 0xFFFF) in [0x55AA, 0x5AA5]))
        elif address == 0x022FE048:
            m = self.member(r0)
            self.half(m + 0xE, self.half(r1 + 0x10))
            self.uc.mem_write(m + 0x1C, bytes(self.uc.mem_read(r1 + 0x124, 34)))
            self.return_from_stub(m)
        elif address == 0x0234B714:
            self.logs.append((r0, r1))
            self.return_from_stub()
        elif address == 0x022FC50C:
            # Model vanilla spawn's reading of the repaired active roster.
            for i in range(4):
                m, entity, info = self.member(i), self.entity(i), self.info(i)
                if self.byte(m) & 3 != 3:
                    continue
                self.word(entity, 1)
                self.half(info + 0xC, i)
                self.half(info + 0x10, self.half(m + 0xE))
                self.uc.mem_write(info + 0x124, bytes(self.uc.mem_read(m + 0x1C, 34)))
                for move in range(4):
                    pp = info + 0x124 + move * 8 + 6
                    self.byte(pp, min(255, self.byte(pp) + self.spawn_pp_bonus))
                self.byte(info + 7, self.byte(m + 1))
                if self.byte(m + 1):
                    self.word(0x0235355C, entity)
            if self.spawn_retained_leader is not None:
                # Regression: do not assume the engine pointer follows the
                # repaired flags. Simulate its retained last-floor selection.
                self.word(0x0235355C, self.entity(self.spawn_retained_leader))
                for i in range(4):
                    self.byte(self.info(i) + 7, int(i == self.spawn_retained_leader))
            self.return_from_stub(0x1234)
        elif address == 0x0230DBD4:
            # Wrapper has replayed RecruitCheck's original push, eight words.
            sp = uc.reg_read(UC_ARM_REG_SP)
            saved = struct.unpack('<8I', uc.mem_read(sp, 32))
            for reg, value in zip([UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                                  UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
                                  UC_ARM_REG_R9], saved):
                uc.reg_write(reg, value)
            uc.reg_write(UC_ARM_REG_SP, sp + 32)
            uc.reg_write(UC_ARM_REG_R0, self.recruit_result)
            uc.reg_write(UC_ARM_REG_PC, saved[-1])
        elif address in [0x022E1C0C, 0x022DDB68, 0x022E2978, 0x022E8104, 0x022E81F8]:
            self.calls.append(address)
            self.return_from_stub()

    def run(self, name, *args, stop=RETURN):
        self.uc.reg_write(UC_ARM_REG_CPSR, 0x1F)
        self.uc.reg_write(UC_ARM_REG_SP, SP)
        self.uc.reg_write(UC_ARM_REG_LR, RETURN)
        self.uc.mem_write(SP, b'\0' * 0x800)
        for i, value in enumerate(args):
            self.uc.reg_write([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2][i], value)
        self.stop, self.stopped = stop, False
        self.uc.emu_start(self.address(name), 0, count=30000)
        assert self.stopped, f'{name} did not return'
        if stop == RETURN:
            assert self.uc.reg_read(UC_ARM_REG_SP) == SP, f'{name} corrupted stack'
        return self.uc.reg_read(UC_ARM_REG_R0)

    def setup(self, guests=(), leader=0, order=(0, 1, 2, 3)):
        self.uc.mem_write(DUNGEON, b'\0' * 0x20000)
        self.uc.mem_write(TEAM, b'\0' * 0x200)
        self.uc.mem_write(ENTITY, b'\0' * 0x1000)
        self.uc.mem_write(INFO, b'\0' * 0x1000)
        self.word(0x02353538, DUNGEON)
        self.word(0x0235355C, self.entity(leader))
        for i in range(4):
            m, e, info = self.member(i), self.entity(i), self.info(i)
            self.byte(m, 3)
            self.byte(m + 1, int(i == leader))
            self.half(m + 8, 0x55AA if i in guests else i)
            self.half(m + 0xE, 100)
            self.word(e, 1)
            self.word(e + 0xB4, info)
            self.half(info + 0xC, i)
            self.half(info + 0x10, 100)
            self.half(info + 0x12, 100)
            self.half(info + 0x16, 20)
            self.byte(info + 7, int(i == leader))
            for j, pp in enumerate([0, 2, 7, 11]):
                self.byte(info + 0x124 + j * 8 + 6, pp)
                self.byte(m + 0x1C + j * 8 + 6, pp)
        for physical, roster in enumerate(order):
            self.word(DUNGEON + 0x12B28 + physical * 4, self.entity(roster))
        for name in ['CeHome', 'CeLeader', 'CeRoundOrigin', 'CeLastAct']:
            self.word(self.address(name), self.entity(leader))
        self.word(self.address('CeEntryLeader'), leader)
        self.word(self.address('CeEntryMemberId'), leader)
        self.word(self.address('CeDeadMask'), 0)
        self.logs.clear()


def main():
    rom = NintendoDSRom.fromFile(ROOT / 'PatchTesting/Export Rom/Explorers of Alpha+.nds')
    overlays = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    cfg = yaml.safe_load((MODULE / 'manifest.yaml').read_text(encoding='utf-8'))
    profile = yaml.safe_load((ROOT / 'patch_engine/rom_profile_us.yaml').read_text(encoding='utf-8'))
    base = NintendoDSRom.fromFile(ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds')
    original = loadOverlayTable(base.arm9OverlayTable, lambda _, n: base.files[n])[29]
    for hook in cfg['hooks'][-6:]:
        address = profile['symbols'][hook['symbol']]
        assert struct.unpack_from('<I', original.data, address - original.ramAddress)[0] == hook['vanilla_word']
        current = struct.unpack_from('<I', overlays[29].data, address - original.ramAddress)[0]
        # The read-only fixture may already be a v14 build. The application
        # engine separately enforces hook ownership/expected words on rebuild.
        assert current == hook['vanilla_word'] or current >> 24 in [0xEA, 0xEB], hook['name']
    with tempfile.TemporaryDirectory(prefix='cme_survival_test_') as tmp:
        work = Path(tmp)
        shutil.copytree(MODULE / 'asm', work / 'asm')
        work = work / 'asm'
        offset = (len(overlays[36].data) + 3) & ~3
        ov36 = bytes(overlays[36].data).ljust(offset + cfg['cave']['estimated_bytes'], b'\0')
        (work / 'overlay_0036.bin').write_bytes(ov36)
        (work / 'overlay_0029.bin').write_bytes(overlays[29].data)
        (work / 'generated.inc').write_text(f'ControlModeEnhanceCodeAddress equ 0x{offset:X}\n', encoding='utf-8')
        result = subprocess.run([str(ROOT / 'tools/armips.exe'), '-sym', 'test.sym', 'main.asm'],
                                cwd=work, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        symbols = {}
        for line in (work / 'test.sym').read_text().splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    symbols[parts[1].lower()] = int(parts[0], 16)
                except ValueError:
                    pass
        assert symbols['celeader'] == overlays[36].ramAddress + offset + 8
        candidate29 = (work / 'overlay_0029.bin').read_bytes()
        assert candidate29[0x022F7F30 - original.ramAddress:0x022F7F34 - original.ramAddress] == bytes(overlays[29].data[0x022F7F30 - original.ramAddress:0x022F7F34 - original.ramAddress])
        machine = Machine(rom, candidate29, (work / 'overlay_0036.bin').read_bytes(), symbols)

    # Each possible leader hands off in roster order, excluding guest slots.
    cases = 0
    for leader in range(4):
        for guest in range(4):
            if leader == guest:
                continue
            machine.setup(guests=[guest], leader=leader, order=(2, 0, 3, 1))
            machine.half(machine.info(leader) + 0x10, 0)
            assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(leader)) == 1
            expected = next(i % 4 for i in range(leader + 1, leader + 4) if i % 4 != guest)
            assert machine.word(symbols['celeader']) == machine.entity(expected)
            assert machine.word(symbols['cedeadmask']) == 1
            assert machine.word(symbols['cedeadmemberid']) == leader
            assert machine.byte(machine.member(leader)) & 3 == 3
            assert machine.word(machine.entity(leader)) == 0
            assert machine.run('ControlModeEnhance_TryRecruit', machine.entity(expected)) == 0
            assert machine.logs[-1][1] == 19300
            machine.run('ControlModeEnhance_PrepareFloor')
            assert machine.half(machine.member(leader) + 0xE) == 120
            assert [machine.byte(machine.member(leader) + 0x1C + j * 8 + 6) for j in range(4)] == [0, 2, 7, 11]
            assert machine.word(symbols['cedeadmask']) == 0
            assert [machine.byte(machine.member(i) + 1) for i in range(4)] == [int(i == leader) for i in range(4)]
            machine.run('ControlModeEnhance_SpawnTeam')
            assert machine.word(symbols['celeader']) == machine.entity(leader)
            cases += 1

    # A guest must not prevent loss; guest fainting stays entirely vanilla.
    machine.setup(guests=[1, 2, 3])
    machine.half(machine.info(0) + 0x10, 0)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(0)) == 0
    assert machine.byte(machine.info(0) + 7) == 1
    machine.setup(guests=[1])
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(1)) == 0
    assert machine.word(symbols['cedeadmask']) == 0

    machine.setup()
    machine.byte(machine.info(1) + 6, 1)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(1)) == 0
    machine.byte(machine.info(1) + 6, 0)
    machine.half(machine.info(1) + 0xC, 0x55AA)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(1)) == 0
    machine.half(machine.info(1) + 0xC, 1)
    machine.byte(machine.member(1), 0)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(1)) == 0

    # Nonleader faint doesn't change the chosen leader; multiple deaths persist.
    machine.setup(leader=2)
    for dead in [0, 1]:
        machine.half(machine.info(dead) + 0x10, 0)
        assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(dead)) == 1
        assert machine.word(symbols['celeader']) == machine.entity(2)
    assert machine.word(symbols['cedeadmask']) == 3
    machine.run('ControlModeEnhance_PrepareFloor')
    assert all(machine.half(machine.member(i) + 0xE) == 120 for i in [0, 1])

    machine.setup(guests=[3])
    for dead in [0, 1]:
        machine.half(machine.info(dead) + 0x10, 0)
        assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(dead)) == 1
    machine.half(machine.info(2) + 0x10, 0)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(2)) == 0
    assert machine.word(symbols['celeader']) == machine.entity(2)
    assert machine.byte(machine.info(2) + 7) == 1

    # Start's chosen leader is distinct from the dungeon-entry leader.
    machine.setup(leader=2)
    machine.run('ControlModeEnhance_SetLeader', machine.entity(1))
    machine.half(machine.info(1) + 0x10, 0)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(1)) == 1
    machine.run('ControlModeEnhance_PrepareFloor')
    assert machine.byte(machine.member(2) + 1) == 1
    assert machine.word(symbols['ceentryleader']) == 2

    # Deliberately change saved PP, then verify death-time values are restored
    # before spawn, and that later vanilla PP changes are NOT overwritten.
    machine.setup()
    machine.half(machine.info(0) + 0x10, 0)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(0)) == 1
    for move in range(4):
        machine.byte(machine.member(0) + 0x1C + move * 8 + 6, 99)
    machine.run('ControlModeEnhance_PrepareFloor')
    machine.spawn_pp_bonus = 2
    machine.run('ControlModeEnhance_SpawnTeam')
    assert [machine.byte(machine.info(0) + 0x124 + j * 8 + 6) for j in range(4)] == [2, 4, 9, 13]
    machine.spawn_pp_bonus = 0

    # Restore the saved entry identity after spawn even when the engine keeps
    # the last-floor leader; physical slot order is independent of roster ID.
    for entry in range(4):
        for last in range(4):
            if entry == last:
                continue
            machine.setup(leader=entry, order=(2, 0, 3, 1))
            machine.run('ControlModeEnhance_SetLeader', machine.entity(last))
            machine.half(machine.info(entry) + 0x10, 0)
            assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(entry)) == 1
            machine.run('ControlModeEnhance_PrepareFloor')
            machine.spawn_retained_leader = last
            assert machine.run('ControlModeEnhance_SpawnTeam') == 0x1234
            assert machine.word(0x0235355C) == machine.entity(entry)
            assert machine.word(symbols['celeader']) == machine.entity(entry)
            assert machine.word(symbols['cehome']) == machine.entity(entry)
            assert machine.word(symbols['ceentryleader']) == entry
            assert [machine.byte(machine.member(i) + 1) for i in range(4)] == [int(i == entry) for i in range(4)]
            assert [machine.byte(machine.info(i) + 7) for i in range(4)] == [int(i == entry) for i in range(4)]
    machine.spawn_retained_leader = None

    # Actual active-record reorder, rather than just physical entity order:
    # original member 0 moves to roster slot 1; its successor now occupies 0.
    machine.setup()
    machine.half(machine.info(0) + 0x10, 0)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(0)) == 1
    records = [bytes(machine.uc.mem_read(machine.member(i), 0x80)) for i in range(4)]
    for slot, identity in enumerate([1, 0, 2, 3]):
        machine.uc.mem_write(machine.member(slot), records[identity])
        machine.half(machine.info(identity) + 0xC, slot)
    machine.half(machine.info(1) + 0x12, 150)
    machine.half(machine.info(1) + 0x16, 0)
    machine.half(machine.info(1) + 0x10, 0)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(1)) == 1
    assert machine.word(symbols['cedeadmask']) == 3
    assert [machine.word(symbols['cedeadmemberid'] + i * 4) for i in range(2)] == [0, 1]
    machine.run('ControlModeEnhance_PrepareFloor')
    assert machine.word(symbols['ceentryleader']) == 1
    assert machine.half(machine.member(1) + 0xE) == 120
    assert machine.half(machine.member(0) + 0xE) == 150
    machine.spawn_retained_leader = 2
    machine.run('ControlModeEnhance_SpawnTeam')
    assert machine.word(symbols['celeader']) == machine.entity(1)
    assert machine.word(symbols['ceentrymemberid']) == 0
    machine.spawn_retained_leader = None

    # Shared exit is after result selection, before final export/free. Do not
    # revive, refill PP or change the result, even if entry member is dead.
    for outcome in [1, 2, 3]:  # clear, escape, defeat fixture values
        for entry_dead in [False, True]:
            machine.setup()
            machine.run('ControlModeEnhance_SetLeader', machine.entity(1))
            if entry_dead:
                machine.half(machine.info(0) + 0x10, 0)
                assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(0)) == 1
            records = [bytes(machine.uc.mem_read(machine.member(i), 0x80)) for i in range(4)]
            for slot, identity in enumerate([1, 0, 2, 3]):
                machine.uc.mem_write(machine.member(slot), records[identity])
                machine.half(machine.info(identity) + 0xC, slot)
            # Vanilla defeat can deactivate the original member record.
            if outcome == 3 and entry_dead:
                machine.byte(machine.member(1), machine.byte(machine.member(1)) & ~3)
            before = [(machine.half(machine.member(i) + 0xE), bytes(machine.uc.mem_read(machine.member(i) + 0x1C, 34))) for i in range(4)]
            machine.run('ControlModeEnhance_DungeonEnd', outcome, 0x76543210, 0x12345678, stop=0x0234CF60)
            assert machine.uc.reg_read(UC_ARM_REG_R0) == outcome
            assert machine.uc.reg_read(UC_ARM_REG_R1) == 0x76543210
            assert machine.uc.reg_read(UC_ARM_REG_R2) == 0x12345678
            assert machine.uc.reg_read(UC_ARM_REG_SP) == SP
            assert [machine.byte(machine.member(i) + 1) for i in range(4)] == [0, 1, 0, 0]
            assert before == [(machine.half(machine.member(i) + 0xE), bytes(machine.uc.mem_read(machine.member(i) + 0x1C, 34))) for i in range(4)]
            assert machine.word(symbols['cedeadmask']) == 0
            if entry_dead:
                assert machine.half(machine.info(0) + 0x10) == 0
            else:
                assert machine.word(symbols['celeader']) == machine.entity(0)

    machine.setup()
    machine.half(machine.info(0) + 0x10, 0)
    machine.half(machine.info(0) + 0x12, 32760)
    assert machine.run('ControlModeEnhance_ReserveFaint', machine.entity(0)) == 1
    machine.run('ControlModeEnhance_PrepareFloor')
    assert machine.half(machine.member(0) + 0xE) == 32767

    # Healthy recruiting follows the vanilla result and retains TryRecruit r2.
    machine.setup()
    assert machine.run('ControlModeEnhance_RecruitCheck', machine.entity(0), machine.entity(1)) == 1
    assert not machine.logs
    machine.word(symbols['cedeadmask'], 1)
    machine.recruit_result = 0
    assert machine.run('ControlModeEnhance_RecruitCheck', machine.entity(0), machine.entity(1)) == 0
    assert not machine.logs
    machine.recruit_result = 1
    assert machine.run('ControlModeEnhance_RecruitCheck', machine.entity(0), machine.entity(1)) == 0
    assert len(machine.logs) == 1
    machine.word(symbols['cedeadmask'], 0)
    machine.run('ControlModeEnhance_TryRecruit', machine.entity(0), machine.entity(1), 0x123456,
                stop=0x0230E068)
    assert machine.uc.reg_read(UC_ARM_REG_R2) == 0x123456
    machine.run('ControlModeEnhance_DungeonStart', 0, 0, stop=0x022E1644)
    assert machine.word(symbols['ceentryleader']) == 0xFFFFFFFF
    assert machine.word(symbols['cedeadmask']) == 0
    machine.run('ControlModeEnhance_SpawnTeam')
    assert machine.word(symbols['ceentryleader']) == 0
    machine.setup(leader=3)
    machine.run('ControlModeEnhance_DungeonStart', 0, 0, stop=0x022E1644)
    machine.run('ControlModeEnhance_SpawnTeam')
    assert machine.word(symbols['ceentryleader']) == 3

    # Manual's temporary actor can already be the engine leader while the
    # persistent roster still says somebody else. Auto selection must fix both.
    machine.setup()
    machine.word(0x0235355C, machine.entity(2))
    machine.byte(machine.info(0) + 7, 0)
    machine.byte(machine.info(2) + 7, 1)
    machine.run('ControlModeEnhance_SetLeader', machine.entity(2))
    assert [machine.byte(machine.member(i) + 1) for i in range(4)] == [0, 0, 1, 0]
    assert machine.word(symbols['celeader']) == machine.entity(2)
    assert machine.byte(DUNGEON + 0xE) == 1
    machine.byte(DUNGEON + 0xE, 0)
    machine.run('ControlModeEnhance_SetLeader', machine.entity(2))
    assert machine.byte(DUNGEON + 0xE) == 0

    # Auto returns out of Alpha's scan to vanilla's complete ally/deferred
    # phases. Manual still enters the custom scan. Check the real stack ABI.
    for manual in [0, 1]:
        machine.setup()
        machine.byte(0x023A7090, manual)
        frame = [0x11000000 + i for i in range(13)] + [RETURN]
        machine.uc.mem_write(SP, struct.pack('<14I', *frame))
        machine.uc.reg_write(UC_ARM_REG_CPSR, 0x1F)
        machine.uc.reg_write(UC_ARM_REG_SP, SP)
        machine.uc.reg_write(UC_ARM_REG_LR, 0x023A73C8)
        machine.stop = 0x023A7430 if manual else RETURN
        machine.stopped = False
        machine.uc.emu_start(symbols['controlmodeenhance_scanstay'], 0, count=30000)
        assert machine.stopped
        assert machine.uc.reg_read(UC_ARM_REG_SP) == SP + (0 if manual else 56)
        if not manual:
            assert machine.uc.reg_read(UC_ARM_REG_R5) == frame[5]
            assert machine.word(symbols['ceroundpending']) == 1

    # English/Korean slot reservation and import are tested on in-memory ROMs.
    fixture_text = parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    expected_text = yaml.safe_load((MODULE / 'strings.yaml').read_text(encoding='utf-8'))['entries'][0]['text'].encode('ascii')
    assert fixture_text[19299] in [b'', expected_text]
    # Reconstruct the pre-application empty slot in this in-memory fixture.
    fixture_text[19299] = b''
    rom.setFileByName('MESSAGE/text_e.str', build_str_file(fixture_text))
    _patch_strings(rom, MODULE, cfg)
    try:
        _patch_strings(rom, MODULE, cfg)
    except RuntimeError:
        pass
    else:
        raise AssertionError('occupied message slot was overwritten')
    korean = ROOT / 'true_patches/korean'
    source = load_source(korean, yaml.safe_load((korean / 'manifest.yaml').read_text(encoding='utf-8')))
    plan = plan_translation(rom, source)
    assert plan.final_text_e()[19299] == source.user['text_e']['19299']['ko']
    encoder = DenseEncoder(source.ziti)
    encoder.collect(plan.final_text_e()[19299])
    encoder.finalize()
    encoder.encode(plan.final_text_e()[19299])
    assert not encoder.stats.unmapped
    for path in (ROOT / 'true_patches').rglob('*.yaml'):
        if path == MODULE / 'strings.yaml':
            continue
        doc = yaml.safe_load(path.read_text(encoding='utf-8'))
        if isinstance(doc, dict):
            assert all(x.get('id') != 19299 for x in doc.get('entries', []) if isinstance(x, dict)), path
    print(json.dumps({'leader_guest_permutations': cases, 'full_HP_and_PP_before_vanilla': 'passed',
                      'entry_leader_restored': 'passed', 'guild_identity_after_roster_reorder': 'passed',
                      'shared_exit_clear_escape_defeat': 'passed', 'guest_only_game_over': 'passed',
                      'recruit_gate_and_message': 'passed', 'korean_message_index': 19299,
                      'Z_gauge_hook_unchanged': True, 'manual_auto_leader_flags': 'passed',
                      'auto_returns_to_vanilla_ally_batch': 'passed', 'ROM_written': False}, indent=2))


if __name__ == '__main__':
    main()
