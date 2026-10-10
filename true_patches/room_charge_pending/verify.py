"""Execute the secondary-effect gate and Alpha probability roll on ARM."""

import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))

from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

from patch_engine.apply_module import apply_module, verify_module_applied

MODULE = Path(__file__).resolve().parent
SOURCE = ROOT / "PatchTesting/Explorers of Alpha/Explorers of Alpha.nds"
ENTRY, BODY = 0x02324934, 0x02324938
ATTACKER, DEFENDER = 0x02120000, 0x02120200
MONSTER_A, MONSTER_D = 0x02121000, 0x02121400
STACK, RETURN = 0x0273F000, 0x0273E000


def check_gate(rom, cave):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_map(0x02700000, 0x40000)
    uc.mem_write(0x02000000, bytes(rom.arm9))
    overlays = rom.loadArm9Overlays()
    for index in (29, 36):
        overlay = overlays[index]
        uc.mem_write(overlay.ramAddress, bytes(overlay.data))
    uc.mem_write(ATTACKER, struct.pack("<I", 1))
    uc.mem_write(DEFENDER, struct.pack("<I", 1))
    uc.mem_write(ATTACKER + 0xB4, struct.pack("<I", MONSTER_A))
    uc.mem_write(DEFENDER + 0xB4, struct.pack("<I", MONSTER_D))
    uc.mem_write(MONSTER_D + 0x10, struct.pack("<H", 100))
    uc.mem_write(MONSTER_D + 0x162, b"\x01")
    case, delegated, rolls = {}, [], []

    def service(machine, address, _size, _data):
        if address == BODY and case["boundary"]:
            delegated.append(tuple(machine.reg_read(reg) for reg in
                                   (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                    UC_ARM_REG_R2, UC_ARM_REG_R3)))
            # The gate already replayed the original push before entering BODY.
            sp = machine.reg_read(UC_ARM_REG_SP)
            for reg, value in zip((UC_ARM_REG_R4, UC_ARM_REG_R5,
                                   UC_ARM_REG_R6, UC_ARM_REG_LR),
                                  struct.unpack("<4I", machine.mem_read(sp, 16))):
                machine.reg_write(reg, value)
            machine.reg_write(UC_ARM_REG_SP, sp + 16)
            value = case["outcome"]
        elif address == 0x022EC7E8:
            value = 0
        elif address == 0x02321438:
            value = int(machine.reg_read(UC_ARM_REG_R0) in (ATTACKER, DEFENDER))
        elif address == 0x02301D78:
            value = int(machine.reg_read(UC_ARM_REG_R1) == case["ability"]
                        and case["ability"] != 0)
        elif address == 0x022EAB50:
            rolls.append(machine.reg_read(UC_ARM_REG_R0))
            value = case["outcome"]
        elif address == 0x02322D64:
            value = 0  # No Shield Dust protection.
        else:
            return
        machine.reg_write(UC_ARM_REG_R0, value)
        machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, service)
    count = 0
    for boundary in (True, False):
        for state in (0, 1, 2):  # Idle, charging, releasing.
            for outcome in (0, 1):
                for ability in ((0,) if boundary else (0, 38, 162)):
                    case.update(boundary=boundary, outcome=outcome, ability=ability)
                    delegated.clear()
                    rolls.clear()
                    uc.mem_write(MONSTER_A + 0x173, bytes([state]))
                    uc.reg_write(UC_ARM_REG_SP, STACK)
                    uc.reg_write(UC_ARM_REG_LR, RETURN)
                    args = (ATTACKER, DEFENDER, 15, 0x12345678)
                    for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1,
                                           UC_ARM_REG_R2, UC_ARM_REG_R3), args):
                        uc.reg_write(reg, value)
                    saved = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                             UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                             UC_ARM_REG_R10, UC_ARM_REG_R11)
                    for index, reg in enumerate(saved):
                        uc.reg_write(reg, 0xABC000 + index)
                    uc.emu_start(ENTRY, RETURN, count=10000)
                    assert uc.reg_read(UC_ARM_REG_PC) == RETURN
                    assert uc.reg_read(UC_ARM_REG_SP) == STACK
                    assert [uc.reg_read(reg) for reg in saved] == [
                        0xABC000 + index for index in range(len(saved))]
                    expected = 0 if state == 1 or ability == 162 else outcome
                    assert uc.reg_read(UC_ARM_REG_R0) == expected, case
                    if boundary:
                        assert delegated == ([] if state == 1 else [args]), case
                    else:
                        expected_rolls = ([] if state == 1 or ability == 162
                                          else [30 if ability == 38 else 15])
                        assert rolls == expected_rolls, (case, rolls)
                    count += 1
    # Exported offsets used by tm_read and z_move must still point at functions.
    for offset, instruction in ((0x48, 0xE92D000E), (0xF4, 0xE59010B4),
                                (0x2B4, 0xE92D40F0)):
        assert bytes(uc.mem_read(cave.load_address + offset, 4)) == struct.pack(
            "<I", instruction)
    return count


def main():
    with tempfile.TemporaryDirectory(prefix="alpha_room_secondary_") as temp:
        output = Path(temp) / "test.nds"
        state = apply_module("room_charge_pending", SOURCE, output,
                             state_path=Path(temp) / "state.json")
        verify_module_applied(output, MODULE, state)
        cave = state.get_module("room_charge_pending").caves[0]
        count = check_gate(NintendoDSRom.fromFile(str(output)), cave)
        print(f"ARM secondary-effect checks: {count} cases passed")


if __name__ == "__main__":
    main()
