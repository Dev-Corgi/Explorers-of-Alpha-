#!/usr/bin/env python3
"""Find Drink post-pick submenu path: C290, BarInitTeamMenuWindow, E290 xrefs."""
from __future__ import annotations

import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent


def find_pc_refs(data: bytes, load: int, target: int, cs: Cs) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for ins in cs.disasm(data, load):
        if ins.mnemonic != "ldr" or "[pc" not in ins.op_str:
            continue
        pc = (ins.address + 8) & ~3
        for imm in range(-0x3000, 0x3000, 4):
            if (pc + imm) & 0xFFFFFFFF == target:
                hits.append((ins.address, f"{ins.mnemonic} {ins.op_str}"))
                break
    return hits


def disasm_window(data: bytes, load: int, addr: int, before: int = 0x20, after: int = 0x30) -> None:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    start = max(load, addr - before)
    print(f"\n=== @{addr:#010x} ===")
    for ins in cs.disasm(data[start - load : addr - load + after], start):
        mark = " >>>" if ins.address == addr else ""
        print(f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}{mark}")


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROOT / "Explorers of Alpha_berryboost.nds"))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov = rom.files[table[19].fileID]
    load = table[19].ramAddress
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    targets = [
        ("E290 BAR_SUBMENU_ITEMS_2", 0x0238E290),
        ("DD04 cave", 0x0238DD04),
        ("B474 pool", 0x0238B474),
        ("C504 pool (C290 r1)", 0x0238C504),
        ("E1F8 BarInit params", 0x0238E1F8),
    ]
    for name, tgt in targets:
        refs = find_pc_refs(ov, load, tgt, cs)
        print(f"\n{name} @{tgt:#010x}: {len(refs)} pc-relative ldr hits")
        for addr, op in refs[:12]:
            print(f"  {addr:08X}: {op}")

    print("\n=== bl to BarInitTeamMenuWindow (238D3A0) ===")
    for ins in cs.disasm(ov, load):
        if ins.mnemonic == "bl" and "238d3a0" in ins.op_str.lower():
            disasm_window(ov, load, ins.address, 0x30, 0x8)

    print("\n=== bl to 238C290 region callers (inner ~53?) ===")
    for ins in cs.disasm(ov, load):
        if ins.address == 0x0238C290:
            disasm_window(ov, load, ins.address, 0x40, 0x10)
            break

    # Who branches to C290 block? Search for b/bl to 238C250-238C2A0
    print("\n=== branches into 238C260-238C2A0 ===")
    for ins in cs.disasm(ov, load):
        if ins.mnemonic not in ("b", "bl"):
            continue
        # capstone might show target in op_str
        if "238c2" in ins.op_str.lower():
            print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

    # arm9: search for 0x45DF or menu 1904
    arm9 = bytes(rom.arm9)
    print("\n=== arm9 occurrences of 0x45DF ===")
    needle = struct.pack("<H", 0x45DF)
    off = 0
    while True:
        i = arm9.find(needle, off)
        if i < 0:
            break
        print(f"  arm9+{i:#x} (ram {0x02000000 + i:#010x})")
        off = i + 2

    print("\n=== arm9 occurrences of 1904 (menu str?) ===")
    for needle in (struct.pack("<H", 1904), struct.pack("<I", 1904)):
        off = 0
        while True:
            i = arm9.find(needle, off)
            if i < 0:
                break
            print(f"  arm9+{i:#x} val={struct.unpack_from('<H' if len(needle)==2 else '<I', arm9, i)[0]}")
            off = i + len(needle)


if __name__ == "__main__":
    main()
