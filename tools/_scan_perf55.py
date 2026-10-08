"""Scan EoA arm9 for direct reads of performance flag 55 and team level loops."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
EOA = Path(r"C:\Working\SkyTemple\tools\_tmp_eoa_arm9.bin")
OUT = Path(r"C:\Working\SkyTemple\tools\_scan_perf55.txt")
LOAD = 0x02000000
TAIL = 0xDCD48


def parse_symbol(name: str) -> tuple[int, int]:
    t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    m = re.search(rf"{name}\s*=\s*Symbol\((.*?)\)\n\n", t, re.S)
    nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(1))]
    return nums[0], nums[1]


def find_refs(data: bytes, addr: int) -> list[int]:
    pat = struct.pack("<I", addr)
    out = []
    i = 0
    while True:
        p = data.find(pat, i)
        if p == -1:
            break
        out.append(p)
        i = p + 1
    return out


def disasm_at(data: bytes, off: int, before=0x40, after=0x60) -> list[str]:
    start = max(0, off - before)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    lines = []
    for ins in md.disasm(data[start : off + after], LOAD + start):
        mark = " <--" if ins.address - LOAD == off else ""
        lines.append(f"0x{ins.address-LOAD:06X}: {ins.mnemonic:7} {ins.op_str}{mark}")
    return lines


def main() -> None:
    data = EOA.read_bytes()
    lines: list[str] = []

    perf_fn_off, perf_fn_ram = parse_symbol("GetPerformanceFlagWithChecks")
    lines.append(f"GetPerformanceFlagWithChecks off=0x{perf_fn_off:X} ram=0x{perf_fn_ram:X}")

    # literal pool refs to function
    refs = find_refs(data, perf_fn_ram)
    lines.append(f"Literal pool refs to perf fn ram addr: {len(refs)}")
    for r in refs[:15]:
        region = "tail" if r >= TAIL else "base"
        lines.append(f"  pool@0x{r:X} ({region})")
        lines.extend("    " + x for x in disasm_at(data, r - 8, 0x30, 0x20)[:8])

    # Search VAR_PERFORMANCE symbols
    t = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"(VAR_PERFORMANCE\w*)\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
        name = m.group(1)
        nums = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]+)", m.group(2))]
        if len(nums) < 2:
            continue
        off, ram = nums[0], nums[1]
        lines.append(f"\n{name} off=0x{off:X} ram=0x{ram:X}")
        refs2 = find_refs(data, ram)
        lines.append(f"  refs: {len(refs2)}")
        for r in refs2[:5]:
            lines.append(f"    0x{r:X}")

    # Scan tail for functions with: mov r0,#0..3 loop + ldrh level + cmp/update max
    lines.append("\n=== Tail functions referencing CheckTeamMemberIdx ===")
    chk_off, chk_ram = parse_symbol("CheckTeamMemberIdx")
    refs3 = find_refs(data, chk_ram)
    tail_refs = [r for r in refs3 if r >= TAIL - 0x1000 or True]
    lines.append(f"CheckTeamMemberIdx pool refs: {len(refs3)}")
    for r in refs3:
        # find code referencing this pool (rough: disasm backwards)
        if r < TAIL:
            continue
        lines.append(f"\n-- pool near tail 0x{r:X} --")
        lines.extend(disasm_at(data, r, 0x80, 0x10)[:20])

    # Search EoA tail for sequence: cmp r?, #3 / cmp r?, #4 with ldrh [..,#0x?] level offset
    # team_member level offset in EoS is 0x34 (52) for current level? Let me check pmdsky struct
    for m in re.finditer(r"TEAM_MEMBER_LEVEL\w*\s*=\s*Symbol\((.*?)\)\n\n", t, re.S):
        pass

    # brute: find in tail all ldrh with #0x34 or #0x36 (common level offsets)
    lines.append("\n=== Tail thumb: ldrh [..,#0x34] occurrences (first 20) ===")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    count = 0
    for ins in md.disasm(data[TAIL:], LOAD + TAIL):
        if "#0x34" in ins.op_str and "ldrh" in ins.mnemonic:
            lines.append(f"0x{ins.address-LOAD:X}: {ins.mnemonic} {ins.op_str}")
            count += 1
            if count >= 20:
                break

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
