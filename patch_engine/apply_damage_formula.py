"""Unified damage_formula apply: main-series CalcDamage + Gen9 BP + UI + RA/projectile."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.waza_p.handler import WazaPHandler

from .apply_asm import apply_asm_single
from .apply_power_stars_scale import apply_power_stars_scale_module
from .apply_technician_threshold import apply_technician_threshold_module
from .overlay_caves import get_rom_binary, write_rom_binary
from .state import AppliedModule, BuildState

OV29_LOAD = 0x022DC240
PROJECTILE_MULT_SITE = 0x0230CFA8
MOV_R1_0x80 = 0xE3A01080
MOV_R1_0x100 = 0xE3A01C01
WAZA_CD_PATHS = ("BALANCE/waza_cd.bin", "UTILITY/waza_cd.bin")
ITEM_CD_PATHS = ("BALANCE/item_cd.bin", "UTILITY/item_cd.bin")
EFFECT_REGULAR_ATTACK = 1
PROJECTILE_MOVE_ID = 0x195
# Stick-like item_cd stub: InitMove(projectile) + DealDamageProjectile(power from ov10).
# item_id / power_abs / stack move slot offset (bytes).
ROCK_TO_PROJECTILE = (
    # effect_id, item_id, power_abs (Alpha/NA absolute)
    (6, 8, 0x022C46B4),   # Geo Pebble
    (7, 7, 0x022C46B8),   # Gravelerock
    (9, 10, 0x022C46BC),  # Rare Fossil
)
# MATCHUP_SUPER_EFFECTIVE_MULTIPLIER. Fx32, 8 fraction bits (1.0 = 0x100).
# Applied once per defending type. 0x166 = 358/256 ≈ 1.4; 0x180 = 384/256 = 1.5.
MATCHUP_SUPER_EFFECTIVE_ABS = 0x022C4818
MATCHUP_SUPER_FX_1_4 = 0x166
MATCHUP_SUPER_FX_1_5 = 0x180
OV10_LOAD = 0x022BCA80
# DoMovePsywave: the 13 instructions that turn DungeonRandRange into r3.
# Replaced with (x + 5) * (level / 10), x = DungeonRandInt(10) + 1.
PSYWAVE_SITE = 0x02327C80
DUNGEON_RAND_INT = 0x022EAA98
SOFT_DIV = 0x0208FEA4
PSYWAVE_VANILLA = (
    0xE3A00080,  # mov r0, #0x80
    0xE3A01D06,  # mov r1, #0x180
    0xE1A05002,  # mov r5, r2
    0xE1A04003,  # mov r4, r3
    0xEBFF0B8A,  # bl DungeonRandRange
    0xE59710B4,  # ldr r1, [r7, #0xb4]
    0xE1A02005,  # mov r2, r5
    0xE5D1100A,  # ldrb r1, [r1, #0xa]
    0xE0010190,  # mul r1, r0, r1
    0xE1B03441,  # asrs r3, r1, #8
    0x43A03001,  # movmi r3, #1
    0xE35300C7,  # cmp r3, #0xc7
    0xC3A030C7,  # movgt r3, #0xc7
)
# DoMovePresent power immediates. Heal branch (10–29) is left alone.
PRESENT_POWERS = (
    (0x0232B29C, 0xE3A0304B, 0xE3A03078),  # 0–9: 75 → 120
    (0x0232B320, 0xE3A03032, 0xE3A03050),  # 30–59: 50 → 80
    (0x0232B344, 0xE3A03019, 0xE3A03028),  # 60–99: 25 → 40
)
# Magnitude power halfwords, index 0–6. The following 0 sentinel stays.
MAGNITUDE_ABS = 0x022C4924
MAGNITUDE_OLD = (5, 10, 15, 25, 30, 35, 40)
MAGNITUDE_NEW = (10, 30, 50, 70, 90, 110, 150)
# Natural Gift rows: i16 item, u8 type, u8 0, i16 added power. Item 0 ends the table.
GIFT_ABS = 0x022C5130
GIFT_STRIDE = 6
# Vanilla added power. Plain Seed 85, Golden Seed 93, Reviser Seed 105 become 70.
GIFT_VANILLA = {
    69: 1, 70: 1, 71: 3, 72: 2, 73: 1, 74: 2, 75: 1, 76: 2, 77: 3, 78: 2,
    79: 5, 80: 2, 81: 2, 82: 2, 83: 2, 84: 2, 85: 15, 86: 2, 87: 5,
    89: 3, 90: 2, 91: 2, 93: 10, 94: 5, 95: 5, 96: 5, 97: 5,
    104: 2, 105: 10, 106: 2, 107: 2, 117: 5, 118: 1,
}
GIFT_FIXED = {85: 70, 93: 70, 105: 70}


def _waza_move_count(raw: bytes) -> int:
    from skytemple_files.common.util import read_u32
    from skytemple_files.container.sir0.handler import Sir0Handler
    from skytemple_files.data.waza_p._model import MOVE_ENTRY_BYTELEN

    sir0 = Sir0Handler.deserialize(raw)
    move_ptr = read_u32(sir0.content, sir0.data_pointer)
    learn_ptr = read_u32(sir0.content, sir0.data_pointer + 4)
    span = learn_ptr - move_ptr
    count, rem = divmod(span, MOVE_ENTRY_BYTELEN)
    if count < 1 or rem >= 16:
        raise RuntimeError(f"waza move table is not aligned: span={span}")
    return count


def _apply_waza_powers(rom: NintendoDSRom, module_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    comps = manifest.get("components") or {}
    data_cfg = manifest.get("data") or {}
    powers_path = module_dir / str(
        comps.get("powers_json") or data_cfg.get("powers_json", "data/gen9_powers_by_move_id.json")
    )
    powers = {int(k): int(v) for k, v in json.loads(powers_path.read_text(encoding="utf-8")).items()}
    paths = list(
        comps.get("waza_paths")
        or data_cfg.get("waza_paths")
        or [
            "BALANCE/waza_p.bin",
            "UTILITY/waza_p.bin",
            "BALANCE/waza_p2.bin",
            "UTILITY/waza_p2.bin",
        ]
    )
    writes = 0
    for path in paths:
        if path not in rom.filenames:
            continue
        raw = rom.getFileByName(path)
        import skytemple_files.data.waza_p._model as waza_p_model

        waza_p_model.MOVE_COUNT = _waza_move_count(raw)
        wp = WazaPHandler.deserialize(raw)
        for mid, powv in powers.items():
            if mid >= len(wp.moves):
                continue
            if int(wp.moves[mid].base_power) != powv:
                wp.moves[mid].base_power = powv  # type: ignore[assignment]
                writes += 1
        rom.setFileByName(path, WazaPHandler.serialize(wp))
    return {"writes": writes, "moves": len(powers), "paths": paths}


def _patch_regular_attack_effect(code: bytearray) -> bytearray:
    for off in range(0, len(code) - 4, 4):
        w = struct.unpack_from("<I", code, off)[0]
        if (w & 0x0FFFFFFF) == 0x03A00018:
            struct.pack_into("<I", code, off, (w & 0xF0000000) | 0x03A00014)

    for off in range(0, len(code) - 20, 4):
        w0 = struct.unpack_from("<I", code, off)[0]
        w1 = struct.unpack_from("<I", code, off + 4)[0]
        w3 = struct.unpack_from("<I", code, off + 12)[0]
        if w0 == 0xE5D12000 and w1 == 0xE352008B and w3 == 0xE5D12000:
            struct.pack_into("<I", code, off + 12, 0xE5D12001)
            break

    idx = None
    for off in range(0, len(code) - 8, 4):
        w0 = struct.unpack_from("<I", code, off)[0]
        w1 = struct.unpack_from("<I", code, off + 4)[0]
        if w0 == 0xE1A03000 and w1 in (0xE3A01C01, 0xE3A01080, 0xE3A01040):
            idx = off
            break
        if w0 == 0xE58D0008 and w1 == 0xE3A02000:
            idx = off
            break
    if idx is None:
        raise RuntimeError("regular-attack CalcDamage arg site not found")

    orig_ldrh = 0xE1D8A0B4
    for off in range(idx, min(idx + 0x28, len(code)), 4):
        w = struct.unpack_from("<I", code, off)[0]
        if w == 0xE1D8A0B4:
            orig_ldrh = w
            break

    # r3=power, [sp,#8]=0x40 (0.25), full_calc nonzero
    new_words = [
        0xE1A03000,
        0xE3A01040,
        0xE58D1008,
        0xE3A02000,
        orig_ldrh,
        0xE58DA00C,
        0xE58D1010,
    ]
    for i, w in enumerate(new_words):
        struct.pack_into("<I", code, idx + i * 4, w)

    after = idx + len(new_words) * 4
    if struct.unpack_from("<I", code, after)[0] != 0xE1A00009:
        raise RuntimeError("expected mov r0, sb after regular-attack arg block")
    if struct.unpack_from("<I", code, after + 4)[0] != 0xE1A01004:
        raise RuntimeError("expected mov r1, r4 after regular-attack arg block")
    bl = struct.unpack_from("<I", code, after + 8)[0]
    if (bl & 0x0F000000) != 0x0B000000:
        raise RuntimeError(f"expected bl CalcDamage, got {bl:#010x}")
    return code


def _apply_regular_attack(rom: NintendoDSRom) -> dict[str, Any]:
    code = None
    for path in WAZA_CD_PATHS:
        cd = DataCDHandler.deserialize(rom.getFileByName(path))
        patched = _patch_regular_attack_effect(bytearray(cd.get_effect_code(EFFECT_REGULAR_ATTACK)))
        cd.set_effect_code(EFFECT_REGULAR_ATTACK, bytes(patched))
        rom.setFileByName(path, DataCDHandler.serialize(cd))
        code = patched
    return {"effect_id": EFFECT_REGULAR_ATTACK, "multiplier_f88": 0x40, "paths": list(WAZA_CD_PATHS), "bytes": len(code or b"")}


def _apply_projectile_mult(rom: NintendoDSRom) -> dict[str, Any]:
    config = get_ppmdu_config_for_rom(rom)
    ov29 = get_rom_binary(rom, "ov29")
    off = PROJECTILE_MULT_SITE - OV29_LOAD
    cur = struct.unpack_from("<I", ov29, off)[0]
    if cur not in (MOV_R1_0x80, MOV_R1_0x100):
        raise RuntimeError(f"projectile mult site {PROJECTILE_MULT_SITE:#x}: unexpected {cur:#010x}")
    struct.pack_into("<I", ov29, off, MOV_R1_0x100)
    write_rom_binary(rom, config, "ov29", bytes(ov29))
    return {"site": f"0x{PROJECTILE_MULT_SITE:X}", "was": f"0x{cur:08X}", "now": "0x100 (1.0)"}


def _apply_super_effective_mult(rom: NintendoDSRom, config) -> dict[str, Any]:
    from skytemple_files.common.util import get_binary_from_rom, set_binary_in_rom

    sec = config.bin_sections.overlay10
    ov10 = bytearray(get_binary_from_rom(rom, sec))
    off = MATCHUP_SUPER_EFFECTIVE_ABS - int(sec.loadaddress)
    if off < 0 or off + 4 > len(ov10):
        raise RuntimeError(f"super-effective multiplier OOB at ov10+{off:#x}")
    cur = struct.unpack_from("<I", ov10, off)[0]
    if cur not in (MATCHUP_SUPER_FX_1_4, MATCHUP_SUPER_FX_1_5):
        raise RuntimeError(
            f"MATCHUP_SUPER_EFFECTIVE_MULTIPLIER at {MATCHUP_SUPER_EFFECTIVE_ABS:#x} "
            f"is {cur:#x}, expected 0x166 or 0x180"
        )
    struct.pack_into("<I", ov10, off, MATCHUP_SUPER_FX_1_5)
    set_binary_in_rom(rom, sec, bytes(ov10))
    return {"site": f"0x{MATCHUP_SUPER_EFFECTIVE_ABS:X}", "was": f"0x{cur:X}", "now": "0x180 (1.5)"}


def _apply_throwable_ov10(rom: NintendoDSRom, module_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    from skytemple_files.common.util import get_binary_from_rom, set_binary_in_rom

    comps = manifest.get("components") or {}
    path = module_dir / str(comps.get("throwable_json", "data/throwable_ov10.json"))
    entries = json.loads(path.read_text(encoding="utf-8"))
    config = get_ppmdu_config_for_rom(rom)
    ov10 = bytearray(get_binary_from_rom(rom, config.bin_sections.overlay10))
    written: list[dict[str, Any]] = []
    for ent in entries:
        fo = int(ent["file_offset"], 16) if isinstance(ent["file_offset"], str) else int(ent["file_offset"])
        val = int(ent["value"])
        if fo < 0 or fo + 2 > len(ov10):
            raise RuntimeError(f"throwable ov10 offset OOB: {fo:#x}")
        old = struct.unpack_from("<H", ov10, fo)[0]
        struct.pack_into("<H", ov10, fo, val)
        written.append({"name": ent.get("name"), "file_offset": f"0x{fo:X}", "was": old, "now": val})
    set_binary_in_rom(rom, config.bin_sections.overlay10, bytes(ov10))
    return {"entries": written}


def _psywave_words() -> tuple[int, ...]:
    """(x + 5) * (level / 10). x is 1..10. Level under 10 yields 0."""
    site = PSYWAVE_SITE
    return (
        0xE1A05002,  # mov r5, r2
        0xE1A04003,  # mov r4, r3
        0xE3A0000A,  # mov r0, #10
        _encode_bl(site + 12, DUNGEON_RAND_INT),
        0xE2800006,  # add r0, r0, #6   ; (0..9) + 6 = (1..10) + 5
        0xE58D0000,  # str r0, [sp]
        0xE59700B4,  # ldr r0, [r7, #0xb4]
        0xE5D0000A,  # ldrb r0, [r0, #0xa]
        0xE3A0100A,  # mov r1, #10
        _encode_bl(site + 36, SOFT_DIV),
        0xE59D1000,  # ldr r1, [sp]
        0xE0030091,  # mul r3, r1, r0
        0xE1A02005,  # mov r2, r5
    )


def _read_words(buf: bytes, off: int, n: int) -> tuple[int, ...]:
    return tuple(struct.unpack_from("<" + "I" * n, buf, off))


def _apply_variable_power(rom: NintendoDSRom, config) -> dict[str, Any]:
    from skytemple_files.common.util import get_binary_from_rom, set_binary_in_rom

    ov29 = get_rom_binary(rom, "ov29")
    psy_off = PSYWAVE_SITE - OV29_LOAD
    psy_new = _psywave_words()
    if len(psy_new) != len(PSYWAVE_VANILLA):
        raise RuntimeError("psywave replacement length drifted")
    cur = _read_words(ov29, psy_off, len(psy_new))
    if cur not in (PSYWAVE_VANILLA, psy_new):
        raise RuntimeError(f"Psywave site {PSYWAVE_SITE:#x} unexpected {cur[0]:#010x}")
    for i, word in enumerate(psy_new):
        struct.pack_into("<I", ov29, psy_off + i * 4, word)
    present: list[dict[str, Any]] = []
    for addr, old, new in PRESENT_POWERS:
        off = addr - OV29_LOAD
        word = struct.unpack_from("<I", ov29, off)[0]
        if word not in (old, new):
            raise RuntimeError(f"Present power at {addr:#x} is {word:#010x}")
        struct.pack_into("<I", ov29, off, new)
        present.append({"addr": f"0x{addr:X}", "was": f"0x{word:08X}", "now": f"0x{new:08X}"})
    write_rom_binary(rom, config, "ov29", bytes(ov29))

    sec = config.bin_sections.overlay10
    ov10 = bytearray(get_binary_from_rom(rom, sec))
    mag_off = MAGNITUDE_ABS - OV10_LOAD
    magnitude: list[dict[str, int]] = []
    for i, (old, new) in enumerate(zip(MAGNITUDE_OLD, MAGNITUDE_NEW)):
        val = struct.unpack_from("<h", ov10, mag_off + i * 2)[0]
        if val not in (old, new):
            raise RuntimeError(f"Magnitude index {i} is {val}, expected {old} or {new}")
        struct.pack_into("<h", ov10, mag_off + i * 2, new)
        magnitude.append({"index": i, "was": val, "now": new})
    sentinel = struct.unpack_from("<h", ov10, mag_off + 7 * 2)[0]
    if sentinel != 0:
        raise RuntimeError(f"Magnitude table sentinel is {sentinel}")

    gift_off = GIFT_ABS - OV10_LOAD
    gift: list[dict[str, int]] = []
    seen: set[int] = set()
    for row in range(len(GIFT_VANILLA) + 1):
        base = gift_off + row * GIFT_STRIDE
        item, _typ, _zero, power = struct.unpack_from("<hBBh", ov10, base)
        if item == 0:
            break
        if item not in GIFT_VANILLA:
            raise RuntimeError(f"Natural Gift row {row} item {item} is not in the vanilla table")
        target = GIFT_FIXED.get(item, GIFT_VANILLA[item] * 10)
        if power not in (GIFT_VANILLA[item], target):
            raise RuntimeError(f"Natural Gift item {item} power {power} is neither vanilla nor the new value")
        struct.pack_into("<h", ov10, base + 4, target)
        seen.add(item)
        gift.append({"item": item, "was": power, "now": target})
    if seen != set(GIFT_VANILLA):
        raise RuntimeError(f"Natural Gift table missing items {set(GIFT_VANILLA) - seen}")
    set_binary_in_rom(rom, sec, bytes(ov10))
    return {"psywave": " (x+5)*(level/10)", "present": present, "magnitude": magnitude, "gift": gift}


def _encode_bl(pc: int, target: int) -> int:
    return 0xEB000000 | (((target - (pc + 8)) // 4) & 0xFFFFFF)


def _make_projectile_item_stub(*, item_id: int, power_abs: int, sp_off: int = 0x52) -> bytes:
    """Clone Stick item_cd stub: InitMove(0x195) + DealDamageProjectile(power)."""
    # Assembled for execution at ItemStartAddress 0x0231BE50 (same layout as Stick).
    item_start = 0x0231BE50
    init_move = 0x020137B8
    deal_proj = 0x02332C4C
    item_jump = 0x0231CB14
    words = [
        0xE59F1030,  # ldr r1, [pc, #0x30] ; move id pool
        0xE28D0000 | sp_off,  # add r0, sp, #sp_off
        _encode_bl(item_start + 0x08, init_move),
        0xE59F0028,  # ldr r0, [pc, #0x28] ; power ptr pool
        0xE3A04C01,  # mov r4, #0x100
        0xE1D030F0,  # ldrsh r3, [r0]
        0xE58D4000,  # str r4, [sp]
        0xE3A04000 | (item_id & 0xFF),  # mov r4, #item_id
        0xE28D2000 | sp_off,  # add r2, sp, #sp_off
        0xE1A00008,  # mov r0, r8
        0xE1A01007,  # mov r1, r7
        0xE58D4004,  # str r4, [sp, #4]
        _encode_bl(item_start + 0x30, deal_proj),
        0xEA000000 | (((item_jump - (item_start + 0x34 + 8)) // 4) & 0xFFFFFF),
        PROJECTILE_MOVE_ID,
        power_abs,
    ]
    return b"".join(struct.pack("<I", w) for w in words)


def _apply_rock_projectile_effects(rom: NintendoDSRom) -> dict[str, Any]:
    patched: list[dict[str, Any]] = []
    for path in ITEM_CD_PATHS:
        if path not in rom.filenames:
            continue
        cd = DataCDHandler.deserialize(rom.getFileByName(path))
        for effect_id, item_id, power_abs in ROCK_TO_PROJECTILE:
            stub = _make_projectile_item_stub(item_id=item_id, power_abs=power_abs)
            cd.set_effect_code(effect_id, stub)
            patched.append(
                {
                    "path": path,
                    "effect_id": effect_id,
                    "item_id": item_id,
                    "power_abs": f"0x{power_abs:X}",
                    "bytes": len(stub),
                }
            )
        rom.setFileByName(path, DataCDHandler.serialize(cd))
    return {"effects": patched}


def apply_damage_formula_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    profile: dict[str, Any],
    rom: NintendoDSRom,
    config,
    armips_exe: Path,
    state: BuildState | None,
    prior_hook_sites: set[int],
    rom_in: Path | None = None,
) -> AppliedModule:
    del rom_in
    comps = manifest.get("components") or {}
    data: list[dict[str, Any]] = []

    # 1) Main-series CalcDamage base (ov36 cave + ov29 hook)
    asm_record, rom = apply_asm_single(
        module_id=module_id,
        module_dir=module_dir,
        manifest=manifest,
        profile=profile,
        rom=rom,
        config=config,
        armips_exe=armips_exe,
        prior_hook_sites=prior_hook_sites,
        state=state,
    )
    data.append({"asm": "CalcDamage main-series base"})

    # 2) Gen9 waza powers
    if comps.get("waza_gen9_power", True):
        data.append({"waza_gen9_power": _apply_waza_powers(rom, module_dir, manifest)})

    # 3) Power stars UI (arm9; half star = vanilla [M:R1] like IQ)
    if comps.get("power_stars_scale", True):
        stars_manifest = {
            "version": manifest.get("version", 1),
            "data": {
                "power_stars_asm": comps.get("power_stars_asm", "power_stars/main.asm"),
            },
            "asm": {"entry": comps.get("power_stars_asm", "power_stars/main.asm")},
        }
        stars = apply_power_stars_scale_module(
            module_id=f"{module_id}:power_stars",
            module_dir=module_dir,
            manifest=stars_manifest,
            rom=rom,
            armips=armips_exe,
        )
        data.extend(stars.data or [])

    # 4) Technician threshold 60
    if comps.get("technician_threshold", True):
        tech_manifest = {
            "version": manifest.get("version", 1),
            "data": {
                "file_offset": int(comps.get("technician_file_offset", 0x7ADC)),
                "old_value": int(comps.get("technician_old", 4)),
                "new_value": int(comps.get("technician_new", 60)),
            },
        }
        tech = apply_technician_threshold_module(
            module_id=f"{module_id}:technician",
            module_dir=module_dir,
            manifest=tech_manifest,
            rom=rom,
        )
        data.extend(tech.data or [])

    # 5) Regular attack effect args (P + 0.25x)
    if comps.get("regular_attack", True):
        data.append({"regular_attack": _apply_regular_attack(rom)})

    # 6) Projectile post-CalcDamage 1.0x
    if comps.get("projectile_mult", True):
        data.append({"projectile_mult": _apply_projectile_mult(rom)})

    # 7) Super-effective type matchup 1.4 → 1.5
    if comps.get("super_effective", True):
        data.append({"super_effective": _apply_super_effective_mult(rom, config)})

    # 8) Throwable ov10 BP table (Gen9-scale)
    if comps.get("throwable_ov10", True):
        data.append({"throwable_ov10": _apply_throwable_ov10(rom, module_dir, manifest)})

    # 9) Geo Pebble / Gravelerock / Rare Fossil: fixed → DealDamageProjectile
    if comps.get("rock_projectile_effects", True):
        data.append({"rock_projectile_effects": _apply_rock_projectile_effects(rom)})

    # 10) Psywave / Present / Magnitude / Natural Gift variable powers
    if comps.get("variable_power", True):
        data.append({"variable_power": _apply_variable_power(rom, config)})

    return AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=list(asm_record.caves),
        hooks=list(asm_record.hooks),
        data=data,
    )
