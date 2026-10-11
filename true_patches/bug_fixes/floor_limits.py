"""Keep Alpha's story exits, but remove item/difficulty shortening exits."""

from __future__ import annotations

from ndspy.rom import NintendoDSRom
from skytemple_files.data.inter_d.handler import InterDHandler
from skytemple_files.data.inter_d.model import InterDEntryType


def is_shortening_exit(entry, flags) -> bool:
    return (entry.ent_type == InterDEntryType.FSET
            and entry.game_var_id == 78 and entry.param1 in flags)


def apply_floor_limits(rom: NintendoDSRom, settings: dict) -> dict:
    path = settings["path"]
    flags = settings["remove_performance_flags"]
    model = InterDHandler.deserialize(rom.getFileByName(path))
    removed = []
    for dungeon, entries in enumerate(model.list_dungeons):
        kept = []
        for entry in entries:
            if is_shortening_exit(entry, flags):
                removed.append({"dungeon": dungeon, "floor": int(entry.floor),
                                "performance_flag": int(entry.param1)})
            else:
                kept.append(entry)
        model.list_dungeons[dungeon] = kept
    if removed:
        rom.setFileByName(path, InterDHandler.serialize(model))
    return {"overlay": "data", "table": path, "entries": len(removed),
            "fields_changed": len(removed), "details": {"removed": removed}}


def verify_floor_limits(rom: NintendoDSRom, settings: dict) -> None:
    model = InterDHandler.deserialize(rom.getFileByName(settings["path"]))
    for dungeon, entries in enumerate(model.list_dungeons):
        for entry in entries:
            if is_shortening_exit(entry, settings["remove_performance_flags"]):
                raise AssertionError(f"dungeon {dungeon}: shortening exit remains")
