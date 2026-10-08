"""Disassemble EoA arm9 sites that reference performance flag 55."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
EOA = Path(r"C:\Working\SkyTemple\tools\_tmp_eoa_arm9.bin")
OUT = Path(r"C:\Working\SkyTemple\tools\_disasm_flag55.txt")
LOAD = 0x2000000
BASE_SIZE = 0xDCD48

SITES = [
    0x114C30,
    0x11A028,
    0x16C1BC,
    0x2409A4,
    0x240B90,
    0x241634,
    0x243758,
    0x2B37B8,
    0x2C1708,
    0x2E2F2C,
    0x2E2F74,
    0x2E2F9C,
    0x2E5E84,
]


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


def thumb_disasm(data: bytes, off: int, before: int = 0x40, after: int = 0x80) -> list[str]:
    start = max(0, off - before)
    end = min(len(data), off + after)
    chunk = data[start:end]
    # align to thumb
    if start & 1:
        start += 1
        chunk = data[start:end]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    lines = []
    for ins in md.disasm(chunk, LOAD + start):
        mark = " <--" if ins.address - LOAD == off else ""
        lines.append(f"  0x{ins.address - LOAD:06X}: {ins.mnemonic:8} {ins.op_str}{mark}")
    return lines


def find_bl_targets(data: bytes, syms: dict[str, int]) -> dict[int, str]:
    rev = {v: k for k, v in syms.items()}
    return rev


def scan_near_for_calls(data: bytes, off: int, syms: dict[str, int]) -> list[str]:
    rev = {v: k for k, v in syms.items()}
    hits = []
    start = max(0, off - 0x200)
    end = min(len(data), off + 0x200)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for ins in md.disasm(data[start:end], LOAD + start):
        if ins.mnemonic == "bl":
            try:
                tgt = int(ins.op_str.replace("#", ""), 0)
                rel = tgt - LOAD
                name = rev.get(rel, "?")
                hits.append(f"    bl 0x{rel:X} ({name}) @ 0x{ins.address-LOAD:X}")
            except ValueError:
                pass
    return hits


def main() -> None:
    data = EOA.read_bytes()
    syms = parse_symbols()
    lines: list[str] = []
    key = {
        "GetPerformanceFlagWithChecks": syms.get("GetPerformanceFlagWithChecks"),
        "AddGuestMonster": syms.get("AddGuestMonster"),
        "CheckTeamMemberIdx": syms.get("CheckTeamMemberIdx"),
        "GetPartyMembers": syms.get("GetPartyMembers"),
        "GuestMonsterToGroundMonster": syms.get("GuestMonsterToGroundMonster"),
    }
    lines.append("Key symbol addresses:")
    for k, v in key.items():
        lines.append(f"  {k}: {v and f'0x{v:X}' or 'missing'}")

    for off in SITES:
        region = "EoA-tail" if off >= BASE_SIZE else "base"
        lines.append("")
        lines.append(f"=== Site 0x{off:X} ({region}) ===")
        lines.extend(thumb_disasm(data, off))
        calls = scan_near_for_calls(data, off, syms)
        if calls:
            lines.append("  Nearby calls:")
            lines.extend(calls[:20])

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
