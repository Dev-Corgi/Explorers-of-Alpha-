#!/usr/bin/env python3
"""Generate the tables and apply base_stats_speed to a vanilla ROM."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from true_patches.base_stats_speed.generate_tables import patch_arm9_hp_caps
from true_patches.base_stats_speed.verify_samples import verify
from patch_engine.apply_module import apply_module, verify_module_applied


def main() -> None:
    default_in = REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = True
    rom_in = Path(args[0]) if len(args) > 0 else default_in
    rom_out = (
        Path(args[1])
        if len(args) > 1
        else REPO / "PatchTesting" / "Export Rom" / "Unit_Test" / "Explorers of Alpha_Vanilla+base_stats_speed.nds"
    )
    state_path = Path(args[2]) if len(args) > 2 else rom_out.with_suffix(".state.json")
    if not rom_in.is_file():
        raise SystemExit(f"input ROM not found: {rom_in}")
    rom_out.parent.mkdir(parents=True, exist_ok=True)
    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())
    state = apply_module(
        "base_stats_speed",
        rom_out,
        rom_out,
        state_path=state_path,
        force_reapply=force,
    )
    patch_arm9_hp_caps(rom_out)
    verify_module_applied(rom_out, ROOT / "base_stats_speed", state)
    verify(rom_out, state_path)
    mod = state.get_module("base_stats_speed")
    print(f"Applied base_stats_speed -> {rom_out}")
    if mod:
        for cave in mod.caves:
            print(f"  cave {cave.overlay} file {cave.file_offset:#x} ram {cave.load_address:#x}")
        for blob in mod.data or []:
            for key in ("BaseStats_CalcStat", "BaseStats_EvoRate"):
                if key in blob:
                    print(f"  {key} {blob[key]}")


if __name__ == "__main__":
    main()
