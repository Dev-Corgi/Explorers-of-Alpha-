"""Assemble the TM entry wrapper; optionally replay a read-only dungeon DSS.

No ROM/save/state output. Snapshot replay executes the installed cleanup,
native item/learnset/status checks and target-eligibility write. File reads
are modeled; the UI boundary is the stop point, not an emulated button press.
"""
from pathlib import Path
import hashlib
import struct
import subprocess
import sys
import tempfile

from true_patches.mega_evolve.trace_sprite_corruption import read_snapshot, RAM_OFFSET, ITCM_OFFSET, REPO
from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

MODULE = Path(__file__).resolve().parent
RESUME = 0x0231DA84
STACK, STOP = 0x02702000, 0x02703000


def branch_target(address, instruction):
    assert instruction >> 24 in (0xEA, 0xEB)
    displacement = instruction & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 0x1000000
    return address + 8 + displacement * 4


def compile_wrapper(entry, restore, broken=False):
    source = (MODULE / 'asm/ZMoveOv29.asm').read_text(encoding='utf-8')
    body = source.split('TeachItemHandler_EntryHook:\n', 1)[1].split('; LevelUp entry:', 1)[0]
    if broken:
        body = body.replace('{r0-r3, r12, lr}', '{r3, lr}')
    text = f'''.nds
.arm
ZMove_ForceRestoreAllPendingSlots equ 0x{restore:X}
TeachItemHandlerResume equ 0x{RESUME:X}
.create "fixture.bin", 0x{entry:X}
{body}
.close
'''
    with tempfile.TemporaryDirectory(prefix='z_tm_args_') as directory:
        work = Path(directory)
        (work / 'fixture.asm').write_text(text, encoding='utf-8')
        subprocess.run([str(REPO / 'tools/armips.exe'), 'fixture.asm'], cwd=work, check=True)
        return (work / 'fixture.bin').read_bytes()


def verify_arguments():
    entry, restore = 0x023D0000, 0x021F0000
    count = 0
    for broken in (True, False):
        u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        u.mem_map(0x02000000, 0x400000)
        u.mem_map(0x02700000, 0x4000)
        u.mem_write(entry, compile_wrapper(entry, restore, broken))
        cleanups = []

        def cleanup(cpu, address, size, unused):
            assert cpu.reg_read(UC_ARM_REG_SP) % 8 == 0
            cleanups.append(1)
            # A called helper may freely clobber all argument/scratch registers.
            for index, reg in enumerate((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                                         UC_ARM_REG_R3, UC_ARM_REG_R12)):
                cpu.reg_write(reg, 0x12340000 + index)
            cpu.reg_write(UC_ARM_REG_PC, cpu.reg_read(UC_ARM_REG_LR))

        u.hook_add(UC_HOOK_CODE, cleanup, begin=restore, end=restore)
        for slot in range(4):
            for item in (0x02160000, 0x022A38D2, 0x02300000):
                args = (0x02130000 + slot * 0xB8, item, 0x24681357, 0x13572468)
                for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
                    u.reg_write(reg, value)
                u.reg_write(UC_ARM_REG_R12, 0x11223344)
                u.reg_write(UC_ARM_REG_SP, STACK)
                u.reg_write(UC_ARM_REG_LR, STOP)
                u.emu_start(entry, RESUME, count=1000)
                assert u.reg_read(UC_ARM_REG_PC) == RESUME
                assert u.reg_read(UC_ARM_REG_SP) == STACK - 40
                actual = tuple(u.reg_read(reg) for reg in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
                if broken:
                    assert actual[:3] != args[:3] and actual[3] == args[3]
                else:
                    assert actual == args
                    assert u.reg_read(UC_ARM_REG_R12) == 0x11223344
                assert struct.unpack('<I', u.mem_read(STACK - 4, 4))[0] == STOP
                count += 1
        assert len(cleanups) == 12
    print(f'PASS {count} TM entry argument/stack cases; old wrapper corruption reproduced, cleanup still runs')


class World:
    def __init__(self, path):
        self.original, raw = read_snapshot(path)
        self.ram = raw[RAM_OFFSET:RAM_OFFSET + 0x400000]
        self.u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.u.mem_map(0x02000000, 0x400000)
        self.u.mem_write(0x02000000, self.ram)
        self.u.mem_map(0x01FF8000, 0x8000)
        self.u.mem_write(0x01FF8000, raw[ITCM_OFFSET:ITCM_OFFSET + 0x4000])
        self.u.mem_map(0x02700000, 0x4000)
        rom = NintendoDSRom((REPO / 'PatchTesting/Export Rom/Explorers of Alpha+.nds').read_bytes())
        self.waza = bytes(rom.getFileByName('BALANCE/waza_p.bin'))
        self.cursor = 0
        self.stop_at_selector = False
        self.native_arguments = None
        self.u.hook_add(UC_HOOK_CODE, self.service)

    def word(self, address):
        return struct.unpack('<I', self.u.mem_read(address, 4))[0]

    def service(self, u, address, size, unused):
        if address == RESUME:
            self.native_arguments = tuple(u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1))
        if address == 0x023877EC and self.stop_at_selector:
            u.emu_stop()
        if address not in (0x02008168, 0x02008194, 0x020082A8, 0x02008254):
            return
        a, b, c = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)]
        if address == 0x020082A8:
            assert c == 0
            self.cursor = b
        elif address == 0x02008254:
            block = self.waza[self.cursor:self.cursor + c]
            assert len(block) == c
            u.mem_write(b, block)
            self.cursor += c
        u.reg_write(UC_ARM_REG_R0, 0)
        u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

    def call(self, address, a=0, b=0):
        for reg, value in ((UC_ARM_REG_R0, a), (UC_ARM_REG_R1, b),
                           (UC_ARM_REG_SP, STACK), (UC_ARM_REG_LR, STOP)):
            self.u.reg_write(reg, value)
        self.u.emu_start(address, STOP, count=2000000)
        if not self.stop_at_selector:
            assert self.u.reg_read(UC_ARM_REG_PC) == STOP
        return self.u.reg_read(UC_ARM_REG_R0)


def verify_snapshot(path):
    before = hashlib.sha256(path.read_bytes()).digest()
    w = World(path)
    dungeon = w.word(0x02353538)
    entity = w.word(dungeon + 0x12B28)
    monster = w.word(entity + 0xB4)
    bag = w.word(w.word(0x020AF6B8) + 0x384)
    species = struct.unpack('<H', w.u.mem_read(monster + 2, 2))[0]
    assert species == 2065, 'This regression snapshot must contain Mega Lucario'
    swords_dance = None
    for i in range(50):
        item = bag + i * 6
        flags, quantity, item_id = struct.unpack('<3H', w.u.mem_read(item, 6))
        if flags & 1:
            move = w.call(0x0200CAFC, item_id)
            if move == 181:
                swords_dance = item
                break
    assert swords_dance is not None
    entry = branch_target(0x0231DA80, w.word(0x0231DA80))
    restore = branch_target(entry + 4, w.word(entry + 4))
    fixed = compile_wrapper(entry, restore)
    broken = compile_wrapper(entry, restore, broken=True)
    assert bytes(w.u.mem_read(entry, len(broken))) == broken, 'Snapshot entry differs from the reported broken wrapper'

    def replay(compiled, current_species, reject=None):
        run = World(path)
        run.u.mem_write(entry, compiled)
        run.u.ctl_remove_cache(entry, entry + len(compiled))
        run.u.mem_write(monster + 2, struct.pack('<2H', current_species, current_species))
        if reject == 'already_known':
            run.u.mem_write(monster + 0x128, struct.pack('<H', 181))
        elif reject == 'status':
            run.u.mem_write(monster + 0xBC, b'\x07')
        elif reject == 'transformed':
            run.u.mem_write(monster + 0x48, b'\xFA')
        run.stop_at_selector = True
        run.call(0x0231DA80, entity, swords_dance)
        assert run.u.reg_read(UC_ARM_REG_PC) == 0x023877EC
        return run, bytes(run.u.mem_read(monster + 0x161, 1))

    old, eligible = replay(broken, species)
    assert eligible == b'\0' and old.native_arguments != (entity, swords_dance)
    for current_species in (490, 1090, 2065, 2066, 2067, 2068):
        run, eligible = replay(fixed, current_species)
        assert eligible == b'\1', (current_species, eligible)
        assert run.native_arguments == (entity, swords_dance)
        assert struct.unpack('<2H', run.u.mem_read(monster + 2, 4)) == (current_species, current_species)
        assert bytes(run.u.mem_read(swords_dance, 6)) == bytes(w.u.mem_read(swords_dance, 6))
    for reject in ('already_known', 'status', 'transformed'):
        _, eligible = replay(fixed, species, reject)
        assert eligible == b'\0', reject
    _, eligible = replay(fixed, 10)  # Caterpie cannot learn Swords Dance.
    assert eligible == b'\0'
    assert hashlib.sha256(path.read_bytes()).digest() == before
    print('PASS reported DSS: original red target reproduced; normal/Mega/Shiny Lucario of both genders selectable with fix')
    print('PASS known moves, incompatible species, status and transformed-client restrictions retained; source DSS unchanged')


def main():
    verify_arguments()
    if len(sys.argv) > 1:
        verify_snapshot(Path(sys.argv[1]))


if __name__ == '__main__':
    main()
