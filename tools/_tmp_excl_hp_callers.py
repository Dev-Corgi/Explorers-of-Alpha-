from pathlib import Path
import re
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

na = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py"
).read_text(encoding="utf-8", errors="ignore")

# Full ExclusiveItemEffectIsActive docs
idx = na.find("ExclusiveItemEffectIsActive")
print(na[idx : idx + 1200])
print("====")

idx = na.find("GetExclusiveItemWithEffectFromBag")
print(na[idx : idx + 600])
print("====")

arm9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

# Find all BL to GetHpBoostFromExclusiveItems
target = 0x02011394
callers = []
for i in range(0, len(arm9) - 4, 4):
    w = struct.unpack_from("<I", arm9, i)[0]
    if (w & 0x0F000000) != 0x0B000000:
        continue
    pc = 0x02000000 + i + 8
    imm24 = w & 0x00FFFFFF
    if imm24 & 0x800000:
        imm24 -= 0x1000000
    dest = pc + imm24 * 4
    if dest == target:
        callers.append(0x02000000 + i)
print("GetHpBoost callers:", [hex(c) for c in callers])

# Disassemble around each caller
for c in callers:
    print(f"\n=== around caller {c:#x} ===")
    start = c - 0x40
    off = start - 0x02000000
    for insn in md.disasm(arm9[off : off + 0x80], start):
        mark = " <<<" if insn.address == c else ""
        print(f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}{mark}")

# Also search for max_hp patterns near CreateMonsterSummaryFromTeamMember 0x205AE28
print("\n=== CreateMonsterSummaryFromTeamMember start ===")
for insn in md.disasm(arm9[0x5AE28 : 0x5AE28 + 0x120], 0x0205AE28):
    print(f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}")

# Find symbol covering each caller
print("\n=== symbol names for callers ===")
# Parse all Symbol abs addresses
syms = []
for m in re.finditer(
    r'"([^"]+)",\s*"(?:[^"\\]|\\.)*",\s*None,\s*\)',
    na,
):
    pass
# Simpler: find Symbol blocks with absolute address near callers
for c in callers:
    # find closest symbol with abs <= c
    best = None
    for m in re.finditer(r"Symbol\(\s*\[([^\]]+)\],\s*\[([^\]]+)\]", na):
        abs_list = [int(x.strip(), 0) for x in m.group(2).split(",") if x.strip()]
        # name is after
        rest = na[m.end() : m.end() + 200]
        nm = re.search(r'"([A-Za-z0-9_]+)"', rest)
        if not nm:
            continue
        for a in abs_list:
            if a <= c and (best is None or a > best[0]):
                best = (a, nm.group(1))
    print(hex(c), "->", best)

# Exclusive item data tables in na
for name in [
    "EXCLUSIVE_ITEM_STAT_BOOST_DATA",
    "EXCLUSIVE_ITEM_EFFECT_DATA",
    "ExclusiveItemStatBoostData",
    "ExclusiveItemEffects",
]:
    i = na.find(name)
    print(name, "idx", i)
    if i >= 0:
        print(na[max(0, i - 100) : i + 400])
