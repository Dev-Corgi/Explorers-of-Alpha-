#!/usr/bin/env python3
"""Comprehensive orb_charges hook + consume-path audit for Cleanse Orb bug."""
from __future__ import annotations

import struct
import sys
from collections import deque
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom
import pmdsky_debug_py.na as na

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROM = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges.nds"
)

L = 0x022DC240
ARM9 = 0x02000000
OV10 = 0x022BCA80
CLEAR = 0x0200D81C
F600 = 0x0200F600
F694 = 0x0200F694
F558 = 0x0200F558
POST_CLEAR = 0x0231B68C
CAVE_OV29 = 0x023304EC
CAVE_ARM9 = 0x0209F904

HOOKS_OV29 = {
    "RemoveUsedItemEquivPath": 0x022EB648,
    "RemoveUsedItemClearPath": 0x022EB658,
    "Category9UseEquivCheckPath": 0x022F5690,
    "Category9UseClearPath": 0x022F5698,
    "Category9UseEquivDecPath": 0x022F56E0,
    "Category9UseDecrementPath": 0x022F56E8,
    "FloorUseEquivCheckPath": 0x022F51A8,
    "FloorUseClearPath": 0x022F51B8,
    "AltUseClearPath": 0x022F4D48,
    "InlineItemClear": 0x022EC878,
    "Type5InlineClearCall": 0x022ECA90,
    "ItemEffectClearSlot1": 0x022FB2F0,
    "ItemEffectClearSlot2": 0x022FB3A8,
    "ItemEffectPostClearCall1": 0x022FB310,
    "ItemEffectPostClearCall2": 0x022FB3C8,
}
HOOKS_ARM9 = {
    "RemoveEquivItemNoHole": 0x0200F600,
    "RemoveEquivItemVariant": 0x0200F694,
    "RemoveEquivItemScan": 0x0200F558,
}
HOOKS_OV10 = {"DungeonExitCleanStickyCall": 0x022C29F0}

HOOKED_CLEAR_SITES = {
    0x022EB658, 0x022F5698, 0x022F56E8, 0x022F51B8, 0x022F4D48,
    0x022EC878, 0x022ECA90, 0x022FB2F0, 0x022FB3A8,
}
HOOKED_EQUIV = {F600, F694, F558}


def branch_target(pc: int, w: int) -> tuple[str, int | None]:
    cond = (w >> 28) & 0xF
    op = (w >> 26) & 0x3
    imm24 = w & 0xFFFFFF
    if imm24 & 0x800000:
        imm24 -= 1 << 24
    if op == 0b1010:  # bl
        return "bl", (pc + 8 + (imm24 << 2)) & 0xFFFFFFFF
    if op == 0b1011:  # blx imm
        return "blx", (pc + 8 + (imm24 << 2)) & 0xFFFFFFFF
    if op == 0b1010 + 1 or (op == 0b1011 and cond != 0xF):  # b / blx reg handled below
        pass
    if (w & 0x0E000000) == 0x0A000000:  # b
        return "b", (pc + 8 + (imm24 << 2)) & 0xFFFFFFFF
    return "other", None


def verify_hooks(data: bytes, base: int, hooks: dict[str, int], cave: int, label: str) -> None:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    print(f"=== {label} hook verification (cave @{cave:08X}) ===")
    all_ok = True
    for name, addr in sorted(hooks.items(), key=lambda x: x[1]):
        off = addr - base
        w = struct.unpack_from("<I", data, off)[0]
        ins = list(cs.disasm(data[off : off + 4], addr))[0]
        kind, tgt = branch_target(addr, w)
        ok = tgt is not None and tgt >= cave
        if not ok:
            all_ok = False
        tgt_s = f"{tgt:08X}" if tgt else "???"
        print(f"  {name:32s} @{addr:08X}: {ins.mnemonic:4s} -> {tgt_s}  [{'OK' if ok else 'FAIL'}]")
    print(f"  Overall: {'PASS' if all_ok else 'FAIL'}\n")


def find_bl_callers(data: bytes, base: int, target: int, lo: int, hi: int) -> list[int]:
    out = []
    for addr in range(lo, hi, 4):
        off = addr - base
        if off < 0 or off + 4 > len(data):
            continue
        w = struct.unpack_from("<I", data, off)[0]
        _, tgt = branch_target(addr, w)
        if tgt == target:
            out.append(addr)
    return out


def successors(addr: int, cs: Cs, data: bytes, base: int) -> list[int]:
    off = addr - base
    if off < 0 or off + 4 > len(data):
        return []
    ins = list(cs.disasm(data[off : off + 4], addr))
    if not ins:
        return []
    ins = ins[0]
    out: list[int] = []
    w = struct.unpack_from("<I", data, off)[0]
    if ins.mnemonic.startswith("bl"):
        _, tgt = branch_target(addr, w)
        out.append(addr + 4)
        if tgt:
            out.append(tgt)
    elif ins.mnemonic in ("b", "bx") and ins.op_str.startswith("#"):
        out.append(int(ins.op_str.replace("#", ""), 16))
    elif ins.mnemonic.startswith("b"):
        _, tgt = branch_target(addr, w)
        if tgt:
            out.append(tgt)
        out.append(addr + 4)
    else:
        out.append(addr + 4)
    return out


def shortest_path(start: int, target: int, cs: Cs, data: bytes, base: int, limit: int = 600) -> list[int] | None:
    q = deque([(start, [start])])
    seen: set[int] = set()
    while q:
        addr, path = q.popleft()
        if addr == target:
            return path
        if addr in seen or len(path) > limit:
            continue
        seen.add(addr)
        for nxt in successors(addr, cs, data, base):
            if L <= nxt <= 0x02360000 or ARM9 <= nxt <= 0x02100000:
                q.append((nxt, path + [nxt]))
    return None


def bfs_bl_targets(start: int, targets: dict[int, str], cs: Cs, data: bytes, base: int, max_depth: int = 20) -> list[tuple]:
    found = []
    q = deque([(start, 0, hex(start))])
    seen: set[int] = set()
    while q and len(found) < 60:
        addr, depth, path = q.popleft()
        if depth > max_depth or addr in seen:
            continue
        seen.add(addr)
        off = addr - base
        if off < 0 or off + 4 > len(data):
            continue
        for ins in cs.disasm(data[off : off + 0x200], addr):
            if ins.address > addr + 0x200:
                break
            if ins.mnemonic == "bl" and ins.op_str.startswith("#"):
                tgt = int(ins.op_str.replace("#", ""), 16)
                if tgt in targets:
                    found.append((depth, ins.address, targets[tgt], path))
                elif L <= tgt <= 0x02360000 and depth < max_depth:
                    q.append((tgt, depth + 1, f"{path}->{ins.address:08X}"))
            if ins.mnemonic.startswith("b") and ins.op_str.startswith("#"):
                tgt = int(ins.op_str.replace("#", ""), 16)
                if L <= tgt <= 0x02360000 and depth < max_depth:
                    q.append((tgt, depth + 1, f"{path}->b@{ins.address:08X}"))
    return found


def main() -> None:
    rom_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROM
    rom = NintendoDSRom(rom_path.read_bytes())
    arm9 = rom.arm9
    ov10 = rom.loadArm9Overlays([10])[10].data
    ov29 = rom.loadArm9Overlays([29])[29].data
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    print(f"ROM: {rom_path.name}\n")
    verify_hooks(arm9, ARM9, HOOKS_ARM9, CAVE_ARM9, "ARM9")
    verify_hooks(ov10, OV10, HOOKS_OV10, CAVE_ARM9, "OV10")
    verify_hooks(ov29, L, HOOKS_OV29, CAVE_OV29, "OV29")

    # Bag Use -> UseItem path
    use_item = 0x02322374  # from trace_bag_orb_use
    print("=== Bag Use entry points ===")
    for site, desc in [
        (0x02310F40, "Bag submenu USE"),
        (0x022FEF64, "Action 49 USE branch"),
        (0x0231AC48, "UseItem + RemoveUsedItem helper"),
    ]:
        print(f"  {desc} @{site:08X}")
        for ins in cs.disasm(ov29[site - L : site - L + 16], site):
            print(f"    {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
    print()

    # Reachability from FEBAC (action 49 resolver)
    print("=== Reachability from Action49 resolver (0x022FEBAC) ===")
    consume_targets = {
        CLEAR: "ClearItemSlot (arm9)",
        F600: "RemoveEquivItemNoHole",
        F694: "RemoveEquivItemVariant",
        F558: "RemoveEquivItemScan",
        POST_CLEAR: "ItemEffectPostClear",
        0x02346A44: "ov29 ClearItemSlot call",
        0x022FDC1C: "ov29 ClearItemSlot call2",
        0x022F4968: "action57 ClearItemSlot",
        0x022EC878: "InlineItemClear (hooked)",
        0x022FB2F0: "ItemEffectClearSlot1 (hooked)",
    }
    for tgt, name in sorted(consume_targets.items(), key=lambda x: x[0]):
        p = shortest_path(0x022FEBAC, tgt, cs, ov29, L)
        hooked = ""
        if tgt == CLEAR:
            hooked = " (via hooked bl sites)"
        elif tgt in HOOKED_EQUIV:
            hooked = " (ARM9 hooked)"
        elif tgt in HOOKED_CLEAR_SITES:
            hooked = " (hooked entry)"
        elif tgt == POST_CLEAR:
            hooked = " (partial: MaybeSkip hook before call)"
        status = f"REACHABLE len={len(p)}" if p else "NOT reachable"
        print(f"  -> {name} @{tgt:08X}: {status}{hooked}")
    print()

    # All ClearItemSlot bl in ov29
    print("=== All bl ClearItemSlot in ov29 ===")
    callers = find_bl_callers(ov29, L, CLEAR, L, L + len(ov29))
    for c in callers:
        hooked = "HOOKED" if c in HOOKED_CLEAR_SITES else "UNHOOKED"
        p = shortest_path(0x022FEBAC, c, cs, ov29, L)
        reach = "from Action49" if p else "not from Action49"
        print(f"  @{c:08X} [{hooked}] [{reach}]")
        for ins in cs.disasm(ov29[c - L - 12 : c - L + 8], c - 12):
            print(f"    {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
    print()

    # BFS from key starts
    targets = {CLEAR: "ClearItemSlot", F600: "F600", F558: "F558", POST_CLEAR: "PostClear"}
    for start, label in [
        (0x02322374, "UseItem"),
        (0x022FEBAC, "Action49"),
        (0x0231B68C, "ItemEffectPostClear"),
    ]:
        found = bfs_bl_targets(start, targets, cs, ov29, L)
        print(f"=== BFS bl consume targets from {label} ({start:08X}) ===")
        seen = set()
        for depth, site, tgt_name, path in sorted(found, key=lambda x: (x[2], x[1])):
            key = (site, tgt_name)
            if key in seen:
                continue
            seen.add(key)
            hooked = "hooked" if site in HOOKED_CLEAR_SITES or (
                tgt_name in ("F600", "F558") and site > ARM9
            ) else "UNHOOKED"
            print(f"  depth={depth} @{site:08X} bl {tgt_name} [{hooked}]")
        print()

    # Disassemble RemoveUsedItem and Category9 paths
    print("=== RemoveUsedItem region (vanilla labels) ===")
    for addr in range(0x022EB60C, 0x022EB670, 4):
        ins = list(cs.disasm(ov29[addr - L : addr - L + 4], addr))[0]
        mark = ""
        if addr in HOOKS_OV29.values():
            mark = " <-- HOOK"
        print(f"  {addr:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")
    print()

    print("=== UseThrowableItem / Category9 consume region ===")
    for addr in range(0x022F5688, 0x022F5700, 4):
        ins = list(cs.disasm(ov29[addr - L : addr - L + 4], addr))[0]
        mark = " <-- HOOK" if addr in HOOKS_OV29.values() else ""
        print(f"  {addr:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")
    print()

    print("=== ItemEffect consume block (FB2xx) ===")
    for addr in range(0x022FB2D0, 0x022FB3E0, 4):
        ins = list(cs.disasm(ov29[addr - L : addr - L + 4], addr))[0]
        mark = " <-- HOOK" if addr in HOOKS_OV29.values() else ""
        print(f"  {addr:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")
    print()

    # InitItem / struct layout from arm9
    init_item = na.mainFunctions.InitItem.get(0)
    print(f"=== InitItem @ {init_item:08X} (struct layout) ===")
    for ins in cs.disasm(arm9[init_item - ARM9 : init_item - ARM9 + 64], init_item):
        print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

    cat = na.overlay29.data.ITEM_CATEGORY_ACTIONS
    off = cat.addresses[0]
    cat9 = struct.unpack_from("<H", ov29, off + 9 * 2)[0]
    print(f"\nITEM_CATEGORY_ACTIONS[9] = {cat9}")


if __name__ == "__main__":
    main()
