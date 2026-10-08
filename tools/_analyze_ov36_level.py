"""Analyze overlay 36 level scaling patch code."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
OV36 = Path(r"C:\Working\SkyTemple\tools\_ov36.bin").read_bytes()
OUT = Path(r"C:\Working\SkyTemple\tools\_ov36_level_analysis.txt")
OV36_RAM = 0x023A7080
LOAD = 0x02000000


def syms() -> dict[str, int]:
    t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    out = {}
    for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
        if nums:
            out[m.group(1)] = nums[0]
    return out


def bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def disasm_arm(data: bytes, file_off: int, ram_base: int, size: int = 0x200) -> list[str]:
    rev = {v: k for k, v in syms().items()}
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    lines = []
    for ins in md.disasm(data[file_off : file_off + size], ram_base + file_off):
        note = ""
        if ins.mnemonic == "bl":
            w = struct.unpack_from("<I", data, ins.address - ram_base)[0]
            tgt = bl_target(ins.address, w)
            t_off = tgt - LOAD
            if t_off in rev:
                note = f"  ; {rev[t_off]}"
        lines.append(f"ov36+0x{ins.address-ram_base:X}  RAM 0x{ins.address:X}: {ins.mnemonic:7} {ins.op_str}{note}")
    return lines


def main() -> None:
    s = syms()
    lines: list[str] = []
    patch_offs = {
        "IsLevelResetDungeon hook (0x51318)": 0x1115C,
        "Team level hook (0x57868)": 0x11170,
        "cluster start": 0x1114C,
    }
    for label, off in patch_offs.items():
        lines.append(f"\n=== {label} @ ov36+0x{off:X} ===")
        lines.extend(disasm_arm(OV36, off - 0x40, OV36_RAM, 0x280))

    lines.append("\n=== All bl to key funcs in ov36 ===")
    key = {
        s["CheckTeamMemberIdx"]: "CheckTeamMemberIdx",
        s["GetPerformanceFlagWithChecks"]: "GetPerformanceFlagWithChecks",
        s["LoadScriptVariableValueAtIndex"]: "LoadScriptVariableValueAtIndex",
        s["GetGameMode"]: "GetGameMode",
        s["IsLevelResetDungeon"]: "IsLevelResetDungeon",
        0x530D4: "?530D4",
        0x5349C: "?5349C",
        0x58138: "?58138",
    }
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in md.disasm(OV36, OV36_RAM):
        if ins.mnemonic != "bl":
            continue
        w = struct.unpack_from("<I", OV36, ins.address - OV36_RAM)[0]
        tgt = bl_target(ins.address, w)
        t_off = tgt - LOAD
        if t_off in key:
            off = ins.address - OV36_RAM
            lines.append(f"  ov36+0x{off:X}: bl {key[t_off]}")
            # show context
            ctx = disasm_arm(OV36, max(0, off - 0x30), OV36_RAM, 0x70)
            lines.extend("    " + x for x in ctx)

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
