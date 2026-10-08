#!/usr/bin/env python3
"""List all vanilla vs room_charge_v2 patch sites."""
from __future__ import annotations

import json
import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
LOAD = 0x022DC240

SYMBOLS = {
    0x02322B50: "ExecuteMoveEffectHook1",
    0x023238AC: "ExecuteMoveEffectHook2",
    0x022FE4C4: "ExecuteMonsterActionHook",
    0x023245A4: "IsChargingTwoTurnMove (entry)",
    0x0232461C: "IsChargingAnyTwoTurnMove (entry)",
    0x02324934: "DungeonRandOutcomeUserTargetInteraction (entry)",
    0x02330134: "StartMFunc",
    0x023326CC: "EndMFunc",
}


def diff_regions(a: bytes, b: bytes) -> list[tuple[int, int]]:
    regions: list[tuple[int, int]] = []
    i = 0
    n = min(len(a), len(b))
    while i < n:
        while i < n and a[i] == b[i]:
            i += 1
        if i >= n:
            break
        s = i
        while i < n and a[i] != b[i]:
            i += 1
        regions.append((s, i - 1))
    return regions


def word_kind(w: int) -> str:
    top = w >> 24
    if top == 0xEA:
        return "b"
    if top == 0xEB:
        return "bl"
    return f"data({w:#010x})"


def branch_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def main() -> None:
    van_path = ROOT / "true_patches/Vanilla Rom/Explorers of Alpha_Vanilla.nds"
    v2_path = (
        ROOT
        / "true_patches/Export Rom/vanilla+room_charge_v2/Explorers of Alpha_Vanilla+room_charge_v2.nds"
    )
    state_path = ROOT / "true_patches/Export Rom/vanilla+room_charge_v2/build.state.json"

    van = NintendoDSRom.fromFile(str(van_path))
    v2 = NintendoDSRom.fromFile(str(v2_path))
    table = loadOverlayTable(van.arm9OverlayTable, lambda _i, _n: b"")

    print("=== Whole ROM ===")
    if van.arm9 == v2.arm9:
        print("arm9: identical")
    else:
        print(f"arm9: {sum(1 for x, y in zip(van.arm9, v2.arm9) if x != y)} byte diffs")

    for ov_id, name in [(29, "overlay29"), (31, "overlay31")]:
        a = van.files[table[ov_id].fileID]
        b = v2.files[table[ov_id].fileID]
        if a == b:
            print(f"{name}: identical")
        else:
            print(f"{name}: {sum(1 for x, y in zip(a, b) if x != y)} byte diffs")

    vov = van.files[table[29].fileID]
    pov = v2.files[table[29].fileID]
    regions = diff_regions(vov, pov)

    print(f"\n=== overlay29 diff regions ({len(regions)} total) ===")
    for s, e in regions:
        ram_s = LOAD + s
        size = e - s + 1
        label = ""
        for addr, name in SYMBOLS.items():
            if ram_s <= addr <= LOAD + e:
                label = f"  [{name}]"
                break
        vw = struct.unpack_from("<I", vov, s)[0]
        pw = struct.unpack_from("<I", pov, s)[0]
        print(f"file {s:#x}..{e:#x} ({size}B)  RAM {ram_s:#x}..{LOAD + e:#x}{label}")
        if size <= 16:
            print(f"  van: {vov[s:e+1].hex()}")
            print(f"  v2:  {pov[s:e+1].hex()}")
        else:
            print(f"  first word: {vw:#010x} -> {pw:#010x} ({word_kind(vw)} -> {word_kind(pw)})")
            if word_kind(pw) in ("b", "bl"):
                tgt = branch_target(ram_s, pw)
                print(f"  branch target: {tgt:#x}")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    cave = state["applied"][0]["caves"][0]
    coff = cave["file_offset"]
    csize = cave["size"]

    print("\n=== Hook sites (from build state) ===")
    for h in state["applied"][0]["hooks"]:
        site = h["site"]
        off = site - LOAD
        vw = struct.unpack_from("<I", vov, off)[0]
        pw = struct.unpack_from("<I", pov, off)[0]
        print(f"{h['name']}")
        print(f"  RAM {site:#x}  vanilla {vw:#010x} ({word_kind(vw)}) -> patched {pw:#010x} ({word_kind(pw)})")
        if word_kind(pw) in ("b", "bl"):
            print(f"  -> {branch_target(site, pw):#x}  ({h['target_symbol']})")

    print("\n=== Cave injection ===")
    print(
        f"file {cave['file_offset_hex']} .. {cave['file_offset'] + csize:#x} "
        f"({csize}B reserved)"
    )
    print(f"RAM {cave['load_address_hex']} .. {cave['load_address'] + csize:#x}")
    cave_diff = sum(1 for i in range(coff, coff + csize) if vov[i] != pov[i])
    print(f"bytes changed inside cave: {cave_diff}")

    print("\n=== Diff outside cave + hooks ===")
    hook_offs = {h["site"] - LOAD for h in state["applied"][0]["hooks"]}
    other = []
    for s, e in regions:
        if coff <= s and e < coff + csize:
            continue
        if all(not (s <= off <= e) for off in hook_offs):
            other.append((s, e))
        elif s not in hook_offs:
            other.append((s, e))
    if not other:
        print("  none (only hooks + cave)")
    else:
        for s, e in other:
            print(f"  file {s:#x}..{e:#x} RAM {LOAD+s:#x}..{LOAD+e:#x}")


if __name__ == "__main__":
    main()
