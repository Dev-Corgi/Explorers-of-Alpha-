"""Disassemble TeamSync / recruit / InitTeamMember HP paths and list pmdsky symbols."""
from __future__ import annotations

import re
import struct
from pathlib import Path

from ndspy.rom import NintendoDSRom

VENV_NA = Path(r"C:\Working\SkyTemple\.venv\Lib\site-packages\pmdsky_debug_py\na.py")
ROM_PATCHED = Path(
    r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed+spinda_ev_speed.nds"
)
ROM_BASE = Path(
    r"C:\Working\SkyTemple\Export Rom\Unit_Test\Explorers of Alpha_Vanilla+base_stats_speed.nds"
)
ROM_VANILLA = Path(r"C:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds")

OV29_LOAD = 0x022DC240
ARM9_LOAD = 0x02000000

# Regions to dump (start, end exclusive, label)
REGIONS = [
    ("TeamSync vicinity", 0x022FE000, 0x022FE120, "ov29"),
    ("InitTeamMember HP copy", 0x022FD4E0, 0x022FD580, "ov29"),
    ("InitTeamMember entry", 0x022FD3B0, 0x022FD420, "ov29"),
    ("Spawn HP writers", 0x022FE2E0, 0x022FE400, "ov29"),
    ("RecruitInitV vicinity", 0x02055B80, 0x02055C40, "arm9"),
    ("RecruitHpOverwrite vicinity", 0x02048AC0, 0x02048B40, "arm9"),
    ("GroundInitV vicinity", 0x02052D00, 0x02052D80, "arm9"),
]


def dis_arm(word: int, addr: int) -> str:
    cond = (word >> 28) & 0xF
    conds = "EQ NE CS CC MI PL VS VC HI LS GE LT GT LE AL NV".split()
    c = conds[cond] if cond < 15 else f"?{cond}"
    if (word & 0x0FFFFFF0) == 0x012FFF10:
        rn = (word >> 0) & 0xF
        return f"bx{'' if c=='AL' else c.lower()} r{rn}"
    if (word >> 25) & 7 == 5:  # B/BL
        link = (word >> 24) & 1
        imm = word & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        dest = addr + 8 + (imm << 2)
        return f"{'bl' if link else 'b'}{'' if c=='AL' else c.lower()} {dest:#010x}"
    if (word & 0x0FFFFFF0) == 0x01A00000 and ((word >> 4) & 0xFF) == 0:
        # mov rd, rm (lsl #0) == nop when rd==rm? actually mov r0,r0 is E1A00000
        rd = (word >> 12) & 0xF
        rm = word & 0xF
        if rd == rm == 0 and c == "AL":
            return "nop"
    # data processing / ldr/str rough
    if (word >> 26) & 3 == 1:  # single data transfer
        I = (word >> 25) & 1
        P = (word >> 24) & 1
        U = (word >> 23) & 1
        B = (word >> 22) & 1
        W = (word >> 21) & 1
        L = (word >> 20) & 1
        rn = (word >> 16) & 0xF
        rd = (word >> 12) & 0xF
        off = word & 0xFFF
        op = ("ldr" if L else "str") + ("b" if B else "")
        sign = "+" if U else "-"
        if I == 0 and P:
            return f"{op}{'' if c=='AL' else c.lower()} r{rd}, [r{rn}, #{sign}{off:#x}]"
        return f"{op}? {word:#010x}"
    if (word >> 25) & 7 == 0 and (word >> 4) & 0xF == 0xB:  # halfword
        L = (word >> 20) & 1
        S = (word >> 6) & 1
        H = (word >> 5) & 1
        U = (word >> 23) & 1
        rn = (word >> 16) & 0xF
        rd = (word >> 12) & 0xF
        off = ((word >> 4) & 0xF0) | (word & 0xF)
        sign = "+" if U else "-"
        if H and not S:
            op = "ldrh" if L else "strh"
        elif H and S:
            op = "ldrsh" if L else "strh?"
        else:
            op = "ldrsb" if L else "strb?"
        return f"{op}{'' if c=='AL' else c.lower()} r{rd}, [r{rn}, #{sign}{off:#x}]"
    if (word >> 26) & 3 == 0:  # data processing
        opc = (word >> 21) & 0xF
        names = "and eor sub rsb add adc sbc rsc tst teq cmp cmn orr mov bic mvn".split()
        S = (word >> 20) & 1
        rn = (word >> 16) & 0xF
        rd = (word >> 12) & 0xF
        I = (word >> 25) & 1
        if I:
            rot = (word >> 8) & 0xF
            imm = word & 0xFF
            val = ((imm >> (2 * rot)) | (imm << (32 - 2 * rot))) & 0xFFFFFFFF if rot else imm
            if opc in (0xD,):  # mov
                return f"mov{'' if c=='AL' else c.lower()}{'s' if S else ''} r{rd}, #{val:#x}"
            if opc in (0xA, 0xB):
                return f"{names[opc]}{'' if c=='AL' else c.lower()} r{rn}, #{val:#x}"
            return f"{names[opc]}{'' if c=='AL' else c.lower()}{'s' if S else ''} r{rd}, r{rn}, #{val:#x}"
        rm = word & 0xF
        if opc == 0xD:
            return f"mov{'' if c=='AL' else c.lower()}{'s' if S else ''} r{rd}, r{rm}"
        return f"{names[opc]}{'' if c=='AL' else c.lower()}{'s' if S else ''} r{rd}, r{rn}, r{rm}"
    return f".word {word:#010x}"


def load_bins(rom_path: Path):
    rom = NintendoDSRom.fromFile(str(rom_path))
    arm9 = bytes(rom.arm9)
    # overlay 29
    from ndspy.code import loadOverlayTable

    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    ov29 = bytes(rom.files[table[29].fileID])
    return arm9, ov29


def dump_region(label, start, end, which, arm9, ov29):
    data = ov29 if which == "ov29" else arm9
    load = OV29_LOAD if which == "ov29" else ARM9_LOAD
    print(f"\n=== {label} ({start:#x}-{end:#x}) ===")
    for addr in range(start, end, 4):
        off = addr - load
        if off < 0 or off + 4 > len(data):
            continue
        word = struct.unpack_from("<I", data, off)[0]
        print(f"{addr:08X}  {word:08X}  {dis_arm(word, addr)}")


def find_strh_to_offsets(data: bytes, load: int, targets: set[int], label: str):
    """Scan for strh/strb with immediate offset in targets."""
    hits = []
    for off in range(0, len(data) - 3, 4):
        word = struct.unpack_from("<I", data, off)[0]
        # halfword transfer: bits 27-25=000, bit4=1, bits7-4 include H
        if (word >> 25) & 7 != 0:
            continue
        if (word >> 4) & 0xF != 0xB:
            continue
        L = (word >> 20) & 1
        H = (word >> 5) & 1
        S = (word >> 6) & 1
        I = (word >> 22) & 1  # for halfword, bit22 is imm flag
        if not I:
            continue
        imm_off = ((word >> 4) & 0xF0) | (word & 0xF)
        if imm_off not in targets:
            continue
        U = (word >> 23) & 1
        if not U:
            continue
        rn = (word >> 16) & 0xF
        rd = (word >> 12) & 0xF
        op = "ldrh/ldrsh" if L else ("strh" if H and not S else "other")
        if L:
            continue  # only stores
        addr = load + off
        hits.append((addr, word, op, rd, rn, imm_off))
    print(f"\n=== {label}: strh to offsets {sorted(targets)} ({len(hits)} hits) ===")
    for addr, word, op, rd, rn, imm in hits[:80]:
        print(f"{addr:08X}  {word:08X}  {op} r{rd}, [r{rn}, #{imm:#x}]")
    if len(hits) > 80:
        print(f"... +{len(hits)-80} more")
    return hits


def find_strb_to_offsets(data: bytes, load: int, targets: set[int], label: str):
    hits = []
    for off in range(0, len(data) - 3, 4):
        word = struct.unpack_from("<I", data, off)[0]
        # strb imm: 01 I=0 P U B=1 W L=0
        if (word >> 26) & 3 != 1:
            continue
        I = (word >> 25) & 1
        B = (word >> 22) & 1
        L = (word >> 20) & 1
        P = (word >> 24) & 1
        U = (word >> 23) & 1
        if I or not B or L or not P or not U:
            continue
        imm = word & 0xFFF
        if imm not in targets:
            continue
        rn = (word >> 16) & 0xF
        rd = (word >> 12) & 0xF
        addr = load + off
        hits.append((addr, word, rd, rn, imm))
    print(f"\n=== {label}: strb to offsets {sorted(targets)} ({len(hits)} hits) ===")
    for addr, word, rd, rn, imm in hits[:80]:
        print(f"{addr:08X}  {word:08X}  strb r{rd}, [r{rn}, #{imm:#x}]")
    if len(hits) > 80:
        print(f"... +{len(hits)-80} more")
    return hits


def pmdsky_symbols():
    t = VENV_NA.read_text(encoding="utf-8", errors="ignore")
    keys = (
        "recruit",
        "team_member",
        "joined",
        "ground_monster",
        "init_team",
        "update_team",
        "copy_team",
        "sync",
        "max_hp",
        "set_active_team",
        "generate_team",
        "add_member",
    )
    print("\n=== pmdsky symbols ===")
    for m in re.finditer(
        r'([A-Za-z0-9_]+)\s*=\s*Symbol\(\s*"([^"]+)"\s*,\s*"([^"]*)"', t
    ):
        name, sym, desc = m.group(1), m.group(2), m.group(3)
        blob = (name + " " + sym + " " + desc).lower()
        if not any(k in blob for k in keys):
            continue
        chunk = t[m.end() : m.end() + 500]
        am = re.search(r"address(?:es)?\s*=\s*(\{[^}]+\}|0x[0-9A-Fa-f]+)", chunk)
        addr = am.group(1) if am else "?"
        print(f"{name} / {sym}: {addr}")
        print(" ", desc[:160].replace("\n", " "))


def main():
    pmdsky_symbols()
    for tag, path in (("base_stats", ROM_BASE), ("base+spinda", ROM_PATCHED), ("vanilla_alpha", ROM_VANILLA)):
        if not path.exists():
            print("missing", path)
            continue
        print(f"\n########## ROM {tag}: {path.name} ##########")
        arm9, ov29 = load_bins(path)
        for label, start, end, which in REGIONS:
            dump_region(label, start, end, which, arm9, ov29)
        # Focused store scans near TeamSync / recruit
        # Full ov29 strh #0x10 and #0x12 stores (team/dungeon HP-related)
        find_strh_to_offsets(ov29, OV29_LOAD, {0x10, 0x12, 0xA}, f"{tag} ov29")
        find_strb_to_offsets(ov29, OV29_LOAD, {0x10, 0x11, 0xA, 0xB}, f"{tag} ov29")
        find_strh_to_offsets(arm9, ARM9_LOAD, {0x10, 0xA}, f"{tag} arm9")
        find_strb_to_offsets(arm9, ARM9_LOAD, {0x10, 0xA}, f"{tag} arm9")


if __name__ == "__main__":
    main()
