#!/usr/bin/env python3
"""Trace dungeon bag orb Use / Place / action-49 paths in EoS US ov29."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom
import pmdsky_debug_py.na as na

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROM = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost.nds"
)

OV29_LOAD = 0x022DC240

PATHS: list[tuple[str, str, int, str]] = [
    (
        "Bag submenu USE",
        "Player bag -> Use (menu_state+0xD2 == 1)",
        0x02310F40,
        "bl UseItem -> action resolver -> RunDungeonScript (orb effect e.g. Cleanse)",
    ),
    (
        "Bag submenu other",
        "Player bag -> Look / Place / etc. (D2 != 1)",
        0x02310FF0,
        "230FB90 or 230FC24 branch — not the primary Use path",
    ),
    (
        "Orb PLACE on floor",
        "Action 49 place branch",
        0x0230FD00,
        "230FC24 -> TryWarp (monster warp helper) + floor orb setup — NOT bag Use",
    ),
    (
        "Action 49 USE branch",
        "Category-9 default action 49",
        0x022FEF64,
        "22FEDBC -> UseItem (same script path as bag Use)",
    ),
    (
        "Alt UseItem + RemoveUsedItem",
        "231A9F8 item-use helper",
        0x0231AC48,
        "UseItem then RemoveUsedItem on success",
    ),
    (
        "ApplyItemEffect",
        "Effect bytecode (floor / AI / misc)",
        0x0231B68C,
        "NOT primary dungeon bag Use for orbs",
    ),
]


def arm_bl_target(pc: int, word: int) -> int | None:
    if (word & 0xFF000000) not in (0xEB000000, 0xEA000000):
        return None
    imm24 = word & 0xFFFFFF
    if imm24 & 0x800000:
        imm24 -= 1 << 24
    return (pc + 8 + (imm24 << 2)) & 0xFFFFFFFF


def disasm_line(ov: bytes, addr: int, n: int = 3) -> list[str]:
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    off = addr - OV29_LOAD
    return [
        f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}"
        for ins in md.disasm(ov[off : off + n * 4], addr)
    ]


def main() -> None:
    rom_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROM
    if not rom_path.is_file():
        raise SystemExit(f"ROM not found: {rom_path}")

    rom = NintendoDSRom(rom_path.read_bytes())
    ov = rom.loadArm9Overlays([29])[29].data

    cat = na.overlay29.data.ITEM_CATEGORY_ACTIONS
    off = cat.addresses[0]
    cat9_action = struct.unpack_from("<H", ov, off + 9 * 2)[0]

    print("=" * 72)
    print(f"ROM: {rom_path.name}")
    print("=" * 72)
    print(f"ITEM_CATEGORY_ACTIONS[9] (Orbs) default dungeon action: {cat9_action}")
    print()
    print(f"{'Path':<22} {'Site':<12} Description")
    print("-" * 72)
    for name, desc, site, note in PATHS:
        print(f"{name:<22} {site:08X}  {desc}")
        print(f"{'':22} {'':12} -> {note}")
        for line in disasm_line(ov, site):
            print(line)
        print()

    use_item = 0x02322374
    callers: list[int] = []
    for base in range(OV29_LOAD, OV29_LOAD + len(ov), 4):
        w = struct.unpack_from("<I", ov, base - OV29_LOAD)[0]
        if arm_bl_target(base, w) == use_item:
            callers.append(base)

    print("=" * 72)
    print(f"All bl UseItem ({use_item:08X}) callers: {len(callers)}")
    print("=" * 72)
    for c in callers:
        print(f"  {c:08X}")
        for line in disasm_line(ov, c - 8, 5):
            print(line)
        print()


if __name__ == "__main__":
    main()
