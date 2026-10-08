import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
LOAD = 0x02000000

t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
    name = m.group(1)
    if "PERFORMANCE" not in name and "Performance" not in name:
        continue
    nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
    if len(nums) >= 2:
        print(name, f"off=0x{nums[0]:X}", f"ram=0x{nums[1]:X}")

# disassemble GetPerformanceFlagWithChecks itself
m = re.search(r"GetPerformanceFlagWithChecks\s*=\s*Symbol\((.*?)\)\n\n", t, re.S)
nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(1))]
off = nums[0]
print("\n=== GetPerformanceFlagWithChecks disasm ===")
for mode, label in [(CS_MODE_THUMB, "thumb"), (CS_MODE_ARM, "arm")]:
    md = Cs(CS_ARCH_ARM, mode)
    print(label)
    for ins in md.disasm(ARM9[off : off + 0x80], LOAD + off):
        print(f"  0x{ins.address-LOAD:X}: {ins.mnemonic} {ins.op_str}")

# find literal refs to perf fn
perf_ram = nums[1]
pat = struct.pack("<I", perf_ram)
pos = 0
print("\nLiteral refs to perf fn:")
while True:
    p = ARM9.find(pat, pos)
    if p == -1:
        break
    print(f"  0x{p:X}")
    pos = p + 1
