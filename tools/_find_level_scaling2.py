"""Find level scaling: GetPerformanceFlagWithChecks(55) callers in EoA arm9."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
EOA = Path(r"C:\Working\SkyTemple\tools\_tmp_eoa_arm9.bin")
OUT = Path(r"C:\Working\SkyTemple\tools\_level_scaling_analysis.txt")
LOAD = 0x02000000  # thumb bl targets use this base in many EoS disasms


def parse_symbols() -> dict[str, tuple[int, int, str]]:
    text = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    out: dict[str, tuple[int, int, str]] = {}
    for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", text, re.S):
        name = m.group(1)
        body = m.group(2)
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", body)]
        if len(nums) < 2:
            continue
        file_off, ram = nums[0], nums[1]
        dm = re.search(r'"([^"]*)"\s*,\s*"([^"]*)"', body)
        desc = dm.group(2) if dm else ""
        out[name] = (file_off, ram, desc)
    return out


def disasm(data: bytes, start: int, size: int) -> list[str]:
    if start & 1:
        start -= 1
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    return [
        f"0x{ins.address - LOAD:06X}  file=0x{ins.address - LOAD:06X}  {ins.mnemonic:7} {ins.op_str}"
        for ins in md.disasm(data[start : start + size], LOAD + start)
    ]


def scan_all_bl(data: bytes, target_file_off: int, target_ram: int) -> list[int]:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    hits = []
    for ins in md.disasm(data, LOAD):
        if ins.mnemonic != "bl":
            continue
        try:
            t = int(ins.op_str.replace("#", ""), 0)
        except ValueError:
            continue
        rel = t - LOAD
        if rel == target_file_off or t == target_ram or rel == target_ram:
            hits.append(ins.address - LOAD)
    return hits


def has_mov55_before(data: bytes, bl_off: int, back: int = 0x24) -> bool:
    start = max(0, bl_off - back)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for ins in md.disasm(data[start : bl_off + 2], LOAD + start):
        if ins.mnemonic in ("mov", "movs") and ins.op_str.endswith("#0x37"):
            return True
    return False


def main() -> None:
    data = EOA.read_bytes()
    syms = parse_symbols()
    lines: list[str] = []

    perf = syms["GetPerformanceFlagWithChecks"]
    perf_off, perf_ram, perf_desc = perf
    lines.append(f"GetPerformanceFlagWithChecks file=0x{perf_off:X} ram=0x{perf_ram:X}")
    lines.append(perf_desc[:300])
    lines.append("")

    callers = scan_all_bl(data, perf_off, perf_ram)
    lines.append(f"Total bl callers: {len(callers)}")

    flag55 = [c for c in callers if has_mov55_before(data, c)]
    lines.append(f"Callers with mov #55 before bl: {len(flag55)}")
    for c in flag55:
        lines.append(f"\n=== Candidate @ file 0x{c:X} ===")
        lines.extend(disasm(data, c - 0x50, 0xA0))

    # Also scan EoA tail only for movs r0,#55 followed by bl within 8 ins
    lines.append("\n=== Scan: mov r0,#55 then bl GetPerformanceFlag within 16 bytes ===")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    insns = list(md.disasm(data, LOAD))
    for i, ins in enumerate(insns):
        if ins.mnemonic not in ("mov", "movs"):
            continue
        if not (ins.op_str.startswith("r0, #0x37") or ins.op_str == "r0, #0x37"):
            continue
        off = ins.address - LOAD
        for ins2 in insns[i + 1 : i + 6]:
            if ins2.mnemonic == "bl":
                try:
                    t = int(ins2.op_str.replace("#", ""), 0)
                except ValueError:
                    break
                if t - LOAD == perf_off or t == perf_ram:
                    lines.append(f"\n=== Tight pair mov#55 @ 0x{off:X} -> bl @ 0x{ins2.address-LOAD:X} ===")
                    lines.extend(disasm(data, off - 0x30, 0x80))
                break

    # CheckTeamMemberIdx near level scaling candidates
    if "CheckTeamMemberIdx" in syms:
        chk_off = syms["CheckTeamMemberIdx"][0]
        lines.append(f"\nCheckTeamMemberIdx file=0x{chk_off:X}")
        for c in flag55:
            window = data[c : c + 0x200]
            md2 = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
            for ins in md2.disasm(window, LOAD + c):
                if ins.mnemonic != "bl":
                    continue
                try:
                    t = int(ins.op_str.replace("#", ""), 0)
                except ValueError:
                    continue
                if t - LOAD == chk_off:
                    lines.append(f"  CheckTeamMemberIdx call from 0x{ins.address-LOAD:X} (near flag55 site 0x{c:X})")

    # Search for party slot loops: cmp rX, #3 near level reads in flag55 functions
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}, flag55 callers={len(flag55)}")


if __name__ == "__main__":
    main()
