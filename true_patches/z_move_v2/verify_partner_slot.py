"""Execute Z-Move selection/setup/restore with native move and action routines.

Reads the canonical input ROM; assembles only a temporary fixture, never a ROM.
UI append, move typing, base PP lookup and target validation use fixtures.
"""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/.korean_jit_test_deps'))
from patch_engine.apply_z_move import (
    _patch_zmove_category_calls, _encode_bl, GET_MOVE_CATEGORY, apply_z_move_module,
)
from patch_engine.manifest import load_yaml
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

MODULE = Path(__file__).resolve().parent
ENTRY, DUNGEON, ENTITY, STATUS = 0x023D0000, 0x02100000, 0x02130000, 0x02140000
GAUGE, RETURN, SP = 0x02150000, 0x02160000, 0x02702000


def compile_fixture(broken=False):
    source = (MODULE / 'asm/ZMoveOv29.asm').read_text(encoding='utf-8')
    selection = source.split('ZMove_TryAppendZMoveOption:\n', 1)[1].split('ZMove_Ov31MenuHook:', 1)[0]
    if broken:
        selection = selection.replace('ldr r1, [r6, #0xB4]\n\tstr r1, [r0]', 'str r7, [r0]')
    runtime = source.split('ZMove_TryRestoreSlotForEntity:\n', 1)[1].split('; r0 = string id', 1)[0]
    gauge = source.split('ZMove_GetZGauge:\n', 1)[1].split('; r0 = amount', 1)[0]
    load = source.split('ZMove_LoadEntityStatus:\n', 1)[1].split('; When tm_read', 1)[0]
    data = source.split('ZMoveSelectedEntity:\n', 1)[1].split('; Z gauge lives', 1)[0]
    category = source.split('ZMove_GetMoveCategoryHook:\n', 1)[1].split('; DungeonFree entry:', 1)[0]
    text = f'''.nds
.arm
.include "offsetsUS.asm"
ZGauge equ 0x{GAUGE:X}
ZMOVE_DEBUG_FORCE_TYPE equ 0
.create "fixture.bin", 0x{ENTRY:X}
ZMove_GetMoveCategoryHook:
{category}
ZMove_TryAppendZMoveOption:
{selection}
ZMove_TryRestoreSlotForEntity:
{runtime}
ZMove_GetZGauge:
{gauge}
ZMove_LoadEntityStatus:
{load}
PriorGetRoomChargeState:
    mov r0, #0
    bx lr
.pool
ZMoveSelectedEntity:
{data}
.close
'''
    with tempfile.TemporaryDirectory(prefix='z_partner_slot_') as d:
        work = Path(d)
        (work / 'generated.inc').write_text('', encoding='utf-8')
        (work / 'offsetsUS.asm').write_text((MODULE / 'asm/common/offsetsUS.asm').read_text(encoding='utf-8'), encoding='utf-8')
        (work / 'fixture.asm').write_text(text, encoding='utf-8')
        subprocess.run([str(ROOT / 'tools/armips.exe'), '-sym', 'fixture.sym', 'fixture.asm'], cwd=work, check=True)
        symbols = {}
        for line in (work / 'fixture.sym').read_text().splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    symbols[parts[1].lower()] = int(parts[0], 16)
                except ValueError:
                    pass
        return (work / 'fixture.bin').read_bytes(), symbols


def word(uc, address, value):
    uc.mem_write(address, struct.pack('<I', value))


def readword(uc, address):
    return struct.unpack('<I', uc.mem_read(address, 4))[0]


def call(uc, address, r0=0):
    uc.reg_write(UC_ARM_REG_R0, r0)
    uc.reg_write(UC_ARM_REG_SP, SP)
    uc.reg_write(UC_ARM_REG_LR, RETURN)
    uc.emu_start(address, RETURN, count=10000)
    assert uc.reg_read(UC_ARM_REG_PC) == RETURN, hex(uc.reg_read(UC_ARM_REG_PC))
    assert uc.reg_read(UC_ARM_REG_SP) == SP
    return uc.reg_read(UC_ARM_REG_R0)


def run_case(rom, overlays, fixture, symbols, selected, move_slot, gate, valid, broken=False, base_category=0):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_map(0x02700000, 0x4000)
    uc.mem_write(0x02000000, bytes(rom.arm9))
    dungeon_code = bytearray(overlays[29].data)
    category_entry = symbols['zmove_getmovecategoryhook']
    category_sites = _patch_zmove_category_calls(dungeon_code, overlays[29].ramAddress, category_entry)
    assert len(category_sites) == 22
    # Re-apply must find the previous calls even when the cave moves.
    relocated = bytearray(dungeon_code)
    assert _patch_zmove_category_calls(relocated, overlays[29].ramAddress, category_entry + 4, category_entry) == category_sites
    assert all(read == _encode_bl(site, category_entry + 4) for site in category_sites
               for read in [struct.unpack_from('<I', relocated, site - overlays[29].ramAddress)[0]])
    uc.mem_write(overlays[29].ramAddress, bytes(dungeon_code))
    uc.mem_write(ENTRY, fixture)
    word(uc, 0x02353538, DUNGEON)
    originals = []
    for slot in range(4):
        entity, status = ENTITY + slot * 0xB8, STATUS + slot * 0x400
        word(uc, DUNGEON + 0x12B28 + slot * 4, entity)
        word(uc, entity, 1)
        word(uc, entity + 0xB4, status)
        moves = b''.join(struct.pack('<HHHBB', 1, 0x100 + slot * 4 + m, 100 + slot * 4 + m, 10 + m, 20 + slot) for m in range(4))
        originals.append(moves)
        uc.mem_write(status + 0x124, moves)
    symbol = lambda name: symbols[name.lower()]
    word(uc, symbol('MoveMenuSelectedSlotPtr'), move_slot)
    word(uc, GAUGE, 100)
    captured = []
    typed = []
    categories = []
    category_resume = None

    def hook(machine, address, size, user_data):
        if address == category_resume:
            machine.emu_stop()
        elif address == 0x020A5F40:  # Native GetMoveCategory's balance-file reader.
            move = machine.reg_read(UC_ARM_REG_R0)
            assert machine.reg_read(UC_ARM_REG_R1) == 3
            assert machine.reg_read(UC_ARM_REG_R2) == 1
            categories.append(move)
            machine.reg_write(UC_ARM_REG_R0, 1 if move in (467, 559) else base_category)
            machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))
        elif address == 0x022EB81C:  # AddDungeonSubMenuOption: no UI needed.
            machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))
        elif address in (0x0204AF20, 0x022F0C3C, 0x0230227C, 0x02013A50):
            if address == 0x022F0C3C:
                captured.append((machine.reg_read(UC_ARM_REG_R0), machine.reg_read(UC_ARM_REG_R1)))
            if address == 0x0230227C:
                typed.append((machine.reg_read(UC_ARM_REG_R0), machine.reg_read(UC_ARM_REG_R1)))
            result = gate if address == 0x0204AF20 else valid if address == 0x022F0C3C else 10 if address == 0x02013A50 else 5
            machine.reg_write(UC_ARM_REG_R0, result)
            machine.reg_write(UC_ARM_REG_R1, 0xDEAD0001)
            machine.reg_write(UC_ARM_REG_R2, 0xDEAD0002)
            machine.reg_write(UC_ARM_REG_R3, 0xDEAD0003)
            machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.reg_write(UC_ARM_REG_R6, ENTITY + selected * 0xB8)
    uc.reg_write(UC_ARM_REG_R7, STATUS)  # Native menu keeps leader status here.
    call(uc, symbol('ZMove_TryAppendZMoveOption'))
    assert readword(uc, symbol('ZMoveSelectedEntity')) == ENTITY + selected * 0xB8
    assert readword(uc, symbol('ZMoveSelectedStatus')) == (STATUS if broken else STATUS + selected * 0x400)
    success = not gate or valid
    assert call(uc, symbol('ZMove_SetupAction')) == success
    owner = 0 if broken else selected
    assert categories == [100 + owner * 4 + move_slot]
    expected_category = 0 if base_category == 0 else 1
    assert uc.mem_read(symbol('ZMoveActiveCategory'), 1)[0] == expected_category
    assert typed == [(ENTITY + selected * 0xB8, STATUS + owner * 0x400 + 0x124 + move_slot * 8)]
    assert captured == ([(ENTITY + selected * 0xB8, STATUS + owner * 0x400 + 0x13C)] if gate else [])
    if success:
        # Reproduce the old all-special lookup independently of the new wrapper.
        assert call(uc, GET_MOVE_CATEGORY, 559) == 1
        # The native CalcDamage stat selector must choose Atk/Def (0) or SpA/SpD (1).
        assert call(uc, 0x0231EA18, 559) == expected_category
        assert call(uc, symbol('ZMove_GetMoveCategoryHook'), 559) == expected_category
        assert call(uc, symbol('ZMove_GetMoveCategoryHook'), 467) == 1
        assert call(uc, symbol('ZMove_GetMoveCategoryHook'), 100) == base_category
        # Replay every installed category call and check the resumed instruction.
        for site in category_sites:
            category_resume = site + 4
            uc.reg_write(UC_ARM_REG_R0, 559)
            preserved = (UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
                         UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7)
            before = tuple(uc.reg_read(register) for register in preserved)
            uc.reg_write(UC_ARM_REG_SP, SP)
            uc.emu_start(site, site + 4, count=1000)
            assert uc.reg_read(UC_ARM_REG_PC) == site + 4
            assert uc.reg_read(UC_ARM_REG_R0) == expected_category
            assert uc.reg_read(UC_ARM_REG_SP) == SP
            assert tuple(uc.reg_read(register) for register in preserved) == before
        category_resume = None
        assert struct.unpack('<H', uc.mem_read(STATUS + owner * 0x400 + 0x140, 2))[0] == 559
        # Native SetActionUseMovePlayer writes action 20, roster index, slot 3.
        assert struct.unpack('<H', uc.mem_read(STATUS + owner * 0x400 + 0x4A, 2))[0] == 20
        assert uc.mem_read(STATUS + owner * 0x400 + 0x4E, 1)[0] == selected
        assert uc.mem_read(STATUS + owner * 0x400 + 0x54, 1)[0] == 3
        for slot in range(4):
            if slot != owner:
                assert uc.mem_read(STATUS + slot * 0x400 + 0x4A, 12) == bytes(12)
        assert readword(uc, GAUGE) == 0
        if not broken and selected != 0:
            # Another member's validation cannot restore this member's pending slot.
            call(uc, symbol('ZMove_TryRestoreSlotForEntity'), ENTITY)
            assert uc.mem_read(STATUS + selected * 0x400 + 0x124, 32) != originals[selected]
        call(uc, symbol('ZMove_TryRestoreSlotForEntity'), ENTITY + selected * 0xB8)
        assert uc.mem_read(symbol('ZMovePendingFlag'), 1)[0] == 0
    else:
        assert readword(uc, GAUGE) == 100
    # A cancelled or completed Z-Move must use the shell's native category again.
    assert call(uc, symbol('ZMove_GetMoveCategoryHook'), 559) == 1
    if broken:
        assert uc.mem_read(STATUS + 0x124, 32) != originals[0]
        assert uc.mem_read(STATUS + selected * 0x400 + 0x13C, 8) == originals[0][24:]
    else:
        for slot, original in enumerate(originals):
            assert uc.mem_read(STATUS + slot * 0x400 + 0x124, 32) == original


def verify_module_assembly(rom):
    """Assemble the complete module in memory and check its relocated export/bounds."""
    overlays = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    before = bytes(overlays[36].data)
    category_code = bytes(rom.arm9[0x151C8:0x151DC])
    result = apply_z_move_module(
        module_id='z_move_v2', module_dir=MODULE, manifest=load_yaml(MODULE / 'manifest.yaml'),
        profile=load_yaml(ROOT / 'patch_engine/rom_profile_us.yaml'), rom=rom,
        armips=ROOT / 'tools/armips.exe', state=None, prior_hook_sites=set(), force_reapply=True,
    )
    after = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    cave = next(c for c in result.caves if c.overlay == 'ov36')
    start, end = cave.file_offset, cave.file_offset + cave.size
    code = bytes(after[36].data)
    padded_before = before.ljust(len(code), b'\0')
    assert code[:start] == padded_before[:start]
    assert code[end:] == padded_before[end:]
    target = int(result.data[0]['ZMove_GetMoveCategoryHook'], 16)
    assert struct.unpack_from('<I', code, target - after[36].ramAddress)[0] == 0xE92D4002
    for site in result.data[0]['category_call_sites']:
        site = int(site, 16)
        assert struct.unpack_from('<I', after[29].data, site - after[29].ramAddress)[0] == _encode_bl(site, target)
    assert bytes(rom.arm9[0x151C8:0x151DC]) == category_code
    print('PASS: full module assembled in memory; category export/calls and cave bounds verified; ARM9 category unchanged')


def main():
    rom = NintendoDSRom.fromFile(str(ROOT / 'PatchTesting/Explorers of Alpha/Explorers of Alpha.nds'))
    overlays = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    # Native menu establishes r7 from GetLeader, independent of selected r6.
    offset = 0x023854B8 - overlays[31].ramAddress
    leader_call = 0xEB000000 | (((0x022E9580 - (0x023854B8 + 8)) >> 2) & 0xFFFFFF)
    assert bytes(overlays[31].data[offset:offset + 8]) == struct.pack('<II', leader_call, 0xE59070B4)
    fixture, symbols = compile_fixture()
    count = 0
    for selected in range(4):
        for move_slot in range(4):
            for gate, valid in ((0, 0), (1, 1), (1, 0)):
                for category in (0, 1, 2):
                    run_case(rom, overlays, fixture, symbols, selected, move_slot, gate, valid, base_category=category)
                    count += 1
    fixture, symbols = compile_fixture(broken=True)
    run_case(rom, overlays, fixture, symbols, 1, 0, 0, 0, broken=True)
    print(f'PASS: {count} member/slot/category setup/restore cases; 22 category calls; old all-special and leader-slot behavior reproduced')
    verify_module_assembly(rom)


if __name__ == '__main__':
    main()
