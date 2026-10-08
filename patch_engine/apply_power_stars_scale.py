"""Apply power_stars_scale: SetStringPower rewrite using vanilla [M:R1] half-star."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from ndspy.rom import NintendoDSRom

from .armips_runner import run_armips_module
from .state import AppliedModule


def apply_power_stars_scale_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    rom: NintendoDSRom,
    armips: Path,
) -> AppliedModule:
    # Half star is vanilla text tag [M:R1] (same as IQ summary) — no markfont inject.
    asm_cfg = manifest.get("asm") or {}
    asm_path = module_dir / asm_cfg.get("entry", "asm/main.asm")
    # damage_formula passes power_stars_asm via components → data/asm entry override
    data_cfg = manifest.get("data") or {}
    if data_cfg.get("power_stars_asm"):
        asm_path = module_dir / str(data_cfg["power_stars_asm"])
    elif asm_cfg.get("entry"):
        asm_path = module_dir / asm_cfg["entry"]
    asm_dir = asm_path.parent

    with tempfile.TemporaryDirectory(prefix="power_stars_") as tmp:
        arm9_path = Path(tmp) / "arm9.bin"
        arm9_path.write_bytes(bytes(rom.arm9))
        run_armips_module(
            armips=armips,
            asm_dir=asm_dir,
            asm_entry=asm_path.name,
            overlay_path=arm9_path,
            overlay_filename="arm9.bin",
        )
        rom.arm9 = arm9_path.read_bytes()

    return AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=[],
        hooks=[],
        data=[
            {
                "half_star_tag": "[M:R1]",
                "half_star_string": "0x020A3544",
                "set_string_power": "0x02024428",
                "scale": "1 star / 20 BP, half / 10 BP",
                "markfont_inject": False,
            }
        ],
    )
