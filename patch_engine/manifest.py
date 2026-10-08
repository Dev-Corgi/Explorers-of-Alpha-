from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_rom_profile(engine_dir: Path, profile_id: str) -> dict[str, Any]:
    path = engine_dir / f"rom_profile_{profile_id.replace('us_vanilla', 'us')}.yaml"
    if profile_id == "us_vanilla":
        path = engine_dir / "rom_profile_us.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"ROM profile not found: {path}")
    return load_yaml(path)


def resolve_symbol(profile: dict[str, Any], name: str) -> int:
    symbols = profile.get("symbols") or {}
    if name not in symbols:
        raise KeyError(f"Symbol {name!r} missing from ROM profile")
    value = symbols[name]
    return int(value, 16) if isinstance(value, str) else int(value)


def load_module_manifest(module_dir: Path) -> dict[str, Any]:
    manifest_path = module_dir / "manifest.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest.yaml missing in {module_dir}")
    data = load_yaml(manifest_path)
    data["_path"] = str(module_dir)
    return data
