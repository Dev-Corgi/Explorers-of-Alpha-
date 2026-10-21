"""Append Speed-rank visuals cloned from the game's existing stat effects."""
from __future__ import annotations

import copy
import hashlib
import struct

from skytemple_files.container.bin_pack.handler import BinPackHandler
from skytemple_files.data.anim.handler import AnimHandler


EFFECT_PATH = "EFFECT/effect.bin"
ANIM_PATHS = ("BALANCE/anim.bin", "UTILITY/anim.bin")
SOURCE_EFFECT = 257
SPEED_EFFECT = 293
SPEED_DOWN_ANIM = 707
SPEED_UP_ANIM = 708
SOURCE_SHA256 = "604b0ab8f8ee462332e4f3b6aea0fe64b16659a738f0a0450c9479a74e67f02a"


def _speed_palette(source: bytes) -> bytes:
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("mega_evolve Speed visual source effect changed")
    result = bytearray(source)
    wan_header = struct.unpack_from("<I", source, 4)[0]
    image_info = struct.unpack_from("<I", source, wan_header + 4)[0]
    palette_info = struct.unpack_from("<I", source, image_info + 4)[0]
    palette_start = struct.unpack_from("<I", source, palette_info)[0]
    if (palette_start, palette_info) != (0x1110, 0x11d0):
        raise RuntimeError("mega_evolve Speed visual palette layout changed")
    for pos in range(palette_start, palette_info, 4):
        red, green, blue, alpha = source[pos:pos + 4]
        if red == green == blue == 0:
            continue
        brightness = (red * 77 + green * 150 + blue * 29) >> 8
        result[pos:pos + 4] = bytes((brightness * 2 // 5,
                                      brightness * 4 // 5,
                                      min(255, brightness * 6 // 5), alpha))
    return bytes(result)


def prepare(rom) -> dict[str, bytes]:
    original_anim = rom.getFileByName(ANIM_PATHS[0])
    if original_anim != rom.getFileByName(ANIM_PATHS[1]):
        raise RuntimeError("mega_evolve Speed visual animation tables differ")
    animations = AnimHandler.deserialize(original_anim)
    effects = BinPackHandler.deserialize(rom.getFileByName(EFFECT_PATH))
    if len(animations.general_table) != SPEED_DOWN_ANIM or len(effects) != SPEED_EFFECT:
        raise RuntimeError("mega_evolve Speed visual ids are occupied")
    down, up = animations.general_table[686:688]
    if (down.anim_file, down.unk2, down.sfx, up.anim_file, up.unk2, up.sfx) != (257, 0, 544, 257, 1, 547):
        raise RuntimeError("mega_evolve native stat visual entries changed")
    effects.append(_speed_palette(effects[SOURCE_EFFECT]))
    for entry in (down, up):
        clone = copy.deepcopy(entry)
        clone.anim_file = SPEED_EFFECT
        animations.general_table.append(clone)
    new_anim = AnimHandler.serialize(animations)
    result = {EFFECT_PATH: BinPackHandler.serialize(effects)}
    result.update({path: new_anim for path in ANIM_PATHS})
    return result
