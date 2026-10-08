#!/usr/bin/env python3
"""Diagnose freeze-like VFX / room_charge ov36 remnants."""
from __future__ import annotations

import json
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parents[1]
OV29 = 0x022DC240
OV36 = 0x023A7080
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def load(name: str) -> NintendoDSRom:
    return NintendoDSRom.fromFile(str(ROOT / name))


def disasm(data: bytes, addr: int, n: int = 32) -> None:
    for ins in cs.disasm(data[: n * 4], addr):
        print(f"  {ins.address:08x}: {ins.mnemonic} {ins.op_str}")


def main() -> None:
    vanilla = load("Vanilla Rom/Explorers of Alpha_Vanilla.nds")
    no_rc = load("Export Rom/_full_stack_no_rc_zm.nds")
    ov36rom = load("Export Rom/_full_stack_ov36.nds")
    st_no = json.loads((ROOT / "Export Rom/_full_stack_no_rc_zm.state.json").read_text())
    st_36 = json.loads((ROOT / "Export Rom/_full_stack_ov36.state.json").read_text())

    for label, st in [("no_rc", st_no), ("ov36", st_36)]:
        print(f"=== {label} modules ===")
        for m in st["applied"]:
            caves = m.get("caves") or []
            for c in caves:
                print(
                    f"  {m['id']}: {c.get('overlay')} "
                    f"file={c.get('file_offset_hex')} size={c['size']} "
                    f"load={c.get('load_address_hex')}"
                )

    loader = next(m for m in st_no["applied"] if m["id"] == "overlay36_loader")
    cave = loader["caves"][0]
    off, addr = cave["file_offset"], cave["load_address"]
    print("=== no_rc overlay36_loader cave ===")
    print("data:", loader.get("data"))
    disasm(no_rc.files[29][off : off + 96], addr)

    # Prior target should be ExecuteMoveEffect 0x0232E864
    prior = None
    if loader.get("data"):
        prior = loader["data"][0].get("PriorExecuteMoveEffectTarget")
    print("stored prior", prior)

    # Scan ov36 ROM for room_charge TWO_TURN table remnant pattern
    # Vanilla solar-beam style: 151,2 then room moves with status 3
    pattern = struct.pack("<HH", 151, 2) + struct.pack("<HH", 100, 3)
    for label, rom in [("no_rc", no_rc), ("ov36", ov36rom), ("vanilla", vanilla)]:
        for oi, name in [(29, "ov29"), (36, "ov36")]:
            data = rom.files[oi]
            idx = data.find(pattern)
            print(f"{label} {name} two_turn-ish pattern:", hex(idx) if idx >= 0 else None)

    # Check IsChargingTwoTurnMove pool + sample table
    pool_off = 0x02324618 - OV29
    for label, rom in [("vanilla", vanilla), ("no_rc", no_rc), ("ov36", ov36rom)]:
        pool = struct.unpack_from("<I", rom.files[29], pool_off)[0]
        print(f"{label} TWO_TURN pool -> {pool:#010x}")
        if OV29 <= pool < OV29 + len(rom.files[29]):
            toff = pool - OV29
            print("  first entries:", [struct.unpack_from("<HH", rom.files[29], toff + i * 4) for i in range(8)])

    # iq_change frozen hook target in ov36 — is it valid code?
    frozen_site = 0x02312DCC
    for label, rom in [("no_rc", no_rc), ("ov36", ov36rom)]:
        w = struct.unpack_from("<I", rom.files[29], frozen_site - OV29)[0]
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        tgt = frozen_site + 8 + imm * 4
        print(f"{label} FrozenSuccess BL -> {tgt:#010x}")
        if tgt >= OV36:
            foff = tgt - OV36
            print("  ov36 code:")
            disasm(rom.files[36][foff : foff + 48], tgt)

    # Diff ov36 file: any leftover room_charge handler signature (push + IsCharging)
    # RoomChargeV4 starts with push {r3-r8,lr} then sub sp,#4
    sig = bytes.fromhex("f8412de904d04de2")
    for label, rom in [("no_rc", no_rc), ("ov36", ov36rom), ("vanilla", vanilla)]:
        idx = rom.files[36].find(sig)
        print(f"{label} room_charge handler sig in ov36:", hex(idx) if idx >= 0 else None)

    # Berry boost / item stubs — Aspear is freeze cure; check if item_cd effects point into ov36
    from skytemple_files.data.data_cd.handler import DataCDHandler

    for label, rom in [("vanilla", vanilla), ("no_rc", no_rc)]:
        cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/item_cd.bin"))
        # Aspear typically effect related to freeze - print effect ids for berries
        # Cheri/Pecha/Rawst/Chesto/Aspear item ids in EoS: 109-113-ish; check state
        print(f"{label} item_cd effects count", cd.nb_effects())

    # Dump berry_boost effect stubs from no_rc state
    berry = next(m for m in st_no["applied"] if m["id"] == "berry_boost")
    print("berry_boost data", berry.get("data"))

    # Check if ExecuteMoveEffect gate Prior is wrong on no_rc
    # Gate at 0x235141c from earlier output
    gate = 0x235141C
    print("=== gate region ===")
    disasm(no_rc.files[29][gate - OV29 : gate - OV29 + 64], gate)


if __name__ == "__main__":
    main()
