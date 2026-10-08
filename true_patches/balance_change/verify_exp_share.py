"""Exercise Alpha's actual standby EXP loop and its floor-init writers."""
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

ROM = ROOT / 'PatchTesting/Export Rom/Explorers of Alpha+_kor.nds'
PERCENT = 0x02097E34
TEAM = 0x02100000
DUNGEON = 0x02110000
RETURN = 0x02000010


def main():
    rom = NintendoDSRom.fromFile(sys.argv[1] if len(sys.argv) > 1 else ROM)
    overlays = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x02000000, 0x400000)
    u.mem_write(0x02000000, bytes(rom.arm9))
    u.mem_write(overlays[36].ramAddress, bytes(overlays[36].data))
    word = lambda addr: struct.unpack('<I', u.mem_read(addr, 4))[0]
    put = lambda addr, value: u.mem_write(addr, struct.pack('<I', value))
    assert word(PERCENT) == 0xE3A00064
    assert word(0x023A9378) == 0xE3A04064
    assert word(0x023A99A8) == 0xE3A01064

    # Upgrade stages 0-9 and OFF all write to the executable percentage byte.
    for stage in range(10):
        u.mem_write(TEAM, bytes([stage * 10]))
        u.reg_write(UC_ARM_REG_R5, TEAM)
        u.reg_write(UC_ARM_REG_R1, 0)
        u.mem_write(PERCENT, b'\x00')
        u.emu_start(0x023A9370, 0x023A9384)
        assert word(PERCENT) == 0xE3A00064
    u.mem_write(PERCENT, b'\x00')
    u.emu_start(0x023A99A8, 0x023A99B4)
    assert word(PERCENT) == 0xE3A00064

    special, level_reset, exp_enabled = -1, 0, 1

    def stub(uc, address, size, _):
        values = {0x0204C938: special & 0xFFFFFFFF,
                  0x02051318: level_reset, 0x0205171C: exp_enabled}
        if address == 0x0208FEA4:
            values[address] = uc.reg_read(UC_ARM_REG_R0) // uc.reg_read(UC_ARM_REG_R1)
        if address in values:
            uc.reg_write(UC_ARM_REG_R0, values[address])
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    u.hook_add(UC_HOOK_CODE, stub)
    put(0x020B0A48, TEAM)
    put(0x02353538, DUNGEON)
    u.mem_write(DUNGEON + 0x748, b'\x01')
    # Actual EXP award hook must reach the same routine we patched.
    hook = struct.unpack_from('<I', overlays[29].data,
                              0x0230A7CC - overlays[29].ramAddress)[0]
    displacement = hook & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 0x1000000
    entry = 0x0230A7D4 + displacement * 4
    assert entry == 0x02097DF8

    for gain in (1, 101, 10000):
        u.mem_write(TEAM, bytes(0x44 * 555))
        for slot, species, level, exp in ((0, 25, 5, 100), (1, 0, 5, 100),
                                           (2, 25, 100, 100), (554, 25, 5, 9999990)):
            member = TEAM + slot * 0x44
            u.mem_write(member + 1, bytes([level]))
            u.mem_write(member + 4, struct.pack('<H', species))
            put(member + 0x10, exp)
        u.reg_write(UC_ARM_REG_R9, gain)
        u.emu_start(entry, 0x0230A7D0)
        assert word(TEAM + 0x10) == 100 + gain
        assert word(TEAM + 0x44 + 0x10) == 100  # empty entry
        assert word(TEAM + 0x88 + 0x10) == 100  # already level 100
        assert word(TEAM + 554 * 0x44 + 0x10) == min(9999990 + gain, 9999999)

    # Preserve Alpha's special episode / level reset / no EXP restrictions.
    for special, level_reset, exp_enabled in ((0, 0, 1), (-1, 1, 1), (-1, 0, 0)):
        put(TEAM + 0x10, 100)
        u.reg_write(UC_ARM_REG_R9, 101)
        u.emu_start(entry, 0x0230A7D0)
        assert word(TEAM + 0x10) == 100
    print('PASS: all upgrade stages + OFF write 100%; actual standby EXP loop, cap and exclusions')


if __name__ == '__main__':
    main()
