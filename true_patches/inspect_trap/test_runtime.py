"""Assemble/apply in memory and execute the actual ARM hooks with Unicorn.

Run from the repository root with Python and unicorn installed. No ROM is saved.
"""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

from patch_engine.apply_asm import apply_asm_single
from patch_engine.build_full_stack import FULL_STACK_MODULES
from patch_engine.hook_registry import branch_target
from patch_engine.manifest import load_module_manifest, load_rom_profile, load_yaml
from patch_engine.overlay_caves import get_rom_binary

REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_R12]
BLEND = 0x022A37B6
DUNGEON = 0x02080000
TILE = 0x02070000
ENTITY = 0x02071000
TRAP = 0x02072000
POSITION = 0x02073000
GRID = 0x02074000
STACK = 0x02078000
STOP = 0x02001000


class InspectTrapRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_rom_profile(ROOT / 'patch_engine', 'us_vanilla')
        cls.module = ROOT / 'true_patches/inspect_trap'
        manifest = load_module_manifest(cls.module)
        source = ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'
        rom = NintendoDSRom(source.read_bytes())
        cls.record, rom = apply_asm_single(
            module_id='inspect_trap', module_dir=cls.module, manifest=manifest,
            profile=cls.profile, rom=rom, config=get_ppmdu_config_for_rom(rom),
            armips_exe=ROOT / 'tools/armips.exe', prior_hook_sites=set(), rom_in=source,
        )
        cls.ov29 = bytes(get_rom_binary(rom, 'ov29'))
        cls.ov36 = bytes(get_rom_binary(rom, 'ov36'))
        cls.targets = {}
        for hook in manifest['hooks']:
            site = cls.profile['symbols'][hook['symbol']]
            word, = struct.unpack_from('<I', cls.ov29, site - 0x022DC240)
            cls.targets[hook['name']] = branch_target(site, word)
        cls.state = cls.record.caves[0].load_address

    def setUp(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(0x02000000, 0x00400000)
        self.uc.mem_map(0x06000000, 0x00040000)
        self.uc.mem_write(0x022DC240, self.ov29)
        self.uc.mem_write(0x023A7080, self.ov36)
        self.original_blend = bytes([1, 2, 2, 2, 2, 0, 64, 0, 64, 0])
        self.uc.mem_write(BLEND, self.original_blend)
        self.room = 3
        self.uc.mem_write(TILE + 7, bytes([self.room]))
        self.uc.mem_write(TILE + 0x10, struct.pack('<I', ENTITY))
        self.uc.mem_write(ENTITY, struct.pack('<I', 2))
        self.uc.mem_write(ENTITY + 0xb4, struct.pack('<I', TRAP))
        self.uc.mem_write(TRAP, bytes([4]))
        self.uc.mem_write(POSITION, struct.pack('<hh', 10, 8))
        self.grid_args = []
        self.uc.hook_add(UC_HOOK_CODE, self.native_call)

    def native_call(self, uc, address, size, _):
        if address == 0x023360FC:  # GetTile: stub only the world lookup
            uc.reg_write(UC_ARM_REG_R0, TILE)
            # Caller-saved scratch registers are deliberately destroyed.
            for reg in [UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R12]:
                uc.reg_write(reg, 0xdeadbeef)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address == 0x02337428:
            self.grid_args.append([uc.reg_read(r) for r in REGS[:4]])
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def run_hook(self, name, values=None):
        for i, reg in enumerate(REGS):
            self.uc.reg_write(reg, 0x12340000 + i)
        for index, value in (values or {}).items():
            self.uc.reg_write(REGS[index], value)
        self.uc.reg_write(UC_ARM_REG_SP, STACK)
        self.uc.reg_write(UC_ARM_REG_LR, STOP)
        before = [self.uc.reg_read(r) for r in REGS]
        self.uc.emu_start(self.targets[name], STOP, count=10000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_PC), STOP)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_SP), STACK)
        return before, [self.uc.reg_read(r) for r in REGS]

    def begin(self):
        args = {0: POSITION, 1: 5, 2: 0, 3: 1}
        self.run_hook('InspectTrapBegin', args)
        self.assertEqual(self.grid_args[-1], list(args.values()))

    def grid_tile(self, x=1, y=2):
        self.uc.mem_write(GRID, struct.pack('<H', 0x903a))
        self.uc.mem_write(STACK + 0x1c, struct.pack('<I', y))
        before, after = self.run_hook('InspectTrapGridTile', {
            5: DUNGEON, 6: 10, 7: 8, 8: x, 10: GRID,
        })
        self.assertEqual(after[10], GRID + 6)
        for i in range(13):
            if i not in (2, 10):
                self.assertEqual(after[i], before[i], f'r{i} clobbered')
        return after[2]

    def end(self):
        before, after = self.run_hook('InspectTrapEnd', {0: DUNGEON + 0x1a000, 1: 0})
        self.assertEqual(after, before)
        self.assertEqual(bytes(self.uc.mem_read(BLEND, 10)), self.original_blend)
        self.assertEqual(self.uc.mem_read(self.state, 1), b'\x00')
        self.assertEqual(self.uc.mem_read(DUNGEON + 0x1a251, 1), b'\x00')

    def test_hidden_trap_all_subtiles_and_no_reveal(self):
        self.begin()
        blend = bytes(self.uc.mem_read(BLEND, 10))
        self.assertEqual(blend[2:4], b'\x01\x02')
        self.assertEqual(blend[6:10], b'\x40\x00\x40\x00')
        world_before = bytes(self.uc.mem_read(TILE, 0x3000))
        for y in range(3):
            for x in range(3):
                index = 4 * 9 + y * 3 + x
                entry = 0xac23  # palette, both flip bits, character 0x23
                self.uc.mem_write(DUNGEON + 0x11ec8 + index * 2, struct.pack('<H', entry))
                pixels = bytes(range(32))
                self.uc.mem_write(0x06018000 + 0x23 * 32, pixels)
                self.assertEqual(self.grid_tile(x, y), 0xac00 | (0x310 + index))
                self.assertEqual(bytes(self.uc.mem_read(0x06010000 + (0x310 + index) * 32, 32)), pixels)
        self.assertEqual(bytes(self.uc.mem_read(TILE, 0x3000)), world_before)
        self.end()
        self.assertEqual(self.grid_tile(), 0x903a)

    def test_grid_is_unchanged_outside_y(self):
        self.assertEqual(self.grid_tile(), 0x903a)
        self.end()

    def test_excludes_other_rooms_corridors_visible_items_and_invalid_traps(self):
        cases = [(TILE + 7, b'\x04'), (TILE + 7, b'\xff'),
                 (ENTITY + 0x20, b'\x01'), (ENTITY, struct.pack('<I', 3)),
                 (ENTITY, struct.pack('<I', 5)), (TRAP, b'\x19'),
                 (TILE + 0x10, bytes(4)), (ENTITY + 0xb4, bytes(4))]
        for address, data in cases:
            with self.subTest(address=hex(address), data=data):
                self.begin()
                old = bytes(self.uc.mem_read(address, len(data)))
                self.uc.mem_write(address, data)
                self.assertEqual(self.grid_tile(), 0x903a)
                self.uc.mem_write(address, old)
                self.end()

    def test_direction_redraw_restores_original_blending_on_cancel(self):
        self.original_blend = bytes([1, 0, 2, 0, 2, 7, 80, 0, 48, 0])
        self.uc.mem_write(BLEND, self.original_blend)
        for _ in range(5):
            self.begin()
        self.end()
        self.end()

    def test_corridor_start_does_not_enable_and_clears_previous_inspection(self):
        self.begin()
        self.uc.mem_write(TILE + 7, b'\xff')
        self.begin()
        self.assertEqual(self.grid_tile(), 0x903a)
        self.end()

    def test_registration_and_hook_conflicts(self):
        cave = self.record.caves[0]
        self.assertGreaterEqual(cave.file_offset, 0x1a578)
        self.assertLessEqual(cave.file_offset + cave.size, 0x2d300)
        catalog = load_yaml(ROOT / 'patch_engine/catalog.yaml')
        self.assertIn('inspect_trap', catalog['modules'])
        self.assertEqual(FULL_STACK_MODULES.count('inspect_trap'), 1)
        self.assertLess(catalog['recommended_order'].index('inspect_trap'),
                        catalog['recommended_order'].index('korean'))
        sites = {h.site for h in self.record.hooks}
        for module in FULL_STACK_MODULES:
            if module == 'inspect_trap':
                continue
            manifest = load_module_manifest(ROOT / 'true_patches' / module)
            for hook in manifest.get('hooks', []):
                self.assertNotIn(self.profile['symbols'].get(hook.get('symbol')), sites,
                                 f'hook conflict: {module}')

    def test_cave_relocation(self):
        source = ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'
        rom = NintendoDSRom(source.read_bytes())
        manifest = load_module_manifest(self.module)
        manifest['cave']['preferred'] = self.record.caves[0].file_offset + 0x400
        record, rom = apply_asm_single(
            module_id='inspect_trap', module_dir=self.module, manifest=manifest,
            profile=self.profile, rom=rom, config=get_ppmdu_config_for_rom(rom),
            armips_exe=ROOT / 'tools/armips.exe', prior_hook_sites=set(), rom_in=source,
        )
        self.assertNotEqual(record.caves[0].load_address, self.state)
        blob = get_rom_binary(rom, 'ov29')
        for hook in record.hooks:
            word, = struct.unpack_from('<I', blob, hook.site - 0x022dc240)
            target = branch_target(hook.site, word)
            self.assertGreaterEqual(target, record.caves[0].load_address)
            self.assertLess(target, record.caves[0].load_address + record.caves[0].size)

    def test_preview_characters_do_not_overlap_native_graphics(self):
        # Native grid graphics copy in ov29: 0x5e20-byte offset, 0x240 bytes.
        self.assertEqual(struct.unpack_from('<I', self.ov29, 0x022e12f4 - 0x022dc240)[0], 0x5e20)
        self.assertEqual(struct.unpack_from('<I', self.ov29, 0x022e12c8 - 0x022dc240)[0], 0xe3a02d09)
        self.assertGreaterEqual(0x310 * 32, 0x5e20 + 0x240)
        self.assertLessEqual((0x310 + 25 * 9) * 32, 0x8000)
        self.uc.mem_write(0x06010000, bytes([0x55]) * 0x6200)
        self.uc.mem_write(0x06018000, bytes([0x33]) * 0x8000)
        self.begin()
        self.uc.mem_write(TRAP, bytes([24]))
        for y in range(3):
            for x in range(3):
                self.grid_tile(x, y)
        self.assertEqual(bytes(self.uc.mem_read(0x06010000, 0x6200)), bytes([0x55]) * 0x6200)
        self.assertEqual(bytes(self.uc.mem_read(0x06018000, 0x8000)), bytes([0x33]) * 0x8000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
