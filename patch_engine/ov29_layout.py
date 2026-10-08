"""ov29 cave layout — keep hooks out of StartMFunc repack window."""

from __future__ import annotations

from typing import Any

from ndspy.code import loadOverlayTable, saveOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import set_binary_in_rom

from .cave_allocator import CaveSlot, allocate_cave
from .cave_manifest import parse_allocation_strategy, parse_forbidden_ranges
from .cave_reservations import FileRange
from .cave_xref import (
    find_best_interior_cave_slot,
    format_xref_report,
    slot_has_vanilla_xrefs,
)

OV29_LOAD = 0x022DC240

# StartMFunc is copied/repacked in RAM during battle when waza_cd effect IDs change.
# Cave code placed here is wiped (effect-ID bytes overwrite hook stubs).
START_MFUNC_RAM = 0x02330134
END_MFUNC_RAM = 0x023326CC
START_MFUNC_FILE = START_MFUNC_RAM - OV29_LOAD  # 0x53EF4
END_MFUNC_FILE = END_MFUNC_RAM - OV29_LOAD  # 0x5648C

# item_cd Pattern B stubs link at ItemStartAddress; the engine repacks item effects here.
ITEM_START_RAM = 0x0231BE50
ITEM_JUMP_RAM = 0x0231CB14
ITEM_START_FILE = ITEM_START_RAM - OV29_LOAD  # 0x3FC10
ITEM_JUMP_FILE = ITEM_JUMP_RAM - OV29_LOAD  # 0x408D4


def start_mfunc_forbidden() -> FileRange:
    return FileRange(START_MFUNC_FILE, END_MFUNC_FILE)


def item_start_forbidden() -> FileRange:
    return FileRange(ITEM_START_FILE, ITEM_JUMP_FILE)


def cave_overlaps_start_mfunc(slot: CaveSlot) -> bool:
    la_end = slot.load_address + slot.size
    return not (la_end <= START_MFUNC_RAM or slot.load_address >= END_MFUNC_RAM)


def cave_overlaps_item_start(slot: CaveSlot) -> bool:
    la_end = slot.load_address + slot.size
    return not (la_end <= ITEM_START_RAM or slot.load_address >= ITEM_JUMP_RAM)


def cave_overlaps_runtime_repack(slot: CaveSlot) -> bool:
    return cave_overlaps_start_mfunc(slot) or cave_overlaps_item_start(slot)


def ov29_forbidden_ranges(
    cave_cfg: dict[str, Any] | None = None,
    *,
    extra: list[FileRange] | None = None,
) -> list[FileRange]:
    """Manifest forbidden ranges plus the StartMFunc window."""
    out: list[FileRange] = []
    seen: set[tuple[int, int]] = set()

    def _add(block: FileRange) -> None:
        key = (block.start, block.end)
        if key not in seen:
            seen.add(key)
            out.append(block)

    if cave_cfg:
        for block in parse_forbidden_ranges(cave_cfg):
            _add(block)
    if extra:
        for block in extra:
            _add(block)
    _add(start_mfunc_forbidden())
    _add(item_start_forbidden())
    return out


def _tail_start(
    data: bytes,
    *,
    alignment: int,
    reserved: list[FileRange],
) -> int:
    start = max(len(data), END_MFUNC_FILE)
    if reserved:
        start = max(start, max(r.end for r in reserved))
    return (start + alignment - 1) // alignment * alignment


def allocate_ov29_cave(
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
    arm9_data: bytes | None = None,
) -> tuple[CaveSlot, bytearray]:
    """Allocate an ov29 cave outside StartMFunc; grow overlay tail if needed."""
    data = bytearray(overlay_data)
    reserved = reserved_file_offsets or []
    forbidden = ov29_forbidden_ranges(cave_cfg, extra=forbidden_file_offsets)
    strategy = parse_allocation_strategy(cave_cfg)
    interior_only = strategy == "interior"
    effective_max = len(data) - estimated_bytes if interior_only else max_file_offset

    if interior_only:
        interior_start = find_best_interior_cave_slot(
            bytes(data),
            overlay_load,
            estimated_bytes,
            alignment=alignment,
            reserved=reserved,
            forbidden=forbidden,
            arm9_data=arm9_data,
        )
        if interior_start is not None:
            slot = CaveSlot(
                file_offset=interior_start,
                size=estimated_bytes,
                load_address=overlay_load + interior_start,
            )
            if not cave_overlaps_runtime_repack(slot):
                return slot, data
        raise RuntimeError(
            f"no xref-safe interior ov29 cave >= {estimated_bytes} bytes "
            f"(file size {len(data):#x}); tail grow is not allowed for strategy=interior"
        )

    # Grow before preferred allocate when the slot sits past current EOF.
    if preferred_file_offset is not None:
        grow_pref = preferred_file_offset + estimated_bytes
        if grow_pref > len(data):
            data.extend(b"\x00" * (grow_pref - len(data)))

    if strategy != "tail":
        try:
            slot = allocate_cave(
                bytes(data),
                overlay_load,
                estimated_bytes,
                alignment=alignment,
                preferred_file_offset=preferred_file_offset,
                reserved_file_offsets=reserved,
                forbidden_file_offsets=forbidden,
                max_file_offset=effective_max,
            )
            if not cave_overlaps_runtime_repack(slot):
                return slot, data
        except RuntimeError:
            pass

    start = _tail_start(bytes(data), alignment=alignment, reserved=reserved)
    need = estimated_bytes
    if max_file_offset is not None and start > max_file_offset:
        raise RuntimeError(
            f"ov29 tail cave @ {start:#x} exceeds max_file_offset {max_file_offset:#x}"
        )

    # Skip past vanilla literals that point at/near old EOF (e.g. word @0 -> 0x77620).
    for _ in range(64):
        grow_to = start + need
        if grow_to > len(data):
            data.extend(b"\x00" * (grow_to - len(data)))
        ok, xrefs = slot_has_vanilla_xrefs(
            bytes(data), overlay_load, start, need, arm9_data=arm9_data
        )
        if ok:
            break
        bump = start + alignment
        for xr in xrefs:
            tgt = xr.target_file_offset_for(overlay_load)
            if start <= tgt < start + need:
                bump = max(bump, tgt + alignment)
        start = (bump + alignment - 1) // alignment * alignment
        if max_file_offset is not None and start > max_file_offset:
            raise RuntimeError(
                f"ov29 tail cave @ {start:#x} exceeds max_file_offset {max_file_offset:#x}"
            )
    else:
        ok = False
        xrefs = []

    if not ok:
        raise RuntimeError(
            "ov29 tail cave rejected: vanilla xrefs into slot\n"
            + format_xref_report(
                xrefs,
                overlay_load=overlay_load,
                slot_file_offset=start,
                slot_size=need,
            )
        )

    slot = CaveSlot(
        file_offset=start,
        size=need,
        load_address=overlay_load + start,
    )
    if cave_overlaps_runtime_repack(slot):
        raise RuntimeError(
            f"ov29 cave [{slot.file_offset:#x}..{slot.file_offset + slot.size:#x}) "
            f"overlaps StartMFunc [{START_MFUNC_RAM:#x}..{END_MFUNC_RAM:#x}) or "
            f"ItemStart [{ITEM_START_RAM:#x}..{ITEM_JUMP_RAM:#x})"
        )
    return slot, data


def write_ov29_to_rom(rom: NintendoDSRom, config, data: bytes) -> None:
    """Write ov29 bytes and bump overlay table ramSize when the file grows."""
    set_binary_in_rom(rom, config.bin_sections.overlay29, data)
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    entry = table[29]
    if len(data) > entry.ramSize:
        entry.ramSize = len(data)
        rom.arm9OverlayTable = saveOverlayTable(table)
    rom.files[entry.fileID] = data
