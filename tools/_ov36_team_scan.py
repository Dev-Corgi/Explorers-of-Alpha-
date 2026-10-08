from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
import struct
from pathlib import Path

OV36 = Path(r"c:\Working\SkyTemple\tools\_ov36.bin").read_bytes()
RAM = 0x023A7080
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
insns = list(md.disasm(OV36, RAM))

# find functions containing both 0x84c and cmp #4
funcs_with_84c = set()
for i, ins in enumerate(insns):
    if "#0x84c" in ins.op_str:
        func_start = ins.address - RAM
        for back in range(i, max(0, i - 200), -1):
            if insns[back].mnemonic == "push" and "lr" in insns[back].op_str:
                func_start = insns[back].address - RAM
                break
        funcs_with_84c.add(func_start)

print("funcs with 0x84c:", [hex(x) for x in sorted(funcs_with_84c)[:20]])

for fs in sorted(funcs_with_84c):
    chunk = [x for x in insns if fs <= x.address - RAM <= fs + 0x200]
    has_cmp4 = any(x.mnemonic == "cmp" and x.op_str.endswith("#4") for x in chunk)
    has_ldrh42 = any("ldrh" in x.mnemonic and "#0x42" in x.op_str for x in chunk)
    has_ldrh3e = any("ldrh" in x.mnemonic and "#0x3e" in x.op_str for x in chunk)
    has_748 = any("#0x748" in x.op_str for x in chunk)
    has_6264 = any(
        x.mnemonic == "bl" and struct.unpack_from("<I", OV36, x.address - RAM)[0] >> 24 == 0xEB
        for x in chunk
    )
    if has_cmp4 or has_748:
        print(f"\n=== ov36+0x{fs:X} cmp4={has_cmp4} ldrh42={has_ldrh42} ldrh3e={has_ldrh3e} 748={has_748} ===")
        for x in chunk[:40]:
            print(f"  0x{x.address-RAM:X}: {x.mnemonic} {x.op_str}")
