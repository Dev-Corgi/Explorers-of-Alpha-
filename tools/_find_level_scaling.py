"""Find level scaling code in EoA arm9 by tracing GetPerformanceFlagWithChecks(55)."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
EOA = Path(r"C:\Working\SkyTemple\tools\_tmp_eoa_arm9.bin")
OUT = Path(r"C:\Working\SkyTemple\tools\_level_scaling_analysis.txt")
LOAD = 0x2000000
FILE_OFF = lambda ram: ram - LOAD


def parse_symbols() -> dict[str, int]:
    text = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    out: dict[str, int] = {}
    for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", text, re.S):
        name = m.group(1)
        dm = re.search(r'"([^"]*)"', m.group(2))
        if not dm:
            continue
        try:
            out[name] = int(dm.group(1), 16)
        except ValueError:
            pass
    return out


def find_literal_pools(data: bytes, value: int) -> list[int]:
    pat = struct.pack("<I", value)
    out = []
    i = 0
    while True:
        p = data.find(pat, i)
        if p == -1:
            break
        out.append(p)
        i = p + 1
    return out


def disasm_range(data: bytes, start: int, size: int) -> list[str]:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    lines = []
    for ins in md.disasm(data[start : start + size], LOAD + start):
        lines.append(f"0x{ins.address - LOAD:06X}: {ins.mnemonic:8} {ins.op_str}")
    return lines


def scan_bl_to(data: bytes, target_ram: int, syms: dict[str, int]) -> list[tuple[int, str]]:
    rev = {v: k for k, v in syms.items()}
    tgt_off = FILE_OFF(target_ram)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    hits = []
    for ins in md.disasm(data, LOAD):
        if ins.mnemonic != "bl":
            continue
        try:
            t = int(ins.op_str.replace("#", ""), 0)
            if t - LOAD == tgt_off or t == target_ram:
                fn = rev.get(t, rev.get(t if t < LOAD else t, "?"))
                hits.append((ins.address - LOAD, fn))
        except ValueError:
            pass
    return hits


def find_mov_imm55_before_bl(data: bytes, bl_off: int, window: int = 0x30) -> list[int]:
    start = max(0, bl_off - window)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    movs = []
    for ins in md.disasm(data[start:bl_off + 4], LOAD + start):
        if ins.mnemonic == "mov" and "#0x37" in ins.op_str:
            movs.append(ins.address - LOAD)
        if ins.mnemonic == "movs" and "#0x37" in ins.op_str:
            movs.append(ins.address - LOAD)
    return movs


def main() -> None:
    data = EOA.read_bytes()
    syms = parse_symbols()
    lines: list[str] = []

    interesting = [
        "GetPerformanceFlagWithChecks",
        "CheckTeamMemberIdx",
        "GetPartyMembers",
        "AddGuestMonster",
        "GuestMonsterToGroundMonster",
        "GetActiveTeamMember",
        "GetTeamMember",
        "InitDungeonLevel",
        "GenerateFloorMonster",
        "SetMonLevel",
        "GetLevel",
        "GetMaxTeamLevel",
        "GetLeaderLevel",
        "GetActiveTeamLeaderLevel",
        "GetTeamHighestLevel",
        "GetHighestLevelInTeam",
        "GetTeamLevel",
        "ScaleLevel",
        "AdjustLevel",
    ]
    lines.append("=== Symbol addresses ===")
    for name in interesting:
        if name in syms:
            lines.append(f"{name}: 0x{syms[name]:08X} (file 0x{FILE_OFF(syms[name]):X})")

    perf = syms.get("GetPerformanceFlagWithChecks")
    if perf:
        lines.append(f"\n=== BL callers to GetPerformanceFlagWithChecks @ 0x{perf:08X} ===")
        callers = scan_bl_to(data, perf, syms)
        lines.append(f"Total callers: {len(callers)}")
        flag55_callers = []
        for off, fn in callers:
            movs = find_mov_imm55_before_bl(data, off)
            if movs:
                flag55_callers.append((off, movs))
                lines.append(f"\n-- Caller @ 0x{off:X}, mov #55 @ {[hex(m) for m in movs]} --")
                lines.extend(disasm_range(data, max(0, off - 0x40), 0x80))

        lines.append(f"\nFlag-55 callers found: {len(flag55_callers)}")

    # Search for CheckTeamMemberIdx callers - guest detection
    chk = syms.get("CheckTeamMemberIdx")
    if chk:
        lines.append(f"\n=== CheckTeamMemberIdx callers (first 30) ===")
        callers = scan_bl_to(data, chk, syms)[:30]
        for off, _ in callers:
            lines.append(f"  0x{off:X}")
            ctx = disasm_range(data, max(0, off - 0x20), 0x50)
            lines.extend("    " + ln for ln in ctx[:12])

    # Search EoA tail for loops 0..3 with level reads (ldrb/ldrh at team_member+level offset)
    # team_member level is often at offset 0x2C or similar - search for cmp rX, #3 / cmp rX, #4 patterns near bl perf

    # Also search strings in arm9
    for s in [b"Level Scaling", b"level scaling", b"team levels"]:
        p = data.find(s)
        if p != -1:
            lines.append(f"\nString {s!r} in arm9 @ 0x{p:X}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
