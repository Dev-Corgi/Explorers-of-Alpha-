"""Keep trimmed ROMs while growing their declared card capacity when needed.

Card capacity does not expand RAM, species IDs or byte-sized ability fields.
"""
from __future__ import annotations

import struct

from ndspy import _common

MIN_CAPACITY = 10  # 128 KiB << 10 = 128 MiB
MAX_CAPACITY = 12  # 512 MiB: phase5 full animation packages can exceed256 MiB.


def choose_capacity(size: int, previous: int) -> int:
    if size <= 0 or not 0 <= previous <= MAX_CAPACITY:
        raise ValueError("mega_evolve expects a positive ROM size and at most a 512 MiB card")
    if size > (131072 << MAX_CAPACITY):
        raise ValueError("mega_evolve ROM exceeds the selected 512 MiB card capacity")
    required = max(0, (size - 1).bit_length() - 17)
    return max(MIN_CAPACITY, previous, required)


def save_with_capacity(rom) -> bytes:
    previous = rom.deviceCapacity
    # ndspy regenerates filesystem offsets, used-size fields and checksums.
    # Preserve a previously larger card rather than shrinking after translation.
    try:
        output = bytearray(rom.save(updateDeviceCapacity=True))
        chosen = choose_capacity(len(output), previous)
    except Exception:
        rom.deviceCapacity = previous
        raise
    if output[0x14] != chosen:
        output[0x14] = chosen
        struct.pack_into("<H", output, 0x15E, _common.crc16(output[:0x15E]))
    rom.deviceCapacity = chosen
    # No padding to the physical card capacity: existing ROMs are trimmed too.
    return bytes(output)
