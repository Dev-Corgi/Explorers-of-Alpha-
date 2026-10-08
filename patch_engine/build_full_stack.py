#!/usr/bin/env python3
"""Build the canonical Explorers of Alpha full_stack ROM."""

from __future__ import annotations

import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parent
MODULES = REPO / "true_patches"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.apply_module import apply_module, verify_module_applied

# Canonical apply order (cave chain + hook dependencies).
FULL_STACK_MODULES = [
    "team_push",
    "fixed_room_orbs",
    "shop_sell_price",
    "difficulty_unlock",
    "dinner_sprites",
    "room_charge_pending",
    "orb_charges_v2",
    "berry_boost",
    "tm_read",
    "z_move_v2",
    "boost_ribbon",
    "iq_change",
    "status_adjust",
    "level_scaling_guest_fix",
    "damage_formula",
    "size_adjust",
    "no_immediate_house",
    "utility_patch",
    "better_poke",
    "better_food",
    "better_equipment",
    "base_stats_speed",
    "spinda_ev_speed",
    "balance_change",
    "control_mode_enhance",
    "belly_union",
]


def main() -> None:
    force = "--force" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--force"]
    vanilla = (
        REPO
        / "PatchTesting"
        / "Explorers of Alpha"
        / "Explorers of Alpha.nds"
    )
    out = REPO / "PatchTesting" / "Export Rom" / "Explorers of Alpha+.nds"
    state_path = out.with_suffix(".state.json")

    rom_in = Path(args[0]) if len(args) > 0 else vanilla
    rom_out = Path(args[1]) if len(args) > 1 else out
    if len(args) > 2:
        state_path = Path(args[2])

    if rom_out.resolve() != rom_in.resolve():
        rom_out.write_bytes(rom_in.read_bytes())
    if force and state_path.exists():
        state_path.unlink()

    state = None
    for mid in FULL_STACK_MODULES:
        print(f"=== {mid} ===")
        state = apply_module(
            mid,
            rom_out if rom_out.exists() else rom_in,
            rom_out,
            state_path=state_path,
            force_reapply=force,
        )
        verify_module_applied(rom_out, MODULES / mid, state)
        mod = state.get_module(mid)
        for cave in mod.caves:
            print(
                f"  cave {cave.overlay} file {cave.file_offset:#x} "
                f"size {cave.size} ram {cave.load_address:#x}"
            )

    assert state is not None
    print(f"OK full_stack -> {rom_out}")
    print(f"state -> {state_path}")
    print("modules:", [m.id for m in state.applied])


if __name__ == "__main__":
    main()
