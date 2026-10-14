"""Check capacity boundaries and actual NDS serialization without ROM outputs."""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from ndspy import _common
from ndspy.rom import NintendoDSRom
from true_patches.mega_evolve.rom_capacity import choose_capacity, save_with_capacity
from patch_engine.apply_module import _serialize_rom
from patch_engine.state import AppliedModule, BuildState

MIB = 1024 * 1024


def main():
    for size, previous, expected in (
        (1, 0, 10), (128 * MIB - 1, 10, 10), (128 * MIB, 10, 10),
        (128 * MIB + 1, 10, 11), (256 * MIB, 10, 11),
        (125 * MIB, 11, 11),
        (256 * MIB + 1, 11, 12), (512 * MIB, 11, 12), (128 * MIB, 12, 12),
    ):
        assert choose_capacity(size, previous) == expected
    for size, previous in ((0, 10), (512 * MIB + 1, 10), (1, 13)):
        try:
            choose_capacity(size, previous)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid capacity accepted")

    source = REPO / "PatchTesting/Export Rom/Explorers of Alpha+.nds"
    original = source.read_bytes()
    before = hashlib.sha256(original).digest()
    rom = NintendoDSRom(original)
    original_last = rom.files[-1]
    rom.files[-1] = original_last + bytes(4 * MIB)
    # The old image is ~125 MiB; this in-memory fixture crosses 128 MiB.
    state = BuildState(rom_profile="us_vanilla", overlay29_load=0x022DC240)
    state.upsert_module(AppliedModule("mega_evolve", 4))
    output = _serialize_rom(rom, state)
    assert 128 * MIB < len(output) < 256 * MIB
    assert output[0x14] == 11
    assert struct.unpack_from("<H", output, 0x15E)[0] == _common.crc16(output[:0x15E])
    assert struct.unpack_from("<I", output, 0x80)[0] == len(output)
    restored = NintendoDSRom(output)
    assert restored.files == rom.files
    assert restored.arm9 == rom.arm9 and restored.arm9OverlayTable == rom.arm9OverlayTable
    assert all(restored.filenames.filenameOf(i) == rom.filenames.filenameOf(i) for i in range(len(rom.files)))

    # A later smaller image (e.g. translated/compressed assets) keeps 256 MiB.
    restored.files[-1] = original_last
    smaller = _serialize_rom(restored, state)
    assert len(smaller) < 128 * MIB and smaller[0x14] == 11
    assert struct.unpack_from("<H", smaller, 0x15E)[0] == _common.crc16(smaller[:0x15E])

    class UnrelatedRom:
        def save(self, **kwargs):
            assert not kwargs
            return b"unrelated-save"
    assert _serialize_rom(UnrelatedRom(), None) == b"unrelated-save"
    empty = BuildState(rom_profile="us_vanilla", overlay29_load=0x022DC240)
    assert _serialize_rom(UnrelatedRom(), empty) == b"unrelated-save"
    assert hashlib.sha256(source.read_bytes()).digest() == before
    print("PASS: 128/256/512 MiB boundaries, growth, no shrink, header CRC/used size,")
    print("      FAT/FNT/file/overlay round-trip and unaffected unrelated modules.")
    print("No ROM or save files were written.")


if __name__ == "__main__":
    main()
