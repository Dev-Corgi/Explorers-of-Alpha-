"""Search EoA arm9 and pmdsky for level scaling / guest logic."""
from __future__ import annotations

import re
import struct
from pathlib import Path

PMDSKY = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
EOA_ARM9 = Path(r"C:\Working\SkyTemple\tools\_tmp_eoa_arm9.bin")
BASE_ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin")
OUT = Path(r"C:\Working\SkyTemple\tools\_level_scaling_search.txt")


def parse_symbols() -> dict[str, tuple[int, str]]:
    text = PMDSKY.read_text(encoding="utf-8", errors="ignore")
    syms: dict[str, tuple[int, str]] = {}
    for m in re.finditer(r"(\w+)\s*=\s*Symbol\((.*?)\)\n\n", text, re.S):
        name = m.group(1)
        body = m.group(2)
        dm = re.search(r'"([^"]*)"\s*,\s*"([^"]*)"', body)
        if not dm:
            continue
        addr_s, desc = dm.group(1), dm.group(2)
        try:
            addr = int(addr_s, 16)
        except ValueError:
            continue
        syms[name] = (addr, desc)
    return syms


def find_arm_refs(data: bytes, addr: int, load_base: int = 0x2000000) -> list[int]:
    """Find PC-relative LDR refs to addr in ARM/Thumb code."""
    hits: list[int] = []
    # common: ldr rX, [pc, #imm] loading literal pool value == addr
    target = struct.pack("<I", addr)
    off = 0
    while True:
        pos = data.find(target, off)
        if pos == -1:
            break
        hits.append(pos)
        off = pos + 1
    return hits


def main() -> None:
    syms = parse_symbols()
    lines: list[str] = []

    keywords = [
        "guest",
        "performance",
        "scale",
        "level",
        "team",
        "party",
        "spawn",
        "dungeon",
        "enemy",
        "monster",
        "ground",
    ]
    lines.append("=== Relevant pmdsky symbols ===")
    for name, (addr, desc) in sorted(syms.items(), key=lambda x: x[1][0]):
        blob = (name + " " + desc).lower()
        if any(k in blob for k in keywords):
            if any(
                k in blob
                for k in [
                    "guest",
                    "performance",
                    "scale",
                    "team",
                    "party",
                    "spawn",
                    "level",
                    "dungeon",
                    "enemy",
                    "ground_monster",
                    "active",
                ]
            ):
                lines.append(f"0x{addr:08X} {name}: {desc[:160]}")

    eoa = EOA_ARM9.read_bytes()
    base = BASE_ARM9.read_bytes()
    lines.append("")
    lines.append(f"=== arm9 sizes: base=0x{len(base):X} eoa=0x{len(eoa):X} ===")

    # Search EoA-only tail for patterns
    tail = eoa[len(base) :]
    lines.append(f"EoA-only tail size: 0x{len(tail):X} starting at 0x{len(base):X}")

    # Search for immediate 55 (0x37) near performance flag reads
    perf_sym = syms.get("GetPerformanceFlagWithChecks")
    if perf_sym:
        addr, desc = perf_sym
        lines.append(f"\nGetPerformanceFlagWithChecks @ 0x{addr:08X}: {desc}")
        refs = find_arm_refs(eoa[: len(base)], addr)
        lines.append(f"  literal pool refs in base region: {len(refs)}")
        for r in refs[:10]:
            lines.append(f"    pool @ 0x{r:X}")

    # Scan for functions referencing flag index 55
    # Thumb: mov r0, #55 => 0x2037 in some encodings; movw/movt patterns
    lines.append("\n=== Scanning for mov #55 / cmp #55 in EoA arm9 ===")
    count = 0
    i = 0
    while i < len(eoa) - 1:
        hw = eoa[i] | (eoa[i + 1] << 8)
        # thumb mov imm8: 00100ddd iiiiiiii  where imm8=55=0x37, rd=0 => 0x2037
        if (hw & 0xF800) == 0x2000 and (hw & 0xFF) == 0x37:
            lines.append(f"  thumb mov r{(hw>>8)&7}, #55 @ 0x{i:X}")
            count += 1
            if count > 40:
                lines.append("  ... truncated")
                break
        i += 2

    # Guest-related symbol refs
    lines.append("\n=== Guest symbol literal refs in EoA arm9 ===")
    for sym_name in [
        "AddGuestMonster",
        "GuestMonsterToGroundMonster",
        "GUEST_MONSTER_DATA",
        "GetPerformanceFlagWithChecks",
    ]:
        if sym_name not in syms:
            continue
        addr, desc = syms[sym_name]
        refs = find_arm_refs(eoa, addr)
        lines.append(f"{sym_name} @ 0x{addr:08X}: {len(refs)} literal refs")
        for r in refs[:8]:
            lines.append(f"  0x{r:X}")

    # Diff scan: find changed regions in overlapping part
    lines.append("\n=== Changed regions in overlapping arm9 (first 20) ===")
    changes: list[tuple[int, int]] = []
    start = None
    for i in range(min(len(base), len(eoa))):
        if base[i] != eoa[i]:
            if start is None:
                start = i
        elif start is not None:
            changes.append((start, i))
            start = None
    if start is not None:
        changes.append((start, min(len(base), len(eoa))))
    for s, e in changes[:20]:
        lines.append(f"  0x{s:X}-0x{e:X} ({e-s} bytes)")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
