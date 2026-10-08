from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CaveAllocation:
    overlay: str
    file_offset: int
    size: int
    load_address: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "overlay": self.overlay,
            "file_offset": self.file_offset,
            "file_offset_hex": f"0x{self.file_offset:X}",
            "size": self.size,
            "load_address": self.load_address,
            "load_address_hex": f"0x{self.load_address:X}",
        }


@dataclass
class HookRecord:
    name: str
    site: int
    kind: str
    target_symbol: str
    chain: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "site": self.site,
            "site_hex": f"0x{self.site:X}",
            "kind": self.kind,
            "target_symbol": self.target_symbol,
            "chain": self.chain,
        }


@dataclass
class AppliedModule:
    id: str
    version: int
    caves: list[CaveAllocation] = field(default_factory=list)
    hooks: list[HookRecord] = field(default_factory=list)
    data: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out = {
            "id": self.id,
            "version": self.version,
            "caves": [c.to_dict() for c in self.caves],
            "hooks": [h.to_dict() for h in self.hooks],
        }
        if self.data:
            out["data"] = self.data
        return out


@dataclass
class BuildState:
    rom_profile: str
    overlay29_load: int
    applied: list[AppliedModule] = field(default_factory=list)

    def get_module(self, module_id: str) -> AppliedModule | None:
        for mod in self.applied:
            if mod.id == module_id:
                return mod
        return None

    def upsert_module(self, record: AppliedModule) -> None:
        self.applied = [m for m in self.applied if m.id != record.id]
        self.applied.append(record)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rom_profile": self.rom_profile,
            "overlay29_load": self.overlay29_load,
            "overlay29_load_hex": f"0x{self.overlay29_load:X}",
            "applied": [m.to_dict() for m in self.applied],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BuildState:
        applied = []
        for raw in data.get("applied", []):
            caves = [
                CaveAllocation(
                    overlay=c["overlay"],
                    file_offset=int(c["file_offset"]),
                    size=int(c["size"]),
                    load_address=int(c["load_address"]),
                )
                for c in raw.get("caves", [])
            ]
            hooks = [
                HookRecord(
                    name=h["name"],
                    site=int(h["site"]),
                    kind=h["kind"],
                    target_symbol=h["target_symbol"],
                    chain=h["chain"],
                )
                for h in raw.get("hooks", [])
            ]
            applied.append(
                AppliedModule(
                    id=raw["id"],
                    version=int(raw.get("version", 1)),
                    caves=caves,
                    hooks=hooks,
                    data=list(raw.get("data") or []),
                )
            )
        return cls(
            rom_profile=data.get("rom_profile", "us_vanilla"),
            overlay29_load=int(data.get("overlay29_load", 0x022DC240)),
            applied=applied,
        )


def load_state(path: Path) -> BuildState | None:
    if not path.is_file():
        return None
    return BuildState.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_state(path: Path, state: BuildState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")
