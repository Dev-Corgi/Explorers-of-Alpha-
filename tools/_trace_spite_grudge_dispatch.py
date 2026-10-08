#!/usr/bin/env python3
"""Static dispatch trace for Spite/Grudge in US EoS vanilla overlay29."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.waza_p.handler import WazaPHandler
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom

REPO = Path(__file__).resolve().parent.parent
OV29 = 0x022DC240
START_MFUNC = 0x02330134
STRIDE = 0x1C
EXE = 0x0232E864


def bl_target(pc: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def find_branches_to(data: bytes, target: int) -> list[int]:
    hits: list[int] = []
    for off in range(0, len(data) - 4, 4):
        addr = OV29 + off
        word = struct.unpack_from("<I", data, off)[0]
        if word >> 24 not in (0xEA, 0xEB):
            continue
        if bl_target(addr, word) == target:
            hits.append(addr)
    return hits


def main() -> None:
    van_path = REPO / "unpacked/overlay/overlay_0029.bin"
    rom_path = REPO / "Vanilla Rom/Explorers of Alpha_Vanilla.nds"
    van = van_path.read_bytes()
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    rom = NintendoDSRom.fromFile(rom_path)
    alpha_ov = bytes(rom.loadArm9Overlays()[29].data)
    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/waza_cd.bin"))
    wp = WazaPHandler.deserialize(rom.getFileByName("BALANCE/waza_p.bin"))
    strings = FileType.STR.deserialize(rom.getFileByName("MESSAGE/text_e.str"))
    cfg = get_ppmdu_config_for_rom(rom)
    names = strings.strings[
        cfg.string_index_data.string_blocks["Move Names"].begin :
        cfg.string_index_data.string_blocks["Move Names"].end + 1
    ]

    print("=== Move / effect IDs (Alpha vanilla ROM data) ===")
    for mid in (35, 49):
        eid = cd.get_item_effect_id(mid)
        m = wp.moves[mid]
        print(
            f"  Move {mid} ({names[mid]}): effect_id={eid}, "
            f"bp={m.base_power}, pp={m.base_pp}, cat={m.category}"
        )

    sites = {
        "GrudgeHandler": 0x02329664,
        "GrudgeThunkBL": 0x02329668,
        "TryInflictGrudge": 0x023194B8,
        "GrudgeSkipCalc": 0x02319530,
        "GrudgeDurationAdd": 0x02319534,
        "SpiteEffectFn": 0x0232A340,
        "SpiteCallPrimary": 0x0232A3C4,
        "SpiteCallAlt": 0x0232A804,
        "SpiteMessageHelper": 0x0232A834,
        "SpiteDrainBL": 0x0232A8E0,
    }
    print("\n=== Alpha vs unpacked overlay29 (patch sites) ===")
    for name, addr in sites.items():
        off = addr - OV29
        v = struct.unpack_from("<I", van, off)[0]
        a = struct.unpack_from("<I", alpha_ov, off)[0]
        print(f"  {name} {addr:#x}: van={v:#010x} alpha={a:#010x} {'SAME' if v == a else 'DIFF'}")

    print("\n=== Direct branch xrefs ===")
    for label, addr in [
        ("TryInflictGrudgeStatus", 0x023194B8),
        ("GrudgeHandler", 0x02329664),
        ("SpiteEffectFn", 0x0232A340),
        ("SpiteMessageHelper", 0x0232A834),
        ("DrainAllMovePp", 0x02345AD8),
        ("StartMFunc", START_MFUNC),
    ]:
        refs = find_branches_to(van, addr)
        print(f"  {label} {addr:#x}: {len(refs)} refs -> {[hex(r) for r in refs[:8]]}")

    print("\n=== waza_cd effect stubs (28-byte ARM templates) ===")
    for eid in (192, 216):
        code = bytes(cd.get_effect_code(eid))
        bl_addr = START_MFUNC + eid * STRIDE + 0x10
        bl_word = struct.unpack_from("<I", code, 0x10)[0]
        unpatched = bl_target(bl_addr, bl_word)
        print(f"  effect {eid}: BL slot @ {bl_addr:#x}, unpatched target {unpatched:#x}")

    print("\n=== StartMFunc repack tail (branches into effect RAM) ===")
    for ins in cs.disasm(van[0x232F850 - OV29 : 0x232FA00 - OV29], 0x232F850):
        mark = ""
        if ins.mnemonic in ("bl", "b") and ins.op_str.startswith("#"):
            w = struct.unpack_from("<I", van, ins.address - OV29)[0]
            t = bl_target(ins.address, w)
            if t == START_MFUNC:
                mark = "  << enters StartMFunc"
        print(f"  {ins.address:#x}: {ins.mnemonic} {ins.op_str}{mark}")

    print("\n=== Spite inner chain (0x232A340 -> helper -> drain) ===")
    chain = [0x0232A340, 0x0232A834, 0x02345AD8]
    for addr in chain:
        off = addr - OV29
        for ins in cs.disasm(van[off : off + 0x60], addr):
            line = f"  {ins.address:#x}: {ins.mnemonic} {ins.op_str}"
            if ins.mnemonic == "bl":
                w = struct.unpack_from("<I", van, ins.address - OV29)[0]
                line += f"  -> {bl_target(ins.address, w):#x}"
            print(line)
            if ins.mnemonic in ("bx", "pop") and "pc" in ins.op_str and ins.address > addr + 4:
                break

    print("\n=== Grudge inner chain (handler -> TryInflict -> CalcStatus -> D6) ===")
    for addr in (0x02329664, 0x023194B8):
        off = addr - OV29
        for ins in cs.disasm(van[off : off + 0xA0], addr):
            line = f"  {ins.address:#x}: {ins.mnemonic} {ins.op_str}"
            if ins.mnemonic == "bl":
                w = struct.unpack_from("<I", van, ins.address - OV29)[0]
                line += f"  -> {bl_target(ins.address, w):#x}"
            print(line)
            if addr == 0x023194B8 and ins.address >= 0x02319540:
                break
            if addr == 0x02329664 and ins.mnemonic == "pop" and "pc" in ins.op_str:
                break


if __name__ == "__main__":
    main()
