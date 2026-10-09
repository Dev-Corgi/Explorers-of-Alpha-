"""Execute the town team LV/HP update and shared panel setter; write no ROM."""
from pathlib import Path
import json
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
MODULE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))
import yaml
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from true_patches.base_stats_speed.generate_tables import calc_stat_from_tables


def main():
    rom = NintendoDSRom.fromFile(ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds')
    ovs = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    cfg = yaml.safe_load((MODULE / 'manifest.yaml').read_text(encoding='utf-8'))
    profile = yaml.safe_load((ROOT / 'patch_engine/rom_profile_us.yaml').read_text(encoding='utf-8'))
    for hook in cfg['hooks']:
        if hook['binary'] == 'ov11':
            site = profile['symbols'][hook['symbol']]
            assert struct.unpack_from('<I', ovs[11].data, site - ovs[11].ramAddress)[0] == hook['vanilla_word']
    with tempfile.TemporaryDirectory(prefix='town_ui_test_') as temp:
        work = Path(temp) / 'asm'
        shutil.copytree(MODULE / 'asm', work)
        offset = (len(ovs[36].data) + 3) & ~3
        (work / 'overlay_0036.bin').write_bytes(bytes(ovs[36].data).ljust(offset + cfg['cave']['estimated_bytes'], b'\0'))
        for n in [11, 29]:
            (work / f'overlay_{n:04d}.bin').write_bytes(ovs[n].data)
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
        u.mem_write(0x02000000, bytes(rom.arm9))
        u.mem_write(ovs[10].ramAddress, bytes(ovs[10].data))
        u.mem_write(ovs[11].ramAddress, (work / 'overlay_0011.bin').read_bytes())
        u.mem_write(ovs[36].ramAddress, (work / 'overlay_0036.bin').read_bytes())
        # Both declared ov11 hooks must reach their assembled dynamic cave.
        for hook in cfg['hooks']:
            if hook['binary'] != 'ov11':
                continue
            site = profile['symbols'][hook['symbol']]
            word = struct.unpack('<I', u.mem_read(site, 4))[0]
            assert word >> 24 == 0xEA
            displacement = word & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 0x1000000
            assert site + 8 + displacement * 4 == symbols[hook['target_symbol'].lower()]

    team, panel, status, sp = 0x02100000, 0x02110000, 0x02120000, 0x021FF000
    bases = (MODULE / 'asm/generated/base_stats.bin').read_bytes()
    rates = (MODULE / 'asm/generated/evo_rate.bin').read_bytes()
    primary = (MODULE / 'asm/generated/primary.bin').read_bytes()
    state = {'aura': False, 'exclusive': 0, 'stopped': False, 'calc_calls': []}

    def stub(uc, address, size, _):
        r0, r1 = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        if address == 0x022DC674:
            state['stopped'] = True
            uc.emu_stop()
            return
        if address == symbols['basestats_calcstat']:
            state['calc_calls'].append(tuple(uc.reg_read(r) for r in [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]))
            return  # Execute CalcStat itself, including the real table reads.
        if address == 0x0208FEA4:
            uc.reg_write(UC_ARM_REG_R0, r0 // r1)
            uc.reg_write(UC_ARM_REG_R1, r0 % r1)
        elif address in [0x02058EB0, 0x02011220]:
            pass  # Held/exclusive effect context preparation.
        elif address == 0x02058F04:
            assert r1 == 0x38
            uc.reg_write(UC_ARM_REG_R0, int(state['aura']))
        elif address == 0x02052A04:
            uc.reg_write(UC_ARM_REG_R0, 1)  # Ability ID for exclusive context.
        elif address == 0x02011394:
            uc.reg_write(UC_ARM_REG_R0, state['exclusive'])
        elif address == 0x020585B4:
            uc.mem_write(r0, b'Pokemon\0')
        elif address == 0x02089694:
            # strcpy in the actual shared LV/HP panel setter.
            text = bytes(uc.mem_read(r1, 16)).split(b'\0', 1)[0] + b'\0'
            uc.mem_write(r0, text)
        else:
            return
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    u.hook_add(UC_HOOK_CODE, stub)
    cases = 0
    for species in [1, 388, 548, 601]:
        pidx = struct.unpack_from('<H', primary, species * 2)[0]
        for level in [1, 50, 100]:
            for hp_v in [0, 1, 255]:
                for spe_v in [0, 255]:
                    for exclusive, aura in [(0, False), (5, False), (15, True), (255, True)]:
                        for current_override in [0, 1]:
                            state.update(exclusive=exclusive, aura=aura, stopped=False, calc_calls=[])
                            u.mem_write(team, bytes(0x80))
                            u.mem_write(panel, bytes(4 * 0x5C))
                            u.mem_write(status, bytes(0x200))
                            u.mem_write(sp, bytes(0x400))
                            u.mem_write(team, bytes([3, 0, level]))
                            u.mem_write(team + 0xC, struct.pack('<HH', species, 77))
                            u.mem_write(team + 0x10, bytes([hp_v, spe_v]))
                            before = bytes(u.mem_read(team, 0x80))
                            u.mem_write(0x022DB3B0, bytes([current_override]))
                            u.mem_write(0x02324C60, struct.pack('<I', status))
                            u.mem_write(status + 0x194, struct.pack('<h', 123))
                            saved = [0x12340000 + i for i in range(4)]
                            for reg, value in zip([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3], saved):
                                u.reg_write(reg, value)
                            u.reg_write(UC_ARM_REG_CPSR, 0x1F)
                            u.reg_write(UC_ARM_REG_R6, 1)  # Physical panel slot != roster slot.
                            u.reg_write(UC_ARM_REG_R7, 2)
                            u.reg_write(UC_ARM_REG_R8, team)
                            u.reg_write(UC_ARM_REG_R10, panel)
                            u.reg_write(UC_ARM_REG_SP, sp)
                            u.reg_write(UC_ARM_REG_LR, 0x021F0000)
                            u.emu_start(0x022DC580, 0, count=10000)
                            assert state['stopped']
                            assert u.reg_read(UC_ARM_REG_SP) == sp
                            assert u.reg_read(UC_ARM_REG_R8) == team
                            assert bytes(u.mem_read(team, 0x80)) == before
                            hp = calc_stat_from_tables(pidx, level, 0, hp_v, bases, rates)
                            max_hp = calc_stat_from_tables(pidx, level, 0, hp_v + exclusive, bases, rates)
                            max_hp = min(32767, max_hp + (hp // 8 if aura else 0))
                            row = panel + 0x5C
                            assert struct.unpack('<hhh', u.mem_read(row + 0x48, 6)) == (level, 77 if current_override else max_hp, max_hp)
                            assert struct.unpack('<h', u.mem_read(row + 0x42, 2))[0] == species
                            assert struct.unpack('<h', u.mem_read(row + 0x52, 2))[0] == 123
                            assert bytes(u.mem_read(row + 1, 8)) == b'Pokemon\0'
                            assert state['calc_calls'] == [(species, level, 0, hp_v), (species, level, 0, hp_v + exclusive)]
                            cases += 1
    print(json.dumps({'town_panel_cases': cases, 'HP_Spe_separated': True,
                      'exclusive_and_aura_HP': 'passed', 'current_HP_override': 'passed',
                      'saved_doping_unchanged': True, 'ROM_written': False}, indent=2))


if __name__ == '__main__':
    main()
