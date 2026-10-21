"""Compile the separated Tower payload without writing a ROM or save."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/.korean_jit_test_deps"))
from .contract import header
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                               UC_ARM_REG_SP)

MODULE = Path(__file__).resolve().parent


def main() -> None:
    compiler = shutil.which("arm-none-eabi-gcc")
    if not compiler:
        raise RuntimeError("arm-none-eabi-gcc is required")
    prefix = str(Path(compiler).with_name("arm-none-eabi-"))
    suffix = ".exe" if compiler.lower().endswith(".exe") else ""
    with tempfile.TemporaryDirectory(prefix="trial_tower_split_") as temporary:
        work = Path(temporary)
        (work / "trial_tower_generated.h").write_text(header(), encoding="ascii")
        (work / "tower_resident_generated.h").write_text(
            "".join(f"#define {name} {value}\n" for name, value in {
                "TT_DUNGEON": 234, "TT_SOURCE": 102, "TT_GROUP": 113,
                "TT_MARKER": 235, "TT_NAME_ID": 19701, "TT_MENU_PTR": 0x02300000,
                "TT_MENU_CAPACITY": 200,
                **{f"TT_NAME_ALIAS_{i}": 100+i for i in range(4)},
            }.items()), encoding="ascii")
        (work / "tower_runtime_generated.h").write_text(
            "#define TT_PRIOR_TEAM 0x022FC50C\n"
            "#define FORM_STAT_RESUME 0x023B0008\n", encoding="ascii")
        (work / "tower.ld").write_text(
            "SECTIONS { . = 0x023B8000; .text : { *(.text*) *(.rodata*) } "
            ".data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } "
            "/DISCARD/ : { *(.ARM.exidx*) *(.ARM.attributes) *(.comment) } }",
            encoding="ascii")
        elf = work / "tower.elf"
        command = [compiler, "-mcpu=arm946e-s", "-marm", "-Os", "-ffreestanding",
                   "-fno-builtin", "-nostdlib", "-Wall", "-Wextra", "-Werror",
                   "-I", str(work), "-I", str(MODULE / "runtime"),
                   "-include", str(work / "tower_runtime_generated.h"),
                   str(MODULE / "runtime/tower.c"),
                   str(MODULE / "runtime/tower_entry.S"),
                   str(MODULE / "runtime/tower_resident.S"),
                   "-Wl,-T," + str(work / "tower.ld"), "-o", str(elf)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        symbols = {}
        for line in subprocess.check_output(
                [prefix + "nm" + suffix, "--defined-only", str(elf)], text=True).splitlines():
            address, _kind, name = line.split()
            symbols[name] = int(address, 16)
        for name in ("ME_TowerReset", "ME_TowerQuickSave", "ME_TowerQuickLoad",
                     "ME_TowerQuickReady", "ME_TowerSpringComplete",
                     "ME_TowerTeamHook", "ME_TowerMenu", "ME_TowerStats"):
            assert name in symbols, name
        assert max(symbols.values()) - 0x023B8000 < 0x2000
        binary = work / "tower.bin"
        subprocess.run([prefix + "objcopy" + suffix, "-O", "binary", str(elf), str(binary)],
                       check=True, capture_output=True)
        u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        u.mem_map(0x02000000, 0x400000)
        u.mem_write(0x023B8000, binary.read_bytes())
        opened = False
        writes = []

        def ret(value=0):
            u.reg_write(UC_ARM_REG_R0, value)
            u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

        def service(uc, address, _size, _data):
            nonlocal opened
            if address == 0x0204CF9C:
                assert uc.reg_read(UC_ARM_REG_R0) == 234
                ret(int(opened))
            elif address == 0x0204D018:
                assert (uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)) == (234, 1)
                opened = True
                ret()
            elif address == 0x0204B988:
                writes.append(tuple(uc.reg_read(reg) for reg in
                                    (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)))
                ret()

        for address in (0x0204CF9C, 0x0204D018, 0x0204B988):
            u.hook_add(UC_HOOK_CODE, service, begin=address, end=address)
        for _ in range(2):
            u.reg_write(UC_ARM_REG_SP, 0x023FE000)
            u.reg_write(UC_ARM_REG_LR, 0x023FF000)
            u.emu_start(symbols["ME_TowerSpringComplete"], 0x023FF000, count=10000)
            assert u.reg_read(UC_ARM_REG_PC) == 0x023FF000
        assert writes == [(0, 0x53, 234, 1), (0, 0x55, 235, 1)] * 2
    print("PASS standalone Trial Tower ARM payload, addon exports, and Spring unlock")


if __name__ == "__main__":
    main()
