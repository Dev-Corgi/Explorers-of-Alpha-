"""Optional padding between consecutive true_patches caves (debug builds)."""

from __future__ import annotations

import os


def cave_inter_gap_bytes() -> int:
    """Bytes of zero padding reserved after each cave before the next allocation."""
    raw = os.environ.get("TRUE_PATCHES_CAVE_GAP", "").strip()
    if not raw:
        return 0
    return int(raw, 0)


def align_up(value: int, alignment: int = 4) -> int:
    return (value + alignment - 1) // alignment * alignment


def file_offset_after_cave(file_offset: int, size: int, *, alignment: int = 4) -> int:
    """Next aligned file offset after cave body + inter-cave gap."""
    gap = cave_inter_gap_bytes()
    tail = gap if gap > 0 else 0
    return align_up(file_offset + size + tail, alignment)
