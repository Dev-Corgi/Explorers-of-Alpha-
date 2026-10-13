"""Execute every generated Hangul name pair and deletion in the built ROM."""
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from patch_engine.apply_korean_assemble import _dialogue_syllables, _symbol_keys

KEYBOARD, NAME, SP, STOP = 0x02100000, 0x02101000, 0x02702000, 0x02102000


def main():
    rom = NintendoDSRom.fromFile(str(ROOT / 'PatchTesting/Export Rom/Explorers of Alpha+_kor.nds'))
    glyph_count = len(rom.getFileByName('FONT/ko_glyph.bin')) // 28
    syllables = _dialogue_syllables(ROOT, glyph_count)
    symbols = _symbol_keys(bytes(rom.arm9))
    overlays = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_map(0x02700000, 0x4000)
    uc.mem_write(0x02000000, bytes(rom.arm9))
    uc.mem_write(overlays[36].ramAddress, bytes(overlays[36].data))
    uc.mem_write(0x020AFDF0, struct.pack('<I', KEYBOARD))

    def services(machine, address, size, data):
        if address in (0x02017CCC, 0x02037F58, 0x02038ADC):
            machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, services)
    for i, (character, dense) in enumerate(syllables):
        uc.mem_write(KEYBOARD, bytes(0x100))
        uc.mem_write(KEYBOARD + 0xF8, struct.pack('<I', NAME))
        uc.mem_write(KEYBOARD + 0x1B, bytes([10, 1]))
        uc.mem_write(NAME, bytes([symbols[i // 78]]) + bytes(10))
        for reg, value in ((UC_ARM_REG_R1, KEYBOARD), (UC_ARM_REG_R4, symbols[i % 78]),
                           (UC_ARM_REG_R12, 0), (UC_ARM_REG_SP, SP), (UC_ARM_REG_LR, STOP)):
            uc.reg_write(reg, value)
        uc.emu_start(0x020384D8, 0x020388DC, count=1000)
        assert uc.reg_read(UC_ARM_REG_PC) == 0x020388DC, character
        assert bytes(uc.mem_read(NAME, 2)) == bytes([dense >> 8, dense & 255]), character
        assert uc.mem_read(KEYBOARD + 0x1C, 1)[0] == 2
        assert uc.reg_read(UC_ARM_REG_SP) == SP
        uc.reg_write(UC_ARM_REG_SP, SP)
        uc.reg_write(UC_ARM_REG_LR, STOP)
        uc.emu_start(0x02038904, STOP, count=1000)
        assert uc.reg_read(UC_ARM_REG_PC) == STOP, character
        assert uc.mem_read(KEYBOARD + 0x1C, 1)[0] == 0
        assert bytes(uc.mem_read(NAME, 2)) == bytes(2)
        assert uc.reg_read(UC_ARM_REG_SP) == SP
    print(f'PASS: {len(syllables)} built-ROM Hangul pair insertions and whole-character deletions')


if __name__ == '__main__':
    main()
