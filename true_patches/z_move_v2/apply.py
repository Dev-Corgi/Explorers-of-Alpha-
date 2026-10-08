#!/usr/bin/env python3
"""Apply z_move_v2 module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.apply_module import apply_module, verify_module_applied
from patch_engine.state import load_state


def main() -> None:
    default_in = REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
    rom_in = Path(sys.argv[1]) if len(sys.argv) > 1 else default_in
    rom_out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "_true_patches_z_move_v2.nds"
    state_path = Path(sys.argv[3]) if len(sys.argv) > 3 else rom_out.with_suffix(".state.json")

    if not rom_in.is_file():
        raise SystemExit(f"input ROM not found: {rom_in}")

    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())

    state = apply_module(
        "z_move_v2",
        rom_out if rom_out.exists() else rom_in,
        rom_out,
        state_path=state_path,
        force_reapply="--force" in sys.argv,
    )
    verify_module_applied(rom_out, ROOT / "z_move_v2", state)

    mod = state.get_module("z_move_v2")
    print(f"Applied z_move_v2 -> {rom_out}")
    print(f"State -> {state_path}")
    if mod and mod.data:
        print(f"  ov29 base: {mod.data[0].get('cave_base_ov29')}")
        print(f"  arm9 gauge: {mod.data[0].get('arm9_gauge_cave')}")


if __name__ == "__main__":
    main()
