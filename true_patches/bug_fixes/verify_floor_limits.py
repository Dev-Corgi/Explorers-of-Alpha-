"""Exercise Alpha's real stairs exit hook with ROM-backed inter_d reads."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))

from ndspy.rom import NintendoDSRom
from skytemple_files.data.inter_d.model import InterD
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_PC,
    UC_ARM_REG_LR, UC_ARM_REG_SP,
)

SOURCE = ROOT / "PatchTesting/Explorers of Alpha/Explorers of Alpha.nds"
FLAGS = {45, 56, 57}


def shortened(entry) -> bool:
    return entry.ent_type.value == 2 and entry.game_var_id == 78 and entry.param1 in FLAGS


def check_floor_limits(fixed: NintendoDSRom) -> None:
    from verify import recovery_machine

    original = NintendoDSRom(SOURCE.read_bytes())
    before = InterD(original.getFileByName("UTILITY/inter_d.bin"))
    after = InterD(fixed.getFileByName("UTILITY/inter_d.bin"))
    assert len(before.list_dungeons) == len(after.list_dungeons)
    affected = []
    removed = 0
    for dungeon, (old, new) in enumerate(zip(before.list_dungeons, after.list_dungeons)):
        retained = [e.to_bytes() for e in old if not shortened(e)]
        assert [e.to_bytes() for e in new] == retained, dungeon
        if len(old) != len(new):
            affected.append(dungeon)
            removed += len(old) - len(new)
    assert len(affected) == 33 and removed == 62
    # All unrelated story/item flags and unconditional exits retain their bytes.
    assert fixed.getFileByName("UTILITY/fforbid.bin") == original.getFileByName("UTILITY/fforbid.bin")

    uc = recovery_machine(fixed)
    case = {"cursor": 0, "flags": {}, "data": b"", "stop": None}

    def service(machine, address, _size, _data):
        if address in (0x022E00AC, 0x022E00C8):
            case["stop"] = address
            machine.emu_stop()
            return
        if address == 0x0204B678:
            assert machine.reg_read(UC_ARM_REG_R1) == 78
            value = case["flags"].get(machine.reg_read(UC_ARM_REG_R2), 0)
        elif address == 0x02008210:  # FileOpen
            case["cursor"] = 0
            value = 0
        elif address == 0x020082A8:  # FileSeek: SET=0, CUR=1
            offset = machine.reg_read(UC_ARM_REG_R1)
            mode = machine.reg_read(UC_ARM_REG_R2)
            assert mode in (0, 1)
            case["cursor"] = offset + (case["cursor"] if mode == 1 else 0)
            value = 0
        elif address == 0x02008254:  # FileRead
            size = machine.reg_read(UC_ARM_REG_R2)
            start = case["cursor"]
            data = case["data"][start:start + size]
            assert len(data) == size
            machine.mem_write(machine.reg_read(UC_ARM_REG_R1), bytes(data))
            case["cursor"] += size
            value = size
        elif address in (0x02008168, 0x02008194, 0x02008204, 0x020082C4):
            value = 0
        else:
            return
        machine.reg_write(UC_ARM_REG_R0, value)
        machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, service)
    arm = original.loadArm9().save(compress=False)
    count = 0

    def stairs(dungeon, floor, flags, data):
        total = arm[0x9E3A0 + dungeon * 4]
        uc.mem_write(0x02100748, bytes([dungeon, floor]))
        uc.mem_write(0x0212CAF4, bytes([total + 1]))
        uc.reg_write(UC_ARM_REG_SP, 0x0273F000)
        case.update(flags=flags, data=data, stop=None)
        uc.emu_start(0x022E008C, 0, count=20000)
        assert case["stop"] is not None
        return case["stop"] == 0x022E00AC

    # Reproduce the old 20/22/30F exits, including the reported Array case.
    old_data = original.getFileByName("UTILITY/inter_d.bin")
    # inter_d matches the NEXT floor (current floor + 1), including boss floors.
    for flags, floor in (({56: 1}, 19), ({45: 1, 58: 1}, 21), ({57: 1}, 29)):
        assert stairs(78, floor, flags, old_data)
    data = fixed.getFileByName("UTILITY/inter_d.bin")
    for dungeon in affected:
        total = arm[0x9E3A0 + dungeon * 4]
        floors = {f for e in before.list_dungeons[dungeon] if shortened(e)
                  for f in (int(e.floor) - 1, int(e.floor))}
        floors.update((total - 1, total))
        if dungeon == 78:
            floors.add(33)
        hardcore = {floor: stairs(dungeon, floor, {59: 1}, old_data)
                    for floor in floors}
        for difficulty in (56, 57, 58, 59):
            for array in (0, 1):
                flags = {difficulty: 1, 45: array}
                for floor in sorted(floors):
                    assert stairs(dungeon, floor, flags, data) == hardcore[floor], (dungeon, floor, flags)
                    count += 1
    print(f"Dungeon exits: {count} ARM stairs cases; 62 exits removed in 33 dungeon IDs")


if __name__ == "__main__":
    from true_patches.bug_fixes.floor_limits import apply_floor_limits
    from patch_engine.manifest import load_module_manifest

    rom = NintendoDSRom(SOURCE.read_bytes())
    settings = load_module_manifest(Path(__file__).resolve().parent)["dungeon_floor_limits"]
    apply_floor_limits(rom, settings)
    first = rom.getFileByName(settings["path"])
    assert apply_floor_limits(rom, settings)["entries"] == 0
    assert rom.getFileByName(settings["path"]) == first
    check_floor_limits(rom)
