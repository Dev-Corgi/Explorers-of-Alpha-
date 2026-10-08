#!/usr/bin/env python3
"""Trace ground menu -> team -> summary page 1 call chain."""
from __future__ import annotations

import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.data.str.handler import StrHandler

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent

TARGETS: dict[int, str] = {
    0x0205AE28: "CreateMonsterSummaryFromTeamMember",
    0x0203CFCC: "PrintSummaryStats",
    0x02027B58: "GetAdvancedTextBoxFromWindow",
    0x0206096C: "Render206096C",
    0x02060FD8: "Render2060FD8",
    0x02061CC8: "Render2061CC8",
    0x020611DC: "Call2060EB4_site",
    0x02060EB4: "Render2060EB4",
    0x02300D88: "CreateTopGroundMenu",
    0x02300F50: "UpdateTopGroundMenu",
}


def bl_callers(data: bytes, base: int, cs: Cs) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for ins in cs.disasm(data, base):
        if ins.mnemonic != "bl" or not ins.op_str.startswith("#"):
            continue
        t = int(ins.op_str[1:], 16)
        if t in TARGETS:
            out.append((ins.address, t, TARGETS[t]))
    return out


def pool_refs(data: bytes, base: int, target: int) -> list[int]:
    refs: list[int] = []
    for o in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, o)[0]
        if w == target or w == (target | 1):
            refs.append(base + o)
    return refs


def disasm_window(data: bytes, load: int, addr: int, size: int = 0x120) -> None:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    off = addr - load
    print(f"\n=== {addr:#010x} ===")
    for ins in cs.disasm(data[off : off + size], addr):
        print(f"  {ins.address:08X} {ins.mnemonic:8} {ins.op_str}")


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROOT / "Explorers of Alpha_berryboost.nds"))
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    config = get_ppmdu_config_for_rom(rom)
    strings = StrHandler.deserialize(
        rom.getFileByName("MESSAGE/text_e.str"), string_encoding=config.string_encoding
    )

    print("=== bl callers to key symbols ===")
    hits = bl_callers(rom.arm9, 0x02000000, cs)
    for entry in table:
        if not hasattr(entry, "fileID"):
            continue
        hits.extend(bl_callers(bytes(rom.files[entry.fileID]), entry.ramAddress, cs))
    for addr, _t, name in sorted(hits, key=lambda x: x[0]):
        print(f"  {addr:#010x}  bl  {name}")

    print("\n=== pool refs to Render2060FD8 / PrintSummaryStats ===")
    for label, tgt in [( "2060FD8", 0x02060FD8), ("PrintSummaryStats", 0x0203CFCC)]:
        refs: list[str] = []
        refs += [f"arm9 {a:#x}" for a in pool_refs(rom.arm9, 0x02000000, tgt)]
        for entry in table:
            if not hasattr(entry, "fileID"):
                continue
            refs += [
                f"ov@{entry.ramAddress:#x} {a:#x}"
                for a in pool_refs(bytes(rom.files[entry.fileID]), entry.ramAddress, tgt)
            ]
        print(f"  {label}: {len(refs)}")
        for r in refs[:20]:
            print(f"    {r}")

    # 203CE00 AdvancedTextBox page callbacks
    print("\n=== AdvancedTextBox callbacks @ 203CE00 ===")
    for i in range(8):
        a = 0x0203CE00 + i * 4
        t = struct.unpack_from("<I", rom.arm9, a - 0x02000000)[0]
        name = TARGETS.get(t, "?")
        print(f"  [{i}] {t:#010x}  {name}")

    # UpdateTopGroundMenu: find Team (case) handlers
    ov11 = bytes(rom.files[table[11].fileID])
    load11 = table[11].ramAddress
    disasm_window(ov11, load11, 0x02300F50, 0x400)

    # Search ov11 for bl into arm9 summary region
    print("\n=== ov11 bl into arm9 205A000-2063000 ===")
    for ins in cs.disasm(ov11, load11):
        if ins.mnemonic != "bl":
            continue
        t = int(ins.op_str[1:], 16)
        if 0x0205A000 <= t <= 0x02063000:
            print(f"  {ins.address:#010x} -> {t:#010x}")

    # Who calls CreateMonsterSummary - search with capstone all bl in range
    print("\n=== all bl to 205AE28 (any overlay) ===")
    for ins in cs.disasm(rom.arm9, 0x02000000):
        if ins.mnemonic == "bl" and int(ins.op_str[1:], 16) == 0x0205AE28:
            print(f"  arm9 {ins.address:#010x}")
    for entry in table:
        if not hasattr(entry, "fileID"):
            continue
        for ins in cs.disasm(bytes(rom.files[entry.fileID]), entry.ramAddress):
            if ins.mnemonic == "bl" and int(ins.op_str[1:], 16) == 0x0205AE28:
                print(f"  ov {entry.ramAddress:#010x}+{ins.address - entry.ramAddress:#x} = {ins.address:#010x}")

    # Find FormatString users with string 2511 nearby in same function as 2061820 switch
    print("\n=== functions referencing str 2510 pool 200CA20 ===")
    for ins in cs.disasm(rom.arm9, 0x02000000):
        if ins.mnemonic != "bl" or ins.op_str != "#0x20223f0":
            continue
        addr = ins.address
        off = addr - 0x02000000
        window = rom.arm9[max(0, off - 0x80) : off]
        if any(
            struct.unpack_from("<H", window, o)[0] == 2510
            for o in range(0, len(window) - 1, 2)
        ):
            print(f"  FormatString @ {addr:#010x} (2510 in literal pool)")


if __name__ == "__main__":
    main()
