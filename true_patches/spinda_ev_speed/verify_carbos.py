"""Assemble and execute Carbos/Wonder Gummi; inspect data without writing a ROM."""
from pathlib import Path
import gzip
import json
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from verify_save import Machine, CAVE, ENTITY, INFO, STOP, TEAM
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10
from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.data.data_cd.handler import DataCDHandler
from patch_engine.spinda_save_runtime import build_runtime
from patch_engine.apply_spinda_ev import _build_generated_inc, patch_strings
from patch_engine.manifest import load_yaml
from patch_engine.korean_codec import translation_issues
from true_patches.spinda_ev_speed.carbos import CARBOS, VITAMINS, ALL_VITAMINS, install, redistribute, verify


def weights(items, categories, category=2):
    last = 0
    result = {}
    for item, threshold in sorted(items.items()):
        if categories[item] != category or not threshold or threshold > 10000:
            continue
        result[item] = threshold - last
        last = threshold
    return result


class ItemsMachine(Machine):
    def __init__(self, *args):
        self.logs = []
        super().__init__(*args)

    def api(self, u, address, size, context):
        if address == 0x0234B350:
            from unicorn.arm_const import UC_ARM_REG_R2
            self.logs.append(u.reg_read(UC_ARM_REG_R2))
            self.ret()
        elif address in (0x022E3AB4, 0x022E49B4):
            self.ret()
        elif address in (0x0231CB14, 0x0231D0C4):
            u.reg_write(UC_ARM_REG_PC, STOP)
        elif address in (0x02317F50, 0x02317FE4, 0x02318078, 0x0231810C):
            # Vanilla non-Speed vitamin effects; the outer gummi transaction
            # must collect these alongside the actual compiled Speed routine.
            stat = (address - 0x02317F50) // 0x94
            old = u.mem_read(INFO + 26 + stat, 1)[0]
            u.mem_write(INFO + 26 + stat, bytes([min(255, old + 3)]))
            self.ret()
        else:
            super().api(u, address, size, context)


def main():
    module = Path(__file__).parent
    rom = NintendoDSRom.fromFile(str(ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'))
    original = FileType.MAPPA_BIN.deserialize(rom.getFileByName('BALANCE/mappa_s.bin'))
    p = FileType.ITEM_P.deserialize(rom.getFileByName('BALANCE/item_p.bin'))
    categories = [int(e.category) for e in p.item_list]
    assert not p.item_list[CARBOS].is_valid
    example = {99: 8000, 100: 8500, 101: 9000, 102: 9500, 108: 10000}
    result, changed = redistribute(example, categories)
    updated_categories = categories[:]
    updated_categories[CARBOS] = 2
    assert changed and all(weights(result, updated_categories)[i] == 400 for i in ALL_VITAMINS)
    assert redistribute({99: 10000}, categories) == ({99: 10000}, False)

    with tempfile.TemporaryDirectory(prefix='carbos_verify_') as tmp:
        work = Path(tmp)
        runtime, labels = build_runtime(module, work, CAVE, 0x023E0000)
        code = runtime.read_bytes()
        shutil.copytree(module / 'asm', work / 'asm')
        shutil.copy2(runtime, work / 'asm/save_v1.bin')
        generated = _build_generated_inc(module_id='spinda_ev_speed', arm9_code=0x02094624,
            reset_cave=0x020A3550, team_submenu_table=0x0238E380, dungeon_stat_cave=CAVE)
        generated += labels + '.definelabel SpindaEv_PriorDungeonFree, 0x022DEAB4\n'
        generated += '.definelabel SpindaEv_PriorMoveHitRank, 0x02323F98\n'
        (work / 'asm/common/generated.inc').write_text(generated, encoding='utf-8')
        (work / 'asm/generated.inc').write_text(generated, encoding='utf-8')
        (work / 'asm/arm9.bin').write_bytes(rom.arm9)
        for n in (11, 19, 29):
            (work / f'asm/overlay_{n:04d}.bin').write_bytes(rom.loadArm9Overlays()[n].data)
        assembled_result = subprocess.run([str(ROOT / 'tools/armips.exe'), 'main.asm', '-sym2', 'symbols.txt'],
                       cwd=work / 'asm', capture_output=True, text=True)
        if assembled_result.returncode:
            raise RuntimeError(assembled_result.stdout + assembled_result.stderr)
        symbols = {}
        for line in (work / 'asm/symbols.txt').read_text().splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    symbols[parts[1]] = int(parts[0], 16)
                except ValueError:
                    pass
        assembled = (work / 'asm/arm9.bin').read_bytes()

    m = ItemsMachine(rom, code, labels)
    m.u.mem_write(0x02000000, assembled)
    m.u.mem_write(0x020B0A48, struct.pack('<I', TEAM))
    speed = m.labels['EvSave_Speed']
    counts = install(rom, speed)
    verify(rom)
    assert counts == {'BALANCE': 261, 'UTILITY': 261}, counts
    patched = FileType.MAPPA_BIN.deserialize(rom.getFileByName('BALANCE/mappa_s.bin'))
    for before_group, after_group in zip(original.floor_lists, patched.floor_lists):
        for before, after in zip(before_group, after_group):
            assert before.floor_items.categories == after.floor_items.categories
            old = weights(before.floor_items.items, categories)
            new = weights(after.floor_items.items, updated_categories)
            if all(old.get(i, 0) > 0 for i in VITAMINS):
                assert sum(old[i] for i in VITAMINS) == sum(new[i] for i in ALL_VITAMINS)
                assert max(new[i] for i in ALL_VITAMINS) - min(new[i] for i in ALL_VITAMINS) <= 1
                assert {i: v for i, v in old.items() if i not in VITAMINS} == {
                    i: v for i, v in new.items() if i not in ALL_VITAMINS}
            else:
                assert old == new
            # Preserve every other category's thresholds except the disabled TM.
            assert {i: v for i, v in before.floor_items.items.items() if categories[i] != 2 and i != CARBOS} == {
                i: v for i, v in after.floor_items.items.items() if updated_categories[i] != 2}
    assert install(rom, speed) == counts  # safe module reapplication
    assert rom.getFileByName('BALANCE/mappa_s.bin') == rom.getFileByName('UTILITY/mappa_s.bin')

    cd = DataCDHandler.deserialize(rom.getFileByName('UTILITY/item_cd.bin'))
    effect = bytes(cd.get_effect_code(cd.get_item_effect_id(CARBOS)))
    m.u.mem_write(0x0231BE50, effect)
    m.labels['Carbos'] = 0x0231BE50
    for initial in (0, 252, 253, 254, 255):
        m.call('EvSave_NewGame')
        values = [5, 10, 11, 12, 13, initial]
        m.ground(10, values)
        m.member(0, 10)
        m.entity(0)
        m.u.reg_write(UC_ARM_REG_R7, ENTITY)
        m.u.reg_write(UC_ARM_REG_R8, ENTITY)
        m.call('Carbos')
        assert m.ground(10) == values[:5] + [min(255, initial + 3)]
        assert m.logs[-1] == (19613 if initial < 255 else 19614)
        m.call('EvSave_GroupEnd')
        assert m.ground(10) == values

    # Execute the assembled Wonder Gummi entry/exit, including real Speed and
    # HP additions, then verify all six gains are collected and removed.
    m.call('EvSave_NewGame')
    values = [5, 10, 11, 12, 13, 14]
    m.ground(10, values)
    m.member(0, 10)
    m.entity(0)
    m.u.mem_write(INFO + 16, struct.pack('<hhh', 100, 100, 0))
    m.labels.update(symbols)
    m.call('WonderGummi_Entry', ENTITY, ENTITY, 255)
    m.u.reg_write(UC_ARM_REG_R9, ENTITY)
    m.u.reg_write(UC_ARM_REG_R10, ENTITY)
    m.u.mem_write(STOP - 0x100, bytes(44) + struct.pack('<I', STOP))
    m.call('WonderGummi_Exit')
    assert m.ground(10) == [v + 3 for v in values], m.ground(10)
    m.call('EvSave_GroupEnd')
    assert m.ground(10) == values

    # An ordinary type gummi must not receive the Wonder-only additions.
    m.entity(0)
    m.call('WonderGummi_Entry', ENTITY, ENTITY, 0)
    m.u.mem_write(STOP - 0x100, bytes(44) + struct.pack('<I', STOP))
    m.call('WonderGummi_Exit')
    assert m.ground(10) == values
    m.call('EvSave_Speed', ENTITY, 0, 3)
    m.u.mem_write(INFO + 12, struct.pack('<h', -1))
    m.call('EvSave_Speed', ENTITY, ENTITY, 3)
    assert m.ground(10) == values

    manifest = load_yaml(module / 'manifest.yaml')
    patch_strings(rom, module, manifest)
    strings = FileType.STR.deserialize(rom.getFileByName('MESSAGE/text_e.str')).strings
    translations = json.loads(gzip.decompress((ROOT / 'true_patches/korean/data/translations.json.gz').read_bytes()))
    for index in (6967, 10898, 12298, 19612, 19613):
        entry = translations['text_e'][str(index)]
        assert entry['en'] == strings[index]
        assert not translation_issues(entry['en'], entry['ko'])
    assert translations['text_e']['6967']['ko'] == '[M:I3] 알칼로이드'
    print('PASS: full module assembly; Carbos ARM effect +3/cap/outing restore; Wonder Gummi all six +3; '
          '261 floor pools per bank, unchanged total/category/other item weights; reapply; Korean strings')


if __name__ == '__main__':
    main()
