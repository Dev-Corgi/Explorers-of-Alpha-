"""Vanilla overlay xref scan — detect branches/pointers into candidate cave slots."""

from __future__ import annotations

import struct
from dataclasses import dataclass

from .cave_reservations import FileRange


@dataclass(frozen=True)
class CaveXref:
    kind: str
    source_file_offset: int
    source_load_address: int
    target_load_address: int

    def target_file_offset_for(self, overlay_load: int) -> int:
        return self.target_load_address - overlay_load


def _decode_arm_branch(source_load: int, word: int) -> int | None:
    hi = word >> 24
    if hi not in (0xEA, 0xEB):
        return None
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return source_load + 8 + imm * 4


def _in_load_range(addr: int, overlay_load: int, span: int) -> bool:
    return overlay_load <= addr < overlay_load + span


def scan_overlay_xrefs(
    overlay_data: bytes,
    overlay_load: int,
) -> list[CaveXref]:
    """Scan all ARM branches and in-overlay word literals (single pass)."""
    hits: list[CaveXref] = []
    n = len(overlay_data)
    for off in range(0, n - 3, 4):
        source_load = overlay_load + off
        word = struct.unpack_from("<I", overlay_data, off)[0]

        branch_target = _decode_arm_branch(source_load, word)
        if branch_target is not None and _in_load_range(branch_target, overlay_load, n):
            hits.append(
                CaveXref(
                    kind="branch_bl" if (word >> 24) == 0xEB else "branch_b",
                    source_file_offset=off,
                    source_load_address=source_load,
                    target_load_address=branch_target,
                )
            )

        if _in_load_range(word, overlay_load, n):
            hits.append(
                CaveXref(
                    kind="word_literal",
                    source_file_offset=off,
                    source_load_address=source_load,
                    target_load_address=word,
                )
            )
    return hits


def collect_referenced_file_offsets(
    overlay_data: bytes,
    overlay_load: int,
    *,
    arm9_data: bytes | None = None,
    past_end_margin: int = 512,
) -> set[int]:
    """All file offsets in overlay_data that vanilla code/data points at."""
    n = len(overlay_data)
    referenced = {xref.target_file_offset_for(overlay_load) for xref in scan_overlay_xrefs(overlay_data, overlay_load)}

    for off in range(0, n - 3, 4):
        word = struct.unpack_from("<I", overlay_data, off)[0]
        if overlay_load + n <= word < overlay_load + n + past_end_margin:
            referenced.add(word - overlay_load)

    if arm9_data:
        for off in range(0, len(arm9_data) - 3, 4):
            word = struct.unpack_from("<I", arm9_data, off)[0]
            if overlay_load <= word < overlay_load + n + past_end_margin:
                referenced.add(word - overlay_load)

    return referenced


def scan_xrefs_into_range(
    overlay_data: bytes,
    overlay_load: int,
    *,
    range_file_start: int,
    range_size: int,
    arm9_data: bytes | None = None,
) -> list[CaveXref]:
    """Return vanilla code/data references into [range_file_start, +range_size)."""
    slot_start = range_file_start
    referenced = collect_referenced_file_offsets(
        overlay_data, overlay_load, arm9_data=arm9_data
    )
    hits: list[CaveXref] = []
    for xref in scan_overlay_xrefs(overlay_data, overlay_load):
        tgt = xref.target_file_offset_for(overlay_load)
        if slot_start <= tgt < slot_start + range_size:
            hits.append(xref)
    if arm9_data:
        for off in range(0, len(arm9_data) - 3, 4):
            word = struct.unpack_from("<I", arm9_data, off)[0]
            if overlay_load <= word < overlay_load + len(overlay_data):
                tgt = word - overlay_load
                if slot_start <= tgt < slot_start + range_size and tgt not in {
                    x.target_file_offset_for(overlay_load) for x in hits
                }:
                    hits.append(
                        CaveXref(
                            kind="arm9_word",
                            source_file_offset=off,
                            source_load_address=0x02000000 + off,
                            target_load_address=word,
                        )
                    )
    del referenced
    return hits


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


def _zero_run_length(data: bytes, start: int) -> tuple[int, int]:
    if start < 0 or start >= len(data) or data[start] != 0:
        return 0, start
    lo = start
    while lo > 0 and data[lo - 1] == 0:
        lo -= 1
    hi = start
    while hi < len(data) and data[hi] == 0:
        hi += 1
    return hi - lo, lo


def interior_slot_is_safe(
    overlay_data: bytes,
    overlay_load: int,
    file_offset: int,
    size: int,
    *,
    referenced: set[int],
    reserved: list[FileRange],
    forbidden: list[FileRange],
) -> bool:
    n = len(overlay_data)
    if file_offset + size > n:
        return False
    if _range_blocked(file_offset, size, reserved, forbidden):
        return False
    if any(file_offset <= ref < file_offset + size for ref in referenced):
        return False
    if any(overlay_data[file_offset : file_offset + size]):
        return False
    return True


def find_best_interior_cave_slot(
    overlay_data: bytes,
    overlay_load: int,
    need: int,
    *,
    alignment: int = 4,
    reserved: list[FileRange] | None = None,
    forbidden: list[FileRange] | None = None,
    arm9_data: bytes | None = None,
) -> int | None:
    """Pick the largest zero run that fits `need` strictly inside the overlay file."""
    reserved = reserved or []
    forbidden = forbidden or []
    referenced = collect_referenced_file_offsets(
        overlay_data, overlay_load, arm9_data=arm9_data
    )

    best: tuple[int, int] | None = None
    i = 0
    n = len(overlay_data)
    while i < n:
        if overlay_data[i] != 0:
            i += 1
            continue
        j = i
        while j < n and overlay_data[j] == 0:
            j += 1
        run_start_aligned = (i + alignment - 1) // alignment * alignment
        max_start = j - need
        for aligned_start in range(run_start_aligned, max_start + 1, alignment):
            if interior_slot_is_safe(
                overlay_data,
                overlay_load,
                aligned_start,
                need,
                referenced=referenced,
                reserved=reserved,
                forbidden=forbidden,
            ):
                run_len = j - aligned_start
                if best is None or run_len > best[0] or (
                    run_len == best[0] and aligned_start > best[1]
                ):
                    best = (run_len, aligned_start)
        i = j
    return None if best is None else best[1]


def slot_has_vanilla_xrefs(
    overlay_data: bytes,
    overlay_load: int,
    file_offset: int,
    size: int,
    *,
    arm9_data: bytes | None = None,
) -> tuple[bool, list[CaveXref]]:
    xrefs = scan_xrefs_into_range(
        overlay_data,
        overlay_load,
        range_file_start=file_offset,
        range_size=size,
        arm9_data=arm9_data,
    )
    referenced = collect_referenced_file_offsets(
        overlay_data, overlay_load, arm9_data=arm9_data
    )
    if any(file_offset <= ref < file_offset + size for ref in referenced):
        if not xrefs:
            xrefs = [
                CaveXref(
                    kind="referenced",
                    source_file_offset=0,
                    source_load_address=0,
                    target_load_address=overlay_load + file_offset,
                )
            ]
        return False, xrefs
    return not xrefs, xrefs


def find_safe_zero_slots(
    overlay_data: bytes,
    overlay_load: int,
    need: int,
    *,
    alignment: int = 4,
    reserved: list[FileRange] | None = None,
    forbidden: list[FileRange] | None = None,
    max_start: int | None = None,
    arm9_data: bytes | None = None,
) -> list[tuple[int, list[CaveXref]]]:
    """Zero runs that fit `need`, pass reserved/forbidden, and have no vanilla xrefs."""
    reserved = reserved or []
    forbidden = forbidden or []
    referenced = collect_referenced_file_offsets(
        overlay_data, overlay_load, arm9_data=arm9_data
    )
    safe: list[tuple[int, list[CaveXref]]] = []
    i = 0
    n = len(overlay_data)
    while i < n:
        if overlay_data[i] != 0:
            i += 1
            continue
        j = i
        while j < n and overlay_data[j] == 0:
            j += 1
        run_start_aligned = (i + alignment - 1) // alignment * alignment
        max_slot_start = j - need
        if max_start is not None:
            max_slot_start = min(max_slot_start, max_start)
        for aligned_start in range(run_start_aligned, max_slot_start + 1, alignment):
            if interior_slot_is_safe(
                overlay_data,
                overlay_load,
                aligned_start,
                need,
                referenced=referenced,
                reserved=reserved,
                forbidden=forbidden,
            ):
                safe.append((aligned_start, []))
        i = j
    safe.sort(key=lambda item: item[0])
    return safe


def format_xref_report(
    xrefs: list[CaveXref],
    *,
    overlay_load: int,
    slot_file_offset: int,
    slot_size: int,
) -> str:
    if not xrefs:
        return (
            f"  slot file [{slot_file_offset:#x},{slot_file_offset + slot_size:#x}) "
            f"RAM [{overlay_load + slot_file_offset:#x},{overlay_load + slot_file_offset + slot_size:#x}): "
            "no vanilla xrefs"
        )
    lines = [
        f"  slot file [{slot_file_offset:#x},{slot_file_offset + slot_size:#x}) "
        f"RAM [{overlay_load + slot_file_offset:#x},{overlay_load + slot_file_offset + slot_size:#x}): "
        f"{len(xrefs)} vanilla xref(s)"
    ]
    for xref in xrefs[:20]:
        tgt_off = xref.target_load_address - overlay_load
        lines.append(
            f"    {xref.kind:12} from {xref.source_load_address:#010x} (file {xref.source_file_offset:#x}) "
            f"-> {xref.target_load_address:#010x} (file {tgt_off:#x})"
        )
    if len(xrefs) > 20:
        lines.append(f"    ... {len(xrefs) - 20} more")
    return "\n".join(lines)
