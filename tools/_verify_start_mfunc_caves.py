#!/usr/bin/env python3
"""Verify ov29 caves and orb hooks stay outside StartMFunc."""
from __future__ import annotations

import json
import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
START_MFUNC_RAM = 0x02330134
END_MFUNC_RAM = 0x023326CC


def decode_branch(word: int, pc: int) -> int:
    imm24 = word & 0xFFFFFF
    if imm24 & 0x800000:
        imm24 -= 0x1000000
    return pc + 8 + imm24 * 4


def overlaps_start_mfunc(la: int, la_end: int) -> bool:
    return la < END_MFUNC_RAM and la_end > START_MFUNC_RAM


def main() -> None:
    state = json.loads((ROOT / "Export Rom" / "full_stack.state.json").read_text())
    rom = NintendoDSRom((ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = rom.files[table[29].fileID]
    ov29_load = table[29].ramAddress

    print(f"ov29 size={len(ov29):#x} ramSize={table[29].ramSize:#x}")
    print(f"StartMFunc RAM [{START_MFUNC_RAM:#x}..{END_MFUNC_RAM:#x})\n")

    bad = 0
    print("=== ov29 caves ===")
    for mod in state["applied"]:
        for cave in mod.get("caves", []):
            if cave["overlay"] != "ov29":
                continue
            la = cave["load_address"]
            la_end = la + cave["size"]
            hit = overlaps_start_mfunc(la, la_end)
            if hit:
                bad += 1
            print(
                f"  {mod['id']:18} file={cave['file_offset']:#x} "
                f"RAM=[{la:#x}..{la_end:#x}) {'INSIDE StartMFunc' if hit else 'OK'}"
            )

    print("\n=== orb_charges_v2 ov29 hook branch targets ===")
    orb = next(m for m in state["applied"] if m["id"] == "orb_charges_v2")
    cave_lo = orb["caves"][0]["load_address"]
    cave_hi = cave_lo + orb["caves"][0]["size"]
    for hook in orb["hooks"]:
        if hook.get("binary", "ov29") != "ov29":
            continue
        site = hook["site"]
        off = site - ov29_load
        if off < 0 or off + 4 > len(ov29):
            print(f"  {hook['name']:35} site {site:#x} out of ov29 range")
            bad += 1
            continue
        word = struct.unpack_from("<I", ov29, off)[0]
        target = decode_branch(word, site)
        in_sm = START_MFUNC_RAM <= target < END_MFUNC_RAM
        in_cave = cave_lo <= target < cave_hi
        if in_sm:
            bad += 1
        print(
            f"  {hook['name']:35} -> {target:#x} "
            f"StartMFunc={'YES' if in_sm else 'no'} orb_cave={'yes' if in_cave else 'NO'}"
        )

    print(f"\nVERDICT: {'FAIL' if bad else 'PASS'} ({bad} issue(s))")


if __name__ == "__main__":
    main()
