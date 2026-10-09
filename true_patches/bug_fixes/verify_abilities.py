"""Execute the repaired ability paths, with only UI/item services stubbed."""

import struct

from unicorn import UC_HOOK_CODE, UcError
from unicorn.arm_const import *

from verify import recovery_machine

ENTITIES = (0x02120000, 0x02120200, 0x02120400)
MONSTERS = (0x02121000, 0x02121400, 0x02121800)
DUNGEON = 0x02100000
STACK, RETURN = 0x0273F000, 0x0273E000


class World:
    def __init__(self, rom):
        self.uc = recovery_machine(rom)
        self.logs = []
        self.monitor = None
        self.move_type = 13
        ability_entry = struct.unpack("<I", self.uc.mem_read(0x02301D10, 4))[0]
        self.full_stack = ((ability_entry >> 25) & 7) == 5
        self.uc.hook_add(UC_HOOK_CODE, self.service)
        self.reset()

    def service(self, uc, address, _size, _data):
        r0, r1 = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        if address == 0x0234B2A4:
            self.logs.append((r0, r1))
            value = 0
        elif address == 0x02025888:
            value = 0x0273D000
        elif address == 0x023467E4:
            value = int(r0 == self.monitor and r1 == 39)
        elif address == 0x0230227C:
            value = self.move_type
        elif address == 0x022EAA98:
            value = 0
        elif address == 0x023360FC:
            tile = 0x0273C000
            uc.mem_write(tile, bytes(0x20))
            for entity in ENTITIES:
                x, y = struct.unpack("<hh", uc.mem_read(entity + 4, 4))
                if (x, y) == (r0, r1):
                    uc.mem_write(tile + 0xC, struct.pack("<I", entity))
                    break
            value = tile
        elif address in (
            0x020258E4, 0x0234B0B4, 0x022E2AD8, 0x022E4D28, 0x022E4DCC,
            0x022E4E74, 0x022E52F8,
            0x0234B350, 0x022E3AB4, 0x022E6260, 0x022E647C,
            0x0234B084, 0x022FA7DC,
        ):
            value = 0
        else:
            return
        uc.reg_write(UC_ARM_REG_R0, value)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def reset(self):
        self.logs.clear()
        self.monitor = None
        self.uc.mem_write(DUNGEON + 0xCD5E, b"\x00")
        self.uc.mem_write(DUNGEON + 0x12B78, bytes(80))
        for index, (entity, monster) in enumerate(zip(ENTITIES, MONSTERS)):
            self.uc.mem_write(entity, bytes(0xB8))
            self.uc.mem_write(entity, struct.pack("<Ihh", 1, 10 + index, 10))
            self.uc.mem_write(entity + 0xB4, struct.pack("<I", monster))
            self.uc.mem_write(monster, bytes(0x240))
            self.uc.mem_write(monster + 2, struct.pack("<H", 139))
            self.uc.mem_write(monster + 0x10, struct.pack("<HH", 100, 100))
            self.uc.mem_write(monster + 0x24, struct.pack("<6H", *([10] * 6)))
            self.uc.mem_write(DUNGEON + 0x12B78 + index * 4, struct.pack("<I", entity))

    def abilities(self, index, primary, secondary=0):
        self.uc.mem_write(MONSTERS[index] + 0x60, bytes([primary, secondary]))

    def position(self, index, x, y):
        self.uc.mem_write(ENTITIES[index] + 4, struct.pack("<hh", x, y))

    def stage(self, index, offset):
        return struct.unpack("<H", self.uc.mem_read(MONSTERS[index] + offset, 2))[0]

    def call(self, address, *args):
        self.uc.mem_write(STACK, bytes(32))
        self.uc.reg_write(UC_ARM_REG_SP, STACK)
        self.uc.reg_write(UC_ARM_REG_LR, RETURN)
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            self.uc.reg_write(reg, value)
        try:
            self.uc.emu_start(address, RETURN, count=100000)
        except UcError as error:
            raise AssertionError(f"ARM {address:#x} failed at {self.uc.reg_read(UC_ARM_REG_PC):#x}; "
                                 f"r0={self.uc.reg_read(UC_ARM_REG_R0):#x}, "
                                 f"r1={self.uc.reg_read(UC_ARM_REG_R1):#x}") from error
        assert self.uc.reg_read(UC_ARM_REG_PC) == RETURN, hex(self.uc.reg_read(UC_ARM_REG_PC))
        assert self.uc.reg_read(UC_ARM_REG_SP) == STACK
        return self.uc.reg_read(UC_ARM_REG_R0)

    def active(self, index, ability):
        return self.call(0x02301D10, ENTITIES[index], ability)


def check_gas(world):
    count = 0
    for side in (0, 1):
        for legacy_flag in (0, 1, 2):
            for dx, dy in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1), (2, 0), (0, 2), (9, 9)):
                world.reset()
                world.abilities(0, 27)
                world.abilities(1, 160)
                world.position(1, 10 + dx, 10 + dy)
                world.uc.mem_write(MONSTERS[1] + 6, bytes([side]))
                world.uc.mem_write(DUNGEON + 0xCD5E, bytes([legacy_flag]))
                assert world.active(0, 27) == int(max(abs(dx), abs(dy)) > 1)
                assert world.active(1, 160) == 1
                count += 1
    for disabled in ("gastro_acid", "fainted", "invalid_entity", "monitor"):
        if disabled == "monitor" and not world.full_stack:
            continue
        world.reset()
        world.abilities(0, 27)
        world.abilities(1, 160)
        if disabled == "gastro_acid":
            world.uc.mem_write(MONSTERS[1] + 0xD8, b"\x04")
        elif disabled == "fainted":
            world.uc.mem_write(MONSTERS[1] + 0x10, bytes(2))
        elif disabled == "invalid_entity":
            world.uc.mem_write(ENTITIES[1], bytes(4))
        else:
            world.monitor = ENTITIES[1]
        assert world.active(0, 27) == 1, disabled
        count += 1
    world.reset()
    world.abilities(0, 27, 160)
    assert world.active(0, 27) == 1  # no self-suppression
    world.abilities(1, 160)
    assert world.active(0, 27) == 0
    world.position(1, 20, 20)
    assert world.active(0, 27) == 1  # movement takes effect without a flag refresh
    world.position(1, 10, 11)
    assert world.active(0, 27) == 0
    return count + 4


def check_trace(world):
    count = 0
    for mode in ("normal", "gastro_acid", "gas_near", "gas_far", "monitor"):
        if mode == "monitor" and not world.full_stack:
            continue
        for slots in ((40, 0), (0, 40), (40, 40)):
            world.reset()
            world.abilities(0, 27)
            world.abilities(1, *slots)
            if mode == "gastro_acid":
                world.uc.mem_write(MONSTERS[1] + 0xD8, b"\x04")
            elif mode in ("gas_near", "gas_far"):
                world.abilities(2, 160)
                world.position(2, 11, 11 if mode == "gas_near" else 15)
                world.uc.mem_write(DUNGEON + 0xCD5E, b"\x01")
            elif mode == "monitor":
                world.monitor = ENTITIES[1]
            world.call(0x022F94F0, ENTITIES[0], ENTITIES[1], 0)
            expected = list(slots)
            if mode in ("normal", "gas_far"):
                expected[1 if slots[1] == 40 else 0] = 27
            assert list(world.uc.mem_read(MONSTERS[1] + 0x60, 2)) == expected, (mode, slots)
            count += 1
    world.reset()
    world.abilities(0, 27)
    world.abilities(1, 59)  # Color Change must still run when Trace is absent.
    world.uc.mem_write(MONSTERS[1] + 0x164, b"\x01")
    world.uc.mem_write(MONSTERS[1] + 0x5E, b"\x01")
    world.call(0x022F94F0, ENTITIES[0], ENTITIES[1], 0x0273D100)
    assert world.uc.mem_read(MONSTERS[1] + 0x5E, 2) == b"\x0d\x00"
    return count + 1


def check_mirror(world):
    count = 0
    for function, offset in ((0x023135FC, 0x24), (0x02313814, 0x28), (0x0231422C, 0x2C)):
        for category in (0, 1):
            for mode in ("reflect", "no_ability", "gastro_acid", "gas_near", "gas_far", "self",
                         "defiant", "competitive", "double_mirror", "monitor"):
                if mode == "monitor" and not world.full_stack:
                    continue
                world.reset()
                if mode != "no_ability":
                    world.abilities(1, 154)
                if mode == "gastro_acid":
                    world.uc.mem_write(MONSTERS[1] + 0xD8, b"\x04")
                elif mode in ("gas_near", "gas_far"):
                    world.abilities(2, 160)
                    world.position(2, 11, 11 if mode == "gas_near" else 15)
                elif mode == "defiant":
                    world.abilities(0, 150)
                elif mode == "competitive":
                    world.abilities(0, 151)
                elif mode == "double_mirror":
                    world.abilities(0, 154)
                elif mode == "monitor":
                    world.monitor = ENTITIES[1]
                source = ENTITIES[1] if mode == "self" else ENTITIES[0]
                try:
                    world.call(function, source, ENTITIES[1], category, 1)
                except AssertionError as error:
                    raise AssertionError((hex(function), mode, category, str(error))) from error
                reflected = mode in ("reflect", "defiant", "competitive", "gas_far", "double_mirror")
                target = 0 if reflected else 1
                boosted_category = 0 if mode == "defiant" else 1
                response = mode in ("defiant", "competitive")
                expected = 11 if response and offset == 0x24 and category == boosted_category else 9
                assert world.stage(target, offset + category * 2) == expected, (hex(function), mode, category)
                assert world.stage(1 - target, offset + category * 2) == 10
                if response and (offset != 0x24 or category != boosted_category):
                    assert world.stage(0, 0x24 + boosted_category * 2) == 12
                assert all(entity in ENTITIES for entity, _ in world.logs)
                if reflected:
                    globals_ = struct.unpack("<II", world.uc.mem_read(0x023BB478, 8))
                    assert globals_ == (ENTITIES[1], ENTITIES[0])
                    assert world.logs and world.logs[0][0] == ENTITIES[1]
                count += 1
    return count


def check_abilities(rom):
    world = World(rom)
    gas, trace, mirror = check_gas(world), check_trace(world), check_mirror(world)
    print(f"ARM abilities: gas {gas}, Trace {trace}, Mirror Armor {mirror} cases passed")
