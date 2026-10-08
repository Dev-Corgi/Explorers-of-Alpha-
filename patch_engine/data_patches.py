from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DataPatchRecord:
    overlay: str
    table: str
    entries: int
    fields_changed: int
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overlay": self.overlay,
            "table": self.table,
            "entries": self.entries,
            "fields_changed": self.fields_changed,
            "details": self.details,
        }
