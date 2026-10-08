"""Find LoadScriptVariableValueAtIndex(0, 0x4e, 55) — performance flag 55 reads."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
OUT = Path(r"C:\Working\SkyTemple\tools\_perf55_loads.txt")
LOAD = 0x02000000
LOADVAR_OFF = 0x4B678
LOADVAR_RAM = 0x204B678


def parse_syms() -> dict[str, int]:
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


def disasm(data: bytes, off: int, before=0x80, after=0x100) -> list[str]:
    syms = parse_syms()
    rev = {v: k for k, v in syms.items()}
    start = max(0, off - before)
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    lines = []
    for ins in md.disasm(data[start : off + after], LOAD + start):
        note = ""
        if ins.mnemonic == "bl":
            w = struct.unpack_from("<I", data, ins.address - LOAD)[0]
            tgt = bl_target(ins.address, w) - LOAD
            if tgt in rev:
                note = f"  ; {rev[tgt]}"
        lines.append(f"0x{ins.address-LOAD:06X}: {ins.mnemonic:7} {ins.op_str}{note}")
    return lines


def main() -> None:
    syms = parse_syms()
    lines: list[str] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    # Find all bl LoadScriptVariableValueAtIndex
    loadvar_calls = []
    for off in range(0, len(ARM9) - 3, 4):
        w = struct.unpack_from("<I", ARM9, off)[0]
        if w >> 24 != 0xEB:
            continue
        if bl_target(LOAD + off, w) != LOADVAR_RAM:
            continue
        loadvar_calls.append(off)

    lines.append(f"LoadScriptVariableValueAtIndex callers: {len(loadvar_calls)}")

    perf55 = []
    perf_group = []
    for bl_off in loadvar_calls:
        # look back up to 12 insns for mov r1,#0x4e and mov r2,#0x37 (or lsl/lsr pattern)
        start = max(0, bl_off - 0x40)
        chunk = list(md.disasm(ARM9[start : bl_off + 4], LOAD + start))
        r1_4e = any(
            i.mnemonic == "mov" and i.op_str.strip() in ("r1, #0x4e", "r1, #78")
            for i in chunk
        )
        r2_37 = any(
            i.mnemonic == "mov" and i.op_str.strip() in ("r2, #0x37", "r2, #55")
            for i in chunk
        )
        if r1_4e:
            perf_group.append(bl_off)
        if r1_4e and r2_37:
            perf55.append(bl_off)

    lines.append(f"Calls with r1=#0x4e (perf list): {len(perf_group)}")
    lines.append(f"Calls with r1=#0x4e AND r2=#55: {len(perf55)}")

    for bl_off in perf55:
        lines.append(f"\n=== PERF FLAG 55 READ @ 0x{bl_off:X} ===")
        lines.extend(disasm(ARM9, bl_off))

    # Also check GetPerformanceFlagWithChecks callers with r0=55 via mov/lsl pattern
    perf_fn = syms["GetPerformanceFlagWithChecks"]
    lines.append("\n=== GetPerformanceFlagWithChecks callers ===")
    for off in range(0, len(ARM9) - 3, 4):
        w = struct.unpack_from("<I", ARM9, off)[0]
        if w >> 24 != 0xEB:
            continue
        if bl_target(LOAD + off, w) != LOAD + perf_fn:
            continue
        start = max(0, off - 0x30)
        chunk = list(md.disasm(ARM9[start : off + 4], LOAD + start))
        for ins in chunk:
            if ins.mnemonic == "mov" and ins.op_str.strip() in ("r0, #0x37", "r0, #55"):
                lines.append(f"\n=== GetPerformanceFlag(55) @ 0x{off:X} ===")
                lines.extend(disasm(ARM9, off))
                break

    # Search raw for perf group reads with index 55 in literal pool near calls
    lines.append("\n=== All perf-group calls with nearby level/team logic (first 15) ===")
    for bl_off in perf_group[:40]:
        ctx = "\n".join(disasm(ARM9, bl_off, 0x40, 0x60))
        if any(
            k in ctx
            for k in [
                "CheckTeamMemberIdx",
                "GetActiveTeamMember",
                "GetPartyMembers",
                "GetTeamMember",
                "#0x34",
                "#0x36",
                "#3",
                "#4",
            ]
        ):
            lines.append(f"\n--- interesting perf read @ 0x{bl_off:X} ---")
            lines.append(ctx)

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"perf55={len(perf55)} perf_group={len(perf_group)} -> {OUT}")


if __name__ == "__main__":
    main()
