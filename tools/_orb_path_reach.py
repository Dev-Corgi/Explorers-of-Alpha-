#!/usr/bin/env python3
"""Path reachability for Cleanse orb bag Use consume sites."""
from __future__ import annotations

import struct
from collections import deque
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom
from skytemple_files.data.data_cd.handler import DataCDHandler

PATCH = (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges.nds"
)
L = 0x022DC240
ARM9 = 0x02000000
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
ov = NintendoDSRom(open(PATCH, "rb").read()).loadArm9Overlays([29])[29].data


def successors(addr: int) -> list[int]:
    off = addr - L
    w = struct.unpack_from("<I", ov, off)[0]
    ins = list(cs.disasm(ov[off : off + 4], addr))[0]
    out = [addr + 4]
    if ins.mnemonic.startswith("bl") or (ins.mnemonic == "b" and ins.op_str.startswith("#")):
        out.append(int(ins.op_str.replace("#", ""), 16))
    elif ins.mnemonic.startswith("b") and not ins.mnemonic.startswith("bl"):
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 1 << 24
        out.append((addr + 8 + (imm << 2)) & 0xFFFFFFFF)
    return out


def path(start: int, target: int, limit: int = 400) -> list[int] | None:
    q = deque([(start, [start])])
    seen: set[int] = set()
    while q:
        a, p = q.popleft()
        if a == target:
            return p
        if a in seen or len(p) > limit:
            continue
        seen.add(a)
        for n in successors(a):
            if L <= n <= 0x02360000 or ARM9 <= n <= 0x02100000:
                q.append((n, p + [n]))
    return None


sites = {
    0x022EB648: "RemoveUsedItem equiv hook",
    0x022EB658: "RemoveUsedItem clear hook",
    0x022FB2F0: "ItemEffectClear1 hook",
    0x022FB310: "MaybeSkipPostClear hook",
    0x022EC878: "InlineClear hook",
    0x02346A44: "346A44 ClearItemSlot UNHOOKED",
    0x023455A4: "3455A4 RemoveEquiv UNHOOKED",
    0x022F5698: "Cat9 clear hook",
    0x0231AC48: "UseItem->RemoveUsedItem call site",
    0x022FDC1C: "FDC1C entity ClearItemSlot UNHOOKED",
    0x022F4968: "F4968 action57 Clear UNHOOKED",
}
starts = {
    0x02310F40: "Bag submenu USE",
    0x02322374: "UseItem entry",
    0x022FEF64: "Action49 USE branch",
    0x022FEBAC: "Action49 resolver",
}

for s, slabel in starts.items():
    print(f"From {slabel} ({s:08X}):")
    for tgt, name in sites.items():
        p = path(s, tgt)
        status = "YES" if p else "NO"
        ln = len(p) if p else "-"
        print(f"  {name:40s} {status:3s} len={ln}")
    print()

# Who calls 346A44 function - find bl callers to func containing 346A44
func_start = 0x023469A0  # approximate - search
for addr in range(0x02346900, 0x02346A00, 4):
    ins = list(cs.disasm(ov[addr - L : addr - L + 4], addr))[0]
    if ins.mnemonic == "push" and "lr" in ins.op_str and "fp" in ins.op_str:
        func_start = addr
        break

print(f"346A44 function ~{func_start:08X}")
callers = []
for base in range(L, L + len(ov), 4):
    w = struct.unpack_from("<I", ov, base - L)[0]
    if (w >> 26) != 0b101101:
        continue
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 1 << 24
    dest = base + 8 + (imm << 2)
    if func_start <= dest <= func_start + 0x100:
        callers.append(base)

print(f"  bl callers ({len(callers)}):")
for c in callers[:20]:
    print(f"    {c:08X}")

cd = DataCDHandler.deserialize(
    NintendoDSRom(open(PATCH, "rb").read()).getFileByName("BALANCE/item_cd.bin")
)
print(f"\nCleanse 323: effect={cd.get_item_effect_id(323)}")

# Disassemble MaybeSkip vanilla fallback target
print("\nMaybeSkip vanilla path (307E4):")
for ins in cs.disasm(ov[0x023307E4 - L : 0x02330810 - L], 0x023307E4):
    print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
