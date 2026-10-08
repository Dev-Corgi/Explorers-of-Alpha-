#!/usr/bin/env python3
"""Investigate orb_charges crash causes in patched ROM."""

from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost.nds"
)
PATCHED = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbcharges.nds"
)

A9 = 0x02000000
OV29 = 0x022DC240
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def branch_dest(word: int, pc: int) -> int | None:
    top = (word >> 24) & 0xFF
    if top not in (0xEA, 0xEB):
        return None
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return pc + 8 + imm * 4


def hook_info(data: bytes, addr: int, load: int) -> str:
    off = addr - load
    w = struct.unpack_from("<I", data, off)[0]
    top = (w >> 24) & 0xFF
    dest = branch_dest(w, addr)
    if top == 0xEA and dest:
        return f"b -> {dest:#010x}"
    if top == 0xEB and dest:
        return f"bl -> {dest:#010x}"
    return f"word={w:08X}"


def disasm(data: bytes, start: int, size: int, base: int) -> list[str]:
    off = start - base
    return [
        f"  {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}"
        for ins in cs.disasm(data[off : off + size], start)
    ]


def cave_bounds(data: bytes, cave: int, load: int, max_scan: int = 0x800) -> tuple[int, int]:
    off = cave - load
    end = off
    while end < min(len(data), off + max_scan):
        chunk = data[end : end + 4]
        if len(chunk) < 4:
            break
        if chunk == b"\x00" * 4:
            break
        end += 4
    return cave, cave + (end - off)


def find_callers(data: bytes, target: int, load: int, limit: int = 30) -> list[int]:
    hits: list[int] = []
    for off in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if (w >> 24) != 0xEB:
            continue
        pc = load + off
        dest = branch_dest(w, pc)
        if dest == target:
            hits.append(pc)
            if len(hits) >= limit:
                break
    return hits


def main() -> None:
    base_rom = NintendoDSRom(BASE.read_bytes())
    patch_rom = NintendoDSRom(PATCHED.read_bytes())
    arm9 = bytes(patch_rom.arm9)
    base_arm9 = bytes(base_rom.arm9)
    table = loadOverlayTable(patch_rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = bytes(patch_rom.files[table[29].fileID])
    base_ov29 = bytes(base_rom.files[table[29].fileID])

    print("=" * 72)
    print("1. ARM9 HOOK SITES")
    print("=" * 72)
    arm9_hooks = {
        "BuildItemNameDefaultPath": 0x0200D4D8,
        "RemoveEquivNoHole": 0x0200F600,
        "RemoveEquivVariant": 0x0200F694,
        "RemoveEquivScan": 0x0200F558,
    }
    for name, addr in arm9_hooks.items():
        print(f"  {name} @{addr:08X}: {hook_info(arm9, addr, A9)}")

    cave = 0x0209F904
    c0, c1 = cave_bounds(arm9, cave, A9)
    print(f"\n  Cave @{cave:08X} .. {c1:08X} ({c1 - c0} bytes)")
    print(f"  Pre-patch at cave: {base_arm9[cave - A9 : cave - A9 + 32].hex()}")
    print(f"  Post-patch at cave: {arm9[cave - A9 : cave - A9 + 32].hex()}")

    # What was overwritten?
    pre = base_arm9[cave - A9 : c1 - A9]
    if any(pre):
        print("  WARNING: cave overwrote non-zero base data:")
        for ins in cs.disasm(pre[: min(64, len(pre))], cave):
            print(f"    was: {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

    print("\n" + "=" * 72)
    print("2. BuildItemName HOOK + REGISTER CONTEXT")
    print("=" * 72)
    for line in disasm(arm9, 0x0200D460, 0x120, A9):
        print(line)

    print("\n  BuildItemNameCat9Hook disasm:")
    hook_dest = branch_dest(struct.unpack_from("<I", arm9, 0x0200D4D8 - A9)[0], 0x0200D4D8)
    if hook_dest:
        for line in disasm(arm9, hook_dest, 0x80, A9):
            print(line)

    print("\n  BuildItemName callers (first 15):")
    for addr in find_callers(arm9, 0x0200D310, A9)[:15]:
        print(f"    bl BuildItemName @{addr:08X}")

    print("\n" + "=" * 72)
    print("3. FORMAT STRING ADDRESSES")
    print("=" * 72)
    for label, addr in [
        ("CountFmtColored", 0x02097F34),
        ("CountFmtPlain", 0x02097F50),
        ("PlainFmtColored", 0x02097F58),
    ]:
        off = addr - A9
        raw = arm9[off : off + 16]
        nul = raw.find(b"\x00")
        s = raw[: nul if nul >= 0 else len(raw)].decode("ascii", errors="replace")
        print(f"  {label} @{addr:08X}: {s!r}")

    print("\n" + "=" * 72)
    print("4. adr RANGE CHECK (OrbChargeLookup)")
    print("=" * 72)
    # adr r12, label is PC-relative ±4KB on ARM9
    lookup_off = None
    for off in range(cave - A9, c1 - A9 - 4, 4):
        w = struct.unpack_from("<I", arm9, off)[0]
        # adr rd, #imm: cond 1110, op 0b00, bits indicate adr
        if (w & 0x0FFF0000) == 0x028F0000:  # rough - check disasm instead
            pass
    hook_dest = cave + 0x20  # approximate
    for ins in cs.disasm(arm9[cave - A9 : c1 - A9], cave):
        if ins.mnemonic == "adr" and "r12" in ins.op_str:
            print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
        if "OrbChargeTable" in ins.op_str:
            print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

    table_addr = cave + 0x1C  # after lookup prologue - verify from asm
    # table starts right after .org cave + includes
    # From file: .include table right after .org - lookup is before table in asm
    # Actually order: .org cave, .include table, then OrbChargeLookup code
    # Wait - read arm9 asm again:
    # .org OrbChargesArm9CodeAddress
    # .include generated/orb_charge_table_arm9.asm  <- TABLE FIRST
    # OrbChargeLookup: <- code after table
    table_start = cave  # table is at start of cave
    lookup_start = cave + 52 * 4  # 52 entries * 4 bytes
    print(f"  Table @{table_start:08X}, Lookup ~@{lookup_start:08X}")
    for ins in cs.disasm(arm9[lookup_start - A9 : lookup_start - A9 + 0x40], lookup_start):
        if ins.mnemonic == "adr":
            print(f"  {ins.address:08X}: {ins.mnemonic} {ins.op_str}")
            # adr encoding: offset = ((w & 0xFF) | ((w >> 8) & 0xF) << 8) << 2
            off_in = lookup_start - A9 + (ins.address - lookup_start)
            w = struct.unpack_from("<I", arm9, off_in)[0]
            imm = (w & 0xFF) | ((w >> 8) & 0xF00)
            if imm & 0x800:
                imm -= 0x1000
            target = ins.address + 8 + imm
            print(f"    -> targets {target:#010x} (table at {table_start:#010x}, delta {target - table_start})")

    print("\n" + "=" * 72)
    print("5. RemoveEquiv HOOKS -> ARM9 RemoveEquiv in ov29?")
    print("=" * 72)
    for name, addr in [
        ("RemoveEquivNoHole", 0x0200F600),
        ("RemoveEquivVariant", 0x0200F694),
        ("RemoveEquivScan", 0x0200F558),
    ]:
        callers = find_callers(ov29, addr, OV29, 10)
        print(f"  {name}: {len(callers)} ov29 callers (sample {[hex(x) for x in callers[:5]]})")

    print("\n" + "=" * 72)
    print("6. OV29 CAVE + SIZE")
    print("=" * 72)
    cave29 = 0x023304EC
    c0, c1 = cave_bounds(ov29, cave29, OV29, 0x1000)
    print(f"  Cave @{cave29:08X} .. {c1:08X} ({c1 - c0} bytes)")
    print(f"  Pre-patch: {base_ov29[cave29 - OV29 : cave29 - OV29 + 32].hex()}")
    pre = base_ov29[cave29 - OV29 : c1 - OV29]
    if any(pre):
        print("  WARNING: overwrote non-zero ov29 data at cave:")
        for ins in cs.disasm(pre[: min(128, len(pre))], cave29):
            print(f"    was: {ins.address:08X}: {ins.mnemonic} {ins.op_str}")

    print("\n" + "=" * 72)
    print("7. PATHS THAT RUN ON ORB PICKUP / STORAGE UI")
    print("=" * 72)
    pickup_related = [
        ("BuildItemName", 0x0200D310),
        ("ConvertStorageItemAtIdxToItem", 0x0200FFF4),
        ("AddItemToBag", 0x02010260),
        ("GenerateStandardItem", 0x02050300),
        ("InitItem", 0x0200CE9C),
        ("SetItemAcquired", 0x02050300),
        ("GetItemName", 0x0200D088),
        ("GetItemNameFormatted", 0x0200D0D0),
    ]
    hooked = {0x0200D4D8, 0x0200F600, 0x0200F694, 0x0200F558}
    for name, addr in pickup_related:
        patched = addr in hooked or any(
            branch_dest(struct.unpack_from("<I", arm9, h - A9)[0], h) == addr
            for h in hooked
            if h - A9 < len(arm9)
        )
        in_arm9_callers = len(find_callers(arm9, addr, A9, 3))
        in_ov29_callers = len(find_callers(ov29, addr, OV29, 3))
        hook_mark = " [HOOKED/FLOW]" if addr == 0x0200D310 or addr == 0x0200D4D8 else ""
        print(
            f"  {name} @{addr:08X}: arm9 callers~{in_arm9_callers}+ ov29 callers~{in_ov29_callers}{hook_mark}"
        )

    print("\n" + "=" * 72)
    print("8. BuildItemNameCat9Hook: r9 validity concern")
    print("=" * 72)
    print("  Hook uses r9 as struct item* for GetOrbRemainingUsesCat9.")
    print("  Scanning BuildItemName for ldr/str r9 before D4D8:")
    for ins in cs.disasm(arm9[0x0200D310 - A9 : 0x0200D4D8 - A9 + 4], 0x0200D310):
        if "r9" in ins.op_str:
            print(f"    {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")

    print("\n" + "=" * 72)
    print("9. r4==0 storage path vs r4!=0 bag path at D4D8")
    print("=" * 72)
    for ins in cs.disasm(arm9[0x0200D400 - A9 : 0x0200D4E0 - A9], 0x0200D400):
        if ins.mnemonic in ("mov", "cmp", "ldrh", "ldr") and any(
            r in ins.op_str for r in ("r4", "r6", "r7", "r9")
        ):
            print(f"    {ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
