#!/usr/bin/env python3
"""Apply berry_boost module (overlay29 caves + item_cd + strings)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.apply_module import apply_module, verify_module_applied
from patch_engine.state import load_state


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply berry_boost module")
    parser.add_argument("rom_in", type=Path, nargs="?", default=None)
    parser.add_argument("rom_out", type=Path, nargs="?", default=None)
    parser.add_argument("--state", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    default_in = REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
    rom_in = args.rom_in or default_in
    rom_out = args.rom_out or REPO / "_true_patches_berry_boost.nds"
    state_path = args.state or rom_out.with_suffix(".state.json")

    if not rom_in.is_file():
        raise SystemExit(f"input ROM not found: {rom_in}")

    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())

    state = apply_module(
        "berry_boost",
        rom_out if rom_out.exists() else rom_in,
        rom_out,
        state_path=state_path,
        force_reapply=args.force,
    )
    verify_module_applied(rom_out, ROOT / "berry_boost", state)

    mod = state.get_module("berry_boost")
    print(f"Applied berry_boost -> {rom_out}")
    print(f"State -> {state_path}")
    if mod and mod.data:
        print(f"  layout: {mod.data[0].get('layout')}")
        for cave in mod.caves:
            print(f"  cave {cave.load_address:#x} (file {cave.file_offset:#x})")


if __name__ == "__main__":
    main()
