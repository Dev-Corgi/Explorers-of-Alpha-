from __future__ import annotations

from .cave_gap import file_offset_after_cave
from .cave_reservations import FileRange

# Spinda EV v1/v2 sole owner of this ARM9 ExtraBits slot (through boot data @ 0x94AE8).
SPINDA_ARM9_CODE_FILE = 0x94624
SPINDA_ARM9_CODE_END = 0x94AE8

# tm_read ARM9 display cave (256 B).
ARM9_TM_READ_DISPLAY_FILE = 0x9F904
ARM9_TM_READ_DISPLAY_SIZE = 256

# orb_charges ARM9 — high cave after tm_read (640 B). Do not place @ 0x94454 (spinda adjacency).
ORB_ARM9_DISPLAY_FILE = 0x9FA04
ORB_ARM9_DISPLAY_SIZE = 768

# Z-Move v2 gauge trampoline (near GetDungeonResultMsgCallSite).
ZMOVE_ARM9_GAUGE_FILE = 0xAF2C0


def spinda_arm9_legacy_range() -> FileRange:
    return FileRange(SPINDA_ARM9_CODE_FILE, SPINDA_ARM9_CODE_END)


def spinda_arm9_legacy_forbidden_yaml() -> list[dict[str, int]]:
    return [{"start": SPINDA_ARM9_CODE_FILE, "end": SPINDA_ARM9_CODE_END}]


def orb_arm9_cave_forbidden_yaml() -> list[dict[str, int]]:
    return spinda_arm9_legacy_forbidden_yaml()


def preferred_orb_arm9_file_offset(state) -> int:
    """Pin orb ARM9 after tm_read / unite_combat tm display cave when present."""
    _tm_stack_ids = frozenset({"tm_read"})
    if state:
        for mod in state.applied:
            if mod.id not in _tm_stack_ids:
                continue
            for cave in mod.caves:
                if cave.overlay != "arm9":
                    continue
                if cave.size == ARM9_TM_READ_DISPLAY_SIZE or cave.file_offset == ARM9_TM_READ_DISPLAY_FILE:
                    return file_offset_after_cave(cave.file_offset, cave.size)
    return ORB_ARM9_DISPLAY_FILE


def state_has_tm_read_arm9_cave(state) -> bool:
    """True when a tm_read / unite* module already owns an ARM9 cave."""
    _tm_stack_ids = frozenset({"tm_read"})
    if not state:
        return False
    for mod in state.applied:
        if mod.id not in _tm_stack_ids:
            continue
        for cave in mod.caves:
            if cave.overlay == "arm9":
                return True
    return False
