#!/usr/bin/env python3
import struct
from pathlib import Path
from ndspy.rom import NintendoDSRom

OV29 = 0x022DC240
OV36 = 0x023A7080
POOL_OFF = 0x02324618 - OV29

rom = NintendoDSRom(
    Path(r"c:\Working\SkyTemple\Export Rom\Explorers of Alpha_Vanilla+full_stack.nds").read_bytes()
)
ov29 = rom.loadArm9Overlays()[29].data
ov36 = rom.loadArm9Overlays()[36].data

pool = struct.unpack_from("<I", ov29, POOL_OFF)[0]
print(f"pool={pool:#010x} (ov29={pool < OV36})")

for off, name in [
    (0x0232234C - OV29, "NoCharger1"),
    (0x02324D84 - OV29, "NoCharger2"),
]:
    w = struct.unpack_from("<I", ov29, off)[0]
    print(f"{name} @ {OV29+off:#x}: {w:#010x} (bl={(w>>24)==0xEB})")

# handler prologue should call OverlayIsLoaded
handler_off = 0x1A578
w0 = struct.unpack_from("<I", ov36, handler_off)[0]
w2 = struct.unpack_from("<I", ov36, handler_off + 8)[0]
print(f"DoMoveRoomChargeV4 prologue: {w0:#010x} {w2:#010x}")

from skytemple_files.data.data_cd.handler import DataCDHandler

cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/waza_cd.bin"))
code = cd.get_effect_code(cd.get_item_effect_id(521))
w = struct.unpack_from("<I", code, 16)[0]
imm = w & 0xFFFFFF
if imm & 0x800000:
    imm -= 0x1000000
target = 0x02330134 + 16 + 8 + imm * 4
print(f"Discharge BL target {target:#x}")

# table in ov29 at pool
if pool >= OV29 and pool < OV36:
    off = pool - OV29
    for i in range(12, 16):
        move = struct.unpack_from("<H", ov29, off + i * 4)[0]
        status = struct.unpack_from("<H", ov29, off + i * 4 + 2)[0]
        print(f"  table[{i}] move={move} status={status}")
