from pathlib import Path
import re
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

na = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py"
).read_text(encoding="utf-8", errors="ignore")
arm9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

# Find function that contains 0x205B18C - look for push before it
addr = 0x0205B18C
# Walk backwards for push {..., lr}
fn_start = None
for a in range(addr, addr - 0x400, -4):
    w = struct.unpack_from("<I", arm9, a - 0x02000000)[0]
    # STMFD/PUSH with lr: typically E92D4xxx or E92D4xx0
    if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):
        fn_start = a
        break
print("fn_start", hex(fn_start) if fn_start else None)

# Find symbol for fn_start
best = None
for m in re.finditer(r"Symbol\(\s*\[([^\]]+)\],\s*\[([^\]]+)\]", na):
    abs_list = []
    for x in m.group(2).split(","):
        x = x.strip()
        if x:
            abs_list.append(int(x, 0))
    rest = na[m.end() : m.end() + 300]
    nm = re.search(r'"([A-Za-z0-9_]+)"', rest)
    desc = re.search(r'"((?:[^"\\]|\\.)*)"', rest[nm.end() :] if nm else "")
    if not nm:
        continue
    for a in abs_list:
        if fn_start and a <= fn_start and (best is None or a > best[0]):
            d = ""
            # get description
            full = na[m.start() : m.start() + 800]
            dm = re.search(r'"' + nm.group(1) + r'",\s*"((?:[^"\\]|\\.)*)"', full)
            best = (a, nm.group(1), dm.group(1)[:200] if dm else "")
print("symbol", best)

print("\n=== full function to after HP write ===")
off = fn_start - 0x02000000
for insn in md.disasm(arm9[off : off + 0x200], fn_start):
    mark = ""
    if insn.address == 0x0205B18C:
        mark = "  # GetHpBoost"
    if "0x24" in insn.op_str or "0x28" in insn.op_str:
        mark += "  # summary HP?"
    print(f"{insn.address:08X}  {insn.mnemonic} {insn.op_str}{mark}")
    if insn.address > 0x0205B220:
        break

# Also dump EXCLUSIVE_ITEM_STAT_BOOST_DATA table
print("\n=== EXCLUSIVE_ITEM_STAT_BOOST_DATA @ 0x20980E8 ===")
off = 0x980E8
data = arm9[off : off + 0x3C]
for i in range(0, len(data), 4):
    atk, deff, spa, spd = data[i : i + 4]
    # signed
    def s(b):
        return b - 256 if b >= 128 else b

    print(f"idx {i//4}: atk={s(atk)} def={s(deff)} spa={s(spa)} spd={s(spd)} raw={data[i:i+4].hex()}")

# HP boost constants from GetHpBoost pool
print("\n=== GetHpBoost pool constants ===")
# From disasm: ldrne r0, [pc, #0x64] at 020113B0 -> pc+8+0x64 = 0x201141C?
# At 020113B0, pc for ARM is addr+8 = 020113B8, +0x64 = 0201141C
# At 020113D4, ldrne r0,[pc,#0x40]: pc=020113DC+0x40=0201141C same?
# At 020113FC, ldr r0,[pc,#0x18]: pc=02011404+0x18=0201141C
w = struct.unpack_from("<I", arm9, 0x1141C)[0]
print(f"pool ptr at 0x201141C = {w:#x}")
# That points to a halfword value
if 0x02000000 <= w < 0x02000000 + len(arm9):
    val = struct.unpack_from("<h", arm9, w - 0x02000000)[0]
    print(f"HP base boost value = {val}")

# Monster struct fields around 0x224
st = Path(
    r"C:\Working\SkyTemple\.venv\Lib\site-packages\skytemple_files\hardcoded\symbols\manual\structs.py"
).read_text(encoding="utf-8", errors="ignore")
for key in ["0x224", "exclusive", "stat_boost", "atk_boost"]:
    pass
idx = st.find("monster")
# Find monster struct with field near offset 0x224
m = re.search(r'"monster":\s*\((\d+),\s*\[(.*?)\]\s*\)', st, re.S)
if m:
    fields = re.findall(
        r'StructField\("([^"]+)",\s*(\d+)',
        m.group(2),
    )
    print("\n=== monster fields near 0x220 ===")
    for name, off in fields:
        o = int(off)
        if 0x200 <= o <= 0x240:
            print(f"  +{o:#x} ({o}) {name}")

# monster_summary HP fields
m = re.search(r'"monster_summary":\s*\((\d+),\s*\[(.*?)\]\s*\)', st, re.S)
if m:
    fields = re.findall(r'StructField\("([^"]+)",\s*(\d+)', m.group(2))
    print("\n=== monster_summary fields ===")
    for name, off in fields:
        print(f"  +{off} {name}")
