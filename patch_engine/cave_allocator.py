from __future__ import annotations

from dataclasses import dataclass

from .cave_reservations import FileRange
from .cave_xref import format_xref_report, slot_has_vanilla_xrefs


@dataclass
class CaveSlot:
    file_offset: int
    size: int
    load_address: int


def _range_blocked(
    start: int,
    size: int,
    reserved: list[FileRange],
    forbidden: list[FileRange],
) -> bool:
    end = start + size
    for block in (*reserved, *forbidden):
        if start < block.end and end > block.start:
            return True
    return False


def find_zero_run(
    data: bytes,
    min_size: int,
    alignment: int = 4,
    *,
    reserved: list[FileRange] | None = None,
    forbidden: list[FileRange] | None = None,
    max_start: int | None = None,
) -> list[tuple[int, int]]:
    """Return (offset, length) for zero runs >= min_size, aligned, not overlapping reserved."""
    reserved = reserved or []
    forbidden = forbidden or []
    runs: list[tuple[int, int]] = []
    i = 0
    n = len(data)
    while i < n:
        if data[i] != 0:
            i += 1
            continue
        j = i
        while j < n and data[j] == 0:
            j += 1
        length = j - i
        aligned_start = (i + alignment - 1) // alignment * alignment
        aligned_len = j - aligned_start
        if aligned_len >= min_size and aligned_start < n:
            if max_start is not None and aligned_start > max_start:
                i = j
                continue
            if not _range_blocked(aligned_start, min_size, reserved, forbidden):
                runs.append((aligned_start, aligned_len))
        i = j
    return runs


def _region_nonzero(data: bytes, start: int, need: int) -> int:
    end = min(len(data), start + need)
    return sum(1 for b in data[start:end] if b != 0)


def _slot_passes_xref(
    overlay_data: bytes,
    overlay_load: int,
    start: int,
    need: int,
    *,
    check_vanilla_xrefs: bool,
) -> tuple[bool, list]:
    if not check_vanilla_xrefs:
        return True, []
    return slot_has_vanilla_xrefs(overlay_data, overlay_load, start, need)


def allocate_cave(
    overlay_data: bytes,
    overlay_load: int,
    estimated_bytes: int,
    alignment: int = 4,
    preferred_file_offset: int | None = None,
    min_contiguous_zeros: int | None = None,
    reserved_file_offsets: list[FileRange] | None = None,
    forbidden_file_offsets: list[FileRange] | None = None,
    max_file_offset: int | None = None,
    check_vanilla_xrefs: bool = True,
) -> CaveSlot:
    """Pick a cave slot in overlay binary (file offsets), avoiding reserved ranges."""
    need = min_contiguous_zeros or estimated_bytes
    reserved = reserved_file_offsets or []
    forbidden = forbidden_file_offsets or []
    xref_rejects: list[str] = []

    if preferred_file_offset is not None:
        start = preferred_file_offset
        if not any(r.overlaps(start, need) for r in (*forbidden, *reserved)):
            if max_file_offset is None or start <= max_file_offset:
                end = min(len(overlay_data), start + need)
                if end - start >= need:
                    nonzero = _region_nonzero(overlay_data, start, need)
                    if nonzero <= max(need // 8, 16):
                        ok, xrefs = _slot_passes_xref(
                            overlay_data, overlay_load, start, need,
                            check_vanilla_xrefs=check_vanilla_xrefs,
                        )
                        if ok:
                            return CaveSlot(
                                file_offset=start,
                                size=need,
                                load_address=overlay_load + start,
                            )
                        if check_vanilla_xrefs:
                            xref_rejects.append(
                                format_xref_report(
                                    xrefs,
                                    overlay_load=overlay_load,
                                    slot_file_offset=start,
                                    slot_size=need,
                                )
                            )

    # Continue in the same zero run right after prior module reservations (main cave chain).
    for block in sorted(reserved, key=lambda r: r.start):
        start = (block.end + alignment - 1) // alignment * alignment
        if start + need > len(overlay_data):
            continue
        if any(r.overlaps(start, need) for r in forbidden):
            continue
        if max_file_offset is not None and start > max_file_offset:
            continue
        if _range_blocked(start, need, reserved, forbidden):
            continue
        nonzero = _region_nonzero(overlay_data, start, need)
        if nonzero <= max(need // 8, 16):
            ok, xrefs = _slot_passes_xref(
                overlay_data, overlay_load, start, need,
                check_vanilla_xrefs=check_vanilla_xrefs,
            )
            if ok:
                return CaveSlot(
                    file_offset=start,
                    size=need,
                    load_address=overlay_load + start,
                )
            if check_vanilla_xrefs:
                xref_rejects.append(
                    format_xref_report(
                        xrefs,
                        overlay_load=overlay_load,
                        slot_file_offset=start,
                        slot_size=need,
                    )
                )

    runs = find_zero_run(
        overlay_data,
        need,
        alignment,
        reserved=reserved,
        forbidden=forbidden,
        max_start=max_file_offset,
    )
    if not runs:
        raise RuntimeError(
            f"no zero run >= {need} bytes in overlay ({len(overlay_data)} total) "
            f"after {len(reserved)} reserved range(s)"
        )

    runs.sort(key=lambda item: (item[1], item[0]), reverse=True)
    for start, _length in runs:
        ok, xrefs = _slot_passes_xref(
            overlay_data, overlay_load, start, need,
            check_vanilla_xrefs=check_vanilla_xrefs,
        )
        if ok:
            return CaveSlot(
                file_offset=start,
                size=need,
                load_address=overlay_load + start,
            )
        if check_vanilla_xrefs:
            xref_rejects.append(
                format_xref_report(
                    xrefs,
                    overlay_load=overlay_load,
                    slot_file_offset=start,
                    slot_size=need,
                )
            )

    if check_vanilla_xrefs and xref_rejects:
        detail = "\n".join(xref_rejects[:5])
        if len(xref_rejects) > 5:
            detail += f"\n  ... {len(xref_rejects) - 5} more rejected zero run(s)"
        raise RuntimeError(
            f"no xref-safe zero run >= {need} bytes in overlay ({len(overlay_data)} total); "
            f"all candidates referenced by vanilla code/data.\n{detail}"
        )
    raise RuntimeError(
        f"no zero run >= {need} bytes in overlay ({len(overlay_data)} total) "
        f"after {len(reserved)} reserved range(s)"
    )
