"""Execute assembled fixed-seat scaling without rebuilding a ROM."""
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from true_patches.base_stats_speed.generate_tables import calc_stat_from_tables

BOOST = {200, 202, 206, 211, 214, 215, 217, 218, 219, 220, 221, 250}
MODULE = Path(__file__).resolve().parent


def main():
    rom = NintendoDSRom.fromFile(str(ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'))
    ovs = loadOverlayTable(rom.arm9OverlayTable, lambda i, f: rom.files[f])
    with tempfile.TemporaryDirectory(prefix='fixed_scale_test_') as temp:
        work = Path(temp) / 'asm'
        shutil.copytree(MODULE / 'asm', work)
        offset = (len(ovs[36].data) + 3) & ~3
        (work / 'overlay_0036.bin').write_bytes(bytes(ovs[36].data).ljust(offset + 0x3000, b'\0'))
        (work / 'overlay_0029.bin').write_bytes(ovs[29].data)
        (work / 'arm9.bin').write_bytes(rom.arm9)
        (work / 'generated.inc').write_text(f'BaseStatsCodeAddress equ 0x{offset:X}\n')
        result = subprocess.run([str(ROOT / 'tools/armips.exe'), '-sym', 'test.sym', 'main.asm'], cwd=work, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        symbols = {}
        for line in (work / 'test.sym').read_text().splitlines():
            fields = line.split()
            if len(fields) == 2:
                try:
                    symbols[fields[1].lower()] = int(fields[0], 16)
                except ValueError:
                    pass
        u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        u.mem_map(0x02000000, 0x400000)
        u.mem_write(0x023A7080, (work / 'overlay_0036.bin').read_bytes())
    dungeon, entity, info, team = 0x02100000, 0x02120000, 0x02121000, 0x02130000
    u.mem_write(0x02353538, struct.pack('<I', dungeon))
    u.mem_write(entity + 0xB4, struct.pack('<I', info))
    state = {'hp': None}

    def stub(uc, address, size, data):
        r0, r1 = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        if address == 0x0205638C:
            uc.reg_write(UC_ARM_REG_R0, team + r0 * 0x80)
        elif address == 0x02056228:
            uc.reg_write(UC_ARM_REG_R0, int(r0 == 99))
        elif address == 0x0208FEA4:
            uc.reg_write(UC_ARM_REG_R0, r0 // r1)
            uc.reg_write(UC_ARM_REG_R1, r0 % r1)
        elif address == symbols['basestats_calcstat'] and data['hp'] is not None:
            uc.reg_write(UC_ARM_REG_R0, data['hp'])
        else:
            return
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    u.hook_add(UC_HOOK_CODE, stub, state)
    bases = (MODULE / 'asm/generated/base_stats.bin').read_bytes()
    rates = (MODULE / 'asm/generated/evo_rate.bin').read_bytes()
    primary = (MODULE / 'asm/generated/primary.bin').read_bytes()

    def run(room, level, entry=30, species=388, empty=False):
        u.mem_write(dungeon + 0x40DA, bytes([room]))
        u.mem_write(info + 2, struct.pack('<H', species))
        u.mem_write(info + 0xA, b'\x07')
        u.mem_write(info + 0x10, struct.pack('<HH', 51, 73))
        for i, lev in enumerate([level, max(1, level - 3), 100, 100]):
            # Guest at slot 2 and inactive slot 3 must not raise team max.
            u.mem_write(team + i * 0x80, bytes([0 if empty or i == 3 else 1, 0, lev]))
            u.mem_write(team + i * 0x80 + 8, struct.pack('<H', 99 if i == 2 else i))
        saved = [0x12340000 + i for i in range(4)]
        for reg, val in zip([UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7], saved):
            u.reg_write(reg, val)
        u.reg_write(UC_ARM_REG_R0, entity)
        u.reg_write(UC_ARM_REG_R1, entry)
        u.reg_write(UC_ARM_REG_SP, 0x021FF000)
        u.reg_write(UC_ARM_REG_LR, 0x021F0000)
        u.emu_start(symbols['basestats_charmandersescale'], 0x021F0000, count=5000)
        assert u.reg_read(UC_ARM_REG_PC) == 0x021F0000
        assert u.reg_read(UC_ARM_REG_SP) == 0x021FF000
        assert [u.reg_read(r) for r in [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7]] == saved
        actual = (u.mem_read(info + 0xA, 1)[0], struct.unpack('<HH', u.mem_read(info + 0x10, 4)))
        if entry != 30 or room < 200 or empty:
            assert actual == (7, (51, 73)), actual
        else:
            expected_level = min(100, level + (5 if room in BOOST else 0))
            pidx = struct.unpack_from('<H', primary, species * 2)[0]
            hp = state['hp'] if state['hp'] is not None else calc_stat_from_tables(pidx, expected_level, 0, 0, bases, rates)
            hp = min(32767, hp * 2 if room in BOOST else hp + hp // 4)
            assert actual == (expected_level, (hp, hp)), (room, actual, expected_level, hp)

    # Exhaustive room filter plus independent level-boundary/guest checks.
    for room in range(256):
        run(room, 50)
    for room in [200, 201, 202, 206, 211, 214, 215, 217, 218, 219, 220, 221, 224, 240, 248, 250, 251, 255]:
        for level in [1, 94, 95, 96, 99, 100]:
            run(room, level, species=548)
        run(room, 50, entry=84)
        run(room, 50, empty=True)
    state['hp'] = 20000
    run(200, 100)
    run(201, 100)
    print('OK: full ASM layout, 256 room IDs, level caps, guest exclusion, empty party, other entries, HP cap and register ABI')


if __name__ == '__main__':
    main()
