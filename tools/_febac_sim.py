#!/usr/bin/env python3
"""Simulate from FEBAC with call stack; find which bl ClearItemSlot sites are reachable."""
from collections import deque
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

L = 0x022DC240
CLEAR = 0x0200D81C

rom = NintendoDSRom(
    Path(
        "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)-patched_orbs_roomcharge_nodarkness_berryboost.nds"
    ).read_bytes()
)
data = rom.loadArm9Overlays([29])[29].data
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def ins_at(addr):
    off = addr - L
    xs = list(cs.disasm(data[off : off + 4], addr))
    return xs[0] if xs else None


def step(addr, rets):
    ins = ins_at(addr)
    if not ins:
        return []
    out = []
    m = ins.mnemonic
    if m == "pop" and "pc" in ins.op_str:
        if rets:
            out.append((rets[-1], rets[:-1]))
        return out
    if m == "bx" and ins.op_str == "lr":
        if rets:
            out.append((rets[-1], rets[:-1]))
        return out
    if m in ("b", "bx") and ins.op_str.startswith("#"):
        out.append((int(ins.op_str.replace("#", ""), 16), rets))
    elif m.startswith("bl"):
        ret = ins.address + 4
        out.append((ret, rets))
        if ins.op_str.startswith("#"):
            tgt = int(ins.op_str.replace("#", ""), 16)
            if 0x022DC240 <= tgt <= 0x02360000:
                out.append((tgt, rets + [ret]))
    elif m.startswith("b") and ins.op_str.startswith("#"):
        out.append((int(ins.op_str.replace("#", ""), 16), rets))
        out.append((ins.address + 4, rets))
    else:
        out.append((ins.address + 4, rets))
    return out


q = deque([(0x022FEBAC, [], 0)])
seen = set()
hits = []
while q:
    addr, rets, depth = q.popleft()
    key = (addr, tuple(rets))
    if key in seen or depth > 600:
        continue
    seen.add(key)
    ins = ins_at(addr)
    if ins and ins.mnemonic == "bl" and ins.op_str == f"#0x{CLEAR:x}":
        hits.append((depth, addr, len(rets)))
    for nxt, nr in step(addr, rets):
        if 0x022DC240 <= nxt <= 0x02360000:
            q.append((nxt, nr, depth + 1))

print(f"ClearItemSlot sites reachable from FEBAC (call-stack sim): {len(hits)}")
for d, a, rs in sorted(set(hits), key=lambda x: x[1]):
    prev = ins_at(a - 4)
    ps = f"{prev.mnemonic} {prev.op_str}" if prev else "?"
    print(f"  {a:08X} depth={d} stack={rs}  prev={ps}")
