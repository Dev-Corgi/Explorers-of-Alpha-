#!/usr/bin/env python3
"""Check ov29 load/unload vs dungeon item-use paths (hypothesis #4)."""

from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parents[1]
VANILLA = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
PATCHED = ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds"

A9 = 0x02000000
L29 = 0x022DC240
L31 = 0x02382820
OV29_ID = 29

# US EoS — from arm9 symbol tables / pmdsky-debug ram addresses
LOAD_OVERLAY = 0x020040AC
UNLOAD_OVERLAY = 0x02004868
OVERLAY_IS_LOADED = 0x02003ED0

ITEM_ENTRY_POINTS = [
    (0x02310F40, "Bag submenu USE"),
    (0x022FEF64, "Action49 USE branch"),
    (0x0231AC48, "UseItem+RemoveUsedItem"),
    (0x022EB658, "RemoveUsedItem hook site"),
    (0x022EB2E0, "GetSubMenuStringId_Continue hook"),
    (0x02322374, "UseItem"),
]

OV31_PATCH_SITES = [
    (0x02384C48, "orb SaveItemBeforeFill"),
    (0x02384C54, "orb/tm AfterAddSubMenu"),
    (0x023859C0, "z_move menu hook"),
]

cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def bl_dest(word: int, pc: int) -> int | None:
    top = (word >> 24) & 0xFF
    if top not in (0xEA, 0xEB):
        return None
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return pc + 8 + (imm << 2)


def find_bl_callers(data: bytes, base: int, target: int) -> list[int]:
    hits: list[int] = []
    for off in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        pc = base + off
        if bl_dest(w, pc) == target:
            hits.append(pc)
    return hits


def scan_mov_r0_imm(data: bytes, base: int, imm: int, lo: int, hi: int) -> list[int]:
    hits: list[int] = []
    for off in range(lo - base, hi - base, 4):
        if off < 0 or off + 4 > len(data):
            continue
        w = struct.unpack_from("<I", data, off)[0]
        if (w & 0xFFF000FF) == (0xE3A00000 | imm):
            hits.append(base + off)
    return hits


def backward_scan_for_overlay_ops(
    data: bytes,
    base: int,
    from_addr: int,
    max_insns: int = 80,
) -> dict[str, list[int]]:
    """Scan up to max_insns words before from_addr for overlay load/unload/isloaded."""
    off = from_addr - base
    start = max(0, off - max_insns * 4)
    chunk = data[start:off]
    found: dict[str, list[int]] = {"LoadOverlay(29)": [], "UnloadOverlay(29)": [], "OverlayIsLoaded(29)": []}
    for rel in range(0, len(chunk) - 4, 4):
        addr = base + start + rel
        w = struct.unpack_from("<I", chunk, rel)[0]
        w_next = struct.unpack_from("<I", chunk, rel + 4)[0] if rel + 4 < len(chunk) else 0
        is_mov29 = (w & 0xFFFFFFF0) == 0xE3A00010 and (w & 0xFF) == OV29_ID
        if not is_mov29:
            continue
        dest = bl_dest(w_next, addr + 4)
        if dest == LOAD_OVERLAY:
            found["LoadOverlay(29)"].append(addr)
        elif dest == UNLOAD_OVERLAY:
            found["UnloadOverlay(29)"].append(addr)
        elif dest == OVERLAY_IS_LOADED:
            found["OverlayIsLoaded(29)"].append(addr)
    return found


def show_branch(data: bytes, base: int, addr: int, label: str) -> None:
    off = addr - base
    if off < 0 or off + 4 > len(data):
        print(f"  {label} {addr:#010x}: OUT OF RANGE")
        return
    w = struct.unpack_from("<I", data, off)[0]
    dest = bl_dest(w, addr)
    in_ov29 = L29 <= addr < L29 + len(data) if base == L29 else False
    region = "ov29" if base == L29 else ("ov31" if base == L31 else "arm9")
    if dest is not None:
        target_region = "ov29" if L29 <= dest < L29 + 0x100000 else (
            "ov31" if L31 <= dest < L31 + 0x100000 else "arm9/other"
        )
        print(f"  {label} [{region}] {addr:#010x}: branch -> {dest:#010x} ({target_region})")
    else:
        ins = list(cs.disasm(data[off : off + 4], addr))[0]
        print(f"  {label} [{region}] {addr:#010x}: {ins.mnemonic} {ins.op_str}")


def main() -> None:
    van = NintendoDSRom(VANILLA.read_bytes())
    table = loadOverlayTable(van.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = van.files[table[29].fileID]
    ov31 = van.files[table[31].fileID]
    arm9 = bytes(van.arm9)

    print("=" * 72)
    print("ARM9 overlay helpers")
    print("=" * 72)
    for name, addr in [
        ("LoadOverlay", LOAD_OVERLAY),
        ("UnloadOverlay", UNLOAD_OVERLAY),
        ("OverlayIsLoaded", OVERLAY_IS_LOADED),
    ]:
        ins = list(cs.disasm(arm9[addr - A9 : addr - A9 + 8], addr))
        print(f"  {name} @ {addr:#010x}: {ins[0].mnemonic if ins else '?'}")

    print("\n" + "=" * 72)
    print("Who calls UnloadOverlay in ov29 / ov31? (any overlay id)")
    print("=" * 72)
    for label, data, base in [("ov29", ov29, L29), ("ov31", ov31, L31)]:
        callers = find_bl_callers(data, base, UNLOAD_OVERLAY)
        print(f"  {label}: {len(callers)} callers")
        for c in callers[:12]:
            print(f"    {c:#010x}")

    print("\n" + "=" * 72)
    print("Explicit UnloadOverlay(29) in ov29 / ov31")
    print("=" * 72)
    for label, data, base in [("ov29", ov29, L29), ("ov31", ov31, L31)]:
        mov29 = scan_mov_r0_imm(data, base, OV29_ID, base, base + len(data))
        unloads = []
        for m in mov29:
            off = m - base
            if off + 4 >= len(data):
                continue
            w2 = struct.unpack_from("<I", data, off + 4)[0]
            if bl_dest(w2, m + 4) == UNLOAD_OVERLAY:
                unloads.append(m)
        print(f"  {label}: {len(unloads)} UnloadOverlay(29) sites")
        for u in unloads[:15]:
            print(f"    {u:#010x}")

    print("\n" + "=" * 72)
    print("Backward scan: overlay ops before item entry points (vanilla ov29)")
    print("=" * 72)
    for addr, name in ITEM_ENTRY_POINTS:
        found = backward_scan_for_overlay_ops(ov29, L29, addr, max_insns=120)
        hits = {k: v for k, v in found.items() if v}
        print(f"\n  {name} @ {addr:#010x}")
        if not hits:
            print("    (no Load/Unload/IsLoaded(29) in prior 120 insns)")
        else:
            for k, v in hits.items():
                for a in v[-3:]:
                    print(f"    {k} @ {a:#010x} (before entry)")

    print("\n" + "=" * 72)
    print("ov31 -> ov29 cross-overlay branches (vanilla vs patched)")
    print("=" * 72)
    if PATCHED.is_file():
        pat = NintendoDSRom(PATCHED.read_bytes())
        ov31p = pat.files[loadOverlayTable(pat.arm9OverlayTable, lambda _i, _n: b"")[31].fileID]
        for addr, label in OV31_PATCH_SITES:
            print(f"\n  {label}:")
            show_branch(ov31, L31, addr, "vanilla")
            show_branch(ov31p, L31, addr, "patched")
            found = backward_scan_for_overlay_ops(ov31, L31, addr, max_insns=150)
            hits = {k: v for k, v in found.items() if v}
            if hits:
                for k, v in hits.items():
                    print(f"    before vanilla site: {k} @ {v[-1]:#010x}")
            else:
                print("    before vanilla site: no overlay(29) guard in prior 150 insns")

    print("\n" + "=" * 72)
    print("ov29 hook sites: branch targets (patched full_stack)")
    print("=" * 72)
    if PATCHED.is_file():
        pat = NintendoDSRom(PATCHED.read_bytes())
        ov29p = pat.files[loadOverlayTable(pat.arm9OverlayTable, lambda _i, _n: b"")[29].fileID]
        hooks = [
            (0x022EB658, "RemoveUsedItemClearPath"),
            (0x022EB2E0, "GetSubMenuStringId_Continue"),
            (0x022EB2DC, "GetSubMenuStringId+0x14 tm/z chain"),
        ]
        for addr, label in hooks:
            show_branch(ov29p, L29, addr, label)

    print("\n" + "=" * 72)
    print("Dungeon floor transition: UnloadOverlay near ov31 ProcessFloor?")
    print("=" * 72)
    # scan ov31 for clusters of UnloadOverlay callers
    unload_callers_ov31 = find_bl_callers(ov31, L31, UNLOAD_OVERLAY)
    for c in unload_callers_ov31[:20]:
        # show mov r0 before bl
        off = c - L31
        prev = struct.unpack_from("<I", ov31, off - 4)[0] if off >= 4 else 0
        imm = prev & 0xFF if (prev & 0xFFF00000) == 0xE3A00000 else None
        print(f"  UnloadOverlay caller @ {c:#010x}, prior mov r0 imm={imm}")


if __name__ == "__main__":
    main()
