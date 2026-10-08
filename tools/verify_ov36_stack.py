#!/usr/bin/env python3
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

from ndspy.rom import NintendoDSRom
from skytemple_files.data.data_cd.handler import DataCDHandler

OV29 = 0x022DC240
OV36 = 0x023A7080
MOVE_EFFECT_EXEC = 0x02330134


def bl_target(data: bytes, site: int, load: int) -> int:
    w = struct.unpack_from("<I", data, site - load)[0]
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return site + 8 + imm * 4


def main() -> None:
    rom_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Export Rom/_full_stack_ov36.nds")
    state_path = rom_path.with_suffix(".state.json")
    rom = NintendoDSRom(rom_path.read_bytes())
    state = json.loads(state_path.read_text())

    rc = next(m for m in state["applied"] if m["id"] == "room_charge_v4")
    ov29_caves = [c for c in rc["caves"] if c["overlay"] == "ov29"]
    ov36_c = next(c for c in rc["caves"] if c["overlay"] == "ov36")
    ov29_entry_c = min(ov29_caves, key=lambda c: c["size"])
    ov29_table_c = max(ov29_caves, key=lambda c: c["file_offset"])
    entry = ov29_entry_c["load_address"]
    handler = ov36_c["load_address"]

    loader = next(m for m in state["applied"] if m["id"] == "overlay36_loader")
    loader_c = next(c for c in loader["caves"] if c["overlay"] == "ov29")
    prior = int(loader["data"][0]["PriorExecuteMoveEffectTarget"], 16)

    ov29 = rom.loadArm9Overlays()[29].data
    ov36 = rom.loadArm9Overlays()[36].data

    pool = struct.unpack_from("<I", ov29, 0x02324618 - OV29)[0]
    marker = bytes([151, 0, 2, 0, 100, 0, 3, 0])
    fo = ov29_table_c["file_offset"]
    found = None
    for off in range(fo, fo + ov29_table_c["size"] - 8):
        if ov29[off : off + 8] == marker:
            found = OV29 + off
            break

    print("=== room_charge_v4 ===")
    print(f"ov36 handler file {ov36_c['file_offset']:#x} ram {handler:#010x}")
    print(f"ov29 entry  file {ov29_entry_c['file_offset']:#x} ram {entry:#010x}")
    print(f"ov29 table  file {ov29_table_c['file_offset']:#x} ram {ov29_table_c['load_address']:#010x}")
    print(f"TWO_TURN table {found:#010x} pool {pool:#010x} match={pool == found}")

    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/waza_cd.bin"))
    eid = cd.get_item_effect_id(521)
    stub = cd.get_effect_code(eid)
    w = struct.unpack_from("<I", stub, 16)[0]
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    bl = MOVE_EFFECT_EXEC + 16 + 8 + imm * 4
    print(f"Discharge effect {eid} BL -> {bl:#010x} (entry {entry:#010x}) ok={bl == entry}")

    charge_ldr = struct.unpack_from("<I", ov36, handler - OV36 + 0x5C)[0]
    pool_off = handler - OV36 + 0x5C + 8 + (charge_ldr & 0xFFF)
    msg = struct.unpack_from("<I", ov36, pool_off)[0]
    print(f"Charge msg id {msg} (expect 3281)")

    print("=== ov36 chain ===")
    for mod in state["applied"]:
        for cave in mod.get("caves", []):
            if cave["overlay"] == "ov36":
                end = cave["file_offset"] + cave["size"]
                print(
                    f"  {mod['id']:18} [{cave['file_offset']:#7x}..{end:#x}) "
                    f"ram {cave['load_address']:#010x}"
                )

    print("=== overlay36_loader ===")
    print(f"loader cave ram {loader_c['load_address']:#010x}")
    print(f"PriorExecuteMoveEffectTarget {prior:#010x}")
    for site, name in [(0x02322B50, "Hook1"), (0x023238AC, "Hook2")]:
        target = bl_target(ov29, site, OV29)
        in_cave = loader_c["load_address"] <= target < loader_c["load_address"] + loader_c["size"]
        print(f"{name} BL -> {target:#010x} in loader cave={in_cave}")


if __name__ == "__main__":
    main()
