#!/usr/bin/env python3
"""Build one-feature unit test ROMs under PatchTesting/Export Rom/Unit_Test."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parent
MODULES = REPO / "true_patches"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.apply_module import apply_module, verify_module_applied

VANILLA = REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"
OUT_DIR = REPO / "PatchTesting" / "Export Rom" / "Unit_Test"

# module id -> output stem. z_move_v2 is applied first when listed in prereqs.
BUILDS: dict[str, list[str]] = {
    "berry_boost": [],
    "boost_ribbon": ["z_move_v2"],
    "better_equipment": ["z_move_v2"],
    "spinda_ev_speed": ["z_move_v2"],
    "z_move_v2": [],
}


def build_one(stem: str, prereqs: list[str]) -> Path:
    out = OUT_DIR / f"Explorers of Alpha_Vanilla+{stem}.nds"
    state = OUT_DIR / f"Explorers of Alpha_Vanilla+{stem}.state.json"
    if state.exists():
        state.unlink()
    shutil.copy2(VANILLA, out)
    modules = [*prereqs, stem]
    st = None
    for mid in modules:
        st = apply_module(
            mid,
            out,
            out,
            state_path=state,
            force_reapply=True,
        )
        verify_module_applied(out, MODULES / mid, st)
    if state.exists():
        state.unlink()
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for stem, prereqs in BUILDS.items():
        label = "+".join([*prereqs, stem]) if prereqs else stem
        print(f"=== {label} ===")
        path = build_one(stem, prereqs)
        print(f"OK -> {path}")
    print(f"done ({len(BUILDS)} ROMs in {OUT_DIR})")


if __name__ == "__main__":
    main()
