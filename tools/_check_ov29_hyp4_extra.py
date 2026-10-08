#!/usr/bin/env python3
"""Extra checks for hypothesis #4: ov29 unload vs StartMFunc repack."""

from __future__ import annotations

import json
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROOT = Path(__file__).resolve().parents[1]
VANILLA = ROOT / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
STATE = ROOT / "Export Rom" / "full_stack.state.json"

L29 = 0x022DC240
START_MFUNC = 0x02330134
END_MFUNC = 0x023326CC
RELOAD_SITE = 0x0232F980

LOAD = 0x020040AC
UNLOAD = 0x02004868

cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def bl_dest(word: int, pc: int) -> int | None:
    top = (word >> 24) & 0xFF
    if top not in (0xEA, 0xEB):
        return None
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return pc + 8 + (imm << 2)


def branches_to(data: bytes, base: int, target: int) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    for off in range(0, len(data) - 3, 4):
        pc = base + off
        w = struct.unpack_from("<I", data, off)[0]
        dest = bl_dest(w, pc)
        if dest == target:
            kind = "bl" if (w >> 24) == 0xEB else "b"
            hits.append((kind, pc))
    return hits


def main() -> None:
    rom = NintendoDSRom(VANILLA.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = rom.files[table[29].fileID]
    arm9 = bytes(rom.arm9)
    t29 = table[29]

    print("=" * 72)
    print("ov29 RAM map")
    print("=" * 72)
    print(f"  load={t29.ramAddress:#010x} size={t29.ramSize:#x} end={t29.ramAddress + t29.ramSize:#010x}")

    collisions = []
    for i in range(len(table)):
        t = table[i]
        if i == 29 or not hasattr(t, "ramAddress"):
            continue
        a0, a1 = t.ramAddress, t.ramAddress + t.ramSize
        b0, b1 = t29.ramAddress, t29.ramAddress + t29.ramSize
        if a0 < b1 and b0 < a1:
            collisions.append((i, a0, a1))
    print(f"  overlays overlapping ov29 RAM: {len(collisions)}")
    for i, a0, a1 in collisions[:10]:
        print(f"    ov{i} {a0:#010x}-{a1:#010x}")

    print("\n" + "=" * 72)
    print("Branches to waza reload / StartMFunc / EndMFunc (vanilla ov29)")
    print("=" * 72)
    for label, addr in [
        ("ReloadTail", RELOAD_SITE),
        ("b StartMFunc", 0x0232F9A4),
        ("StartMFunc", START_MFUNC),
        ("EndMFunc", END_MFUNC),
    ]:
        hits = branches_to(ov29, L29, addr)
        print(f"  {label} @ {addr:#010x}: {len(hits)} incoming")
        for kind, pc in hits[:6]:
            print(f"    {kind} from {pc:#010x}")

    print("\n" + "=" * 72)
    print("Disasm around waza reload tail (0x232F920-0x232F9B0)")
    print("=" * 72)
    for ins in cs.disasm(ov29[0x232F920 - L29 : 0x232F9B0 - L29], 0x0232F920):
        mark = ">>" if ins.address in (RELOAD_SITE, 0x0232F9A4) else "  "
        print(f"{mark}{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

    print("\n" + "=" * 72)
    print("LoadOverlay(29) broad scan (arm9 + ov29 + ov31)")
    print("=" * 72)
    ov31 = rom.files[table[31].fileID]
    for label, data, base in [("arm9", arm9, 0x02000000), ("ov29", ov29, L29), ("ov31", ov31, 0x02382820)]:
        load29 = []
        unload29 = []
        for off in range(0, len(data) - 7, 4):
            pc = base + off
            for back in range(0, 4):
                w_mov = struct.unpack_from("<I", data, off - back * 4)[0]
                if off - back * 4 < 0:
                    continue
                if (w_mov & 0xFFFFFFF0) != 0xE3A00010:
                    continue
                imm = w_mov & 0xFF
                w_bl = struct.unpack_from("<I", data, off)[0]
                dest = bl_dest(w_bl, pc)
                if imm == 29 and dest == LOAD:
                    load29.append(pc - back * 4)
                if imm == 29 and dest == UNLOAD:
                    unload29.append(pc - back * 4)
        print(f"  {label}: LoadOverlay(29)={len(load29)} UnloadOverlay(29)={len(unload29)}")
        for a in load29[:5]:
            print(f"    Load @ {a:#010x}")
        for a in unload29[:5]:
            print(f"    Unload @ {a:#010x}")

    print("\n" + "=" * 72)
    print("full_stack hook caves vs StartMFunc window")
    print("=" * 72)
    if STATE.is_file():
        state = json.loads(STATE.read_text())
        for mod in state["modules"]:
            for c in mod.get("caves", []):
                if c.get("overlay") != "ov29":
                    continue
                la = c.get("load_address", 0)
                sz = c["size"]
                inside = la >= START_MFUNC and la + sz <= END_MFUNC
                print(
                    f"  {mod['id']:18} la={la:#010x} size={sz:#x} "
                    f"{'INSIDE StartMFunc' if inside else 'OUTSIDE'}"
                )

    hooks = [
        ("RemoveUsedItem hook", 0x0233018C),
        ("GetSubMenuStringId", 0x0233027C),
        ("orb save cave", 0x023303C4),
        ("after add cave", 0x023312F0),
        ("tm/z chain", 0x02331B58),
        ("z menu cave", 0x02331BBC),
    ]
    print("\n  Patched branch targets:")
    for name, addr in hooks:
        inside = START_MFUNC <= addr < END_MFUNC
        print(f"    {name} {addr:#010x}: {'INSIDE' if inside else 'OUTSIDE'}")

    print("\n" + "=" * 72)
    print("Vanilla StartMFunc region: nonzero ratio (file vs padding)")
    print("=" * 72)
    off_start = START_MFUNC - L29
    off_end = END_MFUNC - L29
    chunk = ov29[off_start:off_end]
    nz = sum(1 for b in chunk if b != 0)
    print(f"  StartMFunc..EndMFunc span={len(chunk):#x} bytes, nonzero={nz}/{len(chunk)}")


if __name__ == "__main__":
    main()
