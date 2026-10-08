#!/usr/bin/env python3
"""Map EoS move names to Gen 9 Accuracy. ROM-only names stay out of the JSON."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.common.util import read_u32
from skytemple_files.container.sir0.handler import Sir0Handler
from skytemple_files.data.waza_p._model import MOVE_ENTRY_BYTELEN
from skytemple_files.data.waza_p.handler import WazaPHandler
import skytemple_files.data.waza_p._model as waza_p_model

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
DATA = ROOT / "data"
SHOWDOWN = DATA / "showdown_moves.json"
OUT_ACC = DATA / "gen9_accuracies_by_move_id.json"
OUT_LEFT = DATA / "rom_only_accuracies.json"
OUT_OVERRIDE = DATA / "rom_accuracy_overrides.json"
VANILLA = REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
SHOWDOWN_URL = "https://play.pokemonshowdown.com/data/moves.json"

# EoS / SkyTemple names that do not alnum-match the Showdown key.
ALIASES = {
    "hijumpkick": "highjumpkick",
    "smellingsalt": "smellingsalts",
    "vicegrip": "visegrip",
    "softboiled": "softboiled",
    "solarbeam": "solarbeam",
    "ancientpower": "ancientpower",
    "dragonbreath": "dragonbreath",
    "dynamicpunch": "dynamicpunch",
    "bubblebeam": "bubblebeam",
    "featherdance": "featherdance",
    "grasswhistle": "grasswhistle",
    "poisonssting": "poisonsting",
    "thundershock": "thundershock",
    "thunderpunch": "thunderpunch",
    "selfdestruct": "selfdestruct",
    "extremespeed": "extremespeed",
    "judgement": "judgment",
}

# Always-hit in the main series: write 125 so MoveHitCheck skips the roll.
ALWAYS_HIT = 125


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _waza_move_count(raw: bytes) -> int:
    sir0 = Sir0Handler.deserialize(raw)
    move_ptr = read_u32(sir0.content, sir0.data_pointer)
    learn_ptr = read_u32(sir0.content, sir0.data_pointer + 4)
    span = learn_ptr - move_ptr
    count, rem = divmod(span, MOVE_ENTRY_BYTELEN)
    if count < 1 or rem >= 16:
        raise SystemExit(f"waza move table is not aligned: span={span}")
    return count


def _load_showdown() -> dict[str, int]:
    if not SHOWDOWN.is_file():
        DATA.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            SHOWDOWN_URL,
            headers={"User-Agent": "SkyTemple-true_patches/base_stats_speed"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            SHOWDOWN.write_bytes(resp.read())
    raw = json.loads(SHOWDOWN.read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for key, move in raw.items():
        if not isinstance(move, dict):
            continue
        acc = move.get("accuracy")
        if acc is True:
            value = ALWAYS_HIT
        elif isinstance(acc, int):
            value = acc
        else:
            continue
        if not (0 <= value <= 255):
            continue
        out[_norm(str(move.get("name") or key))] = value
        out[_norm(key)] = value
    return out


def _move_names(rom: NintendoDSRom) -> list[str]:
    cfg = get_ppmdu_config_for_rom(rom)
    from skytemple_files.data.str.handler import StrHandler

    strings = StrHandler.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"), string_encoding=cfg.string_encoding
    )
    block = cfg.string_index_data.string_blocks["Move Names"]
    return [strings.strings[block.begin + i] for i in range(block.end - block.begin)]


def build(rom_path: Path = VANILLA) -> dict:
    rom = NintendoDSRom.fromFile(str(rom_path))
    names = _move_names(rom)
    showdown = _load_showdown()
    raw = rom.getFileByName("BALANCE/waza_p.bin")
    waza_p_model.MOVE_COUNT = _waza_move_count(raw)
    waza = WazaPHandler.deserialize(raw)

    overrides: dict[int, int] = {}
    if OUT_OVERRIDE.is_file():
        overrides = {
            int(k): int(v)
            for k, v in json.loads(OUT_OVERRIDE.read_text(encoding="utf-8")).items()
        }

    matched: dict[str, int] = {}
    leftover: list[dict[str, object]] = []
    for mid, name in enumerate(names):
        if mid >= len(waza.moves):
            break
        clean = name.strip()
        if not clean or clean == "Nothing":
            continue
        if mid in overrides:
            continue
        key = ALIASES.get(_norm(clean), _norm(clean))
        acc_now = int(waza.moves[mid].accuracy)
        gen9 = showdown.get(key)
        if gen9 is None:
            leftover.append({"id": mid, "name": clean, "accuracy": acc_now})
            continue
        matched[str(mid)] = int(gen9)

    DATA.mkdir(parents=True, exist_ok=True)
    OUT_ACC.write_text(json.dumps(matched, indent=2) + "\n", encoding="utf-8")
    OUT_LEFT.write_text(
        json.dumps(leftover, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return {"matched": len(matched), "leftover": len(leftover), "names": len(names)}


if __name__ == "__main__":
    info = build()
    print(f"matched {info['matched']} leftover {info['leftover']} names {info['names']}")
