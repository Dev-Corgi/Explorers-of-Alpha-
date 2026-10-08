"""Catalog every ov36 difficulty check site and extract mechanical effects."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

OV36 = Path(r"c:\Working\SkyTemple\unpacked\overlay\overlay_0036.bin").read_bytes()
ARM9 = Path(r"c:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
LOAD = 0x023A7080
HELPER = 0x0204B678
OUT = Path(r"c:\Working\SkyTemple\tools\_disasm_diff_all_out.txt")

FLAG_NAMES = {
    55: "LevelScaling",
    56: "Vanilla",
    57: "Difficult",
    58: "Expert",
    59: "Hardcore",
}


def bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def main() -> None:
    lines: list[str] = []
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    # Identify GetDifficulty-like function callers: bl to 0x023ACCF8
    GET_DIFF = 0x023ACCF8
    lines.append("=== Callers of GetDifficulty (0x023ACCF8) ===")
    for off in range(0, len(OV36) - 3, 4):
        w = struct.unpack_from("<I", OV36, off)[0]
        if w >> 24 != 0xEB:
            continue
        if bl_target(LOAD + off, w) == GET_DIFF:
            lines.append(f"  0x{LOAD + off:08X}")
            # dump aftermath
            for ins in md.disasm(OV36[off : off + 0x60], LOAD + off):
                lines.append(f"    {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")

    # Also arm9/ov29 callers
    for name, data, load in (
        ("arm9", ARM9, 0x02000000),
        ("ov29", Path(r"c:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin").read_bytes(), 0x022DC240),
    ):
        for off in range(0, len(data) - 3, 4):
            w = struct.unpack_from("<I", data, off)[0]
            if w >> 24 != 0xEB:
                continue
            if bl_target(load + off, w) == GET_DIFF:
                lines.append(f"  {name} 0x{load + off:08X}")
                for ins in md.disasm(data[off : off + 0x60], load + off):
                    lines.append(f"    {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")

    # Disasm 0x208fea4 (used in Vanilla LS level formula)
    lines.append("\n=== 0x0208FEA4 (Vanilla LS math helper) ===")
    off = 0x0208FEA4 - 0x02000000
    for ins in md.disasm(ARM9[off : off + 0x40], 0x0208FEA4):
        lines.append(f"  {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")
        if ins.mnemonic.startswith("bx") or (ins.mnemonic == "pop" and "pc" in ins.op_str):
            break

    # Dump larger regions for every unique function that checks difficulty flags
    # Find all sites with r1=0x4e, r2 in 56-59
    sites = []
    for off in range(0, len(OV36) - 3, 4):
        w = struct.unpack_from("<I", OV36, off)[0]
        if w >> 24 != 0xEB:
            continue
        if bl_target(LOAD + off, w) != HELPER:
            continue
        r2 = None
        r1 = None
        start = max(0, off - 0x20)
        for ins in md.disasm(OV36[start:off], LOAD + start):
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
        if r1 == 0x4E and r2 in FLAG_NAMES:
            sites.append((off, r2))

    lines.append(f"\n=== All PERF list flag checks via LoadScriptVariableValueAtIndex: {len(sites)} ===")
    for off, r2 in sites:
        lines.append(f"  0x{LOAD + off:08X}  {FLAG_NAMES[r2]} ({r2})")

    # Group into clusters (gap > 0x200 = new cluster), dump each cluster fully
    sites_sorted = sorted(sites)
    clusters: list[list[tuple[int, int]]] = []
    cur: list[tuple[int, int]] = []
    for off, r2 in sites_sorted:
        if not cur or off - cur[-1][0] <= 0x200:
            cur.append((off, r2))
        else:
            clusters.append(cur)
            cur = [(off, r2)]
    if cur:
        clusters.append(cur)

    lines.append(f"\n=== {len(clusters)} clusters ===")
    for ci, cl in enumerate(clusters):
        start = max(0, cl[0][0] - 0x40)
        end = min(len(OV36), cl[-1][0] + 0xC0)
        flags = ",".join(FLAG_NAMES[r] for _, r in cl)
        lines.append(
            f"\n######## CLUSTER {ci} flags=[{flags}] "
            f"0x{LOAD + start:08X}-0x{LOAD + end:08X} ########"
        )
        for ins in md.disasm(OV36[start:end], LOAD + start):
            lines.append(f"  {ins.address:08X}  {ins.mnemonic:8} {ins.op_str}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(lines)} lines), clusters={len(clusters)}")


if __name__ == "__main__":
    main()
