"""Copy Pikachu's level-up EXP curve onto every m_level.bin entry.

Only `experience_required` is replaced. Per-level HP/Atk/SpA/Def/SpD growth
bytes stay species-specific. Applies to BALANCE/ and UTILITY/ m_level.bin.
Template: md / pack index 25 (Pikachu, national dex 025).
"""

from __future__ import annotations

from typing import Any

from ndspy.rom import NintendoDSRom
from range_typed_integers import i32
from skytemple_files.common.types.file_types import FileType
from skytemple_files.data.level_bin_entry.model import LevelBinEntry
from skytemple_files.data.level_bin_entry.writer import LevelBinEntryWriter

PIKACHU_INDEX = 25
M_LEVEL_PATHS = ("BALANCE/m_level.bin", "UTILITY/m_level.bin")


def _load_entry(pack, index: int) -> LevelBinEntry:
    sir0 = FileType.SIR0.deserialize(bytes(pack[index]))
    data = FileType.PKDPX.deserialize(sir0.content).decompress()
    return LevelBinEntry(data)


def _store_entry(pack, index: int, entry: LevelBinEntry) -> None:
    raw = LevelBinEntryWriter(entry).write()
    pk = FileType.PKDPX.compress(raw).to_bytes()
    pack[index] = FileType.SIR0.serialize(FileType.SIR0.wrap(pk, []))


def patch_m_level_exp_to_pikachu(rom: NintendoDSRom) -> dict[str, Any]:
    """Set every species' experience_required table to Pikachu's."""
    reports: list[dict[str, Any]] = []
    for path in M_LEVEL_PATHS:
        pack = FileType.BIN_PACK.deserialize(rom.getFileByName(path))
        if PIKACHU_INDEX >= len(pack):
            raise RuntimeError(f"{path}: missing Pikachu entry {PIKACHU_INDEX}")
        template = _load_entry(pack, PIKACHU_INDEX)
        if len(template) != 100:
            raise RuntimeError(
                f"{path}: Pikachu entry has {len(template)} levels, want 100"
            )
        pika_exp = [i32(int(template[i].experience_required)) for i in range(100)]
        changed = 0
        for index in range(len(pack)):
            entry = _load_entry(pack, index)
            if len(entry) != 100:
                raise RuntimeError(
                    f"{path}: entry {index} has {len(entry)} levels, want 100"
                )
            dirty = False
            for i in range(100):
                if int(entry[i].experience_required) != int(pika_exp[i]):
                    entry[i].experience_required = pika_exp[i]
                    dirty = True
            if dirty:
                _store_entry(pack, index, entry)
                changed += 1
        rom.setFileByName(path, FileType.BIN_PACK.serialize(pack))
        reports.append(
            {
                "path": path,
                "entries": len(pack),
                "changed": changed,
                "template_index": PIKACHU_INDEX,
            }
        )
    return {"m_level_exp_pikachu": reports}
