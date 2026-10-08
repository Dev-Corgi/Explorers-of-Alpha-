"""Apply better_poke to a vanilla Explorers of Alpha ROM."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.apply import apply_module, default_output_path, load_rom, save_rom
from engine.paths import VANILLA_NDS
from engine.state import PatchState, state_path_for
from engine.verify import verify_module_applied


def main() -> None:
    rom_in = VANILLA_NDS
    rom_out = default_output_path(rom_in, "better_poke")
    rom = load_rom(rom_in)
    state = PatchState.load(state_path_for(rom_out))
    apply_module(rom, ROOT / "better_poke", state)
    save_rom(rom, rom_out)
    state.save(state_path_for(rom_out))
    verify_module_applied(rom_out, ROOT / "better_poke", state)
    mod = state.get_module("better_poke")
    print(f"Applied better_poke -> {rom_out}")
    if mod:
        for cave in mod.caves:
            print(f"  cave {cave.overlay} file {cave.file_offset:#x} ram {cave.load_address:#x}")


if __name__ == "__main__":
    main()
