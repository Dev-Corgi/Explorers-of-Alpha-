"""Disassemble EoA level-scaling patch cluster around 0x3B81DC."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
OUT = Path(r"C:\Working\SkyTemple\tools\_level_patch_disasm.txt")
LOAD = 0x02000000


def syms() -> dict[int, str]:
    t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    rev = {}
    for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
        if nums:
            rev[nums[0]] = m.group(1)
    return rev


def bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def disasm_range(start: int, size: int) -> list[str]:
    rev = syms()
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    lines = []
    for ins in md.disasm(ARM9[start : start + size], LOAD + start):
        note = ""
        if ins.mnemonic == "bl":
            w = struct.unpack_from("<I", ARM9, ins.address - LOAD)[0]
            tgt = bl_target(ins.address, w) - LOAD
            if tgt in rev:
                note = f"  ; {rev[tgt]}"
        lines.append(f"0x{ins.address-LOAD:06X}: {ins.mnemonic:7} {ins.op_str}{note}")
    return lines


def main() -> None:
    lines = ["=== Patch cluster 0x3B8100-0x3B8700 ==="]
    lines.extend(disasm_range(0x3B8100, 0x600))

    lines.append("\n=== Hook target 0x57868 -> 0x3B81F0 context ===")
    lines.extend(disasm_range(0x3B81F0, 0x200))

    lines.append("\n=== Vanilla caller context 0x57840-0x578A0 ===")
    lines.extend(disasm_range(0x57840, 0x80))

    lines.append("\n=== Search patch region for CheckTeamMemberIdx / perf flag calls ===")
    rev = syms()
    targets = {
        rev.get(k): k
        for k in [
            "CheckTeamMemberIdx",
            "GetPerformanceFlagWithChecks",
            "LoadScriptVariableValueAtIndex",
            "GetGameMode",
            "GetActiveTeamMember",
        ]
        if k in rev or True
    }
    key_funcs = {}
    t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    for name in [
        "CheckTeamMemberIdx",
        "GetPerformanceFlagWithChecks",
        "LoadScriptVariableValueAtIndex",
        "GetGameMode",
    ]:
        m = re.search(rf"{name}\s*=\s*Symbol\((.*?)\)\n\n", t, re.S)
        if m:
            key_funcs[int(re.findall(r"0x([0-9A-Fa-f]+)", m.group(1))[0], 16)] = name

    patch_start, patch_end = 0x3B0000, 0x3E0000
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for ins in md.disasm(ARM9[patch_start:patch_end], LOAD + patch_start):
        if ins.mnemonic != "bl":
            continue
        w = struct.unpack_from("<I", ARM9, ins.address - LOAD)[0]
        tgt = bl_target(ins.address, w) - LOAD
        if tgt in key_funcs:
            lines.append(
                f"  0x{ins.address-LOAD:X}: bl {key_funcs[tgt]} (r0 setup nearby in full dump)"
            )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
