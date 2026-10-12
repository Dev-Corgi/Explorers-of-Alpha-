"""Execute Alpha's native enemy appearance/stat transformation on spawn."""
import struct
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *

ENTITY, INFO, SP = 0x02140000, 0x02150000, 0x0273F000


def exercise(rom, ability, fixed_room, candidates=1, species=151):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_map(0x02700000, 0x40000)
    for i in (29, 36):
        ov = rom.loadArm9Overlays()[i]
        uc.mem_write(ov.ramAddress, bytes(ov.data))
    uc.mem_write(ENTITY + 0xB4, struct.pack('<I', INFO))
    uc.mem_write(INFO + 4, struct.pack('<H', 132 if ability == 166 else 223))
    uc.mem_write(INFO + 0x60, bytes([22, ability]))
    uc.reg_write(UC_ARM_REG_CPSR, 0x1F)
    uc.reg_write(UC_ARM_REG_SP, SP)
    uc.reg_write(UC_ARM_REG_R4, ENTITY)
    appearance = []
    stopped = []

    def service(machine, address, size, data):
        r0, r1 = machine.reg_read(UC_ARM_REG_R0), machine.reg_read(UC_ARM_REG_R1)
        if address == 0x023BF928:
            stopped.append(True)
            machine.emu_stop()
            return
        if address == 0x023361D4:
            value = fixed_room
        elif address == 0x022E7C60:
            value = candidates
        elif address == 0x022EAA98:
            assert r0 > 0, 'empty candidate list reached RNG'
            value = 0
        elif address == 0x02054480:
            value = species
        elif address == 0x022F9408:
            value = r1
        elif address == 0x023C0318:
            appearance.append((r0, r1))
            value = 0
        elif address in (0x02052A04, 0x02052A24):
            value = 3 if r1 == 0 else 6
        elif address in (0x022FE350, 0x022FE3B8):
            value = 70 + machine.reg_read(UC_ARM_REG_R2)
        elif address == 0x02303B18:
            machine.mem_write(r0, struct.pack('<4H', 1, 2, 3, 4))
            value = 0
        elif address == 0x020137E8:
            machine.mem_write(r0, struct.pack('<H6x', r1))
            value = 0
        else:
            return
        machine.reg_write(UC_ARM_REG_R0, value)
        machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, service)
    uc.emu_start(0x023BF464, 0, count=5000)
    assert stopped
    return bytes(uc.mem_read(INFO, 0x240)), appearance


def check_spawn_transform(original, patched):
    for ability in (125, 166):
        before, old_appearance = exercise(original, ability, 0)
        assert before[0xEF] == 0 and not old_appearance
        after, appearance = exercise(patched, ability, 0)
        assert struct.unpack_from('<H', after, 4)[0] == 151
        assert after[0xEF] == 2 and after[0xF0] == 127
        assert appearance == [(ENTITY, 151)]
        if ability == 125:
            assert struct.unpack_from('<HH', after, 0x24) == (11, 11)
            assert after[0x60:0x62] == bytes([22, 125])
        else:
            assert after[0x5E:0x60] == bytes([3, 6])
            assert after[0x60:0x62] == bytes([3, 6])
            assert list(after[0x1A:0x1E]) == [70, 71, 70, 71]
            assert [struct.unpack_from('<H', after, 0x124 + i * 8)[0]
                    for i in range(4)] == [1, 2, 3, 4]
        # No valid alternate species: exit without a disguise or bad RNG.
        empty, appearance = exercise(patched, ability, 0, candidates=0)
        assert empty[0xEF] == 0 and not appearance
        same, appearance = exercise(patched, ability, 0,
                                    species=132 if ability == 166 else 223)
        assert same[0xEF] == 0 and not appearance
        # Fixed-room behavior must exactly match Alpha's previous behavior.
        before, old_appearance = exercise(original, ability, 1)
        after, appearance = exercise(patched, ability, 1)
        assert before == after and old_appearance == appearance
    print('Spawn transform: native Illusion/Imposter appearance, stats, moves, empty/same species and fixed rooms passed')
