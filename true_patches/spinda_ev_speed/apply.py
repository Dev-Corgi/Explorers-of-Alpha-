#!/usr/bin/env python3
"""Apply spinda_ev_speed module."""

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
    rom_out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else REPO / "PatchTesting" / "Export Rom" / "Unit_Test" / "Explorers of Alpha_Vanilla+spinda_ev_speed.nds"
    )
    state_path = Path(sys.argv[3]) if len(sys.argv) > 3 else rom_out.with_suffix(".state.json")

    if not rom_in.is_file():
        raise SystemExit(f"input ROM not found: {rom_in}")

    rom_out.parent.mkdir(parents=True, exist_ok=True)
    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())

    state = apply_module(
        "spinda_ev_speed",
        rom_out if rom_out.exists() else rom_in,
        rom_out,
        state_path=state_path,
        force_reapply="--force" in sys.argv,
    )
    verify_module_applied(rom_out, ROOT / "spinda_ev_speed", state)

    mod = state.get_module("spinda_ev_speed")
    print(f"Applied spinda_ev_speed -> {rom_out}")
    print(f"State -> {state_path}")
    if mod and mod.data:
        print(f"  arm9 code: {mod.data[0].get('arm9_code_cave')}")
        print(f"  arm9 reset: {mod.data[0].get('arm9_reset_cave')}")
        print(f"  ov19 table: {mod.data[0].get('ov19_team_submenu_table')}")


if __name__ == "__main__":
    main()
