"""Focused Speed visual resource and linked ARM ABI regression test; no ROM build."""
from __future__ import annotations

import hashlib
import json
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
from patch_engine.korean_codec import decode_english, parse_str_file
from true_patches.mega_evolve.phase3_visual import prepare
from true_patches.mega_evolve.status_hooks import ENTRIES


SOURCE = ROOT / "PatchTesting/Explorers of Alpha/Explorers of Alpha.nds"
MODULE = ROOT / "true_patches/mega_evolve"
BASE = 0x02140000
ACTOR, TARGET, MONSTER = 0x02250000, 0x02250200, 0x02260000
MOVE = 0x02280000
STOP, STACK = 0x023ff000, 0x023fe000


def _test_effects(rom):
    strings = parse_str_file(rom.getFileByName("MESSAGE/text_e.str"))
    assert decode_english(strings[3773]) == "It had no effect on [string:1]!"
    assert decode_english(strings[3795]) == "[string:0] swapped special abilities with\nthe target!"
    assert decode_english(strings[3167]) == "[string:0] picked up the [item:0]."
    assert decode_english(strings[3807]) == "[string:0] copied the target's ability!"
    weather_messages = json.loads((MODULE / "data/phase1_strings.json").read_text(encoding="utf-8"))
    assert {row["index"] for row in weather_messages["entries"] if 19753 <= row["index"] <= 19755} == {19753, 19754, 19755}
    assert len(strings) <= 19753
    assert struct.unpack_from("<I", rom.arm9, 0x02024fe8 - 0x02000000)[0] == 0xe92d4038
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
    tailwind = anim.move_table[444]
    wind = anim.general_table[471]
    assert tailwind.anim2 == 471 and wind.anim_type.value == 5 and wind.anim_file == 15
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
    telepathy = False
    messages_allowed = False
    blocked_ids = set()

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
            ret(int((telepathy and r2 == 429) or r2 in blocked_ids))
        elif address == 0x020151c8:
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
        elif address in (0x022e5258, 0x022e52f8):
            calls.append(("hit", address, r0, r1))
            ret()
        elif address == 0x0234b350 and messages_allowed:
            calls.append(("message", r0, r1, r2))
            ret()
        elif address == 0x022e2ad8 and messages_allowed:
            calls.append(("name", r0, r1, r2))
            ret()
        elif address == 0x0234b350 or address in (0x0231399c, 0x023135fc):
            raise AssertionError(f"Speed attempted message/stat writer {address:#x}")

    for address in (0x022e95f4, 0x022f96cc, 0x022bdeb4, 0x022e35e4,
                    0x022e5258, 0x022e52f8,
                    0x020151c8,
                    0x022e2ad8,
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
    for stat, delta, expected_call, offset, expected in (
            (5, 1, 0x022e5258, 0x2c, 11),
            (6, -1, 0x022e52f8, 0x2e, 9)):
        calls.clear()
        u.mem_write(MONSTER + offset, struct.pack("<H", 10))
        u.reg_write(UC_ARM_REG_SP, STACK)
        u.reg_write(UC_ARM_REG_LR, STOP)
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3),
                              (ACTOR, TARGET, stat, delta & 0xffffffff)):
            u.reg_write(reg, value)
        u.emu_start(symbols["ME_ChangeStat"], STOP, count=50000)
        assert u.reg_read(UC_ARM_REG_R0) == 1
        assert struct.unpack("<H", bytes(u.mem_read(MONSTER + offset, 2)))[0] == expected
        assert calls == [("hit", expected_call, TARGET, int(stat == 6))]
        assert bytes(u.mem_read(MONSTER + 0x24, 8)) == attack_before
    u.mem_write(MONSTER + 0x2c, struct.pack("<H", 16))
    calls.clear()
    u.reg_write(UC_ARM_REG_SP, STACK)
    u.reg_write(UC_ARM_REG_LR, STOP)
    for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3),
                          (ACTOR, TARGET, 5, 1)):
        u.reg_write(reg, value)
    u.emu_start(symbols["ME_ChangeStat"], STOP, count=50000)
    assert u.reg_read(UC_ARM_REG_R0) == 0 and not calls
    u.mem_write(ACTOR, struct.pack("<I", 1))
    u.mem_write(ACTOR + 0xb4, struct.pack("<I", MONSTER + 0x400))
    u.mem_write(MOVE + 4, struct.pack("<H", 20))
    telepathy = True
    messages_allowed = True
    calls.clear()
    u.reg_write(UC_ARM_REG_SP, STACK)
    u.reg_write(UC_ARM_REG_LR, STOP)
    for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2),
                          (ACTOR, TARGET, MOVE)):
        u.reg_write(reg, value)
    u.emu_start(symbols["ME_TargetBlocked"], STOP, count=50000)
    assert u.reg_read(UC_ARM_REG_R0) == 1
    assert calls == [("name", 1, TARGET, 0), ("message", ACTOR, TARGET, 3774)]
    telepathy = False
    for name, args, identity in (
            ("ME_StatusBlocked", (ACTOR, TARGET, 0), 405),
            ("ME_DefenseDropBlocked", (ACTOR, TARGET, 0, 1), 340),
            ("ME_ForcedMoveBlocked", (ACTOR, TARGET), 458),
            ("ME_ChangeStat", (ACTOR, TARGET, 5, 0xffffffff), 15)):
        blocked_ids = {identity}
        calls.clear()
        u.reg_write(UC_ARM_REG_SP, STACK)
        u.reg_write(UC_ARM_REG_LR, STOP)
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            u.reg_write(reg, value)
        u.emu_start(symbols[name], STOP, count=50000)
        assert u.reg_read(UC_ARM_REG_R0) == (0 if name == "ME_ChangeStat" else 1)
        assert calls == [("name", 1, TARGET, 0), ("message", ACTOR, TARGET, 3774)], (name, calls)


def _test_weather_replay(blob, symbols):
    for before_weather, before_strong, new_weather, new_strong, expected in (
            (1, 0, 1, 0, 0), (4, 1, 4, 1, 0),
            (1, 0, 4, 0, 1), (1, 0, 1, 1, 1)):
        u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        u.mem_map(0x02000000, 0x400000)
        u.mem_write(BASE, blob)
        u.mem_write(0x02353538, struct.pack("<I", 0x02100000))
        u.mem_write(0x02100000 + 0x12b78, struct.pack("<I", TARGET))
        u.mem_write(TARGET, struct.pack("<I", 1))
        u.mem_write(TARGET + 0xb4, struct.pack("<I", MONSTER))
        u.mem_write(MONSTER + 0x10, struct.pack("<H", 100))
        calls = []

        def ret(value=0):
            u.reg_write(UC_ARM_REG_R0, value & 0xffffffff)
            u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

        def service(uc, address, _size, _data):
            if address == symbols["ME_ApparentWeather"]:
                ret(before_weather)
            elif address == symbols["ME_WeatherStrength"]:
                ret(before_strong)
            elif address == symbols["ME_ForcedWeather"]:
                ret(-1)
            elif address == 0x023354c4:
                calls.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
                ret(1)

        for address in (symbols["ME_ApparentWeather"], symbols["ME_WeatherStrength"],
                        symbols["ME_ForcedWeather"], 0x023354c4):
            u.hook_add(UC_HOOK_CODE, service, begin=address, end=address)
        u.reg_write(UC_ARM_REG_SP, STACK)
        u.reg_write(UC_ARM_REG_LR, STOP)
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3),
                              (TARGET, new_weather, new_strong, 0)):
            u.reg_write(reg, value)
        u.emu_start(symbols["ME_SetWeatherSource"], STOP, count=50000)
        assert u.reg_read(UC_ARM_REG_R0) == 1
        assert calls == [(0, expected)], (before_weather, before_strong, new_weather, new_strong, calls)


def _test_strong_weather_messages(blob, symbols):
    for ability, weather, message in ((277, 1, 19754), (362, 4, 19755), (293, 0, 19756)):
        for repeated in (False, True):
            u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
            u.mem_map(0x02000000, 0x400000)
            u.mem_write(BASE, blob)
            u.mem_write(0x02353538, struct.pack("<I", 0x02100000))
            u.mem_write(0x02100000 + 0x12b78, struct.pack("<I", TARGET))
            u.mem_write(TARGET, struct.pack("<I", 1))
            u.mem_write(TARGET + 0xb4, struct.pack("<I", MONSTER))
            u.mem_write(MONSTER + 0x10, struct.pack("<H", 100))
            calls = []
            selected = repeated

            def ret(value=0):
                u.reg_write(UC_ARM_REG_R0, value & 0xffffffff)
                u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

            def service(uc, address, _size, _data):
                nonlocal selected
                if address == symbols["ME_ApparentWeather"]:
                    ret(weather if selected else 4 if weather != 4 else 1)
                elif address == symbols["ME_WeatherStrength"]:
                    ret(int(selected))
                elif address == symbols["ME_ForcedWeather"]:
                    ret(-1)
                elif address == symbols["ME_AbilityGrade"]:
                    ret(0)
                elif address == 0x02001170:
                    ret(0x02290000)
                elif address == 0x023354c4:
                    calls.append(("selector", uc.reg_read(UC_ARM_REG_R1)))
                    selected = True
                    ret(1)
                elif address == 0x022bdeb4:
                    calls.append(("token", uc.reg_read(UC_ARM_REG_R0)))
                    ret(0x1234)
                elif address == 0x022e35e4:
                    args = struct.unpack("<4I", bytes(uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 16)))
                    calls.append(("wind", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1),
                                  uc.reg_read(UC_ARM_REG_R2), uc.reg_read(UC_ARM_REG_R3), args))
                    ret()
                elif address == 0x0234b2a4:
                    calls.append(("message", uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
                    ret()

            for address in (symbols["ME_ApparentWeather"], symbols["ME_WeatherStrength"],
                            symbols["ME_ForcedWeather"], symbols["ME_AbilityGrade"],
                            0x02001170, 0x023354c4, 0x022bdeb4, 0x022e35e4,
                            0x0234b2a4):
                u.hook_add(UC_HOOK_CODE, service, begin=address, end=address)
            u.reg_write(UC_ARM_REG_SP, STACK)
            u.reg_write(UC_ARM_REG_LR, STOP)
            for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3),
                                  (TARGET, weather, 1, ability)):
                u.reg_write(reg, value)
            u.emu_start(symbols["ME_SetWeatherSource"], STOP, count=50000)
            assert u.reg_read(UC_ARM_REG_R0) == 1, (ability, repeated, calls)
            expected = [("selector", 0)] if repeated else [("selector", 1)]
            if not repeated and ability == 293:
                expected += [("token", 471), ("wind", TARGET, 471, 1, 0x34,
                                               (2, 0, 0xffffffff, 0))]
            if not repeated:
                expected.append(("message", TARGET, message))
            assert calls == expected, (ability, repeated, calls)


def _test_pickup(blob, symbols):
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.mem_map(0x02000000, 0x400000)
    u.mem_write(BASE, blob)
    u.mem_write(TARGET, struct.pack("<I", 1))
    u.mem_write(TARGET + 0xb4, struct.pack("<I", MONSTER))
    u.mem_write(MONSTER + 0x10, struct.pack("<H", 100))
    calls = []
    insert_ok = True

    def ret(value=0):
        u.reg_write(UC_ARM_REG_R0, value & 0xffffffff)
        u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

    def service(uc, address, _size, _data):
        r0, r1, r2, r3 = (uc.reg_read(r) for r in
                          (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        if address == symbols["ME_AbilityActive"]:
            ret(int(r0 == TARGET and r1 == 451))
        elif address == 0x0200edc0:
            ret(0)
        elif address == 0x022eab20:
            assert r0 == 50
            ret(1)
        elif address == 0x022eaa98:
            assert r0 > 0
            ret(0)
        elif address == 0x023443b4:
            uc.mem_write(r0, struct.pack("<HHH", 1, 0, r1))
            ret()
        elif address == 0x0200f874:
            calls.append(("insert", bytes(uc.mem_read(r0, 6))))
            ret(int(insert_ok))
        elif address == 0x02024fe8:
            calls.append(("item_tag", r0, bytes(uc.mem_read(r1, 6)), r2))
            ret()
        elif address == 0x022e2ad8:
            calls.append(("name", r0, r1, r2))
            ret()
        elif address == 0x0234b2a4:
            calls.append(("message", r0, r1))
            ret()

    for address in (symbols["ME_AbilityActive"], 0x0200edc0, 0x022eab20,
                    0x022eaa98, 0x023443b4, 0x0200f874, 0x02024fe8,
                    0x022e2ad8, 0x0234b2a4):
        u.hook_add(UC_HOOK_CODE, service, begin=address, end=address)
    u.reg_write(UC_ARM_REG_SP, STACK)
    u.reg_write(UC_ARM_REG_LR, STOP)
    u.reg_write(UC_ARM_REG_R0, TARGET)
    u.emu_start(symbols["ME_PickupItem"], STOP, count=50000)
    assert u.reg_read(UC_ARM_REG_R0) == 1
    assert [x[0] for x in calls] == ["insert", "item_tag", "name", "message"]
    assert calls[1] == ("item_tag", 0, calls[0][1], 0)
    assert calls[2:] == [("name", 0, TARGET, 0), ("message", TARGET, 3168)]
    insert_ok = False
    calls.clear()
    u.reg_write(UC_ARM_REG_SP, STACK)
    u.reg_write(UC_ARM_REG_LR, STOP)
    u.reg_write(UC_ARM_REG_R0, TARGET)
    u.emu_start(symbols["ME_PickupItem"], STOP, count=50000)
    assert u.reg_read(UC_ARM_REG_R0) == 0
    assert [x[0] for x in calls] == ["insert"]


if __name__ == "__main__":
    rom_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    _test_effects(NintendoDSRom(SOURCE.read_bytes()))
    with tempfile.TemporaryDirectory() as temporary:
        blob, symbols = build_runtime(MODULE, Path(temporary), BASE, 0x023bf000,
                                      0x023be000, 3, additional_defines=_defines())
        _test_runtime(blob, symbols)
        _test_pickup(blob, symbols)
        _test_strong_weather_messages(blob, symbols)
    with tempfile.TemporaryDirectory() as temporary:
        blob, symbols = build_runtime(MODULE, Path(temporary), BASE, 0x023bf000,
                                      0x023be000, 1)
        _test_weather_replay(blob, symbols)
    print("PASS stat visuals, blocked messages, Pickup item tags, strong-weather messages/replay suppression")
