#!/usr/bin/env python3
"""Apply unified damage_formula module."""

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
    rom_out = Path(args[1]) if len(args) > 1 else REPO / "PatchTesting" / "Export Rom" / "Explorers of Alpha_Vanilla+damage_formula.nds"
    state_path = Path(args[2]) if len(args) > 2 else rom_out.with_suffix(".state.json")

    if not rom_in.is_file():
        raise SystemExit(f"input ROM not found: {rom_in}")

    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())

    state = apply_module(
        "damage_formula",
        rom_out if rom_out.exists() else rom_in,
        rom_out,
        state_path=state_path,
        force_reapply=force,
    )
    verify_module_applied(rom_out, ROOT / "damage_formula", state)
    mod = state.get_module("damage_formula")
    print(f"Applied damage_formula -> {rom_out}")
    print(f"State -> {state_path}")
    if mod:
        print(f"  version {mod.version} caves={len(mod.caves)} hooks={len(mod.hooks)}")
        for entry in mod.data or []:
            print(f"  {entry}")


if __name__ == "__main__":
    main()
