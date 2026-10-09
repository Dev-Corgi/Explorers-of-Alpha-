"""Checked, in-place instruction fixes for the Alpha base ROM."""

from __future__ import annotations

import struct
from typing import Any

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom

from patch_engine.data_patches import DataPatchRecord
from patch_engine.overlay_caves import get_rom_binary, overlay_index, write_rom_binary


def _patches(rom: NintendoDSRom, manifest: dict[str, Any]):
    cfg = manifest["data"]
    binary = str(cfg["binary"])
    overlays = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _f: b"")
    load = overlays[overlay_index(binary)].ramAddress
    blob = get_rom_binary(rom, binary)
    patches = cfg["word_patches"]
    for patch in patches:
        off = int(patch["address"]) - load
        if off % 4 or not 0 <= off <= len(blob) - 4:
            raise ValueError(f"{patch['name']}: invalid instruction address")
    return binary, load, blob, patches


def apply_bug_fixes_rom(rom: NintendoDSRom, manifest: dict[str, Any]) -> DataPatchRecord:
    binary, load, blob, patches = _patches(rom, manifest)
    changes = []
    for patch in patches:
        address = int(patch["address"])
        off = address - load
        before = struct.unpack_from("<I", blob, off)[0]
        expected, replacement = int(patch["expected"]), int(patch["replace"])
        if before not in (expected, replacement):
            raise RuntimeError(
                f"{patch['name']} @ {address:#x}: expected {expected:#010x} "
                f"or {replacement:#010x}, found {before:#010x}"
            )
        struct.pack_into("<I", blob, off, replacement)
        changes.append({
            "name": patch["name"], "address": address,
            "before": before, "after": replacement, "changed": before != replacement,
        })
    write_rom_binary(rom, get_ppmdu_config_for_rom(rom), binary, bytes(blob))
    return DataPatchRecord(
        overlay=binary, table="instruction_words", entries=len(changes),
        fields_changed=sum(p["changed"] for p in changes), details={"patches": changes},
    )


def verify_bug_fixes_rom(rom: NintendoDSRom, manifest: dict[str, Any]) -> None:
    _, load, blob, patches = _patches(rom, manifest)
    for patch in patches:
        address = int(patch["address"])
        actual = struct.unpack_from("<I", blob, address - load)[0]
        if actual != int(patch["replace"]):
            raise AssertionError(f"{patch['name']} @ {address:#x}: found {actual:#010x}")
