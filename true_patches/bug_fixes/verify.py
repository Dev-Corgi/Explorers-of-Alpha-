"""Apply only bug_fixes in temporary files and exercise recovery and abilities."""

from __future__ import annotations

import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1,
    UC_ARM_REG_R4, UC_ARM_REG_R7, UC_ARM_REG_R10, UC_ARM_REG_SP,
)

from patch_engine.apply_module import apply_module, verify_module_applied
from patch_engine.build_full_stack import FULL_STACK_MODULES
from patch_engine.manifest import load_module_manifest, load_yaml, load_rom_profile, resolve_symbol
from patch_engine.overlay_caves import get_rom_binary
from patch_engine.state import AppliedModule, BuildState, save_state
from patch_engine.hook_registry import assert_hooks_on_binary

MODULE = Path(__file__).resolve().parent
SOURCE = ROOT / "PatchTesting/Explorers of Alpha/Explorers of Alpha.nds"
ENTITY, MONSTER = 0x02120000, 0x02121000


def recovery_machine(rom: NintendoDSRom) -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_write(0x02000000, bytes(rom.arm9))
    overlays = loadOverlayTable(rom.arm9OverlayTable, lambda _i, f: rom.files[f])
    for index in (10, 29, 36):
        ov = overlays[index]
        uc.mem_write(ov.ramAddress, bytes(ov.data))
    uc.mem_map(0x02700000, 0x40000)
    uc.mem_write(ENTITY + 0xB4, struct.pack("<I", MONSTER))
    uc.mem_write(0x02353538, struct.pack("<I", 0x02100000))
    uc.mem_write(0x021040DA, b"\x08")  # Fixed Room 8; no room-6 scaling.
    return uc


def check_recovery(rom: NintendoDSRom, *, fixed: bool) -> int:
    uc = recovery_machine(rom)
    case = {}

    def service(machine, address, _size, _data):
        ability = machine.reg_read(UC_ARM_REG_R1)
        if address == 0x02052890:
            value = 200  # Omastar/Kabutops GetRegenSpeed: md byte 100 * 2.
        elif address == 0x02334D08:
            value = case["weather"]
        elif address == 0x02301D78:
            value = int(ability == case["ability"] and ability != 0)
        elif address == 0x02301F80:
            value = int(case["quick"] and ability == 0x35)
        elif address in (0x02311034, 0x02311064):
            value = 0  # No held item or exclusive recovery effect.
        elif address in (0x022E0864, 0x023ACCF8, 0x0204B678):
            value = 0  # No optional Alpha enemy difficulty scaling.
        else:
            return
        machine.reg_write(UC_ARM_REG_R0, value)
        machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, service)
    count = 0
    for non_team in (0, 1):
        for max_hp, boost in ((600, 75), (700, 87)):
            for ability in (0, 3, 85, 77):  # None, Rain Dish, Dry Skin, Ice Body.
                for weather in (0, 4, 5):
                    for quick in (False, True):
                        case.update(ability=ability, weather=weather, quick=quick)
                        uc.mem_write(MONSTER, bytes(0x240))
                        uc.mem_write(MONSTER + 2, struct.pack("<H", 139))
                        uc.mem_write(MONSTER + 6, bytes([non_team]))
                        uc.mem_write(MONSTER + 0x10, struct.pack("<HHHH", 100, max_hp, 0, boost))
                        uc.reg_write(UC_ARM_REG_SP, 0x0273F000)
                        uc.reg_write(UC_ARM_REG_R7, MONSTER)
                        uc.reg_write(UC_ARM_REG_R10, ENTITY)
                        uc.emu_start(0x02311104, 0x023112A8, count=10000)
                        expected = 200 - (100 if quick else 0)
                        if weather == 4 and ability in (3, 85):
                            expected -= 150
                        if not fixed and weather == 5 and ability != 77:
                            expected -= 100
                        expected = max(20, expected)
                        assert uc.reg_read(UC_ARM_REG_PC) == 0x023112A8
                        assert uc.reg_read(UC_ARM_REG_R4) == expected, (case, non_team)
                        current = struct.unpack("<H", uc.mem_read(MONSTER + 0x10, 2))[0]
                        assert current == 100 + (max_hp + boost) // expected, case
                        assert struct.unpack("<H", uc.mem_read(MONSTER + 0x16, 2))[0] == boost
                        count += 1
    return count


def main() -> None:
    manifest = load_module_manifest(MODULE)
    catalog = load_yaml(ROOT / "patch_engine/catalog.yaml")
    assert FULL_STACK_MODULES.count("bug_fixes") == 1
    assert FULL_STACK_MODULES[-1] == "bug_fixes"
    assert catalog["recommended_order"].index("bug_fixes") < catalog["recommended_order"].index("korean")
    assert catalog["modules"]["bug_fixes"]["kind"] == "asm"
    original = NintendoDSRom.fromFile(str(SOURCE))
    print(f"ARM recovery before: {check_recovery(original, fixed=False)} cases passed")
    with tempfile.TemporaryDirectory(prefix="alpha_bug_fixes_") as temp:
        temp = Path(temp)
        initial_cave = None
        inputs = [SOURCE]
        inputs.extend(path for path in (
            ROOT / "PatchTesting/Export Rom/Explorers of Alpha+.nds",
            ROOT / "PatchTesting/Export Rom/Explorers of Alpha+_kor.nds",
        ) if path.is_file())
        for index, source in enumerate(inputs):
            output, state_path = temp / f"patched_{index}.nds", temp / f"state_{index}.json"
            state = apply_module("bug_fixes", source, output, state_path=state_path)
            verify_module_applied(output, MODULE, state)
            fixed = NintendoDSRom.fromFile(str(output))
            # Only the declared hook words and newly allocated cave may change.
            source_rom = original if source == SOURCE else NintendoDSRom.fromFile(str(source))
            profile = load_rom_profile(ROOT / "patch_engine", "us_vanilla")
            module_record = state.get_module("bug_fixes")
            if source == SOURCE:
                initial_cave = module_record.caves[0]
            for binary, load in (("ov29", 0x022DC240), ("ov36", 0x023A7080)):
                before, after = get_rom_binary(source_rom, binary), get_rom_binary(fixed, binary)
                allowed = set()
                for hook in manifest["hooks"]:
                    if hook["binary"] == binary:
                        off = resolve_symbol(profile, hook["symbol"]) - load
                        allowed.update(range(off, off + 4))
                for cave in module_record.caves:
                    if cave.overlay == binary:
                        allowed.update(range(cave.file_offset, cave.file_offset + cave.size))
                assert len(before) == len(after)
                assert all(a == b or off in allowed for off, (a, b) in enumerate(zip(before, after)))
            print(f"ARM recovery after: {check_recovery(fixed, fixed=True)} cases passed")
            from verify_abilities import check_abilities

            check_abilities(fixed)
            print(f"Module apply/verify: {source.name}")
            output.unlink()
            state_path.unlink()
        # Reserving the first slot must relocate every helper without changing
        # the protected bytes or breaking any ability path.
        reservation = BuildState("us_vanilla", 0x022DC240, [
            AppliedModule("fixture_reservation", 1, caves=[initial_cave]),
        ])
        reservation_path = temp / "reservation.json"
        save_state(reservation_path, reservation)
        relocated_output = temp / "relocated.nds"
        relocated_state = apply_module("bug_fixes", SOURCE, relocated_output, state_path=reservation_path)
        verify_module_applied(relocated_output, MODULE, relocated_state)
        new_cave = relocated_state.get_module("bug_fixes").caves[0]
        assert new_cave.load_address != initial_cave.load_address
        relocated = NintendoDSRom.fromFile(str(relocated_output))
        first, end = initial_cave.file_offset, initial_cave.file_offset + initial_cave.size
        assert get_rom_binary(original, "ov36")[first:end] == get_rom_binary(relocated, "ov36")[first:end]
        check_abilities(relocated)
        print("Dynamic cave relocation and reservation passed")
        # An unknown original instruction must fail instead of silently patching it.
        damaged = NintendoDSRom.fromFile(str(SOURCE))
        overlays = loadOverlayTable(damaged.arm9OverlayTable, lambda _i, f: damaged.files[f])
        ov29 = overlays[29]
        blob = bytearray(damaged.files[ov29.fileID])
        struct.pack_into("<I", blob, 0x023111F0 - ov29.ramAddress, 0)
        damaged.files[ov29.fileID] = bytes(blob)
        try:
            assert_hooks_on_binary(
                bytes(blob), ov29.ramAddress,
                [hook for hook in manifest["hooks"] if hook["binary"] == "ov29"],
                profile, set(),
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("unexpected original instruction accepted")
    print("OK bug_fixes; no full-stack rebuild")


if __name__ == "__main__":
    main()
