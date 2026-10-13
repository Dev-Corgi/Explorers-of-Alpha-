"""Execute Alpha's native story cap and following difficulty setup in ARM.

The real difficulty decoder runs; script flags and entity validation use
fixtures. No full-stack build or ROM file is written.
"""
import struct

from ndspy.code import loadOverlayTable
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

START, CONTINUE, STOP = 0x023AA0D8, 0x023AA1E0, 0x023AA294
DUNGEON, ENTITIES, INFO, STACK = 0x02100000, 0x02110000, 0x02120000, 0x02702000


def machine(rom):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_map(0x02700000, 0x4000)
    ovs = loadOverlayTable(rom.arm9OverlayTable, lambda _, n: rom.files[n])
    uc.mem_write(0x02000000, bytes(rom.arm9))
    uc.mem_write(ovs[36].ramAddress, bytes(ovs[36].data))
    uc.mem_write(0x02353538, struct.pack('<I', DUNGEON))
    return uc


def check_stat_caps(original, patched):
    old, new = machine(original), machine(patched)
    original_cap = bytes(old.mem_read(START, 4)) == struct.pack('<I', 0xE3A07000)
    assert original_cap or bytes(old.mem_read(START, 4)) == struct.pack('<I', 0xEA000040)
    assert bytes(new.mem_read(START, 4)) == struct.pack('<I', 0xEA000040)
    state = {}
    following_writes, following_phase = {}, {}

    def service(uc, address, size, data):
        if address == CONTINUE:
            following_phase[id(uc)] = True
        if address == 0x0204B678:
            flag = uc.reg_read(UC_ARM_REG_R2)
            assert uc.reg_read(UC_ARM_REG_R1) == 78
            flags = {55 + state['difficulty']: 1, 17: int(state['story'] >= 1),
                     18: int(state['story'] >= 2)}
            uc.reg_write(UC_ARM_REG_R0, flags.get(flag, 0))
        elif address == 0x022E95F4:
            uc.reg_write(UC_ARM_REG_R0, int(uc.reg_read(UC_ARM_REG_R0) != 0))
        else:
            return
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    old.hook_add(UC_HOOK_CODE, service)
    new.hook_add(UC_HOOK_CODE, service)
    def writes(uc, access, address, size, value, data):
        if following_phase[id(uc)] and not 0x02700000 <= address < 0x02704000:
            following_writes[id(uc)].append((address, size, value))

    old.hook_add(UC_HOOK_MEM_WRITE, writes)
    new.hook_add(UC_HOOK_MEM_WRITE, writes)
    count = 0
    # Includes small V values with large CalcStat HP, cap boundaries and
    # ordinary Alpha stats. Exempt species rotate across every active slot.
    species = (25, 133, 192, 530, 543)
    values = (0, 5, 25, 89, 90, 91, 119, 120, 121, 149, 150, 151, 179, 180, 181, 255)
    for difficulty in range(1, 5):
        for story in range(3):
            state.update(difficulty=difficulty, story=story)
            cap = (90 if story == 0 else 150) + (30 if difficulty == 3 else 0)
            capped = difficulty >= 3 and story < 2
            for rotation in range(len(species)):
                for v in values:
                    records = []
                    for slot in range(4):
                        record = bytearray(0x240)
                        kind = species[(slot + rotation) % len(species)]
                        struct.pack_into('<H', record, 2, kind)
                        hp = (100, cap + 49, cap + 51, 1000)[slot]
                        struct.pack_into('<HH', record, 16, 50, hp)
                        record[26:30] = bytes([min(255, v + slot)] * 4)
                        record[32:36] = b'\x71\x82\x93\xA4'
                        records.append(bytes(record))
                    for uc, fixed in ((old, False), (new, True)):
                        following_phase[id(uc)] = False
                        following_writes[id(uc)] = []
                        for slot, record in enumerate(records):
                            entity, info = ENTITIES + slot * 0x100, INFO + slot * 0x400
                            uc.mem_write(DUNGEON + 0x12B28 + slot * 4, struct.pack('<I', entity))
                            uc.mem_write(entity + 0xB4, struct.pack('<I', info))
                            uc.mem_write(info, record)
                        uc.reg_write(UC_ARM_REG_SP, STACK)
                        uc.reg_write(UC_ARM_REG_R8, 0x02353538)
                        # Continue through the real post-cap difficulty writes.
                        uc.emu_start(START, STOP, count=10000)
                        assert uc.reg_read(UC_ARM_REG_PC) == STOP
                        assert uc.reg_read(UC_ARM_REG_SP) == STACK
                        for slot, record in enumerate(records):
                            expected = bytearray(record)
                            kind = struct.unpack_from('<H', record, 2)[0]
                            if not fixed and original_cap and capped and kind not in (192, 530, 543):
                                expected[26:30] = bytes(min(x, cap) for x in record[26:30])
                                hp = min(struct.unpack_from('<H', record, 18)[0], cap + 50)
                                struct.pack_into('<H', expected, 18, hp)
                            assert bytes(uc.mem_read(INFO + slot * 0x400, len(record))) == expected
                    # The post-cap setup writes the same difficulty constants.
                    assert following_writes[id(old)]
                    assert following_writes[id(old)] == following_writes[id(new)]
                    count += 1
    print(f'Story caps: {count} ARM cases; Expert/Hardcore boundaries reproduced, all member V/HP preserved, following difficulty setup unchanged')
