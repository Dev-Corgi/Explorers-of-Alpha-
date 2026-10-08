#!/usr/bin/env python3
from collections import deque
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

L = 0x022DC240
CLEAR = 0x0200D81C
FB54 = 0x0200FB54

rom = NintendoDSRom(
    Path(
        "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)-patched_orbs_roomcharge_nodarkness_berryboost.nds"
    ).read_bytes()
)
ov29 = rom.loadArm9Overlays([29])[29]
data = ov29.data
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def insn_at(addr):
    off = addr - L
    ins = list(cs.disasm(data[off : off + 4], addr))
    return ins[0] if ins else None


def step(addr, ret_stack):
    ins = insn_at(addr)
    if not ins:
        return []
    out = []
    m = ins.mnemonic
    if (m == "bx" and ins.op_str == "lr") or (m == "pop" and "pc" in ins.op_str):
        if ret_stack:
            out.append((ret_stack[-1], ret_stack[:-1]))
        return out
    if m in ("b", "bx") and ins.op_str.startswith("#"):
        out.append((int(ins.op_str.replace("#", ""), 16), ret_stack))
    elif m.startswith("bl"):
        ret = ins.address + 4
        rs = ret_stack + [ret]
        out.append((ret, ret_stack))
        if ins.op_str.startswith("#"):
            tgt = int(ins.op_str.replace("#", ""), 16)
            if 0x022DC240 <= tgt <= 0x02360000:
                out.append((tgt, rs))
    elif m.startswith("b") and ins.op_str.startswith("#"):
        out.append((int(ins.op_str.replace("#", ""), 16), ret_stack))
        out.append((ins.address + 4, ret_stack))
    else:
        out.append((ins.address + 4, ret_stack))
    return out


def find_bl_targets(start, target):
    q = deque([(start, [], 0)])
    seen = set()
    hits = []
    while q:
        addr, rs, depth = q.popleft()
        key = (addr, tuple(rs))
        if key in seen or depth > 500:
            continue
        seen.add(key)
        ins = insn_at(addr)
        if ins and ins.mnemonic == "bl" and ins.op_str == f"#0x{target:x}":
            hits.append((depth, addr))
        for nxt, nrs in step(addr, rs):
            if 0x022DC240 <= nxt <= 0x02360000:
                q.append((nxt, nrs, depth + 1))
    return hits


for tgt, name in [(CLEAR, "ClearItemSlot"), (FB54, "FB54")]:
    hits = find_bl_targets(0x022FEBAC, tgt)
    print(f"\n{name} reachable from FEBAC ({len(hits)} sites):")
    for d, a in sorted(hits, key=lambda x: x[1]):
        prev = insn_at(a - 4)
        prev_s = f"{prev.mnemonic} {prev.op_str}" if prev else "?"
        print(f"  {a:08X} depth={d}  prev: {prev_s}")
