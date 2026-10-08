"""Install the SkyTemple teammate-push hook at its original addresses.

The body is PC-relative, so it stays at overlay36 file 0xE00
(RAM 0x023A7E80). That hole is before the truepatch cave chain.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_files_from_rom_with_extension, get_ppmdu_config_for_rom
from skytemple_files.data.str.handler import StrHandler

from patch_engine.overlay_caves import get_rom_binary, write_rom_binary
from patch_engine.state import AppliedModule, CaveAllocation, HookRecord

OV29_LOAD = 0x022DC240
OV36_LOAD = 0x023A7080

HOOK_OFF = 0x022F2680 - OV29_LOAD
TAIL_OFF = 0x022F26C4 - OV29_LOAD
CAVE_OFF = 0x023A7E80 - OV36_LOAD

ORIGINAL_HOOK = bytes.fromhex("14009de5")
PATCHED_HOOK = bytes.fromhex("fed502ea")
ORIGINAL_TAIL = bytes.fromhex("dc081fe50210a0e3b000d0e1020010e30000a0130100a003")
PATCHED_TAIL = bytes.fromhex("0100a0e30210a0e30000a0e10000a0e10000a0e10000a0e1")

# text_e index. LogMessageById subtracts 1 before the lookup, so the
# immediate in the cave is this index plus one.
MESSAGE_STRING_INDEX = 19141
MESSAGE_ID = MESSAGE_STRING_INDEX + 1
MESSAGE_TEXT = "[string:0] pushed [string:1]!"
MESSAGE_LITERAL_OFF = 0x023A814C - 0x023A7E80


def _cave_bytes(module_dir: Path) -> bytes:
    blob = bytearray((module_dir / "cave.bin").read_bytes())
    if len(blob) != 0x300:
        raise RuntimeError(f"team_push cave.bin is {len(blob)} bytes, want 0x300")
    blob[MESSAGE_LITERAL_OFF : MESSAGE_LITERAL_OFF + 4] = MESSAGE_ID.to_bytes(4, "little")
    return bytes(blob)


def _text_e(rom: NintendoDSRom):
    config = get_ppmdu_config_for_rom(rom)
    for filename in get_files_from_rom_with_extension(rom, "str"):
        if filename.endswith("text_e.str"):
            strings = StrHandler.deserialize(
                rom.getFileByName(filename), string_encoding=config.string_encoding
            )
            return filename, config, strings
    raise RuntimeError("text_e.str not found in ROM")


def _write_push_message(rom: NintendoDSRom) -> None:
    filename, _, strings = _text_e(rom)
    if len(strings.strings) <= MESSAGE_STRING_INDEX:
        raise RuntimeError(
            f"team_push string {MESSAGE_STRING_INDEX} is past the end of text_e.str"
        )
    current = strings.strings[MESSAGE_STRING_INDEX]
    if current not in ("", MESSAGE_TEXT):
        raise RuntimeError(
            f"team_push string {MESSAGE_STRING_INDEX} is in use: {current!r}"
        )
    strings.strings[MESSAGE_STRING_INDEX] = MESSAGE_TEXT
    rom.setFileByName(filename, StrHandler.serialize(strings))


def _slice(buf: bytes, off: int, n: int) -> bytes:
    return bytes(buf[off : off + n])


def apply_team_push_module(
    *,
    module_id: str,
    module_dir: Path,
    manifest: dict[str, Any],
    rom: NintendoDSRom,
    config,
) -> AppliedModule:
    cave = _cave_bytes(module_dir)
    ov29 = get_rom_binary(rom, "ov29")
    ov36 = get_rom_binary(rom, "ov36")
    hook = _slice(ov29, HOOK_OFF, 4)
    tail = _slice(ov29, TAIL_OFF, len(PATCHED_TAIL))
    body = _slice(ov36, CAVE_OFF, len(cave))
    already = hook == PATCHED_HOOK and tail == PATCHED_TAIL and body == cave
    fresh = hook == ORIGINAL_HOOK and tail == ORIGINAL_TAIL and body == bytes(len(cave))
    if not already and not fresh:
        raise RuntimeError(
            "team_push site is neither the 4273 original nor the installed push hook"
        )
    if fresh:
        ov29[HOOK_OFF : HOOK_OFF + 4] = PATCHED_HOOK
        ov29[TAIL_OFF : TAIL_OFF + len(PATCHED_TAIL)] = PATCHED_TAIL
        ov36[CAVE_OFF : CAVE_OFF + len(cave)] = cave
        write_rom_binary(rom, config, "ov29", bytes(ov29))
        write_rom_binary(rom, config, "ov36", bytes(ov36))
    _write_push_message(rom)
    return AppliedModule(
        id=module_id,
        version=int(manifest.get("version", 1)),
        caves=[
            CaveAllocation(
                overlay="ov36",
                file_offset=CAVE_OFF,
                size=len(cave),
                load_address=OV36_LOAD + CAVE_OFF,
            )
        ],
        hooks=[
            HookRecord(
                name="TeamPush",
                site=OV29_LOAD + HOOK_OFF,
                kind="overwrite",
                target_symbol="TeamPushCave",
                chain="first",
            )
        ],
        data=[{"already_present": already, "string_index": MESSAGE_STRING_INDEX, "message_id": MESSAGE_ID}],
    )


def verify_team_push_module(rom_path: Path, module_dir: Path) -> None:
    cave = _cave_bytes(module_dir)
    rom = NintendoDSRom(rom_path.read_bytes())
    ov29 = get_rom_binary(rom, "ov29")
    ov36 = get_rom_binary(rom, "ov36")
    if _slice(ov29, HOOK_OFF, 4) != PATCHED_HOOK:
        raise AssertionError("team_push: ov29 hook is not the push branch")
    if _slice(ov29, TAIL_OFF, len(PATCHED_TAIL)) != PATCHED_TAIL:
        raise AssertionError("team_push: ov29 direction check was not replaced")
    if _slice(ov36, CAVE_OFF, len(cave)) != cave:
        raise AssertionError("team_push: ov36 body mismatch")
    _, _, strings = _text_e(rom)
    if strings.strings[MESSAGE_STRING_INDEX] != MESSAGE_TEXT:
        raise AssertionError(
            f"team_push: string {MESSAGE_STRING_INDEX} is {strings.strings[MESSAGE_STRING_INDEX]!r}"
        )
