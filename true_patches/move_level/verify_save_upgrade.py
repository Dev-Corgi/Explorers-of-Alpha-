"""Exercise the compiled move_level save wrapper with old and versioned slots."""
from __future__ import annotations

import re
import struct
import tempfile
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM
from unicorn.arm_const import (
    UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1,
    UC_ARM_REG_R2, UC_ARM_REG_SP,
)

from patch_engine.apply_move_level import _build_runtime


MODULE = Path(__file__).resolve().parent
RUNTIME = 0x02180000
STATE = 0x02183000
MAIN = 0x02210000
POS = 0x02220000
STACK = 0x023FE000
STOP = 0x023FF000
PRIOR_READ = 0x020F1000
PRIOR_WRITE = 0x020F1010
PRIOR_NEW = 0x020F1020
BLOCK_SIZE = 0x2300
RECORD_SIZE = 559 * 4 * 4
STATE_SIZE = RECORD_SIZE + 559


class World:
    def __init__(self, binary: bytes):
        self.u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.u.mem_map(0x02000000, 0x400000)
        self.u.mem_write(RUNTIME, binary)
        self.flash = bytearray(b"\xff" * 0x20000)
        self.heap = 0x022C0000
        self.prior_result = 0
        self.writes = []
        self.u.hook_add(UC_HOOK_CODE, self.service)

    def service(self, u, address, size, _):
        if address not in (PRIOR_READ, PRIOR_WRITE, PRIOR_NEW, 0x02001170,
                           0x02001188, 0x0204A8E0, 0x0204A9C8,
                           0x02048F24, 0x02048F4C):
            return
        a, b, c = (u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
        result = 0
        if address in (PRIOR_READ, PRIOR_WRITE):
            result = self.prior_result
        elif address == 0x02001170:
            result = self.heap
            self.heap = (self.heap + a + 15) & ~15
            assert self.heap < 0x02380000
            u.mem_write(result, bytes(a))
        elif address == 0x0204A8E0:
            assert a * 256 + c <= len(self.flash)
            u.mem_write(b, bytes(self.flash[a * 256:a * 256 + c]))
        elif address == 0x0204A9C8:
            assert a * 256 + c <= len(self.flash)
            self.flash[a * 256:a * 256 + c] = u.mem_read(b, c)
            self.writes.append((a, c))
        elif address == 0x02048F24:
            data = u.mem_read(a + 4, b - 4)
            u.mem_write(a, struct.pack("<I", sum(data) & 0xFFFFFFFF))
        elif address == 0x02048F4C:
            data = u.mem_read(a + 4, b - 4)
            expected = struct.unpack("<I", u.mem_read(a, 4))[0]
            result = int(expected != sum(data) & 0xFFFFFFFF)
        u.reg_write(UC_ARM_REG_R0, result)
        u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

    def call(self, address: int, page: int) -> int:
        self.heap = 0x022C0000
        self.u.mem_write(POS, struct.pack("<I", page))
        for register, value in ((UC_ARM_REG_R0, POS), (UC_ARM_REG_R1, MAIN),
                                (UC_ARM_REG_R2, 0xB65C), (UC_ARM_REG_SP, STACK),
                                (UC_ARM_REG_LR, STOP)):
            self.u.reg_write(register, value)
        self.u.emu_start(address, STOP, count=1000000)
        assert self.u.reg_read(UC_ARM_REG_PC) == STOP
        assert self.u.reg_read(UC_ARM_REG_SP) == STACK
        return self.u.reg_read(UC_ARM_REG_R0)


def main():
    with tempfile.TemporaryDirectory(prefix="move_level_save_verify_") as folder:
        binary, labels = _build_runtime(
            MODULE, Path(folder), RUNTIME, STATE,
            {"tm_pending": 0x023C2C10, "z_pending": 0x023C3718,
             "z_selected_slot": 0x023C3714, "prior_save_read": PRIOR_READ,
             "prior_save_write": PRIOR_WRITE, "prior_new_game": PRIOR_NEW},
        )
        symbols = {name: int(value, 16) for name, value in
                   re.findall(r"\.definelabel (\w+), 0x([0-9A-F]+)", "\n".join(labels))}
        w = World(binary.read_bytes())
        read, write = symbols["MoveLevel_SaveRead"], symbols["MoveLevel_SaveWrite"]
        for page, block_page in ((0, 400), (200, 440)):
            offset = block_page * 256
            # Old saves had no block; either common erased-byte convention is accepted.
            fill = 0 if page else 0xFF
            w.flash[offset:offset + BLOCK_SIZE] = bytes([fill]) * BLOCK_SIZE
            w.u.mem_write(STATE, b"\x55" * STATE_SIZE)
            assert w.call(read, page) == 0
            assert bytes(w.u.mem_read(STATE, STATE_SIZE)) == bytes(STATE_SIZE)
            # The next normal save upgrades that slot to the v1 block.
            w.u.mem_write(STATE, struct.pack("<8H", 7, 0, 0, 0, 300, 0, 0, 0))
            assert w.call(write, page) == 0
            assert w.writes[-1] == (block_page, BLOCK_SIZE)
            assert w.flash[offset + 4:offset + 12] == struct.pack("<IHH", 0x31564C4D, 1, 559)
            w.u.mem_write(STATE, bytes(STATE_SIZE))
            assert w.call(read, page) == 0
            assert bytes(w.u.mem_read(STATE, 16)) == struct.pack("<8H", 7, 0, 0, 0, 300, 0, 0, 0)
            # Damaged or unsupported data is not mistaken for a legacy save.
            w.flash[offset + 30] ^= 1
            assert w.call(read, page) == 2
            w.flash[offset + 30] ^= 1
            w.flash[offset + 8:offset + 10] = struct.pack("<H", 2)
            data = w.flash[offset + 4:offset + BLOCK_SIZE]
            w.flash[offset:offset + 4] = struct.pack("<I", sum(data) & 0xFFFFFFFF)
            assert w.call(read, page) == 2
            w.flash[offset:offset + BLOCK_SIZE] = bytes([fill]) * BLOCK_SIZE
            w.flash[offset + BLOCK_SIZE - 1] ^= 1
            assert w.call(read, page) == 2
        w.prior_result = 1
        before = len(w.writes)
        assert w.call(write, 0) == 1
        assert len(w.writes) == before
        assert w.call(read, 0) == 1
        print("move_level save upgrade: old slots, roundtrip, corruption, future version, prior failure OK")


if __name__ == "__main__":
    main()
