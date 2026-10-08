from pathlib import Path
import re
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

na = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py"
).read_text(encoding="utf-8", errors="ignore")
arm9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

# Name function 0x205B120 properly
print("=== symbols near 0x205B120 ===")
cands = []
for m in re.finditer(r"Symbol\(\s*\[([^\]]+)\],\s*\[([^\]]+)\]", na):
    abs_list = [int(x.strip(), 0) for x in m.group(2).split(",") if x.strip()]
    rest = na[m.end() : m.end() + 400]
    nm = re.search(r'"([A-Za-z0-9_]+)"', rest)
    if not nm:
        continue
    for a in abs_list:
        if 0x0205B000 <= a <= 0x0205B400:
            desc_m = re.search(
                r'"' + re.escape(nm.group(1)) + r'",\s*"((?:[^"\\]|\\.)*)"',
                na[m.start() : m.start() + 900],
            )
            cands.append((a, nm.group(1), desc_m.group(1)[:180] if desc_m else ""))
for a, n, d in sorted(cands):
    print(f"{a:#x} {n}: {d}")

# Continue CreateMonsterSummaryFromTeamMember looking for +0x24/+0x28 and GetHpBoost
print("\n=== CreateMonsterSummaryFromTeamMember continued ===")
for insn in md.disasm(arm9[0x5AF2C : 0x5B120], 0x0205AF2C):
    s = f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}"
    if any(
        x in insn.op_str
        for x in ["#0x24", "#0x28", "0x205b", "0x2011394", "0x205a450"]
    ):
        s += " <<<"
    print(s)

# Full helper through HP store - look for strh to [r5]
print("\n=== helper 0x205B120 full until pop ===")
for insn in md.disasm(arm9[0x5B120 : 0x5B360], 0x0205B120):
    print(f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}")
    if insn.mnemonic == "pop" and insn.address > 0x205B200:
        break

# Search arm9 for pattern: add then store to summary max_hp
# Cross-ref: after GetHpBoost, who uses return value with summary+0x28
print("\n=== search BL GetHpBoost and nearby str to #0x28 ===")
# Already know only one caller. Check if 0x23bf23c is a store helper - disasm veneer
# 0x23BF23C might be in overlay or arm9 overlay region - check size
print("arm9 size", hex(len(arm9)))
# Search all binaries for the add-to-max-hp pattern near exclusive
# In CreateMonsterSummary: look for ldr from 0x24 add something str to 0x28
print("\n=== scan CreateMonsterSummary region for 0x24/0x28 ===")
for insn in md.disasm(arm9[0x5AE28 : 0x5B120], 0x0205AE28):
    if "0x24" in insn.op_str or "0x28" in insn.op_str:
        print(f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}")

# Check vanilla vs note: HP constant at 0x20A1878 - what symbol?
print("\n=== symbol at/near 0x20A1878 ===")
best = None
for m in re.finditer(r"Symbol\(\s*\[([^\]]+)\],\s*\[([^\]]+)\]", na):
    abs_list = [int(x.strip(), 0) for x in m.group(2).split(",") if x.strip()]
    rest = na[m.end() : m.end() + 200]
    nm = re.search(r'"([A-Za-z0-9_]+)"', rest)
    if not nm:
        continue
    for a in abs_list:
        if a <= 0x020A1878 and (best is None or a > best[0]):
            best = (a, nm.group(1))
print(best)
# Read surrounding halfwords
off = 0xA1878 - 0x20
print("halfwords around:", [struct.unpack_from("<h", arm9, 0xA1878 - 0x20 + i)[0] for i in range(0, 0x40, 2)])

# BaseStats patch: find SummaryHpFillContinue address
offs = Path(
    r"C:\Working\SkyTemple\true_patches\base_stats_speed\asm\common\offsetsUS.asm"
).read_text(encoding="utf-8", errors="ignore")
print("\n=== base_stats offsets mentioning Summary/Hp ===")
for line in offs.splitlines():
    if any(k.lower() in line.lower() for k in ["summary", "hp", "exclusive", "town"]):
        print(line)
