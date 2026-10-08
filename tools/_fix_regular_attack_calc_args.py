#!/usr/bin/env python3
"""Fix regular-attack CalcDamage: r3=power, [sp,#8]=0x100 (1.0), exclude-tech flag set."""

from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom
from skytemple_files.data.data_cd.handler import DataCDHandler

ROOT = Path(__file__).resolve().parents[1]
ROM_PATH = ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack_no_loader.nds"
BASE = 0x02330134


def patch_code(code: bytearray) -> bytearray:
    # --- default power #20 (moveq r0, #0x14) ---
    for off in range(0, len(code) - 4, 4):
        w = struct.unpack_from("<I", code, off)[0]
        if (w & 0x0FFFFFFF) == 0x03A00018:  # moveq r0, #24
            struct.pack_into("<I", code, off, (w & 0xF0000000) | 0x03A00014)

    # --- fix 2nd ability load: ldrb r2,[r1,#1] (was wrongly [r1] again) ---
    # Pattern: ldrb r2,[r1]; cmp #0x8b; lsreq; ldrb r2,[r1]; cmp #0x8b
    for off in range(0, len(code) - 20, 4):
        w0 = struct.unpack_from("<I", code, off)[0]
        w1 = struct.unpack_from("<I", code, off + 4)[0]
        w3 = struct.unpack_from("<I", code, off + 12)[0]
        if w0 == 0xE5D12000 and w1 == 0xE352008B and w3 == 0xE5D12000:
            struct.pack_into("<I", code, off + 12, 0xE5D12001)  # ldrb r2, [r1, #1]
            break

    # --- CalcDamage arg block ---
    # Find mov r3,r0 / mov r1,#0x100 (post partial patch) or legacy str r0,[sp,#8]
    idx = None
    for off in range(0, len(code) - 8, 4):
        w0 = struct.unpack_from("<I", code, off)[0]
        w1 = struct.unpack_from("<I", code, off + 4)[0]
        if w0 == 0xE1A03000 and w1 in (0xE3A01C01, 0xE3A01080, 0xE3A01040):
            idx = off
            break
        if w0 == 0xE58D0008 and w1 == 0xE3A02000:
            idx = off
            break
    if idx is None:
        raise RuntimeError("CalcDamage arg site not found")

    orig_ldrh = 0xE1D8A0B4
    for off in range(idx, min(idx + 0x28, len(code)), 4):
        w = struct.unpack_from("<I", code, off)[0]
        if w == 0xE1D8A0B4:
            orig_ldrh = w
            break

    # 7 words — fits exactly through existing str [sp,#0x10].
    # Effect 1 calls CalcDamage directly; RA multiplier is tunable here (F8.8).
    # 0.25 = 0x40. stack[4] (full_calc) must be nonzero; reuse r1 after storing mult.
    new_words = [
        0xE1A03000,  # mov r3, r0          ; power (same P as other moves)
        0xE3A01040,  # mov r1, #0x40       ; 0.25 in F8.8
        0xE58D1008,  # str r1, [sp, #8]    ; damage multiplier
        0xE3A02000,  # mov r2, #0          ; typeless
        orig_ldrh,  # ldrh sl, [r8, #4]   ; move id
        0xE58DA00C,  # str sl, [sp, #0xc]
        0xE58D1010,  # str r1, [sp, #0x10] ; full_calc (nonzero)
    ]
    for i, w in enumerate(new_words):
        struct.pack_into("<I", code, idx + i * 4, w)

    after = idx + len(new_words) * 4
    # Expect: mov r0, sb; mov r1, r4; bl
    if struct.unpack_from("<I", code, after)[0] != 0xE1A00009:
        raise RuntimeError("expected mov r0, sb after arg block")
    if struct.unpack_from("<I", code, after + 4)[0] != 0xE1A01004:
        raise RuntimeError("expected mov r1, r4")
    bl = struct.unpack_from("<I", code, after + 8)[0]
    if (bl & 0x0F000000) != 0x0B000000:
        raise RuntimeError(f"expected bl, got {bl:08X}")

    return code


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROM_PATH))
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    code = patch_code(bytearray(
        DataCDHandler.deserialize(rom.getFileByName("BALANCE/waza_cd.bin")).get_effect_code(1)
    ))

    print("=== effect 1 (power path + CalcDamage args) ===")
    for i in md.disasm(bytes(code), BASE):
        if 0x02330170 <= i.address <= 0x02330218:
            print(f"0x{i.address:08X}: {i.mnemonic}\t{i.op_str}")

    for path in ("BALANCE/waza_cd.bin", "UTILITY/waza_cd.bin"):
        cd = DataCDHandler.deserialize(rom.getFileByName(path))
        cd.set_effect_code(1, bytes(code))
        rom.setFileByName(path, DataCDHandler.serialize(cd))
        print("wrote", path)

    ROM_PATH.write_bytes(rom.save())
    (ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds").write_bytes(ROM_PATH.read_bytes())
    print("synced")


if __name__ == "__main__":
    main()
