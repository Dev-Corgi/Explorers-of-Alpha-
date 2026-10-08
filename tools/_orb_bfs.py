#!/usr/bin/env python3
from collections import deque
import struct
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom

PATCH = (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges.nds"
)
L = 0x022DC240
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
ov = NintendoDSRom(open(PATCH, "rb").read()).loadArm9Overlays([29])[29].data

KEYS = {
    0x022FB4E4: "FB4E4 unhooked PostClear",
    0x022FB310: "FB310 MaybeSkip",
    0x022FB2F0: "FB2F0 clear hook",
    0x023469E0: "3469E0 bag flag clear",
    0x022EB658: "RemoveUsedItem hook",
    0x022EC878: "InlineClear hook",
    0x022FB3A0: "FB3A0 F558 scan",
    0x02346A44: "346A44 ClearItemSlot",
}


def succ(addr: int) -> list[int]:
    off = addr - L
    if off < 0 or off + 4 > len(ov):
        return []
    w = struct.unpack_from("<I", ov, off)[0]
    ins = list(cs.disasm(ov[off : off + 4], addr))[0]
    out = [addr + 4]
    if (w >> 24) & 0xFF == 0xEB:
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 1 << 24
        out.append((addr + 8 + (imm << 2)) & 0xFFFFFFFF)
    elif ins.mnemonic.startswith("b") and ins.op_str.startswith("#"):
        out.append(int(ins.op_str.replace("#", ""), 16))
    return [x for x in out if L <= x <= L + len(ov)]


def bfs(start: int) -> dict[int, int]:
    q = deque([(start, 0)])
    seen: set[int] = set()
    found: dict[int, int] = {}
    while q and len(found) < len(KEYS):
        a, d = q.popleft()
        if a in seen or d > 300:
            continue
        seen.add(a)
        if a in KEYS and a not in found:
            found[a] = d
        for n in succ(a):
            q.append((n, d + 1))
    return found


print("=== 22DFE38 caller of 3469E0 ===")
for ins in cs.disasm(ov[0x022DFE00 - L : 0x022DFE60 - L], 0x022DFE00):
    print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

print("\n=== FB4E0 region ===")
for ins in cs.disasm(ov[0x022FB4C0 - L : 0x022FB520 - L], 0x022FB4C0):
    print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

for label, start in [
    ("BagUse", 0x02310F40),
    ("UseItem", 0x02322374),
    ("Action49Use", 0x022FEF64),
]:
    print(f"\nBFS from {label} ({start:08X}):")
    found = bfs(start)
    for k, lbl in KEYS.items():
        depth = found.get(k, "-")
        print(f"  {lbl:30s} depth={depth}")
