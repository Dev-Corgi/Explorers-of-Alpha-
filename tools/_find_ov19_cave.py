#!/usr/bin/env python3
"""Find safest overlay19 cave for 0x40-byte menu table."""
from __future__ import annotations

import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
NEED = 0x40
POST_MARGIN = 0x10  # zero bytes after table
AVOID_END = 0x80    # skip zeros adjacent to E300 rodata tail


def pc_ldr_targets(data: bytes, load: int) -> set[int]:
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    out: set[int] = set()
    for ins in cs.disasm(data, load):
        if ins.mnemonic != "ldr" or "[pc" not in ins.op_str or "#" not in ins.op_str:
            continue
        imm_part = ins.op_str.split("#")[1].split("]")[0].strip()
        try:
            imm = int(imm_part, 0)
        except ValueError:
            continue
        pc = (ins.address + 8) & ~3
        out.add((pc + imm) & 0xFFFFFFFF)
    return out


def word_xrefs(data: bytes, addr: int) -> list[int]:
    needle = struct.pack("<I", addr)
    hits: list[int] = []
    off = 0
    while True:
        i = data.find(needle, off)
        if i < 0:
            break
        hits.append(i)
        off = i + 4
    return hits


def main() -> None:
    rom = NintendoDSRom.fromFile(str(ROOT / "Explorers of Alpha_berryboost.nds"))
    t = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")[19]
    ov = bytearray(rom.files[t.fileID])
    load = t.ramAddress
    end = load + t.ramSize
    pc = pc_ldr_targets(bytes(ov), load)
    ram_end = load + len(ov)

    total_need = NEED + POST_MARGIN
    candidates: list[tuple[int, int, int, str]] = []

    off = 0
    while off + total_need <= len(ov):
        chunk = ov[off : off + total_need]
        if chunk != b"\x00" * total_need:
            off += 4
            continue
        run_end = off + total_need
        while run_end < len(ov) and ov[run_end] == 0:
            run_end += 1
        addr = load + off
        size = run_end - off
        wx = word_xrefs(ov, addr)
        pool = addr in pc
        near_rodata = addr >= ram_end - AVOID_END
        if not wx and not pool:
            note = []
            if near_rodata:
                note.append("near-rodata-tail")
            if addr + NEED == end:
                note.append("flush-file-end")
            candidates.append((addr, size, off, ",".join(note) or "ok"))
        off = run_end

    print(f"overlay19 {load:#010x}..{end:#010x} file={len(ov):#x}")
    print(f"candidates (>= {total_need:#x} zeros, no xref, +{POST_MARGIN:#x} post margin):\n")
    for addr, size, off, note in sorted(candidates, key=lambda x: (x[3] != "ok", x[0])):
        print(f"  {addr:#010x}  run={size:#x}  file+{off:#x}  [{note}]")

    # append option
    append_addr = load + len(ov)
    print(f"\nappend option: {append_addr:#010x} (extend file+ramSize +{NEED:#x}, pristine)")


if __name__ == "__main__":
    main()
