"""Dispatch mega_evolve; phase 0 is a byte-preserving registry validation gate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .state import AppliedModule
from true_patches.mega_evolve.phase0 import validate


def load_registry(module_dir, manifest):
    if manifest.get("phase") != 0:
        raise RuntimeError("mega_evolve runtime phases are not implemented yet")
    path = module_dir / "data/registry.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    metadata = validate(registry)
    metadata["registry_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return registry, metadata


def validate_rom(rom_path, registry):
    from ndspy.rom import NintendoDSRom
    from skytemple_files.data.md.handler import MdHandler
    rom = NintendoDSRom(Path(rom_path).read_bytes())
    md = MdHandler.deserialize(rom.getFileByName("BALANCE/monster.md"))
    if len(md.entries) != registry["audit"]["rom_evidence"]["md_entries"]:
        raise ValueError("mega_evolve phase0: unexpected MD count")
    for target in registry["targets"]:
        if md.entries[target["source_rom_id"]].national_pokedex_number != target["dex"]:
            raise ValueError("mega_evolve phase0: source species identity changed")
    if md.entries[1137].ability_primary != 250:
        raise ValueError("mega_evolve phase0: story Omniscience changed")


def apply_mega_evolve_module(module_id, module_dir, manifest, rom_path):
    registry, metadata = load_registry(module_dir, manifest)
    validate_rom(rom_path, registry)
    return AppliedModule(id=module_id, version=manifest.get("version", 1),
                         data=[{"mega_evolve": metadata}])


def verify_mega_evolve_module(rom_path, module_dir, manifest, record):
    registry, metadata = load_registry(module_dir, manifest)
    if record is None or record.caves or record.hooks or record.data != [{"mega_evolve": metadata}]:
        raise AssertionError("mega_evolve phase0: missing/stale registry validation record")
    validate_rom(rom_path, registry)
