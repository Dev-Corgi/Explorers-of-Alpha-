"""ov36 (ExtraSpace) cave layout — linker hole @ 0x1A578, avoid c-of-time common."""

from __future__ import annotations

from typing import Any

from ndspy.code import loadOverlayTable, saveOverlayTable
from ndspy.rom import NintendoDSRom
from .cave_allocator import CaveSlot, allocate_cave
from .cave_manifest import parse_forbidden_ranges
from .cave_reservations import FileRange

OV36_LOAD = 0x023A7080

# Largest zero hole in Alpha ExtraSpace (linker padding between used sections).
# team_push owns file 0xE00..0x1100 (RAM 0x023A7E80) inside the prefix below.
OV36_CAVE_CHAIN_FILE = 0x1A578
OV36_CAVE_CHAIN_RAM = OV36_LOAD + OV36_CAVE_CHAIN_FILE
OV36_CAVE_HOLE_END_FILE = 0x2D300

# c-of-time default common slot (partially used on Alpha — do not allocate here).
COT_COMMON_FILE = 0x30F70
COT_COMMON_END_FILE = 0x38F80


def ov36_used_forbidden() -> list[FileRange]:
    """Regions that must not receive combat caves."""
    return [
        FileRange(0, OV36_CAVE_CHAIN_FILE),
        FileRange(COT_COMMON_FILE, COT_COMMON_END_FILE),
        FileRange(OV36_CAVE_HOLE_END_FILE, 0x400000),
    ]


def ov36_forbidden_ranges(
    cave_cfg: dict[str, Any] | None = None,
    *,
    extra: list[FileRange] | None = None,
) -> list[FileRange]:
    out: list[FileRange] = []
    seen: set[tuple[int, int]] = set()

    def _add(block: FileRange) -> None:
        key = (block.start, block.end)
        if key not in seen:
            seen.add(key)
            out.append(block)

    for block in ov36_used_forbidden():
        _add(block)
    if cave_cfg:
        for block in parse_forbidden_ranges(cave_cfg):
            _add(block)
    if extra:
        for block in extra:
            _add(block)
    return out


def allocate_ov36_cave(
    overlay_data: bytes | bytearray,
    overlay_load: int,
    estimated_bytes: int,
    *,
    alignment: int = 4,
    preferred_file_offset: int | None = None,
    reserved_file_offsets: list[FileRange] | None = None,
    forbidden_file_offsets: list[FileRange] | None = None,
    max_file_offset: int | None = None,
    cave_cfg: dict[str, Any] | None = None,
) -> tuple[CaveSlot, bytearray]:
    data = bytearray(overlay_data)
    reserved = reserved_file_offsets or []
    forbidden = ov36_forbidden_ranges(cave_cfg, extra=forbidden_file_offsets)
    preferred = preferred_file_offset
    if preferred is None:
        preferred = OV36_CAVE_CHAIN_FILE

    slot = allocate_cave(
        bytes(data),
        overlay_load,
        estimated_bytes,
        alignment=alignment,
        preferred_file_offset=preferred,
        reserved_file_offsets=reserved,
        forbidden_file_offsets=forbidden,
        max_file_offset=max_file_offset or OV36_CAVE_HOLE_END_FILE,
    )
    end = slot.file_offset + slot.size
    if end > OV36_CAVE_HOLE_END_FILE:
        raise RuntimeError(
            f"ov36 cave [{slot.file_offset:#x}..{end:#x}) exceeds safe hole end {OV36_CAVE_HOLE_END_FILE:#x}"
        )
    return slot, data


def write_ov36_to_rom(rom: NintendoDSRom, _config, data: bytes) -> None:
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    entry = table[36]
    if len(data) > entry.ramSize:
        entry.ramSize = len(data)
        rom.arm9OverlayTable = saveOverlayTable(table)
    rom.files[entry.fileID] = data
