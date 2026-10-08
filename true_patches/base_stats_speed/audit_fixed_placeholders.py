"""Reproduce the base-ROM fixed-room survey; never modifies the ROM.

Run from the repository root with .venv/Scripts/python.exe -B.
Requires Unicorn from tools/.korean_jit_test_deps (same as Korean checks).
"""
from pathlib import Path
import hashlib
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from skytemple_files.common.util import get_ppmdu_config_for_rom, get_binary_from_rom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.hardcoded.fixed_floor import HardcodedFixedFloorTables
from skytemple_files.dungeon_data.fixed_bin.model import EntityRule
from true_patches.base_stats_speed.patch_se_calcstat_hp import _load_names
from true_patches.balance_change.patch_m_level_exp import _load_entry

ROOMS = list(range(200, 222)) + [224] + list(range(240, 249)) + [250, 251, 255]
SOURCE = ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'
REPORT = Path(__file__).with_name('fixed_room_placeholder_audit.md')


def main():
    rom = NintendoDSRom.fromFile(str(SOURCE))
    config = get_ppmdu_config_for_rom(rom)
    overlays = loadOverlayTable(rom.arm9OverlayTable, lambda i, f: rom.files[f])
    names = _load_names(rom, config)
    md = FileType.MD.deserialize(rom.getFileByName('BALANCE/monster.md'))
    pack = FileType.BIN_PACK.deserialize(rom.getFileByName('BALANCE/m_level.bin'))
    floors = FileType.FIXED_BIN.deserialize(rom.getFileByName('BALANCE/fixed.bin'))
    ov29 = get_binary_from_rom(rom, config.bin_sections.overlay29)
    ov10 = get_binary_from_rom(rom, config.bin_sections.overlay10)
    spawns = HardcodedFixedFloorTables.get_monster_spawn_list(ov29, config)
    entities = HardcodedFixedFloorTables.get_entity_spawn_table(ov29, config)
    table = HardcodedFixedFloorTables.get_monster_spawn_stats_table(ov10, config)
    assert (int(table[30].level), int(table[30].hp)) == (22, 90)
    # Historical fixed-level / fixed-HP caves are not installed here.
    assert struct.unpack_from('<I', ov29, 0x022FBE78 - 0x022DC240)[0] == 0xE3A0000C
    assert struct.unpack_from('<I', ov29, 0x022FBEA0 - 0x022DC240)[0] == 0xE1D350F2
    growth = {}

    def entries(species):
        # GetLevelUpEntry (0205379C): remainder by 600, then pack index - 1.
        idx = species % 600 - 1
        if idx not in growth:
            growth[idx] = _load_entry(pack, idx)
        return growth[idx]

    def stats(species, level):
        ent = md.entries[species]
        fields = ['hp', 'atk', 'sp_atk', 'def', 'sp_def']
        increments = ['hp_growth', 'attack_growth', 'special_attack_growth', 'defense_growth', 'special_defense_growth']
        result = []
        for field, inc in zip(fields, increments):
            value = int(getattr(ent, 'base_' + field)) + sum(int(getattr(entries(species)[i], inc)) for i in range(1, level))
            result.append(value if field == 'hp' else min(255, value))
        return result

    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_write(0x02000000, bytes(rom.arm9))
    for index in (10, 29, 36):
        ov = overlays[index]
        uc.mem_write(ov.ramAddress, bytes(ov.data))
    uc.mem_write(0x02353538, struct.pack('<I', 0x02100000))
    state = {'rng': 0}

    def service(u, address, size, data):
        r0 = u.reg_read(UC_ARM_REG_R0)
        r1 = u.reg_read(UC_ARM_REG_R1)
        r2 = u.reg_read(UC_ARM_REG_R2)
        if address == 0x022EAA98:
            assert data['rng'] < r0
            u.reg_write(UC_ARM_REG_R0, data['rng'])
        elif address == 0x0204B678:
            u.reg_write(UC_ARM_REG_R0, 0)  # No optional script-level reduction.
        elif address in (0x02052934, 0x020529C4, 0x020529E4):
            ent = md.entries[r0]
            field = 'base_hp' if address == 0x02052934 else ('base_atk' if r1 == 0 else 'base_sp_atk') if address == 0x020529C4 else ('base_def' if r1 == 0 else 'base_sp_def')
            u.reg_write(UC_ARM_REG_R0, int(getattr(ent, field)))
        elif address == 0x0205379C:
            e = entries(r1)[r2 - 1]
            u.mem_write(r0, struct.pack('<IHBBBBH', int(e.experience_required), int(e.hp_growth), int(e.attack_growth), int(e.special_attack_growth), int(e.defense_growth), int(e.special_defense_growth), 0))
        elif address not in (0x02058EB0, 0x023021F0, 0x022FB83C):
            return
        u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, service, state)

    def run(address, r0, r1=0, r2=0):
        uc.reg_write(UC_ARM_REG_R0, r0)
        uc.reg_write(UC_ARM_REG_R1, r1)
        uc.reg_write(UC_ARM_REG_R2, r2)
        uc.reg_write(UC_ARM_REG_SP, 0x021FF000)
        uc.reg_write(UC_ARM_REG_LR, 0x021F0000)
        uc.emu_start(address, 0x021F0000, count=20000)
        assert uc.reg_read(UC_ARM_REG_PC) == 0x021F0000

    rows = []
    for room in ROOMS:
        cells = [spawns[int(entities[int(a.entity_rule_id)].monster_id)] for a in floors.fixed_floors[room].actions if isinstance(a, EntityRule)]
        count = sum(int(s.md_idx) == 4 and int(s.stats_entry) == 30 for s in cells)
        assert count > 0
        bound = 10 if room in (240, 241) else 4 if room in (242, 243) else 3 if room in (244, 245, 246) else 5 if room in (247, 248) else 1
        choices = {}
        for rng in range(bound):
            state['rng'] = rng
            uc.mem_write(0x021040DA, bytes([room]))
            uc.mem_write(0x02100748, b'\x01')  # Ordinary dungeon calculation path.
            uc.mem_write(0x02110000, b'\x04\x00' + bytes(30))
            run(0x023DA080, 0x02110000)
            species = struct.unpack('<H', uc.mem_read(0x02110000, 2))[0]
            choices.setdefault(species, []).append(rng)
        for species, rngs in choices.items():
            if species >= len(md.entries):
                rows.append(f'| {room} | {count} | **유효하지 않음: {species} (0x{species:04X})** | — | — | — | — | — | — | 교체 분기 없음 |')
                continue
            level = int(table[30].level)
            assert int(md.entries[species].base_movement_speed) == 1
            expected = stats(species, level)
            expected[0] += expected[0] // 4
            uc.mem_write(0x021200B4, struct.pack('<I', 0x02121000))
            uc.mem_write(0x02121000, bytes(0x200))
            uc.mem_write(0x02121002, struct.pack('<H', species))
            uc.mem_write(0x0212100A, bytes([level]))
            uc.mem_write(0x02121012, struct.pack('<H', 100))
            run(0x022FBE58, 0x02120000, 30, 0)
            actual = [struct.unpack('<H', uc.mem_read(0x02121012, 2))[0]] + list(uc.mem_read(0x0212101A, 4))
            assert actual == expected, (room, species, actual, expected)
            assert struct.unpack('<H', uc.mem_read(0x02121010, 2))[0] == expected[0]
            probability = f'{len(rngs)}/{bound}' if bound > 1 else '고정'
            rows.append(f'| {room} | {count} | {names[species]} ({species}) | {level} | {actual[0]} | {actual[1]} | {actual[3]} | {actual[2]} | {actual[4]} | {probability} |')

    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    intro = f'''# 기준 롬 Fixed Room Charmander 대체 조사

조사일: 2026-10-08. 입력: `PatchTesting/Explorers of Alpha/Explorers of Alpha.nds`.
SHA-256: `{digest}`.
풀스택 롬이나 base_stats_speed 적용 결과가 아닌 **기준 롬 자체**를 조사했다.

## 핵심 결과

- 공통 배치 데이터는 spawn 62 / MD 4 Charmander / stats_entry 30 / Strong Enemy(6)이다.
- row 30의 파일상 값은 **레벨 22, HP 90, 공격·방어·특수공격·특수방어 각각 35**다. 그러나 실제 생성 시 HP와 네 전투 능력치를 대체 종족의 성장 데이터로 다시 계산한다. 이 숫자를 실제 적 능력치로 사용하면 틀린다.
- 현재 연결된 생성 경로는 row 30의 레벨 **22**를 읽는다. 방별 고정 레벨 루틴은 ROM 안에 남아 있지만 해당 호출 지점은 연결되어 있지 않다. 팀 최고 레벨로 바꾸는 것은 현재 base_stats_speed의 추가 처리이며, 아래 기준 롬 값과 구분해야 한다.
- 240–248은 자리마다 난수를 다시 뽑는 종족 풀이다. 방 전체가 반드시 한 종족으로 통일되는 구조가 아니다.
- **255는 종족 교체 분기가 없다.** 해당 생성 루틴을 그대로 실행하면 MD 42216(0xA4E8)을 써 버린다. 유효한 포켓몬 ID가 아니므로 정상적인 대체 종족/능력치로 기재할 수 없다. 이는 분리 실행에서 확인한 값이며 실제 게임에서의 최종 증상까지 재현한 것은 아니다.

## 방별 생성 시 능력치

일반 던전 계산 경로, 초기 row 30 레벨 22 기준. HP는 현재/최대 HP에 함께 쓰이는 값이다.
공격·방어 열은 종족 기본치와 레벨업 성장의 합으로, 난이도·버프·장비 등 전투 중 추가 효과를 포함하지 않는다.
`자리 수`는 해당 방의 Charmander placeholder 수다. 각 MD 번호는 게임 내부 번호이며 전국도감 번호가 아니다.
선택 비율은 `DungeonRandInt`의 각 반환값에 대응하는 분기 수다.
기준 롬에는 base_stats_speed가 추가하는 별도 Speed 능력치가 없고, 아래 정상 대체 종족의 `base_movement_speed`는 모두 1이다.

| Fixed Room | 자리 수 | 대체 포켓몬 (MD) | 레벨 | HP | 공격 | 방어 | 특수공격 | 특수방어 | 선택 |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
'''
    tail = '''
## 계산과 검증 근거

1. `BALANCE/fixed.bin`의 EntityRule → overlay29 EntitySpawn → MonsterSpawn을 따라 지정한 35개 방의 실제 placeholder 수를 셌다.
2. `GenerateFixedRoom`의 0x0234389C에서 호출하는 overlay36 0x023DA080을 ARM으로 실행했다. 0x023DA20C부터 Fixed Room ID(dungeon+0x40DA)로 종족을 고른다. 랜덤 방은 유효 난수 값을 모두 열거했다.
3. 0x023437F0에서 row 30의 레벨을 읽어 SpawnMonster에 넘긴다. `ApplyFixedRoomStats`(0x022FBE58)가 0x022FBE7C에서 0x023D8480을 호출한다. entry 30이고 방 ID가 200 이상이면 대체 종족/row 레벨로 HP·공격·특수공격·방어·특수방어를 계산해 row 30에 써서 적용한다.
4. HP = `종족 base_hp + 레벨 2부터 해당 레벨까지 hp_growth 합`, 그 후 `HP + floor(HP/4)`. 공격/방어 계열도 종족 기본치 + 해당 성장 합이며 255 상한을 적용한다. 성장 팩 인덱스는 **(MD % 600) - 1**, 성장 배열 인덱스는 **level - 1**이다. 팩 인덱스를 MD 그대로 사용하면 한 종족 밀린 잘못된 값이 나온다.
5. 보고서의 정상 종족 행마다 실제 `ApplyFixedRoomStats` ARM 경로를 실행하고 위 데이터 계산 결과와 현재/최대 HP 및 네 능력치가 일치하는지 assert했다. 파일 접근·성장 데이터 읽기·메시지/플래그 서비스는 스텁이며 게임 전체를 실행한 테스트는 아니다.

### ROM 안의 미사용 코드와 조건부 경로

- 0x023D7E80: 방별 고정 레벨 코드를 담고 있다. 하지만 실제 0x022FBE78은 `mov r0, #12`이며 이 루틴으로 분기하지 않는다. 이 코드의 45/12/22/35 등의 값을 현재 적용 레벨로 오인하면 안 된다.
- 0x023D86B0: 방별 고정 HP(200=250, 205=130, 207=140, 208=160, 209=150, 224/250=500 등) 코드가 남아 있다. 현재 0x022FBEA0은 `ldrsh r5, [r3,#2]`이며 이 루틴을 호출하지 않는다. 이 값 역시 실제 생성 HP로 사용하지 않았다.
- 일반 성장 함수에는 Dungeon ID 100일 때 다른 계산표를 쓰는 분기가 있고, HP 함수에는 Dungeon ID 165 분기도 있다(0x023B82A8, 0x023B833C, 0x023B8398). 따라서 위 수치를 모든 던전 문맥에 무조건 적용하는 것은 잘못이다. 위 표는 일반 성장 경로의 생성 직후 수치이며, 특정 던전/난이도에서의 이후 보정까지 조사한 표는 아니다.
- optional script 변수(그룹 0x4E, 인덱스 0x38)가 1이면 0x023DA424–0x023DA434에서 SpawnMonster 입력 레벨을 floor(3L/4)로 바꾼다. row 30은 바뀌지 않아 이후 HP/네 능력치 계산은 여전히 row 레벨 22를 사용한다. 표의 레벨 22는 이 옵션이 꺼진 기본 경로다.
- row 30은 런타임에 공유되지만 HP/네 능력치는 각 생성마다 재계산하므로 이전 종족의 수치를 그대로 쓰지 않는다.

### 255의 별도 Genesect

255에는 placeholder 9자리 외에 **spawn 105 / MD 548 Genesect / stats_entry 84 / Strong Enemy(6)** 한 자리가 별도로 있다. 이는 Charmander 교체 결과가 아니다.
'''
    s = table[84]
    tail += f'이 별도 자리의 표 값: 레벨 {int(s.level)}, HP {int(s.hp)}, 공격 {int(s.attack)}, 방어 {int(s.defense)}, 특수공격 {int(s.special_attack)}, 특수방어 {int(s.special_defense)}. entry 30 전용 재계산 분기를 타지 않는다.\n'
    tail += '\n## 재현\n\n```powershell\n.venv\\Scripts\\python.exe -B true_patches\\base_stats_speed\\audit_fixed_placeholders.py\n```\n\n기준 롬은 읽기만 하며 이 Markdown만 갱신한다. 패치 로직과 빌드 결과를 변경하지 않는다.\n'
    REPORT.write_text(intro + '\n'.join(rows) + '\n' + tail, encoding='utf-8')
    print(f'Validated {len(ROOMS)} rooms, {len(rows)} result rows: {REPORT}')


if __name__ == '__main__':
    main()
