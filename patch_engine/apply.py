#!/usr/bin/env python3
"""CLI: apply a true_patches module to a US EoS ROM."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parent
MODULES = REPO / "true_patches"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.apply_module import apply_module, verify_module_applied
from patch_engine.state import load_state


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply one true_patches module")
    parser.add_argument("module", help="module id (e.g. room_charge)")
    parser.add_argument("rom_in", type=Path, help="input .nds")
    parser.add_argument("rom_out", type=Path, help="output .nds")
    parser.add_argument(
        "--state",
        type=Path,
        default=None,
        help="build state JSON (default: <rom_out>.state.json)",
    )
    parser.add_argument("--force", action="store_true", help="re-apply even if in state")
    parser.add_argument(
        "--cave-gap",
        type=lambda s: int(s, 0),
        default=None,
        metavar="BYTES",
        help="reserve zero padding between caves (also TRUE_PATCHES_CAVE_GAP env)",
    )
    args = parser.parse_args()

    if args.cave_gap is not None:
        os.environ["TRUE_PATCHES_CAVE_GAP"] = str(args.cave_gap)

    state_path = args.state or args.rom_out.with_suffix(".state.json")
    if args.rom_out.resolve() != args.rom_in.resolve():
        args.rom_out.write_bytes(args.rom_in.read_bytes())

    state = apply_module(
        args.module,
        args.rom_out if args.rom_out.exists() else args.rom_in,
        args.rom_out,
        state_path=state_path,
        force_reapply=args.force,
    )
    module_dir = MODULES / args.module
    verify_module_applied(args.rom_out, module_dir, state)
    print(f"OK {args.module} -> {args.rom_out}")
    print(f"state: {state_path}")


if __name__ == "__main__":
    main()
