"""Execute the ARM recovery loop with controlled ability/item/weather services."""
from itertools import product
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))

from ndspy.rom import NintendoDSRom
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R4, UC_ARM_REG_R7,
    UC_ARM_REG_R10, UC_ARM_REG_SP, UC_ARM_REG_PC, UC_ARM_REG_LR,
)
from patch_engine.manifest import load_module_manifest, load_rom_profile, resolve_symbol
from true_patches.bug_fixes.verify import recovery_machine, ENTITY, MONSTER


def check(path, simulate=False):
    rom = NintendoDSRom.fromFile(str(path))
    uc = recovery_machine(rom)
    manifest = load_module_manifest(Path(__file__).resolve().parent)
    profile = load_rom_profile(ROOT / "patch_engine", "us_vanilla")
    for hook in manifest["hooks"]:
        if not hook["name"].startswith("Regen"):
            continue
        address = resolve_symbol(profile, hook["symbol"])
        old = struct.unpack("<I", uc.mem_read(address, 4))[0]
        assert old == hook["vanilla_word" if simulate else "patched_word"], hook
        if simulate:
            uc.mem_write(address, struct.pack("<I", hook["patched_word"]))
    hail = 0x023111F0
    assert struct.unpack("<I", uc.mem_read(hail, 4))[0] == (0x00844000 if simulate else 0xE1A00000)
    if simulate:
        uc.mem_write(hail, struct.pack("<I", 0xE1A00000))
    case = {}

    def service(machine, address, _size, _data):
        query = machine.reg_read(UC_ARM_REG_R1)
        if address == 0x02052890:
            value = case["base"]
        elif address == 0x02334D08:
            value = case["weather"]
        elif address == 0x02301D78:
            value = int({3: case["rain"], 85: case["dry"], 77: case["ice"]}.get(query, False))
        elif address == 0x02301F80:
            value = int(query == 53 and case["quick"])
        elif address == 0x02311034:
            value = int(query == 17 and case["ribbon"])
        elif address == 0x02311064:
            value = int(query == 73 and case["exclusive"])
        elif address in (0x022E0864, 0x023ACCF8, 0x0204B678):
            value = 0
        else:
            return
        machine.reg_write(UC_ARM_REG_R0, value)
        machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, service)
    count = 0
    for base, weather, non_team, flags in product(
        (40, 200, 201, 800), (0, 4, 5), (0, 1), product((False, True), repeat=7)
    ):
        ribbon, quick, wish, rain, dry, exclusive, ice = flags
        case.update(base=base, weather=weather, ribbon=ribbon, quick=quick,
                    rain=rain, dry=dry, exclusive=exclusive, ice=ice)
        uc.mem_write(MONSTER, bytes(0x240))
        uc.mem_write(MONSTER + 2, struct.pack("<H", 139))
        uc.mem_write(MONSTER + 6, bytes([non_team]))
        uc.mem_write(MONSTER + 0x10, struct.pack("<HHHH", 100, 600, 0, 75))
        uc.mem_write(MONSTER + 0xD5, bytes([6 if wish else 0]))
        # Carry a remainder to check the actual recovery accumulator as well.
        uc.mem_write(MONSTER + 0x210, struct.pack("<H", 7))
        uc.reg_write(UC_ARM_REG_SP, 0x0273F000)
        uc.reg_write(UC_ARM_REG_R7, MONSTER)
        uc.reg_write(UC_ARM_REG_R10, ENTITY)
        uc.emu_start(0x02311104, 0x023112A8, count=10000)
        active = (ribbon, quick, wish, rain and weather == 4,
                  dry and weather == 4, exclusive)
        expected = max(25, min(400, base // (2 ** sum(active))))
        context = (base, weather, non_team, flags)
        assert uc.reg_read(UC_ARM_REG_PC) == 0x023112A8, context
        assert uc.reg_read(UC_ARM_REG_R4) == expected, context
        assert struct.unpack("<H", uc.mem_read(MONSTER + 0x10, 2))[0] == 100 + 682 // expected, context
        assert struct.unpack("<H", uc.mem_read(MONSTER + 0x210, 2))[0] == 682 % expected, context
        assert struct.unpack("<H", uc.mem_read(MONSTER + 0x16, 2))[0] == 75, context
        count += 1
    print(f"OK {path.name}: {count} recovery cases (simulation={simulate})")


if __name__ == "__main__":
    if "--simulate" in sys.argv:
        check(ROOT / "PatchTesting/Explorers of Alpha/Explorers of Alpha.nds", True)
    else:
        for name in ("Explorers of Alpha+.nds", "Explorers of Alpha+_kor.nds"):
            check(ROOT / "PatchTesting/Export Rom" / name)
