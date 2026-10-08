#!/usr/bin/env python3
"""Build Gen9 move-power map and patch Explorers of Alpha waza_p base_power."""

from __future__ import annotations

import csv
import io
import json
import re
import urllib.request
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.str.handler import StrHandler
from skytemple_files.data.waza_p.handler import WazaPHandler

REPO = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "SkyTemple-damage-formula/1.0"}


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def load_showdown_powers() -> dict[str, int]:
    text = _fetch(
        "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/moves.ts"
    ).decode("utf-8", errors="replace")
    powers: dict[str, int] = {}
    parts = re.split(r"\n\t([a-z0-9]+):\s*\{", text)
    for i in range(1, len(parts), 2):
        body = parts[i + 1] if i + 1 < len(parts) else ""
        m_pow = re.search(r"basePower:\s*(\d+)", body)
        m_name = re.search(r'name:\s*"([^"]+)"', body) or re.search(
            r"name:\s*'([^']+)'", body
        )
        if m_pow and m_name:
            powers[m_name.group(1)] = int(m_pow.group(1))
    return powers


def load_pokeapi_powers() -> dict[str, int]:
    """Fallback / fill gaps: pokeapi moves.csv + english names."""
    moves_csv = _fetch(
        "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/moves.csv"
    ).decode()
    names_csv = _fetch(
        "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/move_names.csv"
    ).decode()
    id_to_power: dict[int, int | None] = {}
    for row in csv.DictReader(io.StringIO(moves_csv)):
        pid = int(row["id"])
        raw = row["power"]
        id_to_power[pid] = int(raw) if raw not in ("", None) else None
    powers: dict[str, int] = {}
    for row in csv.DictReader(io.StringIO(names_csv)):
        if int(row["local_language_id"]) != 9:  # English
            continue
        pid = int(row["move_id"])
        powv = id_to_power.get(pid)
        if powv is not None and powv > 0:
            powers[row["name"]] = powv
    return powers


# ROM name -> Showdown / PokéAPI English name when they differ.
NAME_ALIASES: dict[str, str] = {
    "SmokeScreen": "Smokescreen",
    "Selfdestruct": "Self-Destruct",
    "Softboiled": "Soft-Boiled",
    "AncientPower": "Ancient Power",
    "BubbleBeam": "Bubble Beam",
    "DoubleSlap": "Double Slap",
    "DynamicPunch": "Dynamic Punch",
    "ExtremeSpeed": "Extreme Speed",
    "Faint Attack": "Feint Attack",
    "FeatherDance": "Feather Dance",
    "GrassWhistle": "Grass Whistle",
    "Hi Jump Kick": "High Jump Kick",
    "PoisonPowder": "Poison Powder",
    "Sand-Attack": "Sand Attack",
    "SolarBeam": "Solar Beam",
    "SonicBoom": "Sonic Boom",
    "ThunderPunch": "Thunder Punch",
    "ThunderShock": "Thunder Shock",
    "ViceGrip": "Vise Grip",
    "Vital Throw": "Vital Throw",
    "Conversion 2": "Conversion 2",
    "Lock-On": "Lock-On",
    "Will-O-Wisp": "Will-O-Wisp",
    "U-turn": "U-turn",
    "X-Scissor": "X-Scissor",
    "Mud-Slap": "Mud-Slap",
    "Double-Edge": "Double-Edge",
    "Wake-Up Slap": "Wake-Up Slap",
    "Baby-Doll Eyes": "Baby-Doll Eyes",
    "Forest's Curse": "Forest's Curse",
    "Land's Wrath": "Land's Wrath",
    "Nature's Madness": "Nature's Madness",
    "Multi-Attack": "Multi-Attack",
    "Judgment": "Judgment",
    "Roar of Time": "Roar of Time",
    "Spacial Rend": "Spacial Rend",
    "Electroweb": "Electroweb",
}


def normalize_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def build_lookup(powers: dict[str, int]) -> dict[str, int]:
    out: dict[str, int] = {}
    for name, powv in powers.items():
        out[normalize_key(name)] = powv
        out[name] = powv
    return out


# Showdown lists these as basePower 0 (scripted / variable). For dungeon use a
# Gen9-typical fixed stand-in (max or mid of the usual range).
VARIABLE_BP_FALLBACK: dict[str, int] = {
    "return": 102,
    "frustration": 102,
    "flail": 100,
    "reversal": 100,
    "lowkick": 80,
    "grassknot": 80,
    "heavyslam": 80,
    "heatcrash": 80,
    "electroball": 80,
    "gyroball": 80,
    "wringout": 120,
    "crushgrip": 120,
    "trumpcard": 80,
    "punishment": 60,
    "magnitude": 70,
    "spitup": 100,
    "naturalgift": 80,
    "present": 60,
    "beatup": 10,  # per hit base in modern gens varies; keep modest
}

# Alpha / PMD exclusives — Gen9 peer rebalance (also in exclusive_rebalance.json)
EXCLUSIVE_BP_OVERRIDE: dict[str, int] = {
    "mindcrush": 80,       # Psyshock
    "thunderenergy": 150,  # Eruption
    "sparklywind": 60,     # Silver Wind
    "teslacannon": 120,    # Zap Cannon
    "souleater": 75,       # Giga Drain
    "regularattack": 20,   # user
    "wideslash": 60,       # Brutal Swing
    "takeaway": 40,        # user (Mug)
    "bloopslash": 60,      # Lob mid physical
    "echo": 80,            # size-scaled ≈ Low Kick stand-in
    "projectile": 40,      # user
    "z-move": 100,         # Judgment
    "zmove": 100,
    "moonslash": 70,       # Night Slash / Psycho Cut
}


def resolve_power(rom_name: str, lookup: dict[str, int]) -> int | None:
    if not rom_name or rom_name == "Nothing":
        return None
    candidates = [rom_name]
    if rom_name in NAME_ALIASES:
        candidates.append(NAME_ALIASES[rom_name])
    # spaced/camel variants
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", rom_name)
    if spaced != rom_name:
        candidates.append(spaced)
    for c in candidates:
        if c in lookup:
            return lookup[c]
        k = normalize_key(c)
        if k in lookup:
            return lookup[k]
    return None


def finalize_power(rom_name: str, new_pow: int | None, old_pow: int) -> int | None:
    """Apply exclusive overrides, variable-BP fallbacks; never zero-out damaging moves."""
    key = normalize_key(rom_name)
    if key in EXCLUSIVE_BP_OVERRIDE:
        return EXCLUSIVE_BP_OVERRIDE[key]
    if new_pow is None:
        return None
    if new_pow == 0 and key in VARIABLE_BP_FALLBACK:
        return VARIABLE_BP_FALLBACK[key]
    if new_pow == 0 and old_pow > 0 and key in VARIABLE_BP_FALLBACK:
        return VARIABLE_BP_FALLBACK[key]
    # Fixed-damage / HP-halving / counter moves stay 0 (engine scripts).
    if new_pow == 0 and old_pow == 0:
        return 0
    if new_pow == 0 and old_pow > 0:
        # Unknown variable move: keep old rather than nuking dungeon damage.
        return old_pow
    return new_pow


def patch_waza(rom: NintendoDSRom, powers_by_id: dict[int, int], paths: list[str]) -> dict:
    changed = 0
    for path in paths:
        raw = rom.getFileByName(path)
        wp = WazaPHandler.deserialize(raw)
        for mid, new_pow in powers_by_id.items():
            if mid >= len(wp.moves):
                continue
            m = wp.moves[mid]
            if int(m.base_power) != new_pow:
                m.base_power = new_pow  # type: ignore[assignment]
                changed += 1
        rom.setFileByName(path, WazaPHandler.serialize(wp))
    return {"paths": paths, "slot_writes": changed}


def main() -> None:
    showdown = load_showdown_powers()
    pokeapi = load_pokeapi_powers()
    # Prefer Showdown (current competitive / latest), fill from PokéAPI.
    merged = dict(pokeapi)
    merged.update(showdown)
    lookup = build_lookup(merged)

    rom_path = REPO / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack_no_loader.nds"
    rom = NintendoDSRom.fromFile(str(rom_path))
    config = get_ppmdu_config_for_rom(rom)
    block = config.string_index_data.string_blocks["Move Names"]
    # Prefer ROM strings (patched), fall back unpacked
    str_raw = rom.getFileByName("MESSAGE/text_e.str")
    strs = StrHandler.deserialize(str_raw, string_encoding=config.string_encoding)

    wp = WazaPHandler.deserialize(rom.getFileByName("BALANCE/waza_p.bin"))
    powers_by_id: dict[int, int] = {}
    matched: list[tuple[int, str, int, int]] = []
    unmatched: list[tuple[int, str, int]] = []
    skipped_status: list[tuple[int, str]] = []

    for mid, move in enumerate(wp.moves):
        name = strs.strings[block.begin + mid]
        old = int(move.base_power)
        # Status / empty: leave 0 (and leave already-0 alone)
        if move.category == 2 or name in ("Nothing", ""):
            skipped_status.append((mid, name))
            continue
        resolved = resolve_power(name, lookup)
        key = normalize_key(name)
        if key in EXCLUSIVE_BP_OVERRIDE:
            new_pow = EXCLUSIVE_BP_OVERRIDE[key]
            powers_by_id[mid] = new_pow
            matched.append((mid, name, old, new_pow))
            continue
        if resolved is None:
            # Keep existing if no main-series mapping (PMD/Alpha exclusives)
            unmatched.append((mid, name, old))
            continue
        new_pow = finalize_power(name, resolved, old)
        if new_pow is None:
            unmatched.append((mid, name, old))
            continue
        powers_by_id[mid] = new_pow
        matched.append((mid, name, old, new_pow))

    report = {
        "source": "smogon/pokemon-showdown data/moves.ts (primary) + pokeapi moves.csv",
        "matched": len(matched),
        "unmatched_kept": [{"id": a, "name": b, "power": c} for a, b, c in unmatched],
        "status_skipped": len(skipped_status),
        "sample_changes": [
            {"id": a, "name": b, "old": c, "new": d}
            for a, b, c, d in matched
            if c != d
        ][:40],
        "changed_count": sum(1 for a, b, c, d in matched if c != d),
    }

    out_dir = REPO / "true_patches" / "waza_gen9_power"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "power_map.json").write_text(
        json.dumps(
            {str(mid): {"name": n, "old": o, "new": nw} for mid, n, o, nw in matched},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "unmatched.json").write_text(
        json.dumps(report["unmatched_kept"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    paths = ["BALANCE/waza_p.bin", "UTILITY/waza_p.bin"]
    # Also waza_p2 if present
    for extra in ("BALANCE/waza_p2.bin", "UTILITY/waza_p2.bin"):
        if extra in rom.filenames:
            paths.append(extra)

    meta = patch_waza(rom, powers_by_id, paths)
    rom_path.write_bytes(rom.save())
    fs = REPO / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds"
    fs.write_bytes(rom_path.read_bytes())

    # Persist as module data for rebuilds
    (out_dir / "gen9_powers_by_move_id.json").write_text(
        json.dumps({str(k): v for k, v in sorted(powers_by_id.items())}, indent=2),
        encoding="utf-8",
    )
    (out_dir / "last_report.json").write_text(
        json.dumps({**report, **meta, "rom": str(rom_path)}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2)[:4000])
    print("unmatched", len(unmatched), "changed", report["changed_count"])
    print("wrote", rom_path)


if __name__ == "__main__":
    main()
