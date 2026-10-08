#!/usr/bin/env python3
"""Verify ARM9 cave layout in a stacked true_patches export."""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

REPO = Path(__file__).resolve().parent.parent
SPINDA_CODE = 0x94624
SPINDA_END = 0x94AE8


def verify(rom_path: Path, state_path: Path) -> bool:
    st = json.loads(state_path.read_text())
    arm9 = NintendoDSRom(rom_path.read_bytes()).arm9
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    print(f"=== {rom_path.name} ===")
    ranges: list[tuple[int, int, str]] = []
    ok = True
    for mod in st["applied"]:
        for c in mod.get("caves", []):
            if c.get("overlay") != "arm9":
                continue
            s, e = c["file_offset"], c["file_offset"] + c["size"]
            used_end = s
            for off in range(e - 4, s - 1, -4):
                if any(arm9[off : off + 4]):
                    used_end = off + 4
                    break
            print(
                f"  {mod['id']:14} {c['file_offset_hex']}-{e:#x} "
                f"alloc={c['size']} used~{used_end - s}"
            )
            if used_end > e:
                print(f"    OVERFLOW: used {used_end - s} > alloc {c['size']}")
                ok = False
            ranges.append((s, e, mod["id"]))

    ranges.sort()
    for i in range(1, len(ranges)):
        if ranges[i][0] < ranges[i - 1][1]:
            print(f"  OVERLAP: {ranges[i - 1][2]} vs {ranges[i][2]}")
            ok = False

    if not any(s == SPINDA_CODE for s, _, _ in ranges):
        print("  MISSING: spinda not @ 0x94624")
        ok = False
    else:
        print("  spinda@94624: OK")

    hook_checks = [
        ("ClearItemSlot", 0xD81C, 0xE3A01000),
        ("RemoveEquivNoHole", 0xF600, 0xE92D43F8),
        ("RemoveEquivVariant", 0xF694, 0xE92D43F8),
        ("RemoveEquivScan", 0xF558, 0xE92D43F8),
    ]
    for name, off, vanilla in hook_checks:
        w = struct.unpack_from("<I", arm9, off)[0]
        hooked = w != vanilla
        status = "OK" if hooked else "VANILLA"
        print(f"  hook {name}: {w:#010x} {status}")
        if not hooked:
            ok = False

    orb = next((r for r in ranges if r[2] == "orb_charges"), None)
    if orb:
        s, e, _ = orb
        ins = list(cs.disasm(arm9[s:e], 0x02000000 + s))
        if ins:
            last = ins[-1].address
            limit = 0x02000000 + e
            print(f"  orb disasm ends ~{last:#x} (limit {limit:#x})")
            if last >= limit:
                print("  ORB DISASM OVERFLOW")
                ok = False

    # spinda boot word region should not be zeroed mid-game code garbage
    boot = struct.unpack_from("<I", arm9, SPINDA_END)[0]
    print(f"  boot @ 94AE8 word: {boot:#010x}")

    print("  RESULT:", "SAFE" if ok else "ISSUES")
    return ok


if __name__ == "__main__":
    rom = REPO / "Export Rom/vanilla+stack/Explorers of Alpha_Vanilla+stack.nds"
    state = REPO / "Export Rom/vanilla+stack/build.state.json"
    if len(sys.argv) > 1:
        rom = Path(sys.argv[1])
        state = Path(sys.argv[2])
    sys.exit(0 if verify(rom, state) else 1)
