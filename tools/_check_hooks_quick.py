#!/usr/bin/env python3
from pathlib import Path
import struct
from ndspy.code import loadOverlayTable
from ndspy.rom import NintendoDSRom

LOAD = 0x22DC240
SITES = {
    "ExecuteMoveEffectHook2": 0x023238AC,
    "ExecuteMoveEffectHook1": 0x02322B50,
    "UseItemA": 0x02322608,
    "IsChargingTwoTurnMoveFail": 0x02324610,
    "TryInflictBurnSuccess": 0x02312318,
    "BoostOffensiveStat_entry": 0x023139A4,
}


def get_ov29(path: Path) -> bytes:
    rom = NintendoDSRom(path.read_bytes())
    table = loadOverlayTable(rom.arm9OverlayTable, lambda _i, _n: b"")
    table = loadOverlayTable(rom.arm9OverlayTable, lambda i, _n: rom.files[table[i].fileID])
    return rom.files[table[29].fileID]


def word_at(ov: bytes, addr: int) -> int:
    return struct.unpack_from("<I", ov, addr - LOAD)[0]


def main() -> None:
    van = get_ov29(Path("Vanilla Rom/Explorers of Alpha_Vanilla.nds"))
    exp_path = Path("Export Rom/Explorers of Alpha_Vanilla+full_stack.nds")
    if not exp_path.is_file():
        print(f"Missing {exp_path}")
        return
    exp = get_ov29(exp_path)
    print(f"Checking {exp_path.name}")
    for name, addr in SITES.items():
        vw, ew = word_at(van, addr), word_at(exp, addr)
        status = "HOOKED" if vw != ew else "same"
        print(f"  {name} @{addr:#x}: {status}  van={vw:#010x} exp={ew:#010x}")


if __name__ == "__main__":
    main()
