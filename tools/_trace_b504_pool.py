#!/usr/bin/env python3
import struct
from pathlib import Path
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
p = ROOT / "Export Rom" / "Room_Charge_V3_Test" / "_shell559+spinda_menu.nds"
rom = NintendoDSRom(p.read_bytes())
t = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19]
ov = rom.files[t.fileID]
load = t.ramAddress


def ldr_pool(insn_addr: int) -> tuple[int, int]:
    off = insn_addr - load
    word = struct.unpack_from("<I", ov, off)[0]
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    pool = insn_addr + 8 + imm * 4
    val = struct.unpack_from("<I", ov, pool - load)[0]
    return pool, val


def show_table(ptr: int, label: str) -> None:
    print(f"\n{label} @{ptr:#010x}:")
    if ptr < load or ptr >= load + len(ov):
        print("  out of range")
        return
    for i in range(8):
        off = ptr - load + i * 8
        sid, _, act, _ = struct.unpack_from("<4H", ov, off)
        print(f"  [{i}] str={sid} act={act}")
        if sid == 0:
            break


for addr, name in [
    (0x0238B504, "B504 ldr r1"),
    (0x0238B4C8, "B4C8 ldr r2 inner16 alt"),
    (0x0238AB74, "AB74"),
    (0x0238AB80, "AB80"),
]:
    pool, val = ldr_pool(addr)
    print(f"{name} @{addr:#x}: pool {pool:#x} -> {val:#010x}")
    show_table(val, name)

b474 = struct.unpack_from("<I", ov, 0x0238B474 - load)[0]
print(f"\nB474 word = {b474:#010x}")
show_table(b474, "B474 table")
