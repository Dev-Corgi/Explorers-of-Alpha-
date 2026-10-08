#!/usr/bin/env python3
"""Analyze Helping Hand (move 176) stat boost path: vanilla vs patched."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.data.data_cd.handler import DataCDHandler

ROOT = Path(__file__).resolve().parent.parent
VAN = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
PAT = ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds"
BASE = 0x022DC240
BOOST_OFF = 0x0231399C


def load_ov(rom: NintendoDSRom) -> bytes:
    return rom.files[loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[29].fileID]


def bl_dest(word: int, pc: int) -> int | None:
    if (word >> 24) != 0xEB:
        return None
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return pc + 8 + (imm << 2)


def find_bl_to(ov: bytes, target: int, start: int, end: int) -> list[int]:
    hits: list[int] = []
    for addr in range(start, end, 4):
        w = struct.unpack_from("<I", ov, addr - BASE)[0]
        if bl_dest(w, addr) == target:
            hits.append(addr)
    return hits


def disasm_context(ov: bytes, addr: int, before: int = 6, after: int = 2) -> None:
    print(f"  context @ {addr:#010x}:")
    for i in range(-before, after + 1):
        a = addr + i * 4
        w = struct.unpack_from("<I", ov, a - BASE)[0]
        mark = ">>" if i == 0 else "  "
        extra = ""
        d = bl_dest(w, a)
        if d is not None:
            extra = f"  -> bl {d:#x}"
        print(f"  {mark} {a:#010x}: {w:08x}{extra}")


def waza_cd176(rom: NintendoDSRom) -> bytes:
    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/waza_cd.bin"))
    return cd.get_effect_code(176)


def main() -> None:
    van_rom = NintendoDSRom(VAN.read_bytes())
    pat_rom = NintendoDSRom(PAT.read_bytes())
    ov_v = load_ov(van_rom)
    ov_p = load_ov(pat_rom)

    c_v = waza_cd176(van_rom)
    c_p = waza_cd176(pat_rom)
    print("waza_cd effect 176 same:", c_v == c_p)
    print("waza_cd176 hex:", c_v.hex())

    # Decode bl in waza_cd stub (effect runs from pool; check static copy in ov29 too)
    w = struct.unpack_from("<I", c_v, 16)[0]
    print("waza_cd176 bl word:", hex(w))

    # Search BoostOffensiveStat callers in Helping Hand handler region
    hh_start, hh_end = 0x0232CB08, 0x0232CE00
    print("\n=== BoostOffensiveStat callers in HH handler region ===")
    for label, ov in [("van", ov_v), ("pat", ov_p)]:
        hits = find_bl_to(ov, BOOST_OFF, hh_start, hh_end)
        print(f"{label}: {len(hits)} calls")
        for h in hits:
            disasm_context(ov, h)

    # Broader: all BoostOffensiveStat callers with r2 setup (mov r2, #imm nearby)
    print("\n=== All BoostOffensiveStat calls with r2/r3 setup (scan 0x2320000-0x2330000) ===")
    for label, ov in [("van", ov_v), ("pat", ov_p)]:
        hits = find_bl_to(ov, BOOST_OFF, 0x02320000, 0x02330000)
        print(f"\n{label}: {len(hits)} total callers in range")
        for h in hits:
            r2_imm = None
            r3_imm = None
            for back in range(1, 8):
                a = h - back * 4
                w = struct.unpack_from("<I", ov, a - BASE)[0]
                # mov r2, #imm : e3a02xxx
                if (w & 0xFFFFF000) == 0xE3A02000:
                    r2_imm = w & 0xFF
                # mov r3, #imm : e3a03xxx
                if (w & 0xFFFFF000) == 0xE3A03000:
                    r3_imm = w & 0xFF
            if h >= 0x0232CB08 and h < 0x0232CE00:
                print(f"  HH region {h:#x}: r2=#{r2_imm} r3=#{r3_imm}")
                disasm_context(ov, h, before=4, after=1)

    # Diff ov29 between van/pat in HH + boost regions
    print("\n=== Byte diffs in stat-boost related regions ===")
    regions = [
        (0x0232CB08, 0x400, "HH_handler"),
        (0x0231399C, 0x180, "BoostOffensiveStat"),
        (0x0231657C, 0x120, "helper_657c"),
        (0x02301940, 0x100, "func_1940"),
        (0x02302430, 0x100, "func_2430"),
        (0x0230175C, 0x80, "func_175c"),
        (0x02320D08, 0x100, "func_0d08"),
    ]
    for start, size, name in regions:
        off = start - BASE
        same = ov_v[off : off + size] == ov_p[off : off + size]
        if not same:
            diffs = sum(
                1
                for i in range(size)
                if ov_v[off + i] != ov_p[off + i]
            )
            print(f"  DIFF {name}: {diffs} bytes differ")
        else:
            print(f"  OK   {name}: identical")


if __name__ == "__main__":
    main()
