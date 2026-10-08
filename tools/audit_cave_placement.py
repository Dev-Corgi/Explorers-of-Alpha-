#!/usr/bin/env python3
"""Audit true_patches cave placement (overlap, footprint, vanilla padding)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / "true_patches"
import sys

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.cave_xref import format_xref_report, slot_has_vanilla_xrefs
from patch_engine.manifest import load_rom_profile

OV29_LOAD = 0x022DC240


def _overlay_bytes(rom_obj: NintendoDSRom, index: int) -> bytes:
    table = loadOverlayTable(rom_obj.arm9OverlayTable, lambda _i, _n: b"")
    return rom_obj.files[table[index].fileID]


def get_bin(rom_obj: NintendoDSRom, overlay: str) -> bytes:
    if overlay == "arm9":
        return rom_obj.arm9
    if overlay == "ov29":
        return _overlay_bytes(rom_obj, 29)
    if overlay == "ov31":
        return _overlay_bytes(rom_obj, 31)
    if overlay == "ov19":
        return _overlay_bytes(rom_obj, 19)
    if overlay == "ov36":
        return _overlay_bytes(rom_obj, 36)
    raise KeyError(overlay)


def last_used(data: bytes, start: int, end: int) -> int:
    used_end = start
    for off in range(end - 4, start - 1, -4):
        if any(data[off : off + 4]):
            used_end = off + 4
            break
    return used_end - start


def nonzero_count(data: bytes, start: int, end: int) -> int:
    return sum(1 for b in data[start:end] if b)


def audit(rom_path: Path, state_path: Path, vanilla_path: Path) -> int:
    st = json.loads(state_path.read_text())
    rom = NintendoDSRom(rom_path.read_bytes())
    van = NintendoDSRom(vanilla_path.read_bytes())

    caves: list[dict] = []
    for mod in st["applied"]:
        for c in mod.get("caves", []):
            caves.append(
                {
                    "module": mod["id"],
                    "overlay": c["overlay"],
                    "start": c["file_offset"],
                    "end": c["file_offset"] + c["size"],
                    "size": c["size"],
                    "load": c["load_address"],
                    "load_end": c["load_address"] + c["size"],
                }
            )

    overlap_issues: list[tuple] = []
    overflow_issues: list[dict] = []
    van_pre_issues: list[dict] = []

    print("=" * 72)
    print("1) CAVE-TO-CAVE OVERLAP (same overlay, file offset)")
    print("=" * 72)
    by_ov: dict[str, list] = {}
    for c in caves:
        by_ov.setdefault(c["overlay"], []).append(c)

    for ov, lst in sorted(by_ov.items()):
        lst = sorted(lst, key=lambda x: x["start"])
        print(
            f"\n[{ov}] patched size={len(get_bin(rom, ov)):,} "
            f"vanilla size={len(get_bin(van, ov)):,}"
        )
        prev = None
        for c in lst:
            tag = (
                f"  {c['module']:14} file {c['start']:#x}-{c['end']:#x} "
                f"({c['size']} B)  RAM {c['load']:#x}-{c['load_end']:#x}"
            )
            if prev:
                gap = c["start"] - prev["end"]
                if gap < 0:
                    tag += f"  *** OVERLAP {-gap} B with {prev['module']} ***"
                    overlap_issues.append((ov, prev["module"], c["module"], -gap))
                elif gap == 0:
                    tag += f"  (adjacent, gap=0 after {prev['module']})"
                else:
                    tag += f"  (gap={gap} B after {prev['module']})"
            print(tag)
            prev = c

    print("\n" + "=" * 72)
    print("2) ALLOCATED vs ACTUAL CODE FOOTPRINT (patched ROM)")
    print("=" * 72)
    for c in caves:
        data = get_bin(rom, c["overlay"])
        used = last_used(data, c["start"], c["end"])
        nz_in_alloc = nonzero_count(data, c["start"], c["end"])
        spill = 0
        if c["end"] < len(data):
            spill = nonzero_count(data, c["end"], min(len(data), c["end"] + 64))
        status = "OK"
        if used > c["size"]:
            status = "OVERFLOW alloc"
            overflow_issues.append(c)
        elif used == c["size"] and spill:
            status = f"WARN tail full + {spill} nz in next 64B"
        print(
            f"  {c['module']:14} {c['overlay']:4} alloc={c['size']:5} "
            f"used~={used:5} nz={nz_in_alloc:5} spill64={spill:3}  {status}"
        )

    print("\n" + "=" * 72)
    print("3) VANILLA PRE-PATCH: cave slots in zero/low-data padding?")
    print("=" * 72)
    for c in caves:
        vdata = get_bin(van, c["overlay"])
        if c["start"] + c["size"] > len(vdata):
            print(
                f"  {c['module']} {c['overlay']}: "
                f"*** extends past vanilla overlay ({len(vdata)}) ***"
            )
            van_pre_issues.append(c)
            continue
        nz = nonzero_count(vdata, c["start"], c["end"])
        pct = 100.0 * nz / c["size"]
        allowed = max(c["size"] // 8, 16)
        ok = nz <= allowed
        flag = "OK" if ok else "NOT ZERO PADDING"
        if not ok:
            van_pre_issues.append(c)
        print(
            f"  {c['module']:14} {c['overlay']:4} vanilla nz={nz:4}/{c['size']} "
            f"({pct:5.1f}%) allowed<={allowed:4}  {flag}"
        )

    print("\n" + "=" * 72)
    print("4) CROSS-CAVE SYMBOL REFS (RAM addresses inside another module cave)")
    print("=" * 72)
    ram_ranges = [(c["load"], c["load_end"], c["module"]) for c in caves if c["overlay"] == "ov29"]
    for mod in st["applied"]:
        data = mod.get("data")
        if not data:
            continue
        d = data[0] if isinstance(data, list) else data
        for k, v in d.items():
            if not (isinstance(v, str) and v.startswith("0x")):
                continue
            addr = int(v, 16)
            for lo, hi, owner in ram_ranges:
                if lo <= addr < hi:
                    if mod["id"] != owner:
                        print(f"  {mod['id']}.{k}={v} -> {owner} cave [{lo:#x}-{hi:#x}]")

    print("\n" + "=" * 72)
    print("5) ov29 padding before first cave")
    print("=" * 72)
    first_cave = min(c["start"] for c in caves if c["overlay"] == "ov29")
    for label, r in [("vanilla", van), ("patched", rom)]:
        ov = get_bin(r, "ov29")
        last_code = 0
        for off in range(first_cave - 1, -1, -1):
            if ov[off] != 0:
                last_code = off + 1
                break
        print(
            f"  [{label}] ov29 {len(ov):#x} last nz before {first_cave:#x} = "
            f"{last_code:#x} (padding {first_cave - last_code} B)"
        )

    print("\n" + "=" * 72)
    print("6) ARM9 cave chain")
    print("=" * 72)
    arm9 = rom.arm9
    arm_caves = sorted([c for c in caves if c["overlay"] == "arm9"], key=lambda x: x["start"])
    for i, c in enumerate(arm_caves):
        used = last_used(arm9, c["start"], c["end"])
        print(f"  {c['module']:14} {c['start']:#x}-{c['end']:#x} used~{used}/{c['size']}")
        if i:
            p = arm_caves[i - 1]
            if c["start"] < p["end"]:
                overlap_issues.append(("arm9", p["module"], c["module"], p["end"] - c["start"]))
                print(f"    *** OVERLAP with {p['module']}")

    print("\n" + "=" * 72)
    print("7) HOOK sites inside any cave RAM (should be none)")
    print("=" * 72)
    hook_in_cave = 0
    for mod in st["applied"]:
        for h in mod.get("hooks", []):
            site = h.get("site")
            if site is None:
                continue
            inside = [
                c["module"]
                for c in caves
                if c["load"] <= site < c["load_end"]
            ]
            if inside:
                hook_in_cave += 1
                print(f"  {mod['id']}.{h['name']} @ {site:#x} inside {inside}")

    print("\n" + "=" * 72)
    print("8) VANILLA XREFS INTO CAVE SLOTS (branch / pointer literals)")
    print("=" * 72)
    profile = load_rom_profile(REPO / "patch_engine", st.get("rom_profile", "us_vanilla"))
    xref_issues: list[dict] = []
    for c in caves:
        if c["overlay"] not in ("ov29", "ov36"):
            continue
        vdata = get_bin(van, c["overlay"])
        load = int(
            profile.get(
                "overlay29_load" if c["overlay"] == "ov29" else "overlay36_load",
                OV29_LOAD,
            )
        )
        ok, xrefs = slot_has_vanilla_xrefs(vdata, load, c["start"], c["size"])
        flag = "OK" if ok else "VANILLA XREFS"
        if not ok:
            xref_issues.append(c)
        print(f"  {c['module']:14} {c['overlay']:4} {flag}")
        if xrefs:
            print(
                format_xref_report(
                    xrefs,
                    overlay_load=load,
                    slot_file_offset=c["start"],
                    slot_size=c["size"],
                )
            )

    print("\n" + "=" * 72)
    print("SUMMARY (placement only)")
    print("=" * 72)
    print(f"  Cave overlaps:        {len(overlap_issues)}")
    print(f"  Footprint overflow:   {len(overflow_issues)}")
    print(f"  Vanilla not padding:  {len(van_pre_issues)}")
    print(f"  Hooks inside caves:   {hook_in_cave}")
    print(f"  Vanilla xrefs:        {len(xref_issues)}")

    ok = not (overlap_issues or overflow_issues or van_pre_issues or hook_in_cave or xref_issues)
    print("  VERDICT:", "CAVES PLACED OK" if ok else "CAVES PLACEMENT ISSUES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    rom_p = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "Export Rom/vanilla+stack_no_berry/Explorers of Alpha_Vanilla+stack_no_berry.nds"
    state_p = Path(sys.argv[2]) if len(sys.argv) > 2 else rom_p.parent / "build.state.json"
    van_p = Path(sys.argv[3]) if len(sys.argv) > 3 else REPO / "Vanilla Rom/Explorers of Alpha_Vanilla.nds"
    raise SystemExit(audit(rom_p, state_p, van_p))
