#!/usr/bin/env python3
"""Analyze patched ROM for likely dungeon-exit crash causes (ov36 loader stack)."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parents[1]
VANILLA = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
PATCHED = ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds"
STATE = ROOT / "Export Rom" / "full_stack.state.json"

L29 = 0x022DC240
L31 = 0x02382820
L36 = 0x023A7080
A9 = 0x02000000

LOAD_OVERLAY = 0x020040AC
UNLOAD_OVERLAY = 0x02004868
OVERLAY_IS_LOADED = 0x02003ED0

cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def branch_dest(word: int, pc: int) -> int | None:
    top = (word >> 24) & 0xFF
    if top == 0xEA:
        imm = word & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        return pc + 8 + (imm << 2)
    if top == 0xEB:
        imm = word & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        return pc + 8 + (imm << 2)
    return None


def ov_bytes(rom: NintendoDSRom, idx: int) -> bytes:
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return rom.files[table[idx].fileID]


def ov_word(rom: NintendoDSRom, idx: int, addr: int) -> int:
    base = {29: L29, 31: L31, 36: L36}[idx]
    data = ov_bytes(rom, idx)
    return struct.unpack_from("<I", data, addr - base)[0]


def disasm_blob(data: bytes, base_addr: int, start_off: int, size: int = 0x60) -> list[str]:
    lines: list[str] = []
    for ins in cs.disasm(data[start_off : start_off + size], base_addr + start_off):
        lines.append(f"  {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
    return lines


def scan_bl_immediate(data: bytes, base: int, fn_addr: int, imm: int) -> list[int]:
    hits: list[int] = []
    start = fn_addr - base
    end = min(len(data), start + 0x4000)
    for off in range(max(0, start), end - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if (w >> 24) != 0xEB:
            continue
        if (w & 0xFF) != imm:
            continue
        pc = base + off
        hits.append(pc)
    return hits


def main() -> None:
    van = NintendoDSRom(VANILLA.read_bytes())
    pat = NintendoDSRom(PATCHED.read_bytes())
    state = json.loads(STATE.read_text(encoding="utf-8"))

    sites = {
        "RunDungeon": 0x022DEF38,
        "RunDungeon+4 (body)": 0x022DEF3C,
        "DungeonFree": 0x022DEAB0,
        "AllocTopScreenStatus": 0x022E7EC4,
    }

    print("=" * 72)
    print("1) ov29 dungeon lifecycle prologues (vanilla vs full_stack)")
    print("=" * 72)
    for name, addr in sites.items():
        vw = ov_word(van, 29, addr)
        pw = ov_word(pat, 29, addr)
        print(f"\n{name} @ {addr:#010x}")
        print(f"  vanilla: {vw:#010x}")
        print(f"  patched: {pw:#010x}")
        if dest := branch_dest(pw, addr):
            print(f"  patched branch/bl -> {dest:#010x}")

    ov29_pat = ov_bytes(pat, 29)
    print("\n--- disasm RunDungeon patched ---")
    print("\n".join(disasm_blob(ov29_pat, L29, 0x022DEF38 - L29, 0x20)))
    print("\n--- disasm overlay36_loader stub ---")
    stub_off = 0x40194
    print("\n".join(disasm_blob(ov29_pat, L29, stub_off, 0x80)))

    print("\n" + "=" * 72)
    print("2) LoadOverlay(36) / UnloadOverlay(36) usage in vanilla ov29")
    print("=" * 72)
    ov29_van = ov_bytes(van, 29)
    for label, imm in [("LoadOverlay", 36), ("UnloadOverlay", 36), ("LoadOverlay", 29), ("UnloadOverlay", 29)]:
        fn = LOAD_OVERLAY if "Load" in label else UNLOAD_OVERLAY
        hits = scan_bl_immediate(ov29_van, L29, fn, imm)
        print(f"  ov29 BL {label}({imm}): {len(hits)} site(s)")
        for h in hits[:8]:
            print(f"    caller near {h:#010x}")

    print("\n" + "=" * 72)
    print("3) DungeonFree region — vanilla vs patched disasm")
    print("=" * 72)
    off = 0x022DEAB0 - L29
    print("vanilla:")
    print("\n".join(disasm_blob(ov_bytes(van, 29), L29, off, 0x80)))
    print("patched:")
    print("\n".join(disasm_blob(ov29_pat, L29, off, 0x80)))

    print("\n" + "=" * 72)
    print("4) ov36 combat cave RAM still targeted by ov29 hooks after exit?")
    print("=" * 72)
    hook_sites = [
        ("RemoveUsedItemClearPath", 0x022EB658),
        ("GetSubMenuStringIdUseBranch", 0x022EB2DC),
        ("GetSubMenuStringIdReadBranch", 0x022EB2DC),  # tm/z chain same site family
        ("DealDamageBody", 0x0232E868),
        ("ApplyDamage", 0x0232F990),
    ]
    ov36_caves = [
        c for mod in state["applied"] for c in mod.get("caves", []) if c.get("overlay") == "ov36"
    ]
    cave_lo = min(c["load_address"] for c in ov36_caves)
    cave_hi = max(c["load_address"] + c["size"] for c in ov36_caves)
    print(f"  ov36 cave chain RAM [{cave_lo:#010x}..{cave_hi:#010x})")
    for name, site in hook_sites:
        w = ov_word(pat, 29, site)
        dest = branch_dest(w, site)
        in_cave = dest is not None and cave_lo <= dest < cave_hi
        print(f"  {name:32} @ {site:#010x} -> {dest:#010x if dest else 0}  ov36_cave={in_cave}")

    print("\n" + "=" * 72)
    print("5) ARM9 exit-adjacent sites (GetDungeonResultMsg cluster)")
    print("=" * 72)
    arm9_sites = {
        "GetDungeonResultMsg": 0x0200C4FC,
        "GetDungeonResultMsgCallSite": 0x0200C6F0,
    }
    for name, addr in arm9_sites.items():
        off = addr - A9
        vw = struct.unpack_from("<I", van.arm9, off)[0]
        pw = struct.unpack_from("<I", pat.arm9, off)[0]
        print(f"  {name} @ {addr:#010x}: vanilla {vw:#010x} patched {pw:#010x}")

    print("\n" + "=" * 72)
    print("6) z_move arm9 gauge cave + patched ov29 restore words")
    print("=" * 72)
    z_cave = next(
        c
        for mod in state["applied"]
        if mod["id"] == "z_move_v2"
        for c in mod["caves"]
        if c["overlay"] == "arm9"
    )
    off = z_cave["file_offset"]
    chunk = pat.arm9[off : off + 64]
    print(f"  arm9 cave file [{off:#x}..{off + z_cave['size']:#x}) RAM {z_cave['load_address']:#010x}")
    print(f"  bytes: {chunk.hex()}")

    print("\n" + "=" * 72)
    print("7) overlay36_loader / z_move hook overlap on RunDungeon")
    print("=" * 72)
    rd = ov_word(pat, 29, 0x022DEF38)
    dest = branch_dest(rd, 0x022DEF38)
    loader_stub = 0x022DC240 + 0x40194
    print(f"  RunDungeon -> {dest:#010x}")
    print(f"  loader stub base -> {loader_stub:#010x}")
    if dest and abs(dest - loader_stub) > 0x100:
        print("  *** RunDungeon does NOT branch into loader stub window ***")


if __name__ == "__main__":
    main()
