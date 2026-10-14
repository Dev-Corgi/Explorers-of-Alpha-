"""Compile temporary ARM fixtures; check workbook-E effects without saving a ROM."""
from pathlib import Path
import copy
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *
from patch_engine.apply_asm import apply_asm_single
from patch_engine.apply_korean import load_source, plan_translation
from patch_engine.hook_registry import branch_target
from patch_engine.korean_codec import parse_str_file, translation_issues
from patch_engine.manifest import load_module_manifest, load_rom_profile, resolve_symbol
from patch_engine.state import AppliedModule, BuildState
from true_patches.bug_fixes.verify import recovery_machine
from true_patches.balance_change.patch_ability_names import (
    patch_ability_names, verify_ability_names, normalize_strings,
)

MODULE = Path(__file__).resolve().parent
SOURCE = ROOT / "PatchTesting/Export Rom/Explorers of Alpha+.nds"
STACK, RETURN = 0x0273F000, 0x0273E000
ENTITIES = [0x02120000 + i * 0x200 for i in range(5)]
MONSTERS = [0x02121000 + i * 0x400 for i in range(5)]
RESULT, DUNGEON = 0x0273D000, 0x02100000


def fixture():
    rom = NintendoDSRom.fromFile(str(SOURCE))
    manifest = copy.deepcopy(load_module_manifest(MODULE))
    # Compile the complete assembly; only new hook preconditions are checked.
    arm9_hook = next(h for h in manifest['hooks'] if h['name'] == 'ExpSharePercentage')
    arm9_hook['vanilla_word'] = arm9_hook['patched_word']
    new_hooks = [h for h in manifest['hooks'] if h['name'].startswith(('Ability', 'Remove'))]
    manifest['hooks'] = new_hooks + [arm9_hook]
    profile = load_rom_profile(ROOT / 'patch_engine', 'us_vanilla')
    state = BuildState('us_vanilla', 0x022DC240, [AppliedModule(
        'test_services', 1, data=[{'BaseStats_CalcStat': RETURN}])])
    record, rom = apply_asm_single(
        module_id='ability_fixture', module_dir=MODULE, manifest=manifest,
        profile=profile, rom=rom, config=get_ppmdu_config_for_rom(rom),
        armips_exe=ROOT / 'tools/armips.exe', prior_hook_sites=set(), state=state)
    assert record.caves[0].size == manifest['cave']['estimated_bytes']
    # New sites must not be claimed by another module anywhere in the stack.
    sites = {resolve_symbol(profile, h['symbol']) for h in new_hooks}
    for other in (ROOT / 'true_patches').glob('*/manifest.yaml'):
        if other.parent == MODULE:
            continue
        for h in load_module_manifest(other.parent).get('hooks', []):
            assert resolve_symbol(profile, h['symbol']) not in sites, (other, h)
    return rom


class World:
    def __init__(self, rom):
        self.uc = recovery_machine(rom)
        self.abilities = {}
        self.suppressed = set()
        self.boosts = []
        self.sound = False
        self.category = 0
        self.invoke = None
        self.scope_invoke = None
        self.uc.hook_add(UC_HOOK_CODE, self.service)
        self.reset()

    def reset(self):
        self.abilities.clear()
        self.suppressed.clear()
        self.boosts.clear()
        self.sound = False
        self.uc.mem_write(DUNGEON + 0x12B78, bytes(80))
        for i, (e, m) in enumerate(zip(ENTITIES, MONSTERS)):
            self.uc.mem_write(e, bytes(0x200))
            self.uc.mem_write(m, bytes(0x400))
            self.uc.mem_write(e, struct.pack('<I', 1))
            self.uc.mem_write(e + 0xB4, struct.pack('<I', m))
            self.uc.mem_write(e + 0x25, b'\x02')
            self.uc.mem_write(m + 0x10, struct.pack('<hhh', 100, 100, 0))
            self.uc.mem_write(m + 6, bytes([int(i > 0)]))
            self.uc.mem_write(DUNGEON + 0x12B78 + i * 4, struct.pack('<I', e))
        self.uc.mem_write(STACK, bytes(0x300))

    def service(self, uc, address, _size, _data):
        a, b = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        if address in (0x02301D78, 0x02301D10):
            value = int(b in self.abilities.get(a, set()) and a not in self.suppressed)
        elif address == 0x02301A60:
            value = int(a in ENTITIES)
        elif address == 0x02013D5C:
            value = int(self.sound)
        elif address == 0x020151C8:
            value = self.category
        elif address == 0x02013864:
            value = 1  # Normal move for the conversion-removal regression.
        elif address == 0x0208FEA4:
            value = a // b
        elif address == 0x0231399C:
            assert a == b and uc.reg_read(UC_ARM_REG_R2) == 1
            assert uc.reg_read(UC_ARM_REG_R3) == 1
            self.boosts.append(a)
            value = 0
        elif address == 0x0232E868 and self.invoke:
            self.invoke(self)
            # Simulate the original effect's return, including its saved prologue.
            sp = uc.reg_read(UC_ARM_REG_SP)
            words = struct.unpack('<10I', uc.mem_read(sp, 40))
            for reg, val in zip((UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                    UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                    UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_LR), words):
                uc.reg_write(reg, val)
            uc.reg_write(UC_ARM_REG_SP, sp + 40)
            uc.reg_write(UC_ARM_REG_PC, words[-1])
            return
        elif address == 0x02321460 and self.scope_invoke:
            self.scope_invoke(self)
            sp = uc.reg_read(UC_ARM_REG_SP)
            words = struct.unpack('<9I', uc.mem_read(sp, 36))
            for reg, val in zip((UC_ARM_REG_R4, UC_ARM_REG_R5,
                    UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                    UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_LR), words):
                uc.reg_write(reg, val)
            uc.reg_write(UC_ARM_REG_SP, sp + 36)
            uc.reg_write(UC_ARM_REG_PC, words[-1])
            return
        else:
            return
        uc.reg_write(UC_ARM_REG_R0, value)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def run(self, address, stop=RETURN, **regs):
        self.uc.reg_write(UC_ARM_REG_SP, STACK)
        self.uc.reg_write(UC_ARM_REG_LR, RETURN)
        for name, value in regs.items():
            self.uc.reg_write(globals()['UC_ARM_REG_' + name.upper()], value)
        self.uc.emu_start(address, stop, count=20000)
        assert self.uc.reg_read(UC_ARM_REG_PC) == stop

    def faint(self, killer=0, victim=1, source=33):
        uc = self.uc
        saved = [uc.reg_read(r) for r in range(UC_ARM_REG_R0, UC_ARM_REG_R12 + 1)]
        oldsp, oldlr, oldpc = (uc.reg_read(r) for r in (UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC))
        uc.reg_write(UC_ARM_REG_SP, STACK - 0x400)
        uc.reg_write(UC_ARM_REG_R0, ENTITIES[victim])
        uc.reg_write(UC_ARM_REG_R1, source)
        uc.reg_write(UC_ARM_REG_R2, ENTITIES[killer])
        uc.emu_start(0x022F7F34, 0x022F7F38, count=10000)
        for r, value in zip(range(UC_ARM_REG_R0, UC_ARM_REG_R12 + 1), saved):
            uc.reg_write(r, value)
        for r, value in zip((UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC), (oldsp, oldlr, oldpc)):
            uc.reg_write(r, value)

    def nested_effect(self, user=0):
        uc = self.uc
        registers = list(range(UC_ARM_REG_R0, UC_ARM_REG_R12 + 1)) + [
            UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR]
        saved = [uc.reg_read(r) for r in registers]
        uc.reg_write(UC_ARM_REG_SP, STACK - 0x200)
        uc.mem_write(STACK - 0x200, struct.pack('<I', 0x12345678))
        uc.reg_write(UC_ARM_REG_LR, RETURN)
        for r, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                UC_ARM_REG_R3), (0x1234, ENTITIES[user], RESULT, 77)):
            uc.reg_write(r, value)
        uc.emu_start(0x0232E864, RETURN, count=20000)
        assert uc.reg_read(UC_ARM_REG_PC) == RETURN
        for r, value in zip(registers, saved):
            uc.reg_write(r, value)


def check(rom):
    w = World(rom)
    uc = w.uc
    # Full HP including boosts; no Flying-move requirement; suppression and clamping.
    for hp, bonus, active, suppressed, base, expected in [
        (100, 0, True, False, 0, 2), (99, 0, True, False, 0, 0),
        (110, 10, True, False, 1, 3), (100, 10, True, False, 1, 1),
        (100, 0, False, False, 1, 1), (100, 0, True, True, 1, 1),
        (100, 0, True, False, 3, 4), (100, 0, True, False, -1, 1)]:
        w.reset()
        w.abilities[ENTITIES[0]] = {142} if active else set()
        if suppressed:
            w.suppressed.add(ENTITIES[0])
        uc.mem_write(MONSTERS[0] + 0x10, struct.pack('<hhhh', hp, 100, 0, bonus))
        uc.mem_write(STACK + 20, struct.pack('<I', RETURN))
        w.run(0x022FFEFC, r4=base & 0xFFFFFFFF, r6=MONSTERS[0], r8=ENTITIES[0])
        got = struct.unpack('<I', uc.mem_read(MONSTERS[0] + 0x110, 4))[0]
        assert got == expected, (hp, bonus, active, suppressed, base, got, expected)
    # Both Adaptability IDs activate once, with the original query result contract.
    target = branch_target(0x0230B59C, struct.unpack('<I', uc.mem_read(0x0230B59C, 4))[0])
    for abilities in (set(), {24}, {99}, {24, 99}):
        w.reset()
        w.abilities[ENTITIES[0]] = abilities
        w.run(target, r0=ENTITIES[0])
        assert uc.reg_read(UC_ARM_REG_R0) == bool(abilities)
    w.run(0x0230B5A8, stop=0x0230B5AC)
    upper, lower = struct.unpack('<II', uc.mem_read(uc.reg_read(UC_ARM_REG_R2), 8))
    assert upper==0 and abs(lower / 2**16 - 1.7) < 1/2**16
    # Adaptate changed types in both damage calculation and common GetMoveType.
    w.reset()
    w.abilities[ENTITIES[0]] = {24}
    uc.mem_write(MONSTERS[0] + 2, struct.pack('<H', 181))
    uc.mem_write(MONSTERS[0] + 0x5E, bytes([5, 15]))
    uc.mem_write(RESULT, struct.pack('<IHH', 1, 154, 1))
    uc.mem_write(STACK, struct.pack('<4I', 0, 0, 0, RETURN))
    w.run(0x023DAE00, r4=RESULT, r5=ENTITIES[0])
    assert uc.reg_read(UC_ARM_REG_R0) == 1, uc.reg_read(UC_ARM_REG_R0)
    # Sound damage offense/defense and Aura Break: rooms, suppression, stacking, no aura.
    for attack, defense, sound, amount, expected in [
        (True, False, True, 100, 120), (False, True, True, 100, 80),
        (True, True, True, 100, 96), (True, True, False, 100, 100),
        (False, True, True, 1, 1), (True, True, True, 0, 0)]:
        w.reset()
        w.abilities[ENTITIES[0]] = {148} if attack else set()
        w.abilities[ENTITIES[1]] = {148} if defense else set()
        w.sound = sound
        uc.mem_write(RESULT, struct.pack('<II', amount, 999))
        uc.mem_write(STACK + 0xC, struct.pack('<I', 1))
        uc.mem_write(STACK + 0xF4, struct.pack('<I', 33))
        w.run(0x0230D03C, stop=0x0230D040, r1=0, r8=RESULT, r9=ENTITIES[1], r10=ENTITIES[0])
        assert struct.unpack('<II', uc.mem_read(RESULT, 8)) == (expected, 0)
    for typ, aura, breakers, room, suppressed, expected in [
        (16, 177, 1, 2, False, 80), (18, 176, 2, 2, False, 80),
        (16, 176, 1, 2, False, 100), (9, 177, 1, 2, False, 100),
        (16, 177, 1, 3, False, 100), (16, 177, 0, 2, False, 100),
        (16, 177, 1, 2, True, 100), (16, 177, 1, 255, False, 100)]:
        w.reset()
        w.abilities[ENTITIES[2]] = {aura}
        for index in range(breakers):
            w.abilities[ENTITIES[3 + index]] = {178}
            uc.mem_write(ENTITIES[3 + index] + 0x25, bytes([room]))
        if suppressed:
            w.suppressed.add(ENTITIES[3])
        uc.mem_write(RESULT, struct.pack('<II', 100, 999))
        uc.mem_write(STACK + 0xC, struct.pack('<I', typ))
        w.run(0x0230D03C, stop=0x0230D040, r1=0, r8=RESULT, r9=ENTITIES[1], r10=ENTITIES[0])
        assert struct.unpack('<I', uc.mem_read(RESULT, 4))[0] == expected
    # ExecuteMoveEffect's arguments, source and once-per-action multi-target scope.
    for category, sources, killer, suppressed, expected in [
        (0, [33, 33], 0, False, 1), (1, [33], 0, False, 1),
        (2, [33], 0, False, 0), (0, [999], 0, False, 0),
        (0, [33], 2, False, 0), (0, [33], 0, True, 0)]:
        w.reset()
        w.category = category
        w.abilities[ENTITIES[0]] = {171}
        if suppressed:
            w.suppressed.add(ENTITIES[0])
        move = RESULT
        uc.mem_write(move, struct.pack('<IHH', 1, 33, 10))
        uc.mem_write(STACK, struct.pack('<I', 0x12345678))
        def invoke(world):
            sp = uc.reg_read(UC_ARM_REG_SP)
            # Original prologue occupies 40 bytes; original arguments are untouched.
            assert uc.reg_read(UC_ARM_REG_R0) == 0x1234
            assert uc.reg_read(UC_ARM_REG_R1) == ENTITIES[0]
            assert uc.reg_read(UC_ARM_REG_R2) == move
            assert uc.reg_read(UC_ARM_REG_R3) == 77
            assert struct.unpack('<I', uc.mem_read(sp + 40, 4))[0] == 0x12345678
            for source in sources:
                world.faint(killer=killer, source=source)
        w.invoke = invoke
        w.run(0x0232E864, r0=0x1234, r1=ENTITIES[0], r2=move, r3=77)
        assert len(w.boosts) == expected, (category, sources, w.boosts)
        assert uc.reg_read(UC_ARM_REG_SP) == STACK
        # A second action must be eligible again.
        if expected:
            w.run(0x0232E864, r0=0x1234, r1=ENTITIES[0], r2=move, r3=77)
            assert len(w.boosts) == 2
    # Repeated ExecuteMoveEffect calls within one UseMove are one attack action.
    w.reset()
    w.category = 0
    w.abilities[ENTITIES[0]] = {171}
    uc.mem_write(RESULT, struct.pack('<IHH', 1, 33, 10))
    w.invoke = lambda world: world.faint()
    def action(world):
        world.nested_effect()
        world.nested_effect()
    w.scope_invoke = action
    w.run(0x0232145C, r0=ENTITIES[0], r1=0, r2=0, r3=0)
    assert w.boosts == [ENTITIES[0]]
    w.run(0x0232145C, r0=ENTITIES[0], r1=0, r2=0, r3=0)
    assert w.boosts == [ENTITIES[0], ENTITIES[0]]
    print('ARM: Speed/HP, STAB aliases, sound damage, room auras, Grim Neigh actions passed')


def check_text(rom):
    original = parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    patch_ability_names(rom)
    verify_ability_names(rom)
    changed = parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    assert len(original) == len(changed)
    assert normalize_strings(changed)[0] == changed
    src = load_source(ROOT / 'true_patches/korean', load_module_manifest(ROOT / 'true_patches/korean'))
    plan = plan_translation(rom, src)
    assert not plan.rejected, plan.rejected
    _, start = normalize_strings(changed)
    expected = {12:'멀티스케일',15:'클리어바디',24:'적응력',75:'옹골찬턱',110:'필터',
        139:'퍼코트',140:'얼음인분',142:'질풍날개',148:'펑크록',153:'승리의별',
        157:'전기로바꾸기',171:'흑의울음',178:'오라브레이크',226:'기묘한약'}
    expected.update({10:'그림자밟기',54:'불면',133:'애널라이즈',136:'테일아머',
        145:'눈치우기',180:'미끈미끈',181:'풀모피',189:'절대안깸',191:'무희',
        195:'무도한행동',204:'스펙터가드',205:'브레인포스',206:'AR시스템',
        212:'꾸덕꾸덕굳기',213:'무아지경',220:'바위나르기',221:'노릇노릇바디',
        223:'무기력',225:'내용물분출',228:'불요의검',229:'그대로꿀꺽미사일',
        240:'분노의껍질',244:'총대장',252:'시작의바다'})
    for aid, name in expected.items():
        assert plan.final_text_e()[start + aid] == name
    assert len(expected) == 38
    for i, entry in src.user['text_e'].items():
        assert not translation_issues(entry['en'], entry['ko']), i
    print('Text: canonical names, stable indices, idempotence, Korean tags and translations passed')


if __name__ == '__main__':
    rom = fixture()
    check(rom)
    check_text(rom)
