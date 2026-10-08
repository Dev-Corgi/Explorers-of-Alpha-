from __future__ import annotations

from typing import Any

from .cave_reservations import FileRange


def parse_forbidden_ranges(cave_cfg: dict[str, Any]) -> list[FileRange]:
    out: list[FileRange] = []
    for entry in cave_cfg.get("forbidden") or []:
        if isinstance(entry, dict):
            start = int(entry["start"], 16) if isinstance(entry["start"], str) else int(entry["start"])
            end = int(entry["end"], 16) if isinstance(entry["end"], str) else int(entry["end"])
        elif isinstance(entry, (list, tuple)) and len(entry) == 2:
            start = int(entry[0], 16) if isinstance(entry[0], str) else int(entry[0])
            end = int(entry[1], 16) if isinstance(entry[1], str) else int(entry[1])
        else:
            raise ValueError(f"invalid forbidden range: {entry!r}")
        out.append(FileRange(start, end))
    return out


def parse_max_file_offset(cave_cfg: dict[str, Any]) -> int | None:
    value = cave_cfg.get("max_file_offset")
    if value is None:
        return None
    return int(value, 16) if isinstance(value, str) else int(value)


def parse_allocation_strategy(cave_cfg: dict[str, Any] | None) -> str:
    """Return 'auto' (zero run / reserved chain) or 'tail' (grow overlay end only)."""
    if not cave_cfg:
        return "auto"
    return str(cave_cfg.get("strategy") or cave_cfg.get("allocate") or "auto")
