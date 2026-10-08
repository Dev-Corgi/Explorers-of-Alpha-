#!/usr/bin/env python3
"""Apply difficulty_unlock module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.apply_module import apply_module, verify_module_applied


def main() -> None:
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--force"]
    rom_in = Path(args[0]) if len(args) > 0 else REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
    rom_out = (
        Path(args[1])
        if len(args) > 1
        else REPO / "PatchTesting" / "Export Rom" / "Explorers of Alpha_Vanilla+difficulty_unlock.nds"
    )
    state_path = Path(args[2]) if len(args) > 2 else rom_out.with_suffix(".state.json")

    if not rom_in.is_file():
        raise SystemExit(f"input ROM not found: {rom_in}")
    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())

    state = apply_module(
        "difficulty_unlock",
        rom_out if rom_out.exists() else rom_in,
        rom_out,
        state_path=state_path,
        force_reapply=force,
    )
    verify_module_applied(rom_out, ROOT / "difficulty_unlock", state)
    print(f"Applied difficulty_unlock -> {rom_out}")


if __name__ == "__main__":
    main()
