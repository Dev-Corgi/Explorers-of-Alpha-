#!/usr/bin/env python3
"""Apply fixed_room_orbs module via true_patches engine."""

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
    rom_in = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
    )
    rom_out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "_true_patches_orbs.nds"
    state_path = Path(sys.argv[3]) if len(sys.argv) > 3 else rom_out.with_suffix(".state.json")

    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())

    state = apply_module(
        "fixed_room_orbs",
        rom_out if rom_out.exists() else rom_in,
        rom_out,
        state_path=state_path,
        force_reapply="--force" in sys.argv,
    )
    verify_module_applied(rom_out, ROOT / "fixed_room_orbs", state)

    mod = state.get_module("fixed_room_orbs")
    data = (mod.data[0] if mod and mod.data else {})
    print(f"Applied fixed_room_orbs -> {rom_out}")
    print(f"State -> {state_path}")
    if data:
        print(
            f"  ov10 {data.get('table')}: {data.get('fields_changed')}/"
            f"{data.get('entries')} rows updated"
        )


if __name__ == "__main__":
    main()
