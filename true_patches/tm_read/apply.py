#!/usr/bin/env python3
"""Apply tm_read module."""

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
    default_in = REPO / "_tp_chain_full2.nds"
    rom_in = Path(sys.argv[1]) if len(sys.argv) > 1 else default_in
    rom_out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "_true_patches_tm_read.nds"
    state_path = Path(sys.argv[3]) if len(sys.argv) > 3 else rom_out.with_suffix(".state.json")

    if not rom_in.is_file():
        raise SystemExit(f"input ROM not found: {rom_in}")

    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())

    state = apply_module(
        "tm_read",
        rom_out if rom_out.exists() else rom_in,
        rom_out,
        state_path=state_path,
        force_reapply="--force" in sys.argv,
    )
    verify_module_applied(rom_out, ROOT / "tm_read", state)

    mod = state.get_module("tm_read")
    print(f"Applied tm_read -> {rom_out}")
    print(f"State -> {state_path}")
    if mod and mod.data:
        print(f"  ov29 base: {mod.data[0].get('cave_base_ov29')}")
        print(f"  room_charge_helpers: {mod.data[0].get('room_charge_helpers')}")


if __name__ == "__main__":
    main()
