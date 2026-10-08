#!/usr/bin/env python3
"""Apply room_charge_pending module via true_patches engine."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from patch_engine.apply_module import apply_module, verify_module_applied


def main() -> None:
    repo = ROOT.parent
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--force"]
    default_rom = repo / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
    export_dir = repo / "PatchTesting" / "Export Rom" / "Room_Charge_Pending_Test"
    export_dir.mkdir(parents=True, exist_ok=True)
    default_out = export_dir / "Explorers of Alpha_Vanilla+room_charge_pending.nds"

    rom_in = Path(args[0]) if len(args) > 0 else default_rom
    rom_out = Path(args[1]) if len(args) > 1 else default_out
    state_path = Path(args[2]) if len(args) > 2 else rom_out.with_suffix(".state.json")

    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())

    state = apply_module(
        "room_charge_pending",
        rom_out if rom_out.exists() else rom_in,
        rom_out,
        state_path=state_path,
        force_reapply=force,
    )
    verify_module_applied(rom_out, ROOT / "room_charge_pending", state)
    print(f"Applied room_charge_pending -> {rom_out}")
    print(f"State -> {state_path}")
    for cave in state.get_module("room_charge_pending").caves:
        print(f"  cave {cave.overlay} file {cave.file_offset:#x} ram {cave.load_address:#x}")


if __name__ == "__main__":
    main()
