"""Normalize Alpha ability names without changing IDs or gameplay effects."""

import re

from patch_engine.korean_codec import build_str_file, parse_str_file

TEXT_PATH = "MESSAGE/text_e.str"
RENAMES = {
    12: ("Royal Majesty", "Multiscale"),
    15: ("Healthy Body", "Clear Body"),
    24: ("Adaptate", "Adaptability"),
    75: ("Strong Jaws", "Strong Jaw"),
    110: ("Solid Guard", "Filter"),
    139: ("Marvel Veil", "Fur Coat"),
    140: ("Wonder Veil", "Ice Scales"),
    142: ("Sky Pact", "Gale Wings"),
    148: ("Sound Waves", "Punk Rock"),
    153: ("Guiding Star", "Victory Star"),
    157: ("Overload", "Electromorphosis"),
    171: ("Hubris", "Grim Neigh"),
    178: ("Apex Aura", "Aura Break"),
    226: ("Curious Medecine", "Curious Medicine"),
}

EFFECT_DESCRIPTIONS = {
    24: "[CS:E]Adaptability[CR]: Same-type attacking\nmoves deal 1.7 times normal damage.",
    99: "[CS:E]Adaptability[CR]: Same-type attacking\nmoves deal 1.7 times normal damage.",
    142: "[CS:E]Gale Wings[CR]: Adds 2 calculated Speed\nstages while at full HP.",
    148: "[CS:E]Punk Rock[CR]: Sound moves deal 1.2\ntimes damage. Incoming sound move\ndamage is multiplied by 0.8.",
    171: "[CS:E]Grim Neigh[CR]: Defeating a foe with\nan attacking move raises Sp. Atk\nby 1 stage, once per action.",
    178: "[CS:E]Aura Break[CR]: Same-room Dark and\nFairy Auras reduce their move type's\ndamage to 0.8 instead of boosting it.\nMultiple holders do not stack.",
}


def normalize_strings(strings):
    starts = [i for i in range(len(strings) - 256)
              if strings[i] == b"Unknown" and strings[i + 1] == b"Stench"
              and strings[i + 125] == b"Illusion"]
    if len(starts) != 1:
        raise ValueError("balance_change: ambiguous/missing Alpha ability name block")
    start = starts[0]
    for ability_id, (old, new) in RENAMES.items():
        if strings[start + ability_id] not in (old.encode(), new.encode()):
            raise ValueError(f"balance_change: unexpected ability {ability_id} name")
    mapping = {old.encode(): new.encode() for old, new in RENAMES.values()}
    pattern = re.compile(rb"(?<![A-Za-z])(?:" + b"|".join(
        re.escape(old) for old in sorted(mapping, key=len, reverse=True)
    ) + rb")(?![A-Za-z])")
    result = [pattern.sub(lambda m: mapping[m[0]], text) for text in strings]
    for ability_id, description in EFFECT_DESCRIPTIONS.items():
        previous = result[start + 256 + ability_id]
        updated = description.encode("cp1252")
        if not previous.startswith(b"[CS:E]"):
            raise ValueError(f"balance_change: unexpected ability {ability_id} description")
        # Also update exact copies embedded in species help text.
        result = [text.replace(previous, updated) for text in result]
    return result, start


def patch_ability_names(rom):
    before = parse_str_file(rom.getFileByName(TEXT_PATH))
    after, start = normalize_strings(before)
    rom.setFileByName(TEXT_PATH, build_str_file(after))
    return {"ability_names": {"block_start": start,
            "changed_strings": sum(a != b for a, b in zip(before, after))}}


def verify_ability_names(rom):
    strings = parse_str_file(rom.getFileByName(TEXT_PATH))
    expected, _ = normalize_strings(strings)
    if expected != strings:
        raise AssertionError("balance_change: ability names not normalized")
