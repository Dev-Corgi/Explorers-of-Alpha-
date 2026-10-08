from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
import struct, re
from pathlib import Path

ARM9 = Path(r"c:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py").read_text(
    encoding="utf-8", errors="ignore"
)
rev = {}
for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", PMDSKY, re.S):
    nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
    if nums:
        rev[nums[0]] = m.group(1)


def blt(pc, w):
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


# find function start for 0x57868
start = 0x57868
for back in range(0, 0x400, 4):
    p = 0x57868 - back
    w = struct.unpack_from("<I", ARM9, p)[0]
    if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):
        start = p
        break

print(f"Function start 0x{start:X}")
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
for ins in md.disasm(ARM9[start : start + 0x400], 0x02000000 + start):
    note = ""
    if ins.mnemonic == "bl":
        w = struct.unpack_from("<I", ARM9, ins.address - 0x02000000)[0]
        t = blt(ins.address, w) - 0x02000000
        if t in rev:
            note = f" ; {rev[t]}"
    if ins.mnemonic in ("b", "bl") and note == "":
        w = struct.unpack_from("<I", ARM9, ins.address - 0x02000000)[0]
        if ins.mnemonic == "b":
            t = blt(ins.address, w)
            if t >= 0x023B0000:
                note = f" ; -> ov36 0x{t:X}"
    mark = " ***" if ins.address - 0x02000000 == 0x57868 else ""
    print(f"0x{ins.address-0x02000000:X}: {ins.mnemonic:7} {ins.op_str}{note}{mark}")
