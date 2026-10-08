#!/usr/bin/env python3
"""Build full_stack + korean.

Usage: python build_korean.py [--rebuild-full] [full_stack.nds] [out.nds]

Cave-placement state stays in a temp directory. The build does not leave a
.state.json or an untranslated-strings workbook next to the ROM.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
REPO = ENGINE.parent
MODULES = REPO / "true_patches"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from patch_engine.apply_module import apply_module, verify_module_applied  # noqa: E402

EXPORT = REPO / "PatchTesting" / "Export Rom"
VANILLA = REPO / "PatchTesting" / "Explorers of Alpha" / "Explorers of Alpha.nds"


def _drop_sidecars(*paths: Path) -> None:
    for path in paths:
        if path.is_file():
            path.unlink()


def _rebuild_full(full: Path, full_state: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(ENGINE / "build_full_stack.py"),
            "--force",
            str(VANILLA),
            str(full),
            str(full_state),
        ],
        check=True,
    )


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    full = Path(args[0]) if args else EXPORT / "Explorers of Alpha+.nds"
    out = Path(args[1]) if len(args) > 1 else EXPORT / "Explorers of Alpha+_kor.nds"
    report = out.with_name(out.stem + "_untranslated.xlsx")
    sibling_state = full.with_suffix(".state.json")

    with tempfile.TemporaryDirectory(prefix="korean_build_") as tmpdir:
        tmp = Path(tmpdir)
        full_state = tmp / "full_stack.state.json"
        state_path = tmp / "korean.state.json"
        rebuild = "--rebuild-full" in sys.argv or not full.is_file() or not sibling_state.is_file()
        if rebuild:
            _rebuild_full(full, full_state)
        else:
            shutil.copy2(sibling_state, full_state)

        shutil.copy2(full_state, state_path)
        full_ids = json.loads(full_state.read_text(encoding="utf-8")).get("applied", [])
        if any(m.get("id") == "korean_assemble" for m in full_ids):
            raise RuntimeError("korean_assemble is in the English full_stack state")

        module_dir = MODULES / "korean"
        state = apply_module("korean", full, out, state_path=state_path)
        verify_module_applied(out, module_dir, state)

    _drop_sidecars(sibling_state, out.with_suffix(".state.json"), report)
    mod = state.get_module("korean")
    for cave in mod.caves:
        print(f"  korean cave {cave.overlay} file {cave.file_offset:#x} size {cave.size} ram {cave.load_address:#x}")
    print("  korean data:", mod.data[0])
    print(f"OK korean -> {out}")


if __name__ == "__main__":
    main()
