#!/usr/bin/env python3
"""Audit Alpha ROM: overlay 36 (ExtraSpace) vs ov29 tail gaps for patch placement."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

# US EoS (Alpha base uses same layout)
OV29_LOAD = 0x022DC240
OV36_LOAD = 0x023A7080

# c-of-time default common area (linker.ld)
COT_COMMON_RAM = 0x023D7FF0
COT_COMMON_SIZE = 0x8010

# true_patches first ov29 cave slot seen on Alpha / vanilla+stack builds
TRUE_PATCHES_OV29_HINT_FILE = 0x53EAC

# Typical true_patches ov29/arm9 cave sizes (from manifests / builds)
MODULE_BUDGET = [
    ("room_charge", "ov29", 2048),
    ("z_move_v2", "ov29", 2048),
    ("berry_boost", "ov29", 512),
    ("orb_charges", "ov29", 512),
    ("tm_read", "arm9", 256),
    ("orb_charges", "arm9", 640),
    ("z_move_v2", "arm9", 64),
    ("spinda_ev_v2", "arm9", 17024),
    ("combat stack (built)", "ov29", 6412),
]

# Minimum run length to report (ignore tiny nonzero speckle)
MIN_RUN = 16


@dataclass
class Region:
    file_start: int
    file_end: int
    kind: str  # "zero" | "used"
    load_start: int | None = None
    load_end: int | None = None

    @property
    def size(self) -> int:
        return self.file_end - self.file_start

    def load_range(self, base: int) -> tuple[int, int]:
        return (base + self.file_start, base + self.file_end)


def _overlay_entry(rom: NintendoDSRom, index: int):
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return table[index], rom.files[table[index].fileID]


def _is_zero_chunk(data: bytes, start: int, end: int) -> bool:
    chunk = data[start:end]
    return len(chunk) > 0 and not any(chunk)


def scan_runs(data: bytes, *, min_run: int = MIN_RUN) -> list[Region]:
    """Split binary into zero / used runs (byte granularity, merge short flips)."""
    n = len(data)
    if n == 0:
        return []

    def classify(off: int) -> str:
        end = min(off + min_run, n)
        return "zero" if _is_zero_chunk(data, off, end) else "used"

    runs: list[Region] = []
    i = 0
    while i < n:
        kind = classify(i)
        j = i + min_run
        while j < n and classify(j) == kind:
            j += min_run
        # extend to exact boundary
        while j < n and (data[j] == 0) == (kind == "zero"):
            j += 1
        runs.append(Region(i, j, kind))
        i = j
    return runs


def merge_runs(runs: list[Region]) -> list[Region]:
    if not runs:
        return []
    out = [runs[0]]
    for r in runs[1:]:
        if r.kind == out[-1].kind and r.file_start == out[-1].file_end:
            out[-1] = Region(out[-1].file_start, r.file_end, r.kind)
        else:
            out.append(r)
    return out


def largest_zero_gap(runs: list[Region], *, after_file: int = 0) -> Region | None:
    zeros = [r for r in runs if r.kind == "zero" and r.file_end > after_file]
    if not zeros:
        return None
    if after_file:
        zeros = [
            Region(max(r.file_start, after_file), r.file_end, "zero")
            for r in zeros
            if r.file_end > after_file
        ]
    return max(zeros, key=lambda r: r.size)


def nonzero_ratio(data: bytes, start: int, end: int) -> float:
    if end <= start:
        return 0.0
    chunk = data[start:end]
    return sum(1 for b in chunk if b) / len(chunk)


def last_nonempty_offset(data: bytes) -> int:
    for off in range(len(data) - 1, -1, -1):
        if data[off] != 0:
            return off + 1
    return 0


def audit_ov36(ov36: bytes, load: int) -> dict:
    runs = merge_runs(scan_runs(ov36))
    cot_file_off = COT_COMMON_RAM - load
    cot_end_off = cot_file_off + COT_COMMON_SIZE

    cot_in_range = 0 <= cot_file_off < len(ov36)
    cot_data = (
        ov36[cot_file_off : min(cot_end_off, len(ov36))]
        if cot_in_range
        else b""
    )
    cot_used_end = last_nonempty_offset(cot_data)
    cot_free = COT_COMMON_SIZE - cot_used_end if cot_in_range else 0

    used_regions = [r for r in runs if r.kind == "used"]
    zero_regions = [r for r in runs if r.kind == "zero"]

    return {
        "load": load,
        "file_size": len(ov36),
        "load_end": load + len(ov36),
        "runs": runs,
        "used_regions": used_regions,
        "zero_regions": zero_regions,
        "last_nonempty_file": last_nonempty_offset(ov36),
        "cot_file_off": cot_file_off if cot_in_range else None,
        "cot_ram": (COT_COMMON_RAM, COT_COMMON_RAM + COT_COMMON_SIZE),
        "cot_used_bytes": cot_used_end,
        "cot_free_bytes": max(0, cot_free),
        "cot_nonzero_pct": nonzero_ratio(ov36, max(0, cot_file_off), min(cot_end_off, len(ov36)))
        if cot_in_range
        else None,
    }


def audit_ov29_tail(ov29: bytes, load: int, hint_file: int) -> dict:
    runs = merge_runs(scan_runs(ov29))
    tail_runs = [r for r in runs if r.file_start >= hint_file]
    tail_zero = [r for r in tail_runs if r.kind == "zero"]
    tail_used = [r for r in tail_runs if r.kind == "used"]

    gap = largest_zero_gap(runs, after_file=hint_file)
    padding_from_hint = len(ov29) - hint_file
    hint_zero_pct = nonzero_ratio(ov29, hint_file, len(ov29))

    return {
        "load": load,
        "file_size": len(ov29),
        "hint_file": hint_file,
        "hint_load": load + hint_file,
        "tail_padding_bytes": padding_from_hint,
        "tail_nonzero_pct": 100.0 * hint_zero_pct,
        "tail_zero_pct": 100.0 * (1.0 - hint_zero_pct),
        "largest_zero_gap": gap,
        "tail_zero_regions": tail_zero,
        "tail_used_regions": tail_used,
        "last_nonempty_file": last_nonempty_offset(ov29),
    }


def fmt_region(r: Region, load: int | None) -> str:
    if load is not None:
        ls, le = r.load_range(load)
        return (
            f"  file {r.file_start:#10x}-{r.file_end:#10x}  ({r.size:6} B)  "
            f"RAM {ls:#x}-{le:#x}"
        )
    return f"  file {r.file_start:#10x}-{r.file_end:#10x}  ({r.size:6} B)"


def print_report(rom_path: Path, *, hint: int) -> int:
    rom = NintendoDSRom(rom_path.read_bytes())
    overlays = rom.loadArm9Overlays()
    has_ov36 = 36 in overlays

    ov29_entry, ov29 = _overlay_entry(rom, 29)
    ov29_load = ov29_entry.ramAddress

    print("=" * 76)
    print(f"PATCH PLACEMENT AUDIT - {rom_path.name}")
    print("=" * 76)
    print(f"ROM size: {len(rom.save()):,} bytes")
    print(f"ExtraSpace (overlay 36 present): {has_ov36}")

    # --- ov36 ---
    print("\n" + "=" * 76)
    print("1) OVERLAY 36 (ExtraSpace)")
    print("=" * 76)
    if not has_ov36:
        print("  overlay 36 NOT in ROM - ExtraSpace not applied.")
        ov36_info = None
    else:
        ov36_entry, ov36 = _overlay_entry(rom, 36)
        ov36_load = ov36_entry.ramAddress
        ov36_info = audit_ov36(ov36, ov36_load)
        print(f"  Table RAM: {ov36_load:#x}  file size: {ov36_info['file_size']:,} B")
        print(f"  Last nonzero byte @ file {ov36_info['last_nonempty_file']:#x}")
        print(
            f"  c-of-time common slot: RAM {ov36_info['cot_ram'][0]:#x}-"
            f"{ov36_info['cot_ram'][1]:#x}  "
            f"(file {ov36_info['cot_file_off']:#x}, {COT_COMMON_SIZE} B)"
        )
        print(
            f"    used ~{ov36_info['cot_used_bytes']} B  "
            f"free ~{ov36_info['cot_free_bytes']} B  "
            f"nonzero {ov36_info['cot_nonzero_pct'] * 100:.1f}%"
        )
        print("\n  Used regions (non-zero runs >= 16 B):")
        for r in ov36_info["used_regions"]:
            if r.size >= 64:
                print(fmt_region(r, ov36_load))
        print("\n  Largest zero gaps in ov36:")
        for r in sorted(ov36_info["zero_regions"], key=lambda x: -x.size)[:8]:
            print(fmt_region(r, ov36_load))

    # --- ov29 tail ---
    print("\n" + "=" * 76)
    print(f"2) OV29 TAIL (from file hint {hint:#x} = true_patches first cave slot)")
    print("=" * 76)
    ov29_info = audit_ov29_tail(ov29, ov29_load, hint)
    print(f"  ov29 file size: {ov29_info['file_size']:,} B  RAM base {ov29_load:#x}")
    print(f"  Last nonzero @ file {ov29_info['last_nonempty_file']:#x}")
    print(
        f"  Region [{hint:#x}..end): {ov29_info['tail_padding_bytes']:,} B  "
        f"~{ov29_info['tail_zero_pct']:.1f}% zero / {ov29_info['tail_nonzero_pct']:.1f}% nonzero"
    )
    gap = ov29_info["largest_zero_gap"]
    if gap:
        ls, le = gap.load_range(ov29_load)
        print(
            f"  Largest zero gap from hint: file {gap.file_start:#x}-{gap.file_end:#x} "
            f"({gap.size:,} B)  RAM {ls:#x}-{le:#x}"
        )
    if ov29_info["tail_used_regions"]:
        print("\n  Non-zero blocks in tail (Alpha / prior patch code?):")
        for r in ov29_info["tail_used_regions"]:
            if r.size >= 64:
                print(fmt_region(r, ov29_load))

    if ov29_info["tail_zero_regions"]:
        tail_zero_total = sum(r.size for r in ov29_info["tail_zero_regions"])
        print(f"\n  Total zero bytes in tail (all gaps): {tail_zero_total:,} B")
        print("  Zero gaps >= 512 B:")
        for r in sorted(ov29_info["tail_zero_regions"], key=lambda x: -x.size):
            if r.size >= 512:
                print(fmt_region(r, ov29_load))

    # --- arm9 high region (informational) ---
    arm9 = rom.arm9
    arm9_runs = merge_runs(scan_runs(arm9))
    arm9_high = [r for r in arm9_runs if r.file_start >= 0x90000]
    print("\n" + "=" * 76)
    print("3) ARM9 high file (>= 0x90000) - tm/orb/z/spinda caves")
    print("=" * 76)
    print(f"  arm9 size: {len(arm9):,} B")
    for r in arm9_high:
        if r.kind == "used" and r.size >= 128:
            print(f"  USED  file {r.file_start:#x}-{r.file_end:#x} ({r.size} B)")
        elif r.kind == "zero" and r.size >= 512:
            print(f"  ZERO  file {r.file_start:#x}-{r.file_end:#x} ({r.size} B)")

    # --- module budget ---
    print("\n" + "=" * 76)
    print("5) MODULE SIZE vs AVAILABLE SPACE")
    print("=" * 76)
    ov29_slot = gap.size if gap else 0
    ov36_big = (
        max(ov36_info["zero_regions"], key=lambda r: r.size).size if ov36_info else 0
    )
    for name, ov, size in MODULE_BUDGET:
        if ov == "ov29":
            fits_first = "YES" if size <= ov29_slot else "no"
            fits_ov36 = "yes (custom section)" if size <= ov36_big else "no"
            print(
                f"  {name:22} {size:6} B  first ov29 slot ({ov29_slot:,} B): {fits_first:3}  "
                f"ov36 max gap ({ov36_big:,} B): {fits_ov36}"
            )
        else:
            print(f"  {name:22} {size:6} B  (arm9 - see section 3)")

    # --- comparison ---
    print("\n" + "=" * 76)
    print("6) COMPARISON & RECOMMENDATION")
    print("=" * 76)

    ov29_gap_size = gap.size if gap else 0
    cot_free = ov36_info["cot_free_bytes"] if ov36_info else 0
    cot_total = COT_COMMON_SIZE if ov36_info else 0

    print(f"  ov29 largest zero gap (from {hint:#x}):  {ov29_gap_size:>8,} B")
    if has_ov36:
        print(f"  ov36 largest zero gap (custom linker):   {ov36_big:>8,} B")
    if ov36_info:
        print(f"  ov36 c-of-time common free (est.):       {cot_free:>8,} B / {cot_total:,} B")
        print(f"  ov36 total file unused tail:             {ov36_info['file_size'] - ov36_info['last_nonempty_file']:>8,} B")

    print()
    if not has_ov36:
        print("  -> Use ov29/arm9 dynamic caves (ExtraSpace absent).")
    elif cot_free >= 4096 and ov36_info["cot_nonzero_pct"] is not None and ov36_info["cot_nonzero_pct"] < 0.15:
        print("  -> ov36 c-of-time common area is mostly EMPTY.")
        print("     Good for: C item/move effects, SP >=100 (c-of-time workflow).")
        print("     Still need ov29/ov31/arm9 ASM hooks pointing into ov36.")
    elif cot_free < 2048 or (ov36_info and ov36_info["cot_nonzero_pct"] and ov36_info["cot_nonzero_pct"] > 0.5):
        print("  -> ov36 common area is heavily USED (Alpha / prior patches).")
        print("     Risky to add large blobs to ov36 without linker layout audit.")
        print("     Prefer ov29 tail gaps IF they are zero padding.")
    else:
        print("  -> ov36 partially used; small c-of-time additions OK, large combat bundles risky.")

    if ov29_gap_size >= 6000:
        print(
            f"  -> First ov29 slot [{hint:#x}-...) has {ov29_gap_size:,} B zero - "
            "fits combat stack (~6412 B) if placed here FIRST."
        )
        print(
            "     WARNING: Alpha code starts ~0x5648C (~120 KB block). "
            "Do NOT extend past that without relocating Alpha."
        )
    elif ov29_info["tail_used_regions"]:
        print("  -> ov29 tail has NON-ZERO blocks - may be Alpha code; verify before overwriting.")
    else:
        print("  -> ov29 tail space limited or fragmented.")

    if has_ov36 and ov36_big >= 32768:
        print(
            f"  -> ov36 has a {ov36_big:,} B hole (not c-of-time default slot) - "
            "needs custom linker.ld ORIGIN; good for large C blobs."
        )

    if has_ov36 and ov29_gap_size >= 4096:
        print("\n  HYBRID (typical Alpha stack):")
        print("    * Combat/menu hooks + large asm  -> ov29/ov31/arm9 (true_patches)")
        print("    * Berry/item logic / move effects -> ov36 C (c-of-time)")
    elif has_ov36 and cot_free < 2048 and ov29_gap_size >= 6000:
        print("\n  Prefer true_patches ov29/arm9 only - ov36 common area tight on this ROM.")

    print("\n" + "=" * 76)
    return 0


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    default_rom = root.parent / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
    alt_rom = root / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "rom",
        type=Path,
        nargs="?",
        default=default_rom if default_rom.is_file() else alt_rom,
    )
    parser.add_argument(
        "--ov29-hint",
        type=lambda s: int(s, 0),
        default=TRUE_PATCHES_OV29_HINT_FILE,
        help="First ov29 cave file offset (default 0x53EAC)",
    )
    args = parser.parse_args()
    if not args.rom.is_file():
        print(f"ROM not found: {args.rom}", file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(print_report(args.rom.resolve(), hint=args.ov29_hint))


if __name__ == "__main__":
    main()
