#!/usr/bin/env python3
"""Audit ov29/arm9 caves: overlap, vanilla live-code invasion, hook site sanity."""
from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parent.parent
VANILLA = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
PATCHED = ROOT / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds"
STATE = ROOT / "Export Rom" / "full_stack.state.json"

START_MFUNC_RAM = 0x02330134
END_MFUNC_RAM = 0x023326CC


@dataclass
class Cave:
    module: str
    version: int
    overlay: str
    file_offset: int
    size: int
    load_address: int


def load_caves(state: dict) -> list[Cave]:
    out: list[Cave] = []
    for mod in state["applied"]:
        for c in mod.get("caves", []):
            out.append(
                Cave(
                    module=mod["id"],
                    version=mod["version"],
                    overlay=c["overlay"],
                    file_offset=c["file_offset"],
                    size=c["size"],
                    load_address=c["load_address"],
                )
            )
    return out


def arm_insn_word(w: int) -> bool:
    """Heuristic: looks like a plausible ARM32 instruction (not all-zero / not literal run)."""
    if w == 0 or w == 0xFFFFFFFF:
        return False
    top = (w >> 24) & 0xFF
    # common ARM cond / SWI / branch / load-store / data proc
    if top in range(0xE0, 0xF0):
        return True
    if top in (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F):
        return True
    return False


def scan_vanilla_region(data: bytes, fo: int, size: int) -> dict:
    chunk = data[fo : fo + size]
    words = [struct.unpack_from("<I", chunk, i)[0] for i in range(0, len(chunk) - (len(chunk) % 4), 4)]
    nonzero = sum(1 for b in chunk if b != 0)
    insn_like = sum(1 for w in words if arm_insn_word(w))
    # pointer-ish words into ov29 load range
    ptr_like = 0
    for w in words:
        if 0x022DC000 <= w <= 0x02390000:
            ptr_like += 1
    return {
        "nonzero_bytes": nonzero,
        "insn_like_words": insn_like,
        "total_words": len(words),
        "ptr_like_words": ptr_like,
        "head_hex": chunk[:16].hex(),
        "tail_hex": chunk[-16:].hex() if len(chunk) >= 16 else chunk.hex(),
    }


def overlaps(a: Cave, b: Cave) -> bool:
    if a.overlay != b.overlay:
        return False
    a0, a1 = a.file_offset, a.file_offset + a.size
    b0, b1 = b.file_offset, b.file_offset + b.size
    return a0 < b1 and b0 < a1


def main() -> None:
    state = json.loads(STATE.read_text())
    caves = load_caves(state)
    vrom = NintendoDSRom(VANILLA.read_bytes())
    table = loadOverlayTable(vrom.arm9OverlayTable, lambda _i, _n: b"")
    ov29_v = vrom.files[table[29].fileID]
    arm9_v = bytes(vrom.arm9)

    print("=== CAVE LAYOUT (apply order) ===")
    for c in caves:
        end = c.file_offset + c.size
        print(
            f"{c.module:18} v{c.version:<2} {c.overlay:4} "
            f"file=[{c.file_offset:#7x}..{end:#x}) la={c.load_address:#x} size={c.size}"
        )

    print("\n=== CAVE vs CAVE OVERLAP ===")
    any_overlap = False
    for i, a in enumerate(caves):
        for b in caves[i + 1 :]:
            if overlaps(a, b):
                any_overlap = True
                print(
                    f"OVERLAP: {a.module} [{a.file_offset:#x}..{a.file_offset + a.size:#x}) "
                    f"vs {b.module} [{b.file_offset:#x}..{b.file_offset + b.size:#x})"
                )
    if not any_overlap:
        print("none")

    print("\n=== VANILLA BYTES AT CAVE SITES (invasion check) ===")
    for c in caves:
        blob = ov29_v if c.overlay == "ov29" else arm9_v
        info = scan_vanilla_region(blob, c.file_offset, c.size)
        pct = 100.0 * info["nonzero_bytes"] / c.size
        insn_pct = 100.0 * info["insn_like_words"] / max(info["total_words"], 1)
        status = "PADDING/EMPTY" if info["nonzero_bytes"] == 0 else (
            "LIKELY LIVE CODE" if insn_pct > 25 and info["nonzero_bytes"] > 64 else "MIXED/POSSIBLE DATA"
        )
        print(f"\n{c.module} @ {c.overlay} {c.file_offset:#x} size={c.size} -> {status}")
        print(f"  nonzero={info['nonzero_bytes']}/{c.size} ({pct:.1f}%) insn_like={info['insn_like_words']}/{info['total_words']} ptr_like={info['ptr_like_words']}")
        print(f"  head={info['head_hex']} tail={info['tail_hex']}")

    # z_move_v7 hook sites: verify overwrite is branch/bl not stomping unrelated code
    print("\n=== Z_MOVE_V2 HOOK SITES (overwrite targets) ===")
    zmod = next(m for m in state["applied"] if m["id"] == "z_move_v2")
    ov29_p = None
    if PATCHED.exists():
        prom = NintendoDSRom(PATCHED.read_bytes())
        ov29_p = prom.files[table[29].fileID]
    base = table[29].ramAddress
    for h in zmod["hooks"]:
        site = h["site"]
        off = site - base
        vw = struct.unpack_from("<I", ov29_v, off)[0] if h.get("binary", "ov29") == "ov29" else struct.unpack_from("<I", arm9_v, site - 0x02000000)[0]
        pw = struct.unpack_from("<I", ov29_p, off)[0] if ov29_p is not None and h.get("binary", "ov29") == "ov29" else None
        print(f"  {h['name']:40} {site:#010x} vanilla={vw:#010x} patched={pw:#010x if pw else 'n/a'}")

    # gap check between adjacent ov29 caves
    print("\n=== OV29 CAVES vs StartMFunc REPACK WINDOW ===")
    print(f"  forbidden RAM [{START_MFUNC_RAM:#x}..{END_MFUNC_RAM:#x})")
    smfunc_hits = 0
    for c in caves:
        if c.overlay != "ov29":
            continue
        la_end = c.load_address + c.size
        hit = la_end > START_MFUNC_RAM and c.load_address < END_MFUNC_RAM
        status = "INSIDE StartMFunc" if hit else "SAFE (outside StartMFunc)"
        if hit:
            smfunc_hits += 1
        print(
            f"  {c.module:18} la=[{c.load_address:#x}..{la_end:#x}) -> {status}"
        )
    if smfunc_hits:
        print(f"  *** {smfunc_hits} cave(s) still overlap StartMFunc ***")
    else:
        print("  all ov29 caves clear StartMFunc")

    print("\n=== ADJACENT OV29 CAVE GAPS ===")
    ov29_caves = sorted([c for c in caves if c.overlay == "ov29"], key=lambda c: c.file_offset)
    for a, b in zip(ov29_caves, ov29_caves[1:]):
        gap = b.file_offset - (a.file_offset + a.size)
        print(f"  {a.module} -> {b.module}: gap={gap} bytes ({gap:#x})")


if __name__ == "__main__":
    main()
