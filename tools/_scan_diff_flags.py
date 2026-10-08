"""Scan arm9/ov29/ov36 for GetPerformanceFlagWithChecks(55-59) and related."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

LOADS = {
    "arm9": (Path(r"c:\Working\SkyTemple\unpacked\arm9.bin"), 0x02000000),
    "ov29": (Path(r"c:\Working\SkyTemple\unpacked\overlay\overlay_0029.bin"), 0x022DC240),
    "ov36": (Path(r"c:\Working\SkyTemple\unpacked\overlay\overlay_0036.bin"), 0x023A7080),
}
PERF = 0x0204CA94
OUT = Path(r"c:\Working\SkyTemple\tools\_scan_diff_flags_out.txt")


def bl_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def infer_imm_r0(data: bytes, load: int, off: int):
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    start = max(0, off - 0x60)
    r0 = None
    for ins in md.disasm(data[start:off], load + start):
        ops = ins.op_str
        if ins.mnemonic in ("mov", "movs") and ops.startswith("r0, #"):
            try:
                r0 = int(ops.split("#")[1], 0)
            except Exception:
                r0 = ops
        elif ins.mnemonic == "ldr" and ops.startswith("r0, [pc"):
            try:
                imm = int(ops.split("#")[1].rstrip("]"), 0)
                pool = (ins.address + 8 + imm) & ~3
                poff = pool - load
                if 0 <= poff < len(data) - 3:
                    r0 = ("pool", struct.unpack_from("<I", data, poff)[0])
            except Exception:
                pass
    return r0


def main() -> None:
    lines: list[str] = []
    for name, (path, load) in LOADS.items():
        data = path.read_bytes()
        hits = []
        for off in range(0, len(data) - 3, 4):
            w = struct.unpack_from("<I", data, off)[0]
            if w >> 24 != 0xEB:
                continue
            if bl_target(load + off, w) != PERF:
                continue
            r0 = infer_imm_r0(data, load, off)
            hits.append((load + off, r0))
        lines.append(f"=== {name}: {len(hits)} bl to GetPerformanceFlagWithChecks ===")
        for addr, r0 in hits:
            interesting = False
            if isinstance(r0, int) and r0 in (55, 56, 57, 58, 59, 18, 10):
                interesting = True
            if isinstance(r0, tuple) and r0[0] == "pool" and r0[1] in (55, 56, 57, 58, 59):
                interesting = True
            mark = " ***" if interesting else ""
            lines.append(f"  0x{addr:08X}  r0={r0}{mark}")

    lines.append("")
    lines.append("=== Direct mov r0,#55-59 then bl (ARM) ===")
    for name, (path, load) in LOADS.items():
        data = path.read_bytes()
        for imm in (55, 56, 57, 58, 59):
            word = 0xE3A00000 | imm
            pat = struct.pack("<I", word)
            off = 0
            while True:
                i = data.find(pat, off)
                if i < 0:
                    break
                if i % 4 == 0 and i + 8 <= len(data):
                    w2 = struct.unpack_from("<I", data, i + 4)[0]
                    if w2 >> 24 == 0xEB:
                        tgt = bl_target(load + i + 4, w2)
                        lines.append(
                            f"  {name} 0x{load + i:08X}: mov r0,#{imm}; bl 0x{tgt:08X}"
                        )
                off = i + 1

    # Also find any function that compares multiple of 56-59 in sequence (difficulty decoder)
    lines.append("")
    lines.append("=== Nearby clusters of mov r0,#56-59 within 0x40 bytes ===")
    for name, (path, load) in LOADS.items():
        data = path.read_bytes()
        positions: dict[int, list[tuple[int, int]]] = {}
        for imm in (55, 56, 57, 58, 59):
            word = 0xE3A00000 | imm
            pat = struct.pack("<I", word)
            off = 0
            while True:
                i = data.find(pat, off)
                if i < 0:
                    break
                if i % 4 == 0:
                    positions.setdefault(i, []).append((imm, load + i))
                off = i + 1
        keys = sorted(positions)
        used = set()
        for k in keys:
            if k in used:
                continue
            cluster = [k]
            for k2 in keys:
                if k2 > k and k2 - k <= 0x40:
                    cluster.append(k2)
            if len(cluster) >= 2:
                for c in cluster:
                    used.add(c)
                desc = ", ".join(
                    f"#{imm}@0x{addr:08X}" for imm, addr in sorted(
                        (positions[c][0] for c in cluster), key=lambda x: x[1]
                    )
                )
                lines.append(f"  {name}: {desc}")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
