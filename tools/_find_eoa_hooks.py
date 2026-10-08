"""Find ARM b/bl redirects to EoA patch region (>0x3B0000) in arm9."""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

ARM9 = Path(r"C:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
OUT = Path(r"C:\Working\SkyTemple\tools\_eoa_hooks.txt")
LOAD = 0x02000000
PATCH_MIN = 0x380000  # suspected EoA patch region


def branch_target(pc: int, w: int) -> int:
    imm = w & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x01000000
    return pc + 8 + (imm << 2)


def main() -> None:
    lines = []
    hooks = []
    for off in range(0, len(ARM9) - 3, 4):
        if off >= PATCH_MIN:
            break
        w = struct.unpack_from("<I", ARM9, off)[0]
        top = w >> 24
        if top not in (0xEA, 0xEB):
            continue
        tgt = branch_target(LOAD + off, w) - LOAD
        if tgt >= PATCH_MIN:
            kind = "bl" if top == 0xEB else "b"
            hooks.append((off, tgt, kind))

    lines.append(f"Hooks from base -> patch region: {len(hooks)}")
    for src, tgt, kind in hooks:
        lines.append(f"  0x{src:X} {kind} -> 0x{tgt:X}")

    # disasm first bytes of each unique target
    seen = set()
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for src, tgt, kind in hooks:
        if tgt in seen:
            continue
        seen.add(tgt)
        lines.append(f"\n=== Patch entry 0x{tgt:X} (from 0x{src:X}) ===")
        for ins in md.disasm(ARM9[tgt : tgt + 0x120], LOAD + tgt):
            lines.append(f"  0x{ins.address-LOAD:X}: {ins.mnemonic} {ins.op_str}")
            if ins.mnemonic in ("bx", "pop") and "pc" in ins.op_str:
                break

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(hooks)} hooks, {len(seen)} unique targets -> {OUT}")


if __name__ == "__main__":
    main()
