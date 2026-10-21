"""Focused Speed visual resource and linked ARM ABI regression test; no ROM build."""
from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/.korean_jit_test_deps"))

from ndspy.rom import NintendoDSRom
from skytemple_files.container.bin_pack.handler import BinPackHandler
from skytemple_files.data.anim.handler import AnimHandler
from skytemple_files.graphics.effect_wan.handler import EffectWanHandler
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                               UC_ARM_REG_SP)

from patch_engine.mega_evolve_runtime import build_runtime
from true_patches.mega_evolve.phase3_visual import prepare
from true_patches.mega_evolve.status_hooks import ENTRIES


SOURCE = ROOT / "PatchTesting/Explorers of Alpha/Explorers of Alpha.nds"
MODULE = ROOT / "true_patches/mega_evolve"
BASE = 0x02140000
ACTOR, TARGET, MONSTER = 0x02250000, 0x02250200, 0x02260000
STOP, STACK = 0x023ff000, 0x023fe000


def _test_effects(rom):
    original = BinPackHandler.deserialize(rom.getFileByName("EFFECT/effect.bin"))
    files = prepare(rom)
    effects = BinPackHandler.deserialize(files["EFFECT/effect.bin"])
    anim = AnimHandler.deserialize(files["BALANCE/anim.bin"])
    assert files["BALANCE/anim.bin"] == files["UTILITY/anim.bin"]
    assert len(effects) == 294 and len(anim.general_table) == 709
    assert effects[257] == original[257] and effects[293] != effects[257]
    assert effects[293][:0x1110] == effects[257][:0x1110]
    assert effects[293][0x11d0:] == effects[257][0x11d0:]
    source_wan = EffectWanHandler.deserialize(effects[257])
    speed_wan = EffectWanHandler.deserialize(effects[293])
    assert len(source_wan.customPalette) == len(speed_wan.customPalette) == 3
    assert source_wan.customPalette != speed_wan.customPalette
    assert [e.anim_file for e in anim.general_table[707:709]] == [293, 293]
    assert [(e.unk2, e.sfx) for e in anim.general_table[707:709]] == [(0, 544), (1, 547)]
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == rom_hash


def _defines():
    values = {"TT_PRIOR_TEAM": 0x022df6a4}
    values.update({"PRIOR_" + name: 0x02200000 for name in (
        "USE_MOVE", "MOVE_TYPE", "APPLY_DAMAGE", "DUNGEON_FREE", "FAINT",
        "CALC_DAMAGE", "DEFENSE_DROP", "HIT_CHECK", "EXECUTE_EFFECT")})
    for index, (_, site, head) in enumerate(ENTRIES):
        values[f"STATUS_HEAD_{index}"] = head
        values[f"STATUS_TARGET_{index}"] = site + 4
    return values


def _test_runtime(blob, symbols):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x02000000, 0x400000)
    u.mem_write(BASE, blob)
    u.mem_write(TARGET, struct.pack("<I", 1))
    u.mem_write(TARGET + 0xb4, struct.pack("<I", MONSTER))
    u.mem_write(MONSTER + 0x10, struct.pack("<H", 100))
    u.mem_write(MONSTER + 0x24, struct.pack("<4H", 10, 10, 10, 10))
    stage = 10
    calls = []

    def ret(value=0):
        u.reg_write(UC_ARM_REG_R0, value & 0xffffffff)
        u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

    def service(uc, address, _size, _data):
        nonlocal stage
        r0, r1, r2, r3 = (uc.reg_read(r) for r in
                          (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        if address == 0x022e95f4:
            ret(1)
        elif address == 0x022f96cc:
            ret(0)
        elif address == symbols["ME_GetStoredSpeed"]:
            assert r0 == TARGET
            ret(stage)
        elif address == symbols["ME_SetStoredSpeed"]:
            assert r0 == TARGET
            stage = r1
            ret()
        elif address == 0x022bdeb4:
            calls.append(("token", r0))
            ret(0x1234)
        elif address == 0x022e35e4:
            args = struct.unpack("<4I", bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 16)))
            calls.append(("effect", r0, r1, r2, r3, args))
            ret()
        elif address == 0x0234b350 or address in (0x0231399c, 0x023135fc):
            raise AssertionError(f"Speed attempted message/stat writer {address:#x}")

    for address in (0x022e95f4, 0x022f96cc, 0x022bdeb4, 0x022e35e4,
                    0x0234b350, 0x0231399c, 0x023135fc,
                    symbols["ME_GetStoredSpeed"], symbols["ME_SetStoredSpeed"]):
        u.hook_add(UC_HOOK_CODE, service, begin=address, end=address)
    attack_before = bytes(u.mem_read(MONSTER + 0x24, 8))
    for delta, expected, effect in ((1, 11, 708), (-2, 9, 707)):
        calls.clear()
        u.reg_write(UC_ARM_REG_SP, STACK)
        u.reg_write(UC_ARM_REG_LR, STOP)
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3),
                              (ACTOR, TARGET, 4, delta & 0xffffffff)):
            u.reg_write(reg, value)
        u.emu_start(symbols["ME_ChangeStat"], STOP, count=50000)
        assert u.reg_read(UC_ARM_REG_PC) == STOP
        assert u.reg_read(UC_ARM_REG_R0) == 1
        assert stage == expected
        assert calls == [("token", effect),
                         ("effect", TARGET, effect, 1, 0x34,
                          (2, 0, 0xffffffff, 0))], calls
        assert bytes(u.mem_read(MONSTER + 0x24, 8)) == attack_before
    stage = 16
    calls.clear()
    u.reg_write(UC_ARM_REG_SP, STACK)
    u.reg_write(UC_ARM_REG_LR, STOP)
    for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3),
                          (ACTOR, TARGET, 4, 1)):
        u.reg_write(reg, value)
    u.emu_start(symbols["ME_ChangeStat"], STOP, count=50000)
    assert u.reg_read(UC_ARM_REG_R0) == 0 and stage == 16 and not calls


if __name__ == "__main__":
    rom_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    _test_effects(NintendoDSRom(SOURCE.read_bytes()))
    with tempfile.TemporaryDirectory() as temporary:
        blob, symbols = build_runtime(MODULE, Path(temporary), BASE, 0x023bf000,
                                      0x023be000, 3, additional_defines=_defines())
        _test_runtime(blob, symbols)
    print("PASS Speed palette-swap resources and ARM effect ABI; no attack rank/message calls")
