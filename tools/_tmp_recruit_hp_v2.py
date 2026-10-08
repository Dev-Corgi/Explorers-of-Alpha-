"""Focused disasm of recruit / TeamSync / stores to team+0x10 and ground+0xA."""
from __future__ import annotations

import struct
from pathlib import Path

from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

ROM = Path(
    r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed.nds"
)
ROM_VANILLA = Path(r"C:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")
OV29 = 0x022DC240
ARM9 = 0x02000000


def halfword_op(word: int) -> str | None:
    if (word >> 25) & 7 != 0:
        return None
    if ((word >> 4) & 0xF) != 0xB:
        return None
    cond = (word >> 28) & 0xF
    L = (word >> 20) & 1
    S = (word >> 6) & 1
    H = (word >> 5) & 1
    U = (word >> 23) & 1
    P = (word >> 24) & 1
    I = (word >> 22) & 1  # imm
    rn = (word >> 16) & 0xF
    rd = (word >> 12) & 0xF
    if I:
        imm = ((word >> 4) & 0xF0) | (word & 0xF)
    else:
        imm = word & 0xF  # rm
    sign = "+" if U else "-"
    if H and not S:
        op = "ldrh" if L else "strh"
    elif H and S:
        op = "ldrsh" if L else "str??"
    elif S and not H:
        op = "ldrsb" if L else "str??"
    else:
        return None
    conds = "eq ne cs cc mi pl vs vc hi ls ge lt gt le".split()
    cs = "" if cond == 14 else conds[cond]
    if I and P:
        return f"{op}{cs} r{rd}, [r{rn}, #{sign}{imm:#x}]"
    return f"{op}{cs} r{rd}, [r{rn}], ... {word:#x}"


def word_xfer(word: int) -> str | None:
    if (word >> 26) & 3 != 1:
        return None
    I = (word >> 25) & 1
    P = (word >> 24) & 1
    U = (word >> 23) & 1
    B = (word >> 22) & 1
    L = (word >> 20) & 1
    rn = (word >> 16) & 0xF
    rd = (word >> 12) & 0xF
    if I:
        return None
    imm = word & 0xFFF
    sign = "+" if U else "-"
    cond = (word >> 28) & 0xF
    conds = "eq ne cs cc mi pl vs vc hi ls ge lt gt le".split()
    cs = "" if cond == 14 else conds[cond]
    op = ("ldr" if L else "str") + ("b" if B else "")
    if P:
        return f"{op}{cs} r{rd}, [r{rn}, #{sign}{imm:#x}]"
    return f"{op}{cs} r{rd}, [r{rn}], #{sign}{imm:#x}"


def branch_op(word: int, addr: int) -> str | None:
    if (word >> 25) & 7 != 5:
        return None
    cond = (word >> 28) & 0xF
    link = (word >> 24) & 1
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    dest = addr + 8 + (imm << 2)
    conds = "eq ne cs cc mi pl vs vc hi ls ge lt gt le".split()
    cs = "" if cond == 14 else conds[cond]
    return f"{'bl' if link else 'b'}{cs} {dest:#010x}"


def dis(word: int, addr: int) -> str:
    if word == 0xE1A00000:
        return "nop"
    for fn in (halfword_op, word_xfer):
        s = fn(word)
        if s:
            return s
    s = branch_op(word, addr)
    if s:
        return s
    # mov imm
    if (word >> 21) & 0x7F == 0x1A and (word >> 25) & 1:
        rd = (word >> 12) & 0xF
        rot = (word >> 8) & 0xF
        imm = word & 0xFF
        val = ((imm >> (2 * rot)) | (imm << (32 - 2 * rot))) & 0xFFFFFFFF if rot else imm
        return f"mov r{rd}, #{val:#x}"
    return f".word {word:#010x}"


def load(path: Path):
    rom = NintendoDSRom.fromFile(str(path))
    arm9 = bytes(rom.arm9)
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = bytes(rom.files[table[29].fileID])
    return arm9, ov29


def dump(data: bytes, load_addr: int, start: int, end: int, title: str):
    print(f"\n=== {title} ===")
    for addr in range(start, end, 4):
        off = addr - load_addr
        word = struct.unpack_from("<I", data, off)[0]
        print(f"{addr:08X}  {word:08X}  {dis(word, addr)}")


def scan_strh(data: bytes, load_addr: int, imm_set: set[int], title: str, window=None):
    print(f"\n=== {title} ===")
    for off in range(0, len(data) - 3, 4):
        addr = load_addr + off
        if window and not (window[0] <= addr < window[1]):
            continue
        word = struct.unpack_from("<I", data, off)[0]
        s = halfword_op(word)
        if not s or not s.startswith("strh"):
            continue
        # parse imm
        if ((word >> 4) & 0xF) != 0xB or not ((word >> 22) & 1):
            continue
        imm = ((word >> 4) & 0xF0) | (word & 0xF)
        if imm not in imm_set:
            continue
        if not ((word >> 23) & 1):
            continue
        if (word >> 20) & 1:  # load
            continue
        print(f"{addr:08X}  {word:08X}  {s}")


def scan_strb(data: bytes, load_addr: int, imm_set: set[int], title: str, window=None):
    print(f"\n=== {title} ===")
    for off in range(0, len(data) - 3, 4):
        addr = load_addr + off
        if window and not (window[0] <= addr < window[1]):
            continue
        word = struct.unpack_from("<I", data, off)[0]
        s = word_xfer(word)
        if not s or not s.startswith("strb"):
            continue
        imm = word & 0xFFF
        if imm not in imm_set:
            continue
        print(f"{addr:08X}  {word:08X}  {s}")


def find_func_start(data: bytes, load_addr: int, addr: int) -> int:
    """Walk back for push {..., lr} pattern."""
    off = addr - load_addr
    for i in range(0, 0x200, 4):
        w = struct.unpack_from("<I", data, off - i)[0]
        if (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4000):  # push with lr
            return addr - i
    return addr


def main():
    for tag, path in (("patched", ROM), ("vanilla", ROM_VANILLA)):
        print(f"\n########## {tag} ##########")
        arm9, ov29 = load(path)
        # TeamSync function - find start
        ts = find_func_start(ov29, OV29, 0x022FE068)
        print(f"TeamSync approx start {ts:#x}")
        dump(ov29, OV29, ts, 0x022FE140, f"{tag} TeamSync")
        dump(ov29, OV29, 0x022FD4F0, 0x022FD550, f"{tag} InitTeamMember HP/V")
        dump(arm9, ARM9, 0x02055B60, 0x02055C80, f"{tag} RecruitInitV area")
        dump(arm9, ARM9, 0x02048A80, 0x02048B80, f"{tag} RecruitHpOverwrite area")

        # All ov29 strh #0x10 near TeamSync and InitTeamMember and recruit-like
        scan_strh(ov29, OV29, {0x10}, f"{tag} ov29 all strh #0x10")
        scan_strh(ov29, OV29, {0xE, 0x12}, f"{tag} ov29 strh #0xE/#0x12 (cur/max HP team/dungeon)")
        scan_strh(arm9, ARM9, {0xA, 0x10}, f"{tag} arm9 strh #0xA/#0x10")
        scan_strb(arm9, ARM9, {0xA, 0x10}, f"{tag} arm9 strb #0xA/#0x10")

        # Compare vanilla vs patched at TeamSyncMaxHp and RecruitHpOverwrite
        for addr, blob, load_a, name in (
            (0x022FE060, ov29, OV29, "TeamSync+HP"),
            (0x02048AF0, arm9, ARM9, "RecruitHp"),
            (0x02055BB0, arm9, ARM9, "RecruitInitV"),
        ):
            print(f"\n-- {tag} {name} --")
            dump(blob, load_a, addr, addr + 0x40, name)


if __name__ == "__main__":
    main()
