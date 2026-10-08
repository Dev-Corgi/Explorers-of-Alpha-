"""Rebuild fullstack_no_loader from vanilla with current modules."""
from __future__ import annotations

import shutil
from pathlib import Path

from patch_engine.apply_module import apply_module

ROOT = Path(r"c:\Working\SkyTemple")
VANILLA = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
OUT = ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack_no_loader.nds"
STATE = OUT.with_suffix(".state.json")

# Match previous no_loader stack (no overlay36_loader).
MODULES = [
    "fixed_room_orbs",
    "shop_sell_price",
    "room_charge_v4",
    "orb_charges_v2",
    "berry_boost",
    "tm_read",
    "z_move_v2",
    "damage_formula",
    "spinda_ev_v2",
    "iq_change",
]


def main() -> None:
    if not VANILLA.is_file():
        # fallback path used historically
        alt = ROOT / "true_patches" / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
        src = alt if alt.is_file() else VANILLA
    else:
        src = VANILLA
    if not src.is_file():
        raise SystemExit(f"vanilla missing: {src}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, OUT)
    if STATE.exists():
        STATE.unlink()
    for mid in MODULES:
        print(f"=== apply {mid} ===")
        apply_module(mid, OUT, OUT, state_path=STATE, force_reapply=False)
    print("OK", OUT)


if __name__ == "__main__":
    main()
