#!/usr/bin/env python3
"""Apply better_food module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.apply_module import apply_module, verify_module_applied


def main() -> None:
    default_in = REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv
    rom_in = Path(args[0]) if len(args) > 0 else default_in
    rom_out = (
        Path(args[1])
        if len(args) > 1
        else REPO / "PatchTesting" / "Export Rom" / "Explorers of Alpha_Vanilla+better_food.nds"
    )
    state_path = Path(args[2]) if len(args) > 2 else rom_out.with_suffix(".state.json")

    if not rom_in.is_file():
        raise SystemExit(f"input ROM not found: {rom_in}")
    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())

    state = apply_module(
        "better_food",
        rom_out if rom_out.exists() else rom_in,
        rom_out,
        state_path=state_path,
        force_reapply=force,
    )
    verify_module_applied(rom_out, ROOT / "better_food", state)
    mod = state.get_module("better_food")
    print(f"Applied better_food -> {rom_out}")
    if mod:
        for cave in mod.caves:
            print(f"  cave {cave.overlay} file {cave.file_offset:#x} ram {cave.load_address:#x}")


if __name__ == "__main__":
    main()
