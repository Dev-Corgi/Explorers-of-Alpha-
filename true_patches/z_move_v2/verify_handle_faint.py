"""Run the actual faint-entry wrapper and native team lookup with Unicorn."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import *

MODULE = Path(__file__).resolve().parent
DUNGEON, ENTITY, GAUGE, SP, RETURN = 0x02100000, 0x02130000, 0x02140000, 0x02702000, 0x02150000
STOP = 0x022F7F34


def machine(rom, ovs):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_map(0x02700000, 0x4000)
    uc.mem_write(0x02000000, bytes(rom.arm9))
    for i in (29, 36):
        uc.mem_write(ovs[i].ramAddress, bytes(ovs[i].data))
    uc.mem_write(0x02353538, struct.pack('<I', DUNGEON))
    for i in range(4):
        uc.mem_write(DUNGEON + 0x12B28 + i * 4, struct.pack('<I', ENTITY + i * 0xB8))
    return uc


def run(uc, entry, slot, source, context):
    args = (ENTITY + slot * 0xB8, source, context, 0x13572468)
    for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
        uc.reg_write(reg, value)
    uc.reg_write(UC_ARM_REG_R4, 0x24681357)
    uc.reg_write(UC_ARM_REG_R12, 0x11223344)
    uc.reg_write(UC_ARM_REG_LR, RETURN)
    uc.reg_write(UC_ARM_REG_SP, SP)
    uc.emu_start(entry, STOP, count=10000)
    assert uc.reg_read(UC_ARM_REG_PC) == STOP
    assert uc.reg_read(UC_ARM_REG_SP) == SP - 36
    return tuple(uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))


def compile_wrapper(entry, broken=False):
    code = (MODULE / 'asm/ZMoveOv29.asm').read_text(encoding='utf-8')
    wrapper = code.split('ZMove_HandleFaintHook:\n', 1)[1].split('; r0 = window id.', 1)[0]
    add = code.split('ZMove_AddZGauge:\n', 1)[1].split('.pool', 1)[0]
    text = f'''.nds
.arm
GetTeamMemberIndex equ 0x022E2A38
HandleFaintBody equ 0x022F7F34
Z_GAUGE_MAX equ 100
Z_GAUGE_GAIN_ENEMY_FAINT equ 2
ZGauge equ 0x{GAUGE:X}
.create "fixture.bin", 0x{entry:X}
ZMove_HandleFaintHook:
{wrapper}
ZMove_AddZGauge:
{add}
.pool
.close
'''
    if broken:
        text = text.replace('push {r1-r4, r12, lr}', 'push {r4, lr}').replace('pop {r1-r4, r12, lr}', 'pop {r4, lr}')
    with tempfile.TemporaryDirectory(prefix='z_faint_args_') as d:
        work = Path(d)
        (work / 'fixture.asm').write_text(text, encoding='utf-8')
        subprocess.run([str(ROOT / 'tools/armips.exe'), 'fixture.asm'], cwd=work, check=True)
        return (work / 'fixture.bin').read_bytes()


def main():
    rom = NintendoDSRom.fromFile(str(ROOT / 'PatchTesting/Export Rom/Explorers of Alpha+.nds'))
    ovs = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    entry = ovs[36].ramAddress + ((len(ovs[36].data) + 3) & ~3)
    compiled = compile_wrapper(entry)
    uc = machine(rom, ovs)
    uc.mem_write(entry, compiled)
    count = 0
    for slot in range(5):
        for source in (1, 604, 610):
            for context in (0, 0x02160000):
                for gauge in (0, 98, 100, 255):
                    uc.mem_write(GAUGE, struct.pack('<H', gauge))
                    args = run(uc, entry, slot, source, context)
                    assert args == (ENTITY + slot * 0xB8, source, context, 0x13572468), args
                    assert uc.reg_read(UC_ARM_REG_R12) == 0x11223344
                    assert struct.unpack('<I', uc.mem_read(SP - 36, 4))[0] == 0x24681357
                    assert struct.unpack('<I', uc.mem_read(SP - 4, 4))[0] == RETURN
                    expected = gauge if slot < 4 else min(100, (0 if gauge > 100 else gauge) + 2)
                    assert struct.unpack('<H', uc.mem_read(GAUGE, 2))[0] == expected
                    count += 1
    # Reproduce the previous wrapper's actual source/context loss using its
    # source with the old save/restore pair and the same native lookup.
    uc = machine(rom, ovs)
    uc.mem_write(entry, compile_wrapper(entry, broken=True))
    args = run(uc, entry, 1, 604, 0)
    assert args[1] == ENTITY + 0xB8 and args[2] == 1, args
    print(f'PASS: {count} faint-entry ABI/gauge cases; old source 604 corruption reproduced')


if __name__ == '__main__':
    main()
