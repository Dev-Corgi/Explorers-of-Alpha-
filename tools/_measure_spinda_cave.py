#!/usr/bin/env python3
"""Measure spinda_ev_v2 ARM9 cave usage via armips (no patched ROM needed)."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPINDA = ROOT / "true_patches" / "spinda_ev_v2"
ARMIPS = ROOT / "tools" / "armips.exe"
sys.path.insert(0, str(ROOT))
from patch_engine.armips_runner import run_armips_bundle


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="spinda_measure_") as tmpdir:
        tmp = Path(tmpdir)
        arm9_path = tmp / "arm9.bin"
        ov19_path = tmp / "overlay_0019.bin"
        ov29_path = tmp / "overlay_0029.bin"
        arm9_path.write_bytes(b"\x00" * 904508)
        ov19_path.write_bytes(b"\x00" * 17152)
        ov29_path.write_bytes(b"\x00" * 500000)
        gen_inc = tmp / "generated.inc"
        gen_inc.write_text(
            "\n".join(
                [
                    ".definelabel SpindaEvArm9CodeAddress, 0x02094624",
                    ".definelabel SpindaEvResetCaveAddress, 0x020A3550",
                    ".definelabel SpindaEvTeamSubmenuTable, 0x0238E380",
                    "SummaryRosterIndexAddress equ 0x0209FB30",
                    "EvDrinkSelectedStatAddress equ 0x0209FB34",
                    "EvDrinkBoostCacheAddress equ 0x0209FB38",
                ]
            )
            + "\n"
        )
        run_armips_bundle(
            armips=ARMIPS,
            asm_dir=SPINDA / "asm",
            asm_entry="main.asm",
            binaries={
                "arm9.bin": arm9_path,
                "overlay_0019.bin": ov19_path,
                "overlay_0029.bin": ov29_path,
            },
            generated_inc=gen_inc,
        )
        arm9 = arm9_path.read_bytes()
        for name, start, alloc in [
            ("code", 0x94624, 0x94AE8 - 0x94624),
            ("reset", 0xA3550, 944),
        ]:
            end = start + alloc
            used = start
            for off in range(end - 4, start - 1, -4):
                if any(arm9[off : off + 4]):
                    used = off + 4
                    break
            print(f"{name}: used {used - start} / {alloc} bytes")
            if used > end:
                print(f"  OVERFLOW by {used - end} bytes into boot/after cave!")


if __name__ == "__main__":
    main()
