"""Execute the assembled Perish Song faint hook without building/saving a ROM."""
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

VICTIM, KILLER = 0x02070000, 0x02071000
VICTIM_INFO, KILLER_INFO = 0x02072000, 0x02073000
STACK = 0x02078000
SITE, RESUME = 0x022F7F38, 0x022F7F3C
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_R12, UC_ARM_REG_LR]


class PerishSongDefeatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_rom_profile(ROOT / 'patch_engine', 'us_vanilla')
        cls.manifest = load_module_manifest(ROOT / 'true_patches/status_adjust')
        source = ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'
        rom = NintendoDSRom(source.read_bytes())
        cls.native29 = bytes(get_rom_binary(rom, 'ov29'))
        cls.record, rom = apply_asm_single(
            module_id='status_adjust', module_dir=ROOT / 'true_patches/status_adjust',
            manifest=cls.manifest, profile=cls.profile, rom=rom,
            config=get_ppmdu_config_for_rom(rom), armips_exe=ROOT / 'tools/armips.exe',
            prior_hook_sites=set(), rom_in=source,
        )
        cls.ov29 = bytes(get_rom_binary(rom, 'ov29'))
        cls.ov36 = bytes(get_rom_binary(rom, 'ov36'))

    def setUp(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(0x02000000, 0x00400000)
        self.uc.mem_write(0x022DC240, self.ov29)
        self.uc.mem_write(0x023A7080, self.ov36)
        self.uc.mem_write(VICTIM, struct.pack('<I', 1))
        self.uc.mem_write(KILLER, struct.pack('<I', 1))
        self.uc.mem_write(VICTIM + 0xb4, struct.pack('<I', VICTIM_INFO))
        self.uc.mem_write(KILLER + 0xb4, struct.pack('<I', KILLER_INFO))
        self.uc.mem_write(KILLER_INFO, bytes([0x55]) * 0x200)
        self.uc.mem_write(KILLER_INFO + 0x10, struct.pack('<h', 30))
        self.uc.mem_write(KILLER_INFO + 0x106, b'\x03')
        self.calls = []
        self.uc.hook_add(UC_HOOK_CODE, self.native_call)

    def native_call(self, uc, address, size, _):
        if address not in (0x022E3AB4, 0x0234B350):
            return
        self.assertEqual(uc.mem_read(KILLER_INFO + 0x106, 1), b'\x00')
        args = [uc.reg_read(r) for r in REGS[:3]]
        self.calls.append((address, args))
        self.assertEqual(uc.reg_read(UC_ARM_REG_SP) % 8, 0)
        for r in REGS[:4] + [UC_ARM_REG_R12]:
            uc.reg_write(r, 0xdeadbeef)
        uc.reg_write(UC_ARM_REG_CPSR, 0x60000013)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def execute(self, victim=VICTIM, killer=KILLER, source=100):
        for i, reg in enumerate(REGS):
            self.uc.reg_write(reg, 0x12340000 + i)
        for reg, value in zip(REGS[:3], [victim, source, killer]):
            self.uc.reg_write(reg, value)
        self.uc.reg_write(UC_ARM_REG_SP, STACK)
        self.uc.reg_write(UC_ARM_REG_CPSR, 0xa0000013)
        before = [self.uc.reg_read(r) for r in REGS]
        self.uc.emu_start(SITE, RESUME, count=1000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_PC), RESUME)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_SP), STACK)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_CPSR), 0xa0000013)
        expected = before[:]
        expected[10] = victim  # displaced mov r10,r0
        self.assertEqual([self.uc.reg_read(r) for r in REGS], expected)

    def test_defeat_cures_only_perish_song_and_refreshes_icon_and_message(self):
        before = bytes(self.uc.mem_read(KILLER_INFO, 0x200))
        victim_before = bytes(self.uc.mem_read(VICTIM_INFO, 0x200))
        self.execute()
        expected = before[:0x106] + b'\x00' + before[0x107:]
        self.assertEqual(bytes(self.uc.mem_read(KILLER_INFO, 0x200)), expected)
        self.assertEqual(bytes(self.uc.mem_read(VICTIM_INFO, 0x200)), victim_before)
        self.assertEqual([a for a, _ in self.calls], [0x022e3ab4, 0x0234b350])
        self.assertEqual(self.calls[0][1][0], KILLER)
        self.assertEqual(self.calls[1][1], [KILLER, KILLER, 0xc83])
        self.assertEqual(struct.unpack_from('<I', self.native29, 0x02305bf0 - 0x022dc240)[0], 0xc83)

    def test_all_remaining_counts_cure(self):
        for count in [1, 2, 4, 255]:
            with self.subTest(count=count):
                self.uc.mem_write(KILLER_INFO + 0x106, bytes([count]))
                self.execute(source=559)
                self.assertEqual(self.uc.mem_read(KILLER_INFO + 0x106, 1), b'\x00')

    def test_no_cure_for_self_faint_unattributed_faint_or_send_home(self):
        for kwargs in [{'killer': VICTIM}, {'killer': 0}, {'victim': 0}, {'source': 604}]:
            with self.subTest(kwargs=kwargs):
                before = bytes(self.uc.mem_read(KILLER_INFO, 0x200))
                self.execute(**kwargs)
                self.assertEqual(bytes(self.uc.mem_read(KILLER_INFO, 0x200)), before)
                self.assertEqual(self.calls, [])

    def test_inactive_invalid_or_dead_killer_is_unchanged(self):
        cases = [(KILLER, struct.pack('<I', 0)), (KILLER, struct.pack('<I', 3)),
                 (VICTIM, struct.pack('<I', 3)), (KILLER + 0xb4, bytes(4)),
                 (KILLER_INFO + 0x10, struct.pack('<h', 0)),
                 (KILLER_INFO + 0x10, struct.pack('<h', -1)),
                 (KILLER_INFO + 0x106, b'\x00')]
        for address, value in cases:
            with self.subTest(address=hex(address), value=value):
                old = bytes(self.uc.mem_read(address, len(value)))
                self.uc.mem_write(address, value)
                before = bytes(self.uc.mem_read(KILLER_INFO, 0x200))
                self.execute()
                self.assertEqual(bytes(self.uc.mem_read(KILLER_INFO, 0x200)), before)
                self.assertEqual(self.calls, [])
                self.uc.mem_write(address, old)

    def test_repeated_defeat_does_not_repeat_cure_message(self):
        self.execute()
        self.calls.clear()
        self.execute()
        self.assertEqual(self.calls, [])

    def test_existing_perish_infliction_countdown_and_cures_are_unchanged(self):
        for start, end in [(0x0231662c, 0x02316720),
                           (0x02311420, 0x023131f4),
                           (0x023058c4, 0x02305c28)]:
            with self.subTest(start=hex(start)):
                lo, hi = start - 0x022dc240, end - 0x022dc240
                self.assertEqual(self.ov29[lo:hi], self.native29[lo:hi])

    def test_existing_hooks_and_stack_integration(self):
        for hook in self.manifest['hooks']:
            site = self.profile['symbols'][hook['symbol']]
            word, = struct.unpack_from('<I', self.ov29, site - 0x022dc240)
            if 'patched_word' in hook:
                self.assertEqual(word, hook['patched_word'])
            else:
                self.assertEqual((word >> 25) & 7, 5)
        cave = self.record.caves[0]
        word, = struct.unpack_from('<I', self.ov29, SITE - 0x022dc240)
        self.assertTrue(cave.load_address <= branch_target(SITE, word) < cave.load_address + cave.size)
        for module in FULL_STACK_MODULES:
            if module == 'status_adjust':
                continue
            manifest = load_module_manifest(ROOT / 'true_patches' / module)
            for hook in manifest.get('hooks', []):
                self.assertNotEqual(self.profile['symbols'].get(hook.get('symbol')), SITE,
                                    f'hook conflict: {module}')
        self.assertEqual(self.ov29[SITE - 0x022dc240 - 8:SITE - 0x022dc240],
                         self.native29[SITE - 0x022dc240 - 8:SITE - 0x022dc240])


if __name__ == '__main__':
    unittest.main(verbosity=2)
