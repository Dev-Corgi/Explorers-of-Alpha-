from pathlib import Path
import re
import struct

enums = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\skytemple_files\hardcoded\symbols\manual\enums.py"
).read_text(encoding="utf-8", errors="ignore")
start = enums.find('exclusive_item_effect_id": [')
end = enums.find("],", start)
block = enums[start:end]
vals = re.findall(r'EnumValue\((\d+),\s*"([^"]*)"\)', block)
print("count", len(vals))
print("=== STAT / HP / SPEED RELATED ===")
for i, name in vals:
    low = name.lower()
    if any(
        k in low
        for k in [
            "attack",
            "defense",
            "hp",
            "speed",
            "stat",
            "boost",
            "spa",
            "spd",
            "spe",
            "exp",
        ]
    ):
        print(f"{int(i):3d} 0x{int(i):02X}  {name}")

print("\n=== FULL ENUM ===")
for i, name in vals:
    print(f"{int(i):3d} 0x{int(i):02X}  {name}")

na = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py"
).read_text(encoding="utf-8", errors="ignore")
print("\n=== KEY SYMBOLS ===")
for name in [
    "ExclusiveItemOffenseBoost",
    "ExclusiveItemDefenseBoost",
    "GetHpBoostFromExclusiveItems",
    "GetStatBoostsForMonsterSummary",
    "ApplyExclusiveItemStatBoosts",
    "TeamMemberHasExclusiveItemEffectActive",
    "ExclusiveItemEffectIsActive",
    "MonsterExclusiveItemIsActive",
    "HasExclusiveItemEffectActive",
    "ExclusiveItemEffectFlagTest",
]:
    key = f'"{name}"'
    idx = na.find(key)
    if idx < 0:
        # try alternate
        hits = [m.start() for m in re.finditer(re.escape(name), na)]
        print(name, "NOT as quoted; hits", len(hits))
        if hits:
            print(na[max(0, hits[0] - 200) : hits[0] + 300])
        continue
    start = na.rfind("Symbol(", max(0, idx - 500), idx)
    print(na[start : idx + 450])
    print("---")

# Disassemble ExclusiveItemOffenseBoost / DefenseBoost from overlay_0029
ov = Path(r"C:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin")
arm9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin")
print("\nov29 exists", ov.exists(), "size", ov.stat().st_size if ov.exists() else None)
print("arm9 exists", arm9.exists())

# ov29 load address NA is typically 0x022DC240; ExclusiveItemOffenseBoost abs 0x0230F778
# offset = abs - load = 0x0230F778 - 0x022DC240 = 0x33538 (matches pmdsky relative)
OV29_LOAD = 0x022DC240


def dis_arm(blob, addr, count=40, load=OV29_LOAD):
    off = addr - load
    print(f"\n=== DISASM {addr:#x} off={off:#x} ===")
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    except ImportError:
        # fallback hex dump
        data = blob[off : off + count * 4]
        for i in range(0, len(data), 4):
            w = struct.unpack_from("<I", data, i)[0]
            print(f"{addr+i:08X}  {w:08X}")
        return
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    data = blob[off : off + count * 4]
    for insn in md.disasm(data, addr):
        print(f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}")


if ov.exists():
    blob = ov.read_bytes()
    dis_arm(blob, 0x0230F778, 30)
    dis_arm(blob, 0x0230F788, 30)
    # CalcDamage call site around 0x0230C2F0
    dis_arm(blob, 0x0230C2E0, 40)

# GetHpBoostFromExclusiveItems arm9 0x2011394, arm9 load 0x02000000
if arm9.exists():
    a = arm9.read_bytes()
    print("\n=== GetHpBoostFromExclusiveItems ===")
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

        md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        off = 0x11394
        for insn in md.disasm(a[off : off + 80], 0x02011394):
            print(f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}")
    except ImportError:
        for i in range(0, 80, 4):
            w = struct.unpack_from("<I", a, 0x11394 + i)[0]
            print(f"{0x02011394+i:08X}  {w:08X}")

    print("\n=== ApplyExclusiveItemStatBoosts ===")
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

        md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        off = 0x10E64
        for insn in md.disasm(a[off : off + 120], 0x02010E64):
            print(f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}")
    except ImportError:
        pass
