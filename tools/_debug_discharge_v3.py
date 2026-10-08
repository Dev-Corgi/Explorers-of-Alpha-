#!/usr/bin/env python3
"""Debug room_charge_v3: verify move ID 435 = Discharge and patch landed correctly."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.data_cd.handler import DataCDHandler

ROOT = Path(__file__).resolve().parents[1]
VANILLA = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
PATCHED = ROOT / "Export Rom" / "Room_Charge_V3_Test" / "Explorers of Alpha_Vanilla+room_charge_v3.nds"

MOVE_EFFECT_EXEC_BASE = 0x02330134
MOVE_EFFECT_JUMP = 0x023326CC


def decode_bl(word: int, pc: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return pc + 8 + (imm << 2)


def move_names(rom: NintendoDSRom) -> list[str]:
    config = get_ppmdu_config_for_rom(rom)
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))
    block = config.string_index_data.string_blocks["Move Names"]
    return strings.strings[block.begin : block.end + 1]


def inspect_rom(label: str, path: Path) -> None:
    rom = NintendoDSRom(path.read_bytes())
    names = move_names(rom)
    wp = FileType.WAZA_P.deserialize(rom.getFileByName("BALANCE/waza_p.bin"))
    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/waza_cd.bin"))

    print(f"\n{'='*60}\n{label}: {path.name}\n{'='*60}")
    print(f"moves in waza_p: {len(wp.moves)}, effects in waza_cd: {cd.nb_effects()}")

    # Find Discharge by name
    discharge_indices = [i for i, n in enumerate(names) if n.strip().lower() == "discharge"]
    print(f"indices named 'Discharge': {discharge_indices}")

    for mid in discharge_indices[:3]:
        m = wp.moves[mid]
        sr = m.settings_range
        eff = cd.get_item_effect_id(mid)
        print(
            f"  [{mid}] {names[mid]!r}: move_id={m.move_id} power={m.base_power} "
            f"type={m.type} range={sr.range} effect={eff}"
        )

    print("\n--- hardcoded idx 435 ---")
    if 435 < len(names):
        m = wp.moves[435]
        sr = m.settings_range
        eff = cd.get_item_effect_id(435)
        print(
            f"  [435] {names[435]!r}: move_id={m.move_id} power={m.base_power} "
            f"type={m.type} range={sr.range} effect={eff}"
        )
        code = cd.get_effect_code(eff)
        print(f"  effect {eff} size={len(code)} hex={code.hex()}")
        if len(code) >= 20:
            w = struct.unpack_from("<I", code, 16)[0]
            tgt = decode_bl(w, MOVE_EFFECT_EXEC_BASE + 16)
            print(f"  bl target: {tgt:#x}")

    # TWO_TURN table
    ov = rom.loadArm9Overlays([29])[29].data
    tt_off = 0x02352AAC - 0x022DC240
    entries = []
    for i in range(20):
        move = struct.unpack_from("<H", ov, tt_off + i * 4)[0]
        status = struct.unpack_from("<H", ov, tt_off + i * 4 + 2)[0]
        if move == 0:
            break
        entries.append((move, status))
    print(f"\nTWO_TURN table: {entries}")
    tt_moves = {m for m, _ in entries}
    for idx in discharge_indices:
        print(f"  Discharge idx {idx} in TWO_TURN? {idx in tt_moves}")

    # Compare BALANCE vs UTILITY waza_cd for discharge index
    for idx in discharge_indices[:1]:
        for fpath in ["BALANCE/waza_cd.bin", "UTILITY/waza_cd.bin"]:
            if fpath in rom.filenames:
                cd2 = DataCDHandler.deserialize(rom.getFileByName(fpath))
                print(f"  {fpath} effect[{idx}] = {cd2.get_item_effect_id(idx)}")

    # waza_p2 if exists
    if "BALANCE/waza_p2.bin" in rom.filenames:
        wp2 = FileType.WAZA_P.deserialize(rom.getFileByName("BALANCE/waza_p2.bin"))
        for idx in discharge_indices[:1]:
            m2 = wp2.moves[idx]
            print(f"  waza_p2[{idx}] move_id={m2.move_id} power={m2.base_power}")


def main() -> None:
    inspect_rom("VANILLA", VANILLA)
    inspect_rom("PATCHED", PATCHED)

    # Search all moves with room range (3) and electric type (15?) for discharge-like
    rom = NintendoDSRom(VANILLA.read_bytes())
    names = move_names(rom)
    wp = FileType.WAZA_P.deserialize(rom.getFileByName("BALANCE/waza_p.bin"))
    print("\n--- room-range (3) electric-type moves ---")
    for i, m in enumerate(wp.moves):
        sr = m.settings_range
        if sr.range == 3 and m.type == 15 and m.category == 1:
            print(f"  [{i}] {names[i] if i < len(names) else '?'} power={m.base_power}")


if __name__ == "__main__":
    main()
