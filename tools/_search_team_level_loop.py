"""Find party slot loops (cmp #4) with level reads in arm9 and ov36."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
OV36 = Path(r"C:\Working\SkyTemple\tools\_ov36.bin").read_bytes()
OUT = Path(r"C:\Working\SkyTemple\tools\_team_level_loops.txt")
LOAD = 0x02000000


def find_loops(data: bytes, base_ram: int, label: str) -> list[str]:
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    insns = list(md.disasm(data, base_ram))
    lines = []
    for i, ins in enumerate(insns):
        if ins.mnemonic != "cmp":
            continue
        if ins.op_str not in ("r0, #4", "r4, #4", "sb, #4", "r6, #4", "r1, #4"):
            continue
        off = ins.address - base_ram
        # look ahead for bl CheckTeamMemberIdx or ldrh level
        window = insns[i : i + 25]
        has_level = any("ldrh" in x.mnemonic and ("#0x42" in x.op_str or "#0x3e" in x.op_str) for x in window)
        has_guest = any(x.mnemonic == "bl" for x in window)  # weak
        if has_level or True:
            lines.append(f"\n{label}+0x{off:X} cmp party slot:")
            for x in window[:18]:
                lines.append(f"  0x{x.address-base_ram:X}: {x.mnemonic} {x.op_str}")
    return lines


lines = ["=== ARM9 party loops ==="]
lines.extend(find_loops(ARM9, LOAD, "arm9"))
lines.append("\n=== OV36 party loops ===")
lines.extend(find_loops(OV36, 0x023A7080, "ov36"))

# Search ov36 for byte 55 / 0x37 as immediate
lines.append("\n=== ov36 cmp/mov with #0x37 or #55 ===")
md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
for ins in md.disasm(OV36, 0x023A7080):
    if "#0x37" in ins.op_str or "#55" in ins.op_str:
        lines.append(f"ov36+0x{ins.address-0x023A7080:X}: {ins.mnemonic} {ins.op_str}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT}")
