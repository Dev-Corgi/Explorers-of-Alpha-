#!/usr/bin/env python3
"""Trace consume paths from FEBAC (action 49) in vanilla ov29."""
from collections import deque
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

L = 0x022DC240
CLEAR = 0x0200D81C
FB54 = 0x0200FB54
F600 = 0x0200F600
F558 = 0x0200F558

rom = NintendoDSRom(
    Path(
        "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)-patched_orbs_roomcharge_nodarkness_berryboost.nds"
    ).read_bytes()
)
ov29 = rom.loadArm9Overlays([29])[29]
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def bfs(start, max_depth=14):
    targets = {CLEAR: "ClearItemSlot", FB54: "FB54", F600: "F600", F558: "F558"}
    visited = set()
    q = deque([(start, 0, hex(start))])
    found = []
    while q and len(found) < 40:
        addr, depth, path = q.popleft()
        if depth > max_depth or addr in visited:
            continue
        visited.add(addr)
        off = addr - L
        if off < 0 or off + 4 > len(ov29.data):
            continue
        for ins in cs.disasm(ov29.data[off : off + 0x280], addr):
            if ins.address > addr + 0x280:
                break
            if ins.mnemonic == "bl":
                tgt = int(ins.op_str.replace("#", ""), 16)
                if tgt in targets:
                    found.append((depth, ins.address, targets[tgt], path))
                elif 0x022DC240 <= tgt <= 0x02360000 and depth < max_depth:
                    q.append((tgt, depth + 1, f"{path}->{ins.address:08X}"))
            if ins.mnemonic in ("b", "bx") and ins.op_str.startswith("#"):
                tgt = int(ins.op_str.replace("#", ""), 16)
                if 0x022DC240 <= tgt <= 0x02360000 and depth < max_depth:
                    q.append((tgt, depth + 1, f"{path}->b@{ins.address:08X}"))
    return found


def dump(addr, size=0x80, label=""):
    if label:
        print(f"\n=== {label} @ {addr:08X} ===")
    for ins in cs.disasm(ov29.data[addr - L : addr - L + size], addr):
        print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


print("FEBAC -> FED54 path (2321104 -> 2320D08 type 5)")
dump(0x022FED50, 0x20, "FEBAC tail")
dump(0x02321104, 0x30, "2321104")
found = bfs(0x02320D08)
print("\nBFS from 2320D08:")
for row in sorted(found, key=lambda x: x[1]):
    print(f"  depth={row[0]} {row[1]:08X} bl {row[2]}")

print("\nFEBAC -> FED5C path (230FC24)")
found2 = bfs(0x0230FC24)
print("BFS from 230FC24:")
for row in sorted(found2, key=lambda x: x[1]):
    print(f"  depth={row[0]} {row[1]:08X} bl {row[2]}")

print("\nFEBAC -> FEC88 path (22FF168)")
found3 = bfs(0x022FF168)
print("BFS from 22FF168:")
for row in sorted(found3, key=lambda x: x[1])[:15]:
    print(f"  depth={row[0]} {row[1]:08X} bl {row[2]}")

patched = Path(
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges.nds"
)
def successors(addr, cs, data, base=L):
    off = addr - base
    ins = list(cs.disasm(data[off : off + 4], addr))
    if not ins:
        return []
    ins = ins[0]
    out = []
    if ins.mnemonic in ("b", "bx") and ins.op_str.startswith("#"):
        out.append(int(ins.op_str.replace("#", ""), 16))
    elif ins.mnemonic.startswith("bl"):
        out.append(ins.address + 4)
        if ins.op_str.startswith("#"):
            out.append(int(ins.op_str.replace("#", ""), 16))
    elif ins.mnemonic.startswith("b"):
        if ins.op_str.startswith("#"):
            out.append(int(ins.op_str.replace("#", ""), 16))
            out.append(ins.address + 4)
    else:
        out.append(ins.address + 4)
    return out


def shortest_path(start, target, cs, data, limit=500):
    q = deque([(start, [start])])
    seen = set()
    while q:
        addr, path = q.popleft()
        if addr == target:
            return path
        if addr in seen or len(path) > limit:
            continue
        seen.add(addr)
        for nxt in successors(addr, cs, data):
            if 0x022DC240 <= nxt <= 0x02360000:
                q.append((nxt, path + [nxt]))
    return None


print("\nInstruction-level reachability from FEBAC:")
sites = [
    (0x022FB2F0, "FB2F0 ClearItemSlot (hooked)"),
    (0x022FB3A8, "FB3A8 ClearItemSlot (hooked)"),
    (0x022FB3A0, "FB3A0 F558 scan"),
    (0x022EB65C, "EB65C RemoveUsedItem clear"),
    (0x02346A44, "346A44 ClearItemSlot"),
    (0x022F4D48, "F4D48 AltUse clear (hooked)"),
    (0x022F4968, "F4968 action57 clear"),
    (0x022F4730, "F4730 FB54"),
    (0x022FDC1C, "FDC1C ClearItemSlot"),
]
for tgt, name in sites:
    p = shortest_path(0x022FEBAC, tgt, cs, ov29.data)
    status = f"YES len={len(p)}" if p else "NO"
    print(f"  FEBAC -> {name}: {status}")

if patched.exists():
    ov2 = NintendoDSRom(patched.read_bytes()).loadArm9Overlays([29])[29]
    print("\nPatched ROM hook sites:")
    for addr, name in [
        (0x022FB2F0, "ItemEffectClearSlot1"),
        (0x022FB3A8, "ItemEffectClearSlot2"),
        (0x022EC878, "InlineItemClear"),
        (0x022ECA90, "Type5InlineClearCall"),
        (0x022F4968, "F4968 ClearItemSlot"),
        (0x022F4970, "F4970 FB54"),
        (0x022F4D48, "AltUseClearPath"),
        (0x022EB658, "RemoveUsedItemClearPath"),
    ]:
        w = int.from_bytes(ov2.data[addr - L : addr - L + 4], "little")
        kind = "B" if (w >> 26) == 5 else "bl/other"
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        dest = addr + 8 + imm * 4 if (w >> 26) == 5 else None
        extra = f" -> {dest:08X}" if dest else ""
        print(f"  {name:24s} {addr:08X}: {w:08X} ({kind}{extra})")
