"""Apply in memory and execute native discovery / trap-consumption ARM paths."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from patch_engine.apply_asm import apply_asm_single
from patch_engine.build_full_stack import FULL_STACK_MODULES
from patch_engine.hook_registry import branch_target
from patch_engine.manifest import load_module_manifest, load_rom_profile
from patch_engine.overlay_caves import get_rom_binary

REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_R12]
POSITION, STACK, STOP = 0x02070000, 0x02078000, 0x02001000
DUNGEON, ACTOR = 0x02080000, 0x02071000


class InspectTrapRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_rom_profile(ROOT / 'patch_engine', 'us_vanilla')
        cls.module = ROOT / 'true_patches/inspect_trap'
        cls.manifest = load_module_manifest(cls.module)
        cls.source = ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'
        rom = NintendoDSRom(cls.source.read_bytes())
        cls.native29 = bytes(get_rom_binary(rom, 'ov29'))
        cls.record, rom = cls.apply(rom, cls.manifest)
        cls.ov29 = bytes(get_rom_binary(rom, 'ov29'))
        cls.ov36 = bytes(get_rom_binary(rom, 'ov36'))

    @classmethod
    def apply(cls, rom, manifest):
        return apply_asm_single(
            module_id='inspect_trap', module_dir=cls.module, manifest=manifest,
            profile=cls.profile, rom=rom, config=get_ppmdu_config_for_rom(rom),
            armips_exe=ROOT / 'tools/armips.exe', prior_hook_sites=set(), rom_in=cls.source)

    def setUp(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(0x02000000, 0x00400000)
        self.uc.mem_map(0x06000000, 0x00040000)
        self.uc.mem_write(0x022DC240, self.ov29)
        self.uc.mem_write(0x023A7080, self.ov36)
        self.uc.mem_write(0x02353538, struct.pack('<I', DUNGEON))
        self.uc.mem_write(POSITION, struct.pack('<hh', 10, 8))
        self.tiles, self.entities = {}, {}
        self.lookups, self.calls = [], []
        self.effect_result = 0
        self.uc.hook_add(UC_HOOK_CODE, self.native_call)

    def put_object(self, x, y, kind=2, visible=0, room=3):
        i = len(self.tiles)
        tile, entity = 0x02060000 + i * 0x20, 0x02040000 + i * 0x100
        self.tiles[x, y], self.entities[x, y] = tile, entity
        self.uc.mem_write(tile + 7, bytes([room]))
        self.uc.mem_write(tile + 0x10, struct.pack('<I', entity))
        self.uc.mem_write(entity, struct.pack('<I', kind))
        self.uc.mem_write(entity + 0x20, bytes([visible]))
        return entity

    def native_call(self, uc, address, size, _):
        if address == 0x023360FC:  # real native reveal helper calls GetTile
            xy = tuple(uc.reg_read(r) for r in REGS[:2])
            xy = tuple(v if v < 0x80000000 else v - 0x100000000 for v in xy)
            self.lookups.append(xy)
            result = self.tiles.get(xy, 0x0205f000)  # empty/default tile
        elif address in [0x02337428, 0x02339CE8, 0x02336F4C,
                         0x02051D8C, 0x02051E60, 0x023026FC,
                         0x0234B350, 0x022E2CA0, 0x022EF154, 0x022EDE7C]:
            args = [uc.reg_read(r) for r in REGS[:4]]
            if address not in [0x02051D8C, 0x02051E60]:
                self.calls.append((address, args))
            result = self.effect_result if address == 0x022EF154 else 0
            if address == 0x022EDE7C:
                xy = struct.unpack('<hh', bytes(uc.mem_read(args[0], 4)))
                tile = self.tiles.get(xy)
                if tile:
                    uc.mem_write(tile + 0x10, bytes(4))
                result = 1
        else:
            return
        for reg in REGS[:4] + [UC_ARM_REG_R12]:
            uc.reg_write(reg, 0xdeadbeef)
        uc.reg_write(UC_ARM_REG_R0, result)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def run_at(self, start, stop=STOP, values=None):
        for i, reg in enumerate(REGS):
            self.uc.reg_write(reg, 0x12340000 + i)
        for index, value in (values or {}).items():
            self.uc.reg_write(REGS[index], value)
        self.uc.reg_write(UC_ARM_REG_SP, STACK)
        self.uc.reg_write(UC_ARM_REG_LR, STOP)
        self.uc.emu_start(start, stop, count=100000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_PC), stop)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_SP), STACK)

    def begin(self):
        args = {0: POSITION, 1: 5, 2: 0, 3: 1}
        self.run_at(0x022F2FB0, 0x022F2FB4, args)
        self.assertEqual(self.calls[-1], (0x02337428, list(args.values())))
        for i in range(4, 12):
            self.assertEqual(self.uc.reg_read(REGS[i]), 0x12340000 + i)

    def visible(self, xy):
        return self.uc.mem_read(self.entities[xy] + 0x20, 1)[0]

    def test_exactly_eight_neighbors_revealed_and_persist_after_y_release(self):
        for y in range(6, 11):
            for x in range(8, 13):
                self.put_object(x, y)
        expected = {(10 + dx, 8 + dy) for dx in [-1, 0, 1]
                    for dy in [-1, 0, 1] if dx or dy}
        blend = bytes(self.uc.mem_read(0x022a37b6, 10))
        graphics = bytes(self.uc.mem_read(0x06000000, 0x40000))
        self.begin()
        self.assertEqual(set(self.lookups), expected)
        self.assertEqual(len(self.lookups), 8)
        for xy in self.entities:
            self.assertEqual(self.visible(xy), int(xy in expected))
        self.assertEqual([a for a, _ in self.calls], [0x02339ce8, 0x02336f4c, 0x02337428])
        self.run_at(0x0233779c)  # real HideTileGrid runs on Y release
        for xy in expected:
            self.assertEqual(self.visible(xy), 1)
        self.assertEqual(bytes(self.uc.mem_read(0x022a37b6, 10)), blend)
        self.assertEqual(bytes(self.uc.mem_read(0x06000000, 0x40000)), graphics)

    def test_corridors_room_borders_and_object_types(self):
        self.put_object(9, 7, room=0xff)
        self.put_object(10, 7, room=7)
        self.put_object(11, 7, visible=1)
        self.put_object(9, 8, kind=3)
        self.put_object(11, 8, kind=5)
        self.begin()
        for xy in [(9, 7), (10, 7), (11, 7)]:
            self.assertEqual(self.visible(xy), 1)
        for xy in [(9, 8), (11, 8)]:
            self.assertEqual(self.visible(xy), 0)

    def test_map_edge_and_controlled_actor_position(self):
        self.uc.mem_write(POSITION, struct.pack('<hh', 0, 0))
        self.put_object(1, 0)
        self.put_object(1, 1)
        self.put_object(2, 0)
        self.begin()
        self.assertEqual(len(self.lookups), 8)
        self.assertIn((-1, -1), self.lookups)
        self.assertEqual(self.visible((1, 0)), 1)
        self.assertEqual(self.visible((1, 1)), 1)
        self.assertEqual(self.visible((2, 0)), 0)

    def test_repeated_inspection_without_new_traps_does_not_refresh(self):
        self.put_object(10, 7)
        self.begin()
        self.calls.clear()
        self.begin()
        self.assertEqual([a for a, _ in self.calls], [0x02337428])

    def test_consumption_after_each_effect_including_persistent_and_random_traps(self):
        for trap_id in range(0x21):
            for result in [0, 1]:
                with self.subTest(trap_id=trap_id, result=result):
                    self.effect_result = result
                    self.calls.clear()
                    self.uc.mem_write(STACK + 0x10, struct.pack('<I', 0x02060000))
                    self.uc.mem_write(ACTOR, struct.pack('<I', 1))
                    self.uc.mem_write(0x02072000, bytes([trap_id]))
                    self.put_object(10, 8)
                    # Native TryTriggerTrap argument preparation, effect call,
                    # post-effect checks and removal decision all execute.
                    self.run_at(0x022EE29C, 0x022EE2F4, {
                        4: self.entities[10, 8], 5: ACTOR, 6: 0x02072000,
                        9: POSITION, 10: ACTOR})
                    addresses = [a for a, _ in self.calls]
                    self.assertLess(addresses.index(0x022ef154), addresses.index(0x022ede7c))
                    remove = next(args for a, args in self.calls if a == 0x022ede7c)
                    self.assertEqual(remove[:2], [POSITION, 1])
                    tile = self.tiles[10, 8]
                    self.assertEqual(self.uc.mem_read(tile + 0x10, 4), bytes(4))

    def test_failed_activation_does_not_reach_effect_or_forced_consumption(self):
        self.put_object(10, 8)
        self.run_at(0x022ee110, 0x022ee2f4, {
            5: ACTOR, 8: 0xb00, 9: POSITION, 10: ACTOR, 11: 0})
        self.assertNotIn(0x022ef154, [a for a, _ in self.calls])
        self.assertNotIn(0x022ede7c, [a for a, _ in self.calls])
        self.assertNotEqual(self.uc.mem_read(self.tiles[10, 8] + 0x10, 4), bytes(4))

    def test_native_rendering_effects_and_pre_activation_guards_are_unchanged(self):
        for start, end in [(0x02337428, 0x0233781c), (0x022ef154, 0x022ef478),
                           (0x022edfa0, 0x022ee2c4), (0x022ee2c8, 0x022ee2fc)]:
            lo, hi = start - 0x022dc240, end - 0x022dc240
            self.assertEqual(self.ov29[lo:hi], self.native29[lo:hi])
        sites = {h.site for h in self.record.hooks}
        for module in FULL_STACK_MODULES:
            if module == 'inspect_trap':
                continue
            for hook in load_module_manifest(ROOT / 'true_patches' / module).get('hooks', []):
                self.assertNotIn(self.profile['symbols'].get(hook.get('symbol')), sites)

    def test_cave_can_relocate(self):
        manifest = load_module_manifest(self.module)
        manifest['cave']['preferred'] = self.record.caves[0].file_offset + 0x400
        record, rom = self.apply(NintendoDSRom(self.source.read_bytes()), manifest)
        self.assertNotEqual(record.caves[0].load_address, self.record.caves[0].load_address)
        blob = get_rom_binary(rom, 'ov29')
        word, = struct.unpack_from('<I', blob, 0x022f2fb0 - 0x022dc240)
        target = branch_target(0x022f2fb0, word)
        self.assertTrue(record.caves[0].load_address <= target < record.caves[0].load_address + 1024)


if __name__ == '__main__':
    unittest.main(verbosity=2)
