"""Patch Technician move-power threshold (overlay10) + description strings."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import (
    get_binary_from_rom,
    get_files_from_rom_with_extension,
    get_ppmdu_config_for_rom,
    set_binary_in_rom,
)
from skytemple_files.data.str.handler import StrHandler

from .state import AppliedModule


def apply_technician_threshold_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    rom: NintendoDSRom,
) -> AppliedModule:
    _ = module_dir
    data_cfg = manifest.get("data") or {}
    file_off = int(data_cfg.get("file_offset", 0x7ADC))
    old_v = int(data_cfg.get("old_value", 4))
    new_v = int(data_cfg.get("new_value", 60))

    config = get_ppmdu_config_for_rom(rom)
    ov10 = bytearray(get_binary_from_rom(rom, config.bin_sections.overlay10))
    cur = struct.unpack_from("<H", ov10, file_off)[0]
    if cur not in (old_v, new_v):
        raise RuntimeError(
            f"Technician threshold at ov10+{file_off:#x} is {cur}, expected {old_v} or {new_v}"
        )
    struct.pack_into("<H", ov10, file_off, new_v)
    set_binary_in_rom(rom, config.bin_sections.overlay10, bytes(ov10))

    # ★★ → ★★★ (60 BP = 3 stars under power_stars_scale)
    old_star = "[M:S3][M:S3]"
    new_star = "[M:S3][M:S3][M:S3]"
    str_changes = 0
    for filename in get_files_from_rom_with_extension(rom, "str"):
        if not filename.endswith("text_e.str"):
            continue
        strings = StrHandler.deserialize(
            rom.getFileByName(filename),
            string_encoding=config.string_encoding,
        )
        changed = False
        for i, s in enumerate(strings.strings):
            if "Technician" not in s or old_star not in s:
                continue
            if new_star in s:
                continue
            ns = s.replace(f"{old_star}-power", f"{new_star}-power")
            ns = ns.replace(f"power of {old_star}", f"power of {new_star}")
            if ns == s:
                ns = s.replace(old_star, new_star)
            if ns != s:
                strings.strings[i] = ns
                changed = True
                str_changes += 1
        if changed:
            rom.setFileByName(filename, StrHandler.serialize(strings))

    return AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=[],
        hooks=[],
        data=[
            {
                "overlay10_offset": f"0x{file_off:X}",
                "threshold": new_v,
                "was": cur,
                "string_edits": str_changes,
            }
        ],
    )
