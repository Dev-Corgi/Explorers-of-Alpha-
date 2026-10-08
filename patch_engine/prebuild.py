from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


def run_prebuild(module_dir: Path, rom_in: Path, steps: list[dict[str, Any]]) -> None:
    for step in steps:
        script = step.get("script")
        if not script:
            raise ValueError(f"prebuild step missing script: {step}")
        script_path = module_dir / script
        if not script_path.is_file():
            raise FileNotFoundError(f"prebuild script not found: {script_path}")
        args = [str(script_path), str(Path(rom_in).resolve())]
        extra = step.get("args") or []
        args.extend(str(a) for a in extra)
        result = subprocess.run(
            [sys.executable, *args],
            cwd=module_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"prebuild {script} failed:\n"
                + (result.stdout or "")
                + "\n"
                + (result.stderr or "")
            )
