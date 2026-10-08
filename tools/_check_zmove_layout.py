#!/usr/bin/env python3
"""Verify Z-Move cave does not overlap TM Read / other ov29 regions."""
from __future__ import annotations

import struct
import subprocess
import shutil
import tempfile
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
TMREAD = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges_orbcount_tmread.nds"
)
ZMOVE = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges_orbcount_tmread_zmove.nds"
)
ARMIPS = ROOT / "tools" / "armips.exe"
ASM_DIR = ROOT / "asm_patches" / "z_move"

OV29_BASE = 0x022DC240
OV31_BASE = 0x02382820

REGIONS = [
    ("BerryBoost cave", 0x02330100, None),
    ("OrbCharges table", 0x023302B0, None),
    ("TmRead code", 0x02330478, 0x02330900 - 0x02330478),
    ("TmChargeTable", 0x02330900, 121 * 4),
    ("ZMove cave start", 0x02330B20, None),
]


def load_ov(rom_path: Path, ov_id: int) -> bytes:
    rom = NintendoDSRom(rom_path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    return rom.files[table[ov_id].fileID]


def armips_symbol_end() -> dict[str, int]:
    """Assemble z_move alone and parse armips listing if available."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "zmove"
        shutil.copytree(ASM_DIR, work)
        rom = NintendoDSRom(TMREAD.read_bytes())
        table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
        (work / "overlay_0029.bin").write_bytes(rom.files[table[29].fileID])
        (work / "overlay_0031.bin").write_bytes(rom.files[table[31].fileID])
        result = subprocess.run(
            [str(ARMIPS), "-sym", "zmove.sym", "main.asm"],
            cwd=work,
            capture_output=True,
            text=True,
        )
        sym_path = work / "zmove.sym"
        symbols: dict[str, int] = {}
        if sym_path.is_file():
            for line in sym_path.read_text(encoding="utf-8", errors="replace").splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0].startswith("0x"):
                    try:
                        symbols[parts[1]] = int(parts[0], 16)
                    except ValueError:
                        pass
        return symbols, result.returncode, result.stderr or result.stdout


def diff_span(a: bytes, b: bytes) -> tuple[int | None, int | None]:
    start = end = None
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            if start is None:
                start = i
            end = i
    return start, end


def main() -> None:
    ov29_tm = load_ov(TMREAD, 29)
    ov29_zm = load_ov(ZMOVE, 29)
    ov31_tm = load_ov(TMREAD, 31)
    ov31_zm = load_ov(ZMOVE, 31)

    print("=== overlay29 size ===")
    print(f"  bytes: {len(ov29_zm)} ({hex(len(ov29_zm))})")
    print(f"  RAM:   {OV29_BASE:#x} - {OV29_BASE + len(ov29_zm):#x}")

    print("\n=== reserved regions (fixed addresses) ===")
    for name, start, size in REGIONS:
        end = start + size if size else None
        in_file = start - OV29_BASE < len(ov29_zm)
        line = f"  {name}: {start:#x}"
        if size:
            line += f" .. {end:#x} ({size} bytes)"
        line += f"  [{'OK in file' if in_file else 'PAST END'}]"
        print(line)

    table_end = 0x02330900 + 121 * 4
    gap = 0x02330B20 - table_end
    print(f"\n  TmChargeTable ends {table_end:#x}, ZMove starts 0x02330B20, gap = {gap} bytes")

    print("\n=== ov29 diff (tmread -> zmove) ===")
    s, e = diff_span(ov29_tm, ov29_zm)
    if s is None:
        print("  (no differences)")
    else:
        print(f"  file offset {s:#x}..{e:#x}  ({e - s + 1} bytes)")
        print(f"  RAM         {OV29_BASE + s:#x}..{OV29_BASE + e:#x}")

    cave_off = 0x02330B20 - OV29_BASE
    cs, ce = diff_span(ov29_tm[cave_off:], ov29_zm[cave_off:])
    if cs is not None:
        print(f"\n=== ZMove cave write span ===")
        print(f"  RAM {0x02330B20 + cs:#x} .. {0x02330B20 + ce:#x}  ({ce - cs + 1} bytes)")

    print("\n=== tmread padding at ZMove cave (before patch) ===")
    pad = ov29_tm[cave_off : cave_off + gap]
    nonzero = sum(1 for b in pad if b != 0)
    print(f"  {gap} bytes before ZMove start: {nonzero} non-zero (expect 0 = free padding)")

    print("\n=== ov31 hook sites ===")
    for addr, label in [(0x023859C0, "menu hook"), (0x02385FC0, "confirm hook")]:
        o = addr - OV31_BASE
        w_tm = struct.unpack_from("<I", ov31_tm, o)[0]
        w_zm = struct.unpack_from("<I", ov31_zm, o)[0]
        print(f"  {label} {addr:#x}: tmread={w_tm:#010x} zmove={w_zm:#010x} changed={w_tm != w_zm}")

    print("\n=== armips symbols (Z-Move assemble on tmread base) ===")
    symbols, rc, log = armips_symbol_end()
    if rc != 0:
        print(f"  armips failed ({rc}): {log[:500]}")
    else:
        for key in sorted(symbols):
            if "ZMove" in key or key.endswith("Dispatch") or key.endswith("MenuHook"):
                print(f"  {key}: {symbols[key]:#x}")
        # estimate code end from last symbol
        zmove_addrs = [v for k, v in symbols.items() if v >= 0x02330B20 and v < 0x02340000]
        if zmove_addrs:
            print(f"  ZMove code region approx end: {max(zmove_addrs):#x}")

    checks = [
        ("TmRead code", 0x02330478, 0x02330900 - 0x02330478),
        ("TmChargeTable", 0x02330900, 121 * 4),
        ("Gap padding", 0x02330AE4, 0x02330B20 - 0x02330AE4),
        ("StartMFunc entry", 0x02330134, 0x40),
        ("EndMFunc entry", 0x023326CC, 0x20),
        ("RoomCharge cave", 0x022DC240 + 0x40145, 0x100),
    ]

    for name, start, size in checks:
        o = start - OV29_BASE
        same = ov29_tm[o : o + size] == ov29_zm[o : o + size]
        status = "OK identical" if same else "CHANGED!"
        print(f"  {name} {start:#x} len={size}: {status}")

    print("\n=== discrete diff regions ===")
    regions: list[tuple[int, int]] = []
    i = 0
    n = min(len(ov29_tm), len(ov29_zm))
    while i < n:
        while i < n and ov29_tm[i] == ov29_zm[i]:
            i += 1
        if i >= n:
            break
        s = i
        while i < n and ov29_tm[i] != ov29_zm[i]:
            i += 1
        regions.append((s, i - 1))
    print(f"  count: {len(regions)}")
    for s, e in regions:
        print(f"  file {s:#x}..{e:#x} ({e - s + 1} B)  RAM {OV29_BASE + s:#x}..{OV29_BASE + e:#x}")

    cave_off = 0x02330B20 - OV29_BASE
    pre = ov29_tm[cave_off : cave_off + 0x400]
    print("\n=== ZMove cave pre-patch (tmread ROM) ===")
    print("  first 64 bytes:", pre[:64].hex())
    print("  zero ratio:", sum(1 for b in pre if b == 0), "/", len(pre))
    print("  ff ratio:", sum(1 for b in pre if b == 0xFF), "/", len(pre))

    print("\n=== StartMFunc / EndMFunc window ===")
    for label, addr in [("StartMFunc", 0x02330134), ("EndMFunc", 0x023326CC)]:
        o = addr - OV29_BASE
        print(f"  {label} {addr:#x}: tm={ov29_tm[o:o+4].hex()} zm={ov29_zm[o:o+4].hex()}")

    print("\n=== overlap check ===")
    zmove_start = 0x02330B20
    zmove_end_est = max(zmove_addrs) + 64 if symbols and zmove_addrs else zmove_start + 0x400
    tm_table_end = 0x02330900 + 121 * 4
    tm_code_end = 0x02330900
    ok_table = zmove_start >= tm_table_end
    print(f"  ZMove [{zmove_start:#x}..~{zmove_end_est:#x}] vs TmChargeTable [{0x02330900:#x}..{tm_table_end:#x}]: {'OK' if ok_table else 'OVERLAP!'}")
    ok_tmcode = zmove_start >= tm_code_end
    print(f"  ZMove vs TmRead code [{0x02330478:#x}..{tm_code_end:#x}]: {'OK' if ok_tmcode else 'OVERLAP!'}")

    # check if ZMove extends past overlay
    if zmove_end_est > OV29_BASE + len(ov29_zm):
        print(f"  WARNING: ZMove may extend past overlay29 end ({OV29_BASE + len(ov29_zm):#x})!")
    else:
        print(f"  ZMove end within overlay29: OK")


if __name__ == "__main__":
    main()
