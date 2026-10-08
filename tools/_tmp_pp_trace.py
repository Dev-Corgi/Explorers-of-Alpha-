"""Trace UpdateMovePp vs ExecuteMoveEffect call order in vanilla Alpha ov29."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom

ROM = Path(r"c:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
LOAD = 0x022DC240
UPDATE_PP = 0x02324D8C
EXE = 0x0232E864
SHOULD = 0x0231A7A0
CAN = 0x02324B24
HOOK1 = 0x02322B50
HOOK2 = 0x023238AC


def bl_target(pc: int, word: int) -> int:
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm |= ~0xFFFFFF
    return (pc + 8 + (imm << 2)) & 0xFFFFFFFF


def find_bls(ov29: bytes, target: int) -> list[int]:
    hits = []
    for off in range(0, len(ov29) - 4, 4):
        w = struct.unpack_from("<I", ov29, off)[0]
        if (w & 0x0F000000) == 0x0B000000:
            pc = LOAD + off
            if bl_target(pc, w) == target:
                hits.append(pc)
    return hits


def disasm_window(ov29: bytes, addr: int, before: int = 0x40, after: int = 0x60, mark: int | None = None):
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    start = addr - before
    off = start - LOAD
    code = bytes(ov29[off : off + before + after])
    for insn in md.disasm(code, start):
        tag = ""
        if mark is not None and insn.address == mark:
            tag = " <<<<"
        print(f"  {insn.address:08X}: {insn.mnemonic} {insn.op_str}{tag}")


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROM))
    ov29 = bytes(rom.files[29])

    for label, tgt in [
        ("UpdateMovePp", UPDATE_PP),
        ("ExecuteMoveEffect", EXE),
        ("ShouldUsePp", SHOULD),
        ("CanMonsterUseMove", CAN),
    ]:
        hits = find_bls(ov29, tgt)
        print(f"BL to {label} ({tgt:#x}): {len(hits)}")
        for h in hits:
            print(f"  {h:#x}")

    print("\n==== Hook1 neighborhood ====")
    disasm_window(ov29, HOOK1, 0x50, 0x40, HOOK1)
    print("\n==== Hook2 neighborhood ====")
    disasm_window(ov29, HOOK2, 0x50, 0x40, HOOK2)

    pp_callers = find_bls(ov29, UPDATE_PP)
    for i, addr in enumerate(pp_callers):
        print(f"\n==== UpdateMovePp caller[{i}] @ {addr:#x} ====")
        disasm_window(ov29, addr, 0x80, 0x40, addr)

    # Walk backward from Hook1 to find function start (push lr)
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for hook_name, hook in [("Hook1", HOOK1), ("Hook2", HOOK2)]:
        print(f"\n==== scan back for fn start near {hook_name} ====")
        for addr in range(hook, hook - 0x800, -4):
            off = addr - LOAD
            w = struct.unpack_from("<I", ov29, off)[0]
            # push with lr: typically 0xE92D4xxx
            if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):
                print(f"  candidate push@ {addr:#x}: {w:08X}")
                # check if UpdateMovePp or ExecuteMoveEffect called between start and hook+0x200
                region_end = hook + 0x200
                for off2 in range(addr - LOAD, min(region_end - LOAD, len(ov29) - 4), 4):
                    w2 = struct.unpack_from("<I", ov29, off2)[0]
                    if (w2 & 0x0F000000) != 0x0B000000:
                        continue
                    pc = LOAD + off2
                    tgt = bl_target(pc, w2)
                    if tgt in (UPDATE_PP, EXE, SHOULD, CAN):
                        name = {
                            UPDATE_PP: "UpdateMovePp",
                            EXE: "ExecuteMoveEffect",
                            SHOULD: "ShouldUsePp",
                            CAN: "CanMonsterUseMove",
                        }[tgt]
                        print(f"    BL {pc:#x} -> {name}")
                break


if __name__ == "__main__":
    main()
