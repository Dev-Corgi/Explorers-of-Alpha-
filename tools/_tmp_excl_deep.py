from pathlib import Path
import re
import struct

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

    HAS_CS = True
except ImportError:
    HAS_CS = False

na = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py"
).read_text(encoding="utf-8", errors="ignore")

# Find all symbols mentioning exclusive OR 0x224 / exclusive boost fields
print("=== symbols with Exclusive in name ===")
for m in re.finditer(
    r'(\w+)\s*=\s*Symbol\(\s*\[([^\]]+)\],\s*\[([^\]]+)\],\s*None,\s*"([^"]+)",\s*"([^"]*)"',
    na,
    re.S,
):
    name, rel, abs_, dname, desc = m.groups()
    if "exclusive" in name.lower() or "exclusive" in dname.lower() or "exclusive" in desc.lower():
        print(f"{dname:45s} {abs_.strip()}  {desc.splitlines()[0][:90]}")

arm9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
ov29 = Path(r"C:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin").read_bytes()
OV29_LOAD = 0x022DC240
md = Cs(CS_ARCH_ARM, CS_MODE_ARM) if HAS_CS else None


def dis(blob, addr, n, load):
    off = addr - load
    print(f"\n=== {addr:#x} ===")
    if md:
        for insn in md.disasm(blob[off : off + n * 4], addr):
            print(f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}")
    else:
        for i in range(n):
            w = struct.unpack_from("<I", blob, off + i * 4)[0]
            print(f"{addr+i*4:08X}  {w:08X}")


# Full GetHpBoostFromExclusiveItems
dis(arm9, 0x02011394, 50, 0x02000000)
# ApplyExclusiveItemStatBoosts
dis(arm9, 0x02010E64, 60, 0x02000000)

# Find who writes monster+0x224 in ov29: search for strb with #0x224
# ARM: strb rt, [rn, #imm] encoding
# Look for immediate 0x224 in instructions near exclusive setup
print("\n=== searching ov29 for 0x224 / 0x226 immediates in ARM ===")
# LDRB/STRB with imm12: bits [11:0] = imm, and for offset 0x224
hits = []
for i in range(0, len(ov29) - 4, 4):
    w = struct.unpack_from("<I", ov29, i)[0]
    # data-processing / ldr/str with imm
    if (w & 0x0C000000) == 0x04000000:  # LDR/STR
        imm = w & 0xFFF
        if imm in (0x224, 0x225, 0x226, 0x227, 0x228):
            hits.append((OV29_LOAD + i, w, imm))
print("hits", len(hits))
for addr, w, imm in hits[:40]:
    print(f"{addr:08X} imm={imm:#x} word={w:08X}")

# GetStatBoostsForMonsterSummary - find where it adds exclusive HP to max
dis(arm9, 0x0205A450, 80, 0x02000000)

# Search arm9 for bl to GetHpBoostFromExclusiveItems (0x02011394)
print("\n=== callers of GetHpBoostFromExclusiveItems ===")
target = 0x02011394
for i in range(0, len(arm9) - 4, 4):
    w = struct.unpack_from("<I", arm9, i)[0]
    if (w & 0x0F000000) != 0x0B000000:
        continue  # not BL
    pc = 0x02000000 + i + 8
    imm24 = w & 0x00FFFFFF
    if imm24 & 0x800000:
        imm24 -= 0x1000000
    dest = pc + imm24 * 4
    if dest == target:
        print(f"BL from {0x02000000+i:#x}")
