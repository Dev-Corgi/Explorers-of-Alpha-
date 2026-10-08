#!/usr/bin/env python3
"""Report provably-safe cave space across ov29, ov36, arm9 (vanilla + patched)."""
from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
VANILLA = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
PATCHED = ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds"
STATE = ROOT / "Export Rom" / "full_stack.state.json"

OV29_LOAD = 0x022DC240
OV36_LOAD = 0x023A7080
ARM9_LOAD = 0x02000000

START_MFUNC_RAM = 0x02330134
END_MFUNC_RAM = 0x023326CC
START_MFUNC_FILE = START_MFUNC_RAM - OV29_LOAD
END_MFUNC_FILE = END_MFUNC_RAM - OV29_LOAD

COT_COMMON_RAM = 0x023D7FF0
COT_COMMON_SIZE = 0x8010


@dataclass
class Gap:
    overlay: str
    file_start: int
    file_end: int
    load_start: int
    load_end: int
    zone: str

    @property
    def size(self) -> int:
        return self.file_end - self.file_start


def find_zero_gaps(data: bytes, load: int, overlay: str, *, min_size: int = 64, align: int = 4) -> list[Gap]:
    gaps: list[Gap] = []
    i = 0
    n = len(data)
    while i < n:
        if data[i] != 0:
            i += 1
            continue
        j = i
        while j < n and data[j] == 0:
            j += 1
        s = (i + align - 1) // align * align
        e = j
        if e - s >= min_size:
            la = load + s
            le = load + e
            if overlay == "ov29":
                if le <= START_MFUNC_RAM:
                    zone = "pre-StartMFunc"
                elif la >= END_MFUNC_RAM:
                    zone = "post-EndMFunc"
                else:
                    zone = "StartMFunc-FORBIDDEN"
            else:
                zone = "free"
            gaps.append(Gap(overlay, s, e, la, le, zone))
        i = j
    return gaps


def load_caves(state_path: Path) -> list[dict]:
    if not state_path.is_file():
        return []
    state = json.loads(state_path.read_text())
    out = []
    for mod in state["applied"]:
        for c in mod.get("caves", []):
            out.append({**c, "module": mod["id"]})
    return out


def cave_ranges(caves: list[dict], overlay: str) -> list[tuple[int, int, str]]:
    return [
        (c["file_offset"], c["file_offset"] + c["size"], c["module"])
        for c in caves
        if c["overlay"] == overlay
    ]


def subtract_claimed(gaps: list[Gap], claimed: list[tuple[int, int, str]]) -> list[Gap]:
    """Remove portions of gaps already used by patched caves."""
    out: list[Gap] = []
    for g in gaps:
        parts = [(g.file_start, g.file_end)]
        for cs, ce, _ in claimed:
            new_parts = []
            for ps, pe in parts:
                if ce <= ps or cs >= pe:
                    new_parts.append((ps, pe))
                    continue
                if ps < cs:
                    new_parts.append((ps, cs))
                if ce < pe:
                    new_parts.append((ce, pe))
            parts = new_parts
        for ps, pe in parts:
            if pe - ps >= 64:
                out.append(
                    Gap(g.overlay, ps, pe, g.load_start + (ps - g.file_start), g.load_start + (pe - g.file_start), g.zone)
                )
    return out


def report_overlay(name: str, data: bytes, load: int, caves: list[dict], *, extra_forbidden: list[tuple[int, int]] | None = None) -> None:
    print(f"\n{'=' * 72}")
    print(f"{name.upper()}  load={load:#x}  file_size={len(data):#x} ({len(data):,} B)")
    print(f"{'=' * 72}")

    gaps = find_zero_gaps(data, load, name)
    forbidden = extra_forbidden or []
    safe = [g for g in gaps if g.zone != "StartMFunc-FORBIDDEN"]
    forbidden_gaps = [g for g in gaps if g.zone == "StartMFunc-FORBIDDEN"]

    claimed = cave_ranges(caves, name)
    if claimed:
        print("\n  Patched caves (file ranges):")
        for cs, ce, mod in sorted(claimed):
            print(f"    {mod:18} [{cs:#x}..{ce:#x}) = {ce - cs} B")

    safe_free = subtract_claimed(safe, claimed)

    by_zone: dict[str, list[Gap]] = {}
    for g in safe_free:
        by_zone.setdefault(g.zone, []).append(g)

    total_safe = sum(g.size for g in safe_free)
    print(f"\n  SAFE zero gaps (excl. StartMFunc): {len(safe_free)} runs, {total_safe:,} B total")
    for zone in sorted(by_zone):
        zs = sum(g.size for g in by_zone[zone])
        print(f"    [{zone}] {zs:,} B in {len(by_zone[zone])} run(s)")
        for g in sorted(by_zone[zone], key=lambda x: -x.size)[:5]:
            print(f"      file [{g.file_start:#x}..{g.file_end:#x}) {g.size:,} B  RAM [{g.load_start:#x}..{g.load_end:#x})")

    if forbidden_gaps:
        fz = sum(g.size for g in forbidden_gaps)
        print(f"\n  FORBIDDEN (StartMFunc repack): {fz:,} B at file [{START_MFUNC_FILE:#x}..{END_MFUNC_FILE:#x})")
        print("    Looks like zero padding in vanilla but RAM is repacked in battle.")

    if forbidden:
        for fs, fe in forbidden:
            print(f"\n  Note: manual forbidden [{fs:#x}..{fe:#x})")

    # tail append headroom
    if name == "ov29":
        ram_end = load + len(data)
        print(f"\n  Tail append: file end RAM = {ram_end:#x} (current file size = load + file_offset)")
        print(f"    Unlimited growth possible via ramSize bump IF nothing else maps this RAM.")


def report_ov36_cot(data: bytes, load: int) -> None:
    off = COT_COMMON_RAM - load
    end = off + COT_COMMON_SIZE
    if off < 0 or off >= len(data):
        print("\n  c-of-time common slot: OUT OF ov36 file range")
        return
    chunk = data[off:min(end, len(data))]
    used_end = 0
    for i in range(len(chunk) - 1, -1, -1):
        if chunk[i] != 0:
            used_end = i + 1
            break
    free = COT_COMMON_SIZE - used_end
    nz = sum(1 for b in chunk if b)
    print(f"\n  c-of-time common slot: RAM [{COT_COMMON_RAM:#x}..{COT_COMMON_RAM + COT_COMMON_SIZE:#x})")
    print(f"    file [{off:#x}..{end:#x})  used~{used_end:,} B  free~{free:,} B  nonzero={100 * nz / len(chunk):.1f}%")


def stack_need() -> int:
    return 768 + 896 + 512 + 768 + 2300 + 2048 + 768 + 16 * 6  # gaps


def main() -> None:
    caves = load_caves(STATE)

    print("=" * 72)
    print("SAFE CAVE SPACE REPORT (US EoS Alpha vanilla base)")
    print("=" * 72)
    print(f"full_stack ov29 need (6 modules + gaps): ~{stack_need():,} B ({stack_need():#x})")

    for label, path in [("VANILLA", VANILLA), ("PATCHED full_stack", PATCHED)]:
        if not path.is_file():
            print(f"\nMissing {path}")
            continue
        rom = NintendoDSRom(path.read_bytes())
        table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
        c = caves if label != "VANILLA" else []

        print(f"\n\n{'#' * 72}")
        print(f"# {label}: {path.name}")
        print(f"{'#' * 72}")

        ov29 = rom.files[table[29].fileID]
        report_overlay("ov29", ov29, table[29].ramAddress, c)
        print(f"  ov29 ramSize table entry: {table[29].ramSize:#x}")

        if len(table) > 36 and table[36].fileID < len(rom.files):
            ov36 = rom.files[table[36].fileID]
            report_overlay("ov36", ov36, table[36].ramAddress, c)
            report_ov36_cot(ov36, table[36].ramAddress)
            print("\n  ov36 role: ExtraSpace overlay (SkyTemple/c-of-time). Loaded when game loads ov36.")
            print("  Largest hole is linker padding, NOT runtime-allocated unless you add a section.")
        else:
            print("\n  overlay 36: NOT PRESENT in this ROM")

        arm9 = bytes(rom.arm9)
        report_overlay("arm9", arm9, ARM9_LOAD, c)

    # invasion check on patched
    if PATCHED.is_file() and STATE.is_file():
        print(f"\n\n{'=' * 72}")
        print("PATCHED: cave vs vanilla live-code check")
        print("=" * 72)
        vrom = NintendoDSRom(VANILLA.read_bytes())
        prom = NintendoDSRom(PATCHED.read_bytes())
        vtable = loadOverlayTable(vrom.arm9OverlayTable, lambda _i, _n: b"")
        ptable = loadOverlayTable(prom.arm9OverlayTable, lambda _i, _n: b"")
        vov29 = vrom.files[vtable[29].fileID]
        pov29 = prom.files[ptable[29].fileID]

        for c in caves:
            if c["overlay"] != "ov29":
                continue
            fo, sz = c["file_offset"], c["size"]
            if fo + sz <= len(vov29):
                nz = sum(1 for b in vov29[fo : fo + sz] if b)
                kind = "vanilla padding" if nz == 0 else f"VANILLA LIVE CODE ({nz}/{sz} nz)"
            else:
                kind = "tail append (beyond vanilla file)"
            # overlap StartMFunc?
            la, le = c["load_address"], c["load_address"] + c["size"]
            sm = la < END_MFUNC_RAM and le > START_MFUNC_RAM
            print(f"  {c['module']:18} [{fo:#x}..{fo+sz:#x}) la=[{la:#x}..{le:#x})")
            print(f"    site: {kind}  StartMFunc={'YES-CRASH RISK' if sm else 'no'}")

        # tail extension
        print(f"\n  ov29 vanilla size: {len(vov29):#x}  patched: {len(pov29):#x}  grown: {len(pov29)-len(vov29):+#x}")
        print(f"  patched ramSize: {ptable[29].ramSize:#x}  vanilla ramSize: {vtable[29].ramSize:#x}")


if __name__ == "__main__":
    main()
