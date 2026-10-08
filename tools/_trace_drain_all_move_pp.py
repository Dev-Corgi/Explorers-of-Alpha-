#!/usr/bin/env python3
"""Map DrainAllMovePp call sites to in-game moves/effects."""
from __future__ import annotations

import struct
from collections import defaultdict
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.waza_p.handler import WazaPHandler

REPO = Path(__file__).resolve().parent.parent
OV29 = 0x022DC240
START_MFUNC = 0x02330134
STRIDE = 0x1C

DRAIN = 0x02345AD8
GENERIC_HELPER = 0x02345A3C
SPITE_HELPER = 0x0232A834
SPITE_EFFECT = 0x0232A340


def bl_target(pc: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def find_fn_start(van: bytes, addr: int, max_back: int = 0x900) -> int:
    for back in range(0, max_back, 4):
        a = addr - back
        if a < OV29:
            break
        w = struct.unpack_from("<I", van, a - OV29)[0]
        if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):
            return a
    return addr & ~0xF


def scan_bl_in_fn(van: bytes, fn: int, limit: int = 0x500) -> list[tuple[int, int]]:
    off = fn - OV29
    if off < 0 or off >= len(van):
        return []
    hits: list[tuple[int, int]] = []
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in cs.disasm(van[off : off + limit], fn):
        if ins.mnemonic == "bl":
            w = struct.unpack_from("<I", van, ins.address - OV29)[0]
            hits.append((ins.address, bl_target(ins.address, w)))
        if ins.mnemonic == "pop" and "pc" in ins.op_str and ins.address > fn + 8:
            break
    return hits


def main() -> None:
    van = (REPO / "unpacked/overlay/overlay_0029.bin").read_bytes()
    rom = NintendoDSRom.fromFile(REPO / "Vanilla Rom/Explorers of Alpha_Vanilla.nds")
    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/waza_cd.bin"))
    wp = WazaPHandler.deserialize(rom.getFileByName("BALANCE/waza_p.bin"))
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))
    cfg = get_ppmdu_config_for_rom(rom)
    move_names = strings.strings[
        cfg.string_index_data.string_blocks["Move Names"].begin :
        cfg.string_index_data.string_blocks["Move Names"].end + 1
    ]

    callers_of: dict[int, list[int]] = defaultdict(list)
    for off in range(0, len(van) - 4, 4):
        addr = OV29 + off
        w = struct.unpack_from("<I", van, off)[0]
        if w >> 24 not in (0xEA, 0xEB):
            continue
        callers_of[bl_target(addr, w)].append(addr)

    def primary_handler(eid: int) -> int | None:
        code = bytes(cd.get_effect_code(eid))
        if len(code) < 0x14:
            return None
        bl_addr = START_MFUNC + eid * STRIDE + 0x10
        return bl_target(bl_addr, struct.unpack_from("<I", code, 0x10)[0])

    handler_to_effects: dict[int, list[int]] = defaultdict(list)
    for eid in range(cd.nb_effects()):
        fn = primary_handler(eid)
        if fn is not None:
            handler_to_effects[fn].append(eid)

    effect_to_moves: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for mid in range(len(wp.moves)):
        eid = cd.get_item_effect_id(mid)
        effect_to_moves[eid].append((mid, move_names[mid]))

    def fmt_moves(eids: list[int]) -> str:
        parts: list[str] = []
        for eid in eids:
            for mid, name in effect_to_moves.get(eid, []):
                parts.append(f"{mid}:{name}")
        return ", ".join(parts) if parts else "(no move mapped)"

    print("=== 4 DrainAllMovePp sites -> game context ===\n")

    # --- Site 1: Spite ---
    print("1) 0x0232A8E0  SpiteMessageHelper (Spite only)")
    print(f"   Move: 35 Spite (effect 216 -> handler stub -> runtime repack)")
    spite_refs = callers_of.get(SPITE_HELPER, [])
    print(f"   SpiteMessageHelper callers: {[hex(x) for x in spite_refs]}")
    print(f"   Spite effect fn: {SPITE_EFFECT:#x}, BLs inside:")
    for a, t in scan_bl_in_fn(van, SPITE_EFFECT):
        mark = " << DRAIN PATH" if t in (SPITE_HELPER, DRAIN) else ""
        print(f"     {a:#x} -> {t:#x}{mark}")
    print()

    # --- Site 2: Generic helper ---
    print("2) 0x02345ACC  Generic message helper @ 0x02345A3C")
    print("   Same PP-drain + message pattern as Spite helper, shared by multiple effects.")
    for site in callers_of.get(GENERIC_HELPER, []):
        fn = find_fn_start(van, site)
        eids = handler_to_effects.get(fn, [])
        print(f"   caller {site:#x} in fn {fn:#x}")
        print(f"     effects {eids} -> {fmt_moves(eids)}")
    print()

    # Also scan: any effect handler that BLs generic helper or drain directly
    print("   All effect handlers that reach generic helper / DrainAllMovePp:")
    seen_effects: set[int] = set()
    for eid in range(cd.nb_effects()):
        fn = primary_handler(eid)
        if fn is None:
            continue
        for _, t in scan_bl_in_fn(van, fn):
            if t in (GENERIC_HELPER, DRAIN):
                if eid not in seen_effects:
                    seen_effects.add(eid)
                    print(f"     effect {eid} handler {fn:#x} -> {t:#x} | {fmt_moves([eid])}")
    print()

    # --- Sites 3 & 4: 0x22F54BC subtree ---
    print("3) 0x02347B14  inside fn ~0x02347518")
    print("4) 0x02348000  inside fn 0x02347BC8")
    print("   Both called from parent ~0x022F54BC:")
    parent = 0x022F54BC
    for child in (0x02347BC8, 0x02347518):
        print(f"     {parent:#x} -> {child:#x} (sites {[hex(x) for x in callers_of.get(child, []) if x in callers_of.get(child, [])]})")
    print(f"   Parent callers ({parent:#x}):")
    for site in callers_of.get(parent, []):
        fn = find_fn_start(van, site)
        eids = handler_to_effects.get(fn, [])
        print(f"     {site:#x} fn {fn:#x} effects {eids} -> {fmt_moves(eids)}")

    # Walk up one more level from parent callers
    print("\n   Parent-of-parent (who calls the fn that calls 0x22F54BC):")
    for site in callers_of.get(parent, []):
        outer_fn = find_fn_start(van, site)
        for up in callers_of.get(outer_fn, []):
            up_fn = find_fn_start(van, up)
            eids = handler_to_effects.get(up_fn, [])
            print(f"     {up:#x} fn {up_fn:#x} effects {eids} -> {fmt_moves(eids)}")

    # Disasm head of 0x22F54BC for message/param clues
    print("\n   Disasm 0x22F54BC (first 40 ins):")
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in cs.disasm(van[parent - OV29 : parent - OV29 + 0xA0], parent):
        extra = ""
        if ins.mnemonic == "bl" and ins.op_str.startswith("#"):
            w = struct.unpack_from("<I", van, ins.address - OV29)[0]
            extra = f" -> {bl_target(ins.address, w):#x}"
        print(f"     {ins.address:#x}: {ins.mnemonic} {ins.op_str}{extra}")

    # Search waza_cd for effects pointing near these fns
    print("\n   Effects whose primary handler matches 0x22F54BC subtree fns:")
    subtree = {parent, 0x02347BC8, 0x02347518}
    for eid in range(cd.nb_effects()):
        fn = primary_handler(eid)
        if fn is None:
            continue
        bls = [t for _, t in scan_bl_in_fn(van, fn)]
        if fn in subtree or any(t in subtree for _, t in scan_bl_in_fn(van, fn)):
            print(f"     effect {eid} primary {fn:#x} | {fmt_moves([eid])}")
        elif any(t in (DRAIN, GENERIC_HELPER, SPITE_HELPER) for t in bls):
            pass  # already covered


if __name__ == "__main__":
    main()
