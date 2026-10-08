#!/usr/bin/env python3
"""Pre-patch audit: list xref-safe cave slots in vanilla overlay binaries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / "true_patches"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.cave_manifest import parse_forbidden_ranges
from patch_engine.cave_reservations import FileRange
from patch_engine.cave_xref import format_xref_report, scan_overlay_xrefs, scan_xrefs_into_range, slot_has_vanilla_xrefs
from patch_engine.manifest import load_rom_profile
from patch_engine.ov29_layout import ov29_forbidden_ranges, start_mfunc_forbidden

OV29_LOAD = 0x022DC240
OV36_LOAD = 0x023A7080


def _overlay_bytes(rom: NintendoDSRom, index: int) -> bytes:
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return rom.files[table[index].fileID]


def _parse_hex(value: str) -> int:
    return int(value, 16)


def audit_slots(
    *,
    vanilla_path: Path,
    overlay: str,
    need: int,
    preferred: list[int],
    extra_forbidden: list[FileRange],
) -> int:
    rom = NintendoDSRom(vanilla_path.read_bytes())
    profile = load_rom_profile(REPO / "patch_engine", "us_vanilla")

    if overlay in ("ov29", "overlay29"):
        data = _overlay_bytes(rom, 29)
        load = int(profile.get("overlay29_load", OV29_LOAD))
        forbidden = ov29_forbidden_ranges(None, extra=extra_forbidden)
    elif overlay in ("ov36", "overlay36"):
        data = _overlay_bytes(rom, 36)
        load = int(profile.get("overlay36_load", OV36_LOAD))
        forbidden = list(extra_forbidden)
    else:
        raise SystemExit(f"unsupported overlay: {overlay}")

    print("=" * 72)
    print(f"VANILLA CAVE SLOT AUDIT  overlay={overlay}  need={need}  file_size={len(data):#x}")
    print(f"  load={load:#x}  forbidden_blocks={len(forbidden)}")
    print("=" * 72)

    print("\n--- preferred slots ---")
    any_safe_preferred = False
    for start in preferred:
        blocked = next((b for b in forbidden if start < b.end and start + need > b.start), None)
        if blocked:
            print(f"\n{start:#x}: BLOCKED forbidden [{blocked.start:#x},{blocked.end:#x})")
            continue
        if start + need > len(data):
            print(f"\n{start:#x}: TAIL (extends past file end by {start + need - len(data)} B)")
        ok, xrefs = slot_has_vanilla_xrefs(data, load, start, need)
        print()
        print(format_xref_report(xrefs, overlay_load=load, slot_file_offset=start, slot_size=need))
        print(f"  VERDICT: {'PATCH OK' if ok else 'DO NOT PATCH'}")
        if ok:
            any_safe_preferred = True

    all_xrefs = scan_overlay_xrefs(data, load)
    referenced: set[int] = {xref.target_file_offset_for(load) for xref in all_xrefs}

    def slot_is_safe(start: int) -> bool:
        if any(start <= off < start + need for off in referenced):
            return False
        return True

    print("\n--- all xref-safe zero runs (no reserved modules) ---")
    safe_count = 0
    i = 0
    shown = 0
    while i < len(data):
        if data[i] != 0:
            i += 1
            continue
        j = i
        while j < len(data) and data[j] == 0:
            j += 1
        run_start = (i + 3) // 4 * 4
        max_start = j - need
        for start in range(run_start, max_start + 1, 4):
            blocked = any(start < b.end and start + need > b.start for b in forbidden)
            if not blocked and slot_is_safe(start):
                safe_count += 1
                if shown < 25:
                    shown += 1
                    print(
                        f"  [{start:#x},{start + need:#x}) RAM [{load + start:#x},{load + start + need:#x})"
                    )
        i = j
    if safe_count > shown:
        print(f"  ... {safe_count - shown} more xref-safe slot(s)")

    tail_start = (len(data) + 3) // 4 * 4
    tail_blocked = any(tail_start < b.end and tail_start + need > b.start for b in forbidden)
    tail_xrefs = scan_xrefs_into_range(
        data, load, range_file_start=tail_start, range_size=need
    )
    print("\n--- tail grow candidate (after file end) ---")
    print(f"  start={tail_start:#x} blocked={tail_blocked} vanilla_xrefs={len(tail_xrefs)}")
    if not tail_blocked and not tail_xrefs:
        safe_count += 1
        print(f"  [{tail_start:#x},{tail_start + need:#x}) RAM [{load + tail_start:#x},{load + tail_start + need:#x})  PATCH OK (grow)")

    print("\n" + "=" * 72)
    print(f"SUMMARY: {safe_count} xref-safe slot(s) found")
    if preferred and not any_safe_preferred:
        print("  preferred slot(s) are NOT safe - pick another slot or grow tail")
    print("=" * 72)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit xref-safe cave slots in vanilla ROM")
    parser.add_argument(
        "vanilla",
        nargs="?",
        type=Path,
        default=REPO / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds",
    )
    parser.add_argument("--overlay", default="ov29", help="ov29 or ov36")
    parser.add_argument("--need", type=_parse_hex, default="0x300", help="cave size bytes")
    parser.add_argument(
        "--preferred",
        type=_parse_hex,
        nargs="*",
        default=[0x3FBC8, 0x548A0],
        help="candidate file offsets to check first",
    )
    parser.add_argument(
        "--forbidden",
        type=_parse_hex,
        nargs="*",
        default=[],
        help="extra forbidden start..end pairs as hex start end start end",
    )
    args = parser.parse_args()

    extra: list[FileRange] = []
    if args.forbidden:
        if len(args.forbidden) % 2:
            raise SystemExit("--forbidden requires start/end pairs")
        for i in range(0, len(args.forbidden), 2):
            extra.append(FileRange(args.forbidden[i], args.forbidden[i + 1]))

    raise SystemExit(
        audit_slots(
            vanilla_path=args.vanilla,
            overlay=args.overlay,
            need=args.need,
            preferred=list(args.preferred),
            extra_forbidden=extra,
        )
    )


if __name__ == "__main__":
    main()
