"""Shared overlay cave allocation (ov29 / ov36)."""

from __future__ import annotations

from typing import Any

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

from .cave_allocator import CaveSlot, allocate_cave
from .cave_manifest import parse_forbidden_ranges, parse_max_file_offset
from .cave_reservations import FileRange, reserved_file_ranges
from .ov29_layout import allocate_ov29_cave, write_ov29_to_rom
from .ov36_layout import allocate_ov36_cave, write_ov36_to_rom

OV29_NAMES = frozenset({"ov29", "overlay29", "overlay_0029"})
OV36_NAMES = frozenset({"ov36", "overlay36", "overlay_0036"})
OV31_NAMES = frozenset({"ov31", "overlay31", "overlay_0031"})
OV11_NAMES = frozenset({"ov11", "overlay11", "overlay_0011"})
ARM9_NAMES = frozenset({"arm9", "arm9.bin"})


def normalize_cave_binary(cave_cfg: dict[str, Any]) -> str:
    return str(cave_cfg.get("binary") or cave_cfg.get("overlay") or "ov29")


def binary_load(profile: dict[str, Any], name: str) -> int:
    if name in OV29_NAMES:
        return int(profile.get("overlay29_load", 0x022DC240))
    if name in OV36_NAMES:
        return int(profile.get("overlay36_load", 0x023A7080))
    if name in OV31_NAMES:
        return int(profile.get("overlay31_load", 0x02382820))
    if name in OV11_NAMES:
        return int(profile.get("overlay11_load", 0x022DC240))
    if name in ARM9_NAMES:
        return int(profile.get("arm9_load", 0x02000000))
    raise ValueError(f"unknown binary {name!r}")


def overlay_index(name: str) -> int:
    if name in OV29_NAMES:
        return 29
    if name in OV31_NAMES:
        return 31
    if name in OV11_NAMES:
        return 11
    if name in OV36_NAMES:
        return 36
    raise ValueError(f"not an overlay binary: {name!r}")


def get_rom_binary(rom: NintendoDSRom, name: str) -> bytearray:
    if name in ARM9_NAMES:
        return bytearray(rom.arm9)
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return bytearray(rom.files[table[overlay_index(name)].fileID])


def write_rom_binary(rom: NintendoDSRom, config, name: str, data: bytes) -> None:
    if name in OV29_NAMES:
        write_ov29_to_rom(rom, config, data)
        return
    if name in OV36_NAMES:
        write_ov36_to_rom(rom, config, data)
        return
    if name in OV31_NAMES:
        from skytemple_files.common.util import set_binary_in_rom

        set_binary_in_rom(rom, config.bin_sections.overlay31, data)
        return
    if name in OV11_NAMES:
        from skytemple_files.common.util import set_binary_in_rom

        set_binary_in_rom(rom, config.bin_sections.overlay11, data)
        return
    if name in ARM9_NAMES:
        from skytemple_files.common.util import set_binary_in_rom

        set_binary_in_rom(rom, config.bin_sections.arm9, data)
        return
    raise ValueError(f"unknown binary {name!r}")


def overlay_filename(name: str) -> str:
    if name in OV29_NAMES:
        return "overlay_0029.bin"
    if name in OV36_NAMES:
        return "overlay_0036.bin"
    if name in OV31_NAMES:
        return "overlay_0031.bin"
    if name in OV11_NAMES:
        return "overlay_0011.bin"
    if name in ARM9_NAMES:
        return "arm9.bin"
    raise ValueError(f"unknown binary {name!r}")


def _parse_fixed(value) -> int | None:
    if value is None:
        return None
    return int(value, 16) if isinstance(value, str) else int(value)


def allocate_overlay_cave(
    *,
    binary: str,
    overlay_data: bytes | bytearray,
    profile: dict[str, Any],
    state,
    cave_cfg: dict[str, Any],
    module_id: str | None = None,
    preferred_file_offset: int | None = None,
    arm9_data: bytes | None = None,
    extra_reserved: list | None = None,
) -> tuple[CaveSlot, bytearray]:
    load = binary_load(profile, binary)
    reserved = [
        *reserved_file_ranges(state, binary, exclude_module=module_id),
        *(extra_reserved or []),
    ]
    need = int(cave_cfg.get("estimated_bytes", 2048))
    alignment = int(cave_cfg.get("alignment", 4))
    preferred = (
        preferred_file_offset
        if preferred_file_offset is not None
        else _parse_fixed(cave_cfg.get("preferred"))
    )
    max_off = parse_max_file_offset(cave_cfg)

    if binary in OV36_NAMES:
        return allocate_ov36_cave(
            overlay_data,
            load,
            need,
            alignment=alignment,
            preferred_file_offset=preferred,
            reserved_file_offsets=reserved,
            max_file_offset=max_off,
            cave_cfg=cave_cfg,
        )
    if binary in OV29_NAMES:
        return allocate_ov29_cave(
            overlay_data,
            load,
            need,
            alignment=alignment,
            preferred_file_offset=preferred,
            reserved_file_offsets=reserved,
            max_file_offset=max_off,
            cave_cfg=cave_cfg,
            arm9_data=arm9_data,
        )
    slot = allocate_cave(
        bytes(overlay_data),
        load,
        need,
        alignment=alignment,
        preferred_file_offset=preferred,
        reserved_file_offsets=reserved,
        forbidden_file_offsets=parse_forbidden_ranges(cave_cfg),
        max_file_offset=max_off,
    )
    return slot, bytearray(overlay_data)
