"""Disassemble Alpha difficulty mechanics via 0x0204B678 flag checks."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

ARM9 = Path(r"c:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
OV36 = Path(r"c:\Working\SkyTemple\unpacked\overlay\overlay_0036.bin").read_bytes()
OV29 = Path(r"c:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin").read_bytes()
OUT = Path(r"c:\Working\SkyTemple\tools\_disasm_diff_mech_out.txt")

HELPER = 0x0204B678
LOADS = {
    "arm9": (ARM9, 0x02000000),
    "ov29": (OV29, 0x022DC240),
    "ov36": (OV36, 0x023A7080),
}


def bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def main() -> None:
    lines: list[str] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    # Disassemble helper
    off = HELPER - 0x02000000
    lines.append("=== Helper 0x0204B678 (likely GetPerformanceFlag alt) ===")
    for ins in md.disasm(ARM9[off : off + 0x80], HELPER):
        lines.append(f"  {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")
        if ins.mnemonic == "bx" and "lr" in ins.op_str:
            break

    # Also check if it just wraps GetPerformanceFlagWithChecks
    lines.append("\n=== All bl to 0x0204B678 with r2 imm (55-59) ===")
    for name, (data, load) in LOADS.items():
        for off in range(0, len(data) - 3, 4):
            w = struct.unpack_from("<I", data, off)[0]
            if w >> 24 != 0xEB:
                continue
            if bl_target(load + off, w) != HELPER:
                continue
            # look back for mov r2,#imm
            r2 = None
            r1 = None
            start = max(0, off - 0x30)
            for ins in md.disasm(data[start:off], load + start):
                if ins.mnemonic in ("mov", "movs") and ins.op_str.startswith("r2, #"):
                    try:
                        r2 = int(ins.op_str.split("#")[1], 0)
                    except Exception:
                        r2 = ins.op_str
                if ins.mnemonic in ("mov", "movs") and ins.op_str.startswith("r1, #"):
                    try:
                        r1 = int(ins.op_str.split("#")[1], 0)
                    except Exception:
                        r1 = ins.op_str
            if r2 in (55, 56, 57, 58, 59) or r1 in (55, 56, 57, 58, 59):
                lines.append(
                    f"  {name} 0x{load + off:08X}  r1={r1} r2={r2}"
                )

    # Full disasm of key clusters in ov36 that check multiple difficulty flags
    clusters = [
        (0x023ACCE0, 0x100, "Difficulty decode / return enum?"),
        (0x023D9100, 0x200, "Level scaling spawn / party max area"),
        (0x023BF140, 0x100, "BF168 difficulty checks"),
        (0x023BF260, 0x80, "BF280 difficulty checks"),
        (0x023BFB90, 0x100, "BFBA8 difficulty checks"),
        (0x023B5FA0, 0x80, "B5FBC difficulty checks"),
        (0x023B0490, 0x80, "B04B4 difficulty checks"),
        (0x023D5A50, 0x80, "D5A70 difficulty checks"),
        (0x023DA400, 0x50, "DA41C vanilla check + maybe damage"),
        (0x023DA9F0, 0x50, "DAA0C vanilla check"),
        (0x023DBC90, 0x50, "DBCA8 vanilla check"),
        (0x023DC050, 0x80, "DC074 vanilla check"),
        (0x023A9A20, 0x40, "A9A38 flag 55?"),
    ]
    for addr, size, title in clusters:
        off = addr - 0x023A7080
        lines.append(f"\n===== {title} @ 0x{addr:08X} =====")
        for ins in md.disasm(OV36[off : off + size], addr):
            lines.append(f"  {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")

    # Search ALL helpers that take r2=#56-59 pattern across ov36 and dump unique call sites with aftermath
    lines.append("\n===== Aftermath of every r2=#56-59; bl HELPER in ov36 =====")
    data, load = OV36, 0x023A7080
    seen = set()
    for off in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if w >> 24 != 0xEB:
            continue
        if bl_target(load + off, w) != HELPER:
            continue
        # find r2
        r2 = None
        r1 = None
        start = max(0, off - 0x20)
        for ins in md.disasm(data[start:off], load + start):
            if ins.mnemonic in ("mov", "movs") and ins.op_str.startswith("r2, #"):
                try:
                    r2 = int(ins.op_str.split("#")[1], 0)
                except Exception:
                    pass
            if ins.mnemonic in ("mov", "movs") and ins.op_str.startswith("r1, #"):
                try:
                    r1 = int(ins.op_str.split("#")[1], 0)
                except Exception:
                    pass
        if r2 not in (55, 56, 57, 58, 59):
            continue
        # dump from a bit before through 0x60 after, but group by function start-ish
        func = off & ~0xFF
        key = (func, r2)
        if key in seen:
            continue
        seen.add(key)
        dump_start = max(0, off - 0x10)
        dump_end = min(len(data), off + 0x60)
        lines.append(f"\n--- {load + off:08X} r1={r1} r2={r2} ---")
        for ins in md.disasm(data[dump_start:dump_end], load + dump_start):
            lines.append(f"  {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
