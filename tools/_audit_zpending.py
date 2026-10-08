import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV36=0x023A7080
f36=full.loadArm9Overlays()[36].data
cs=Cs(CS_ARCH_ARM, CS_MODE_ARM)

# Find BSS / flag addresses from pools near pending checks
# Disassemble SetAction / append Z option and confirm path
print("=== ZMove_TryAppendZMoveOption @ 0x23c2ab0 ===")
for ins in cs.disasm(f36[0x23c2ab0-OV36:0x23c2ab0-OV36+0x80], 0x23c2ab0):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

print("\n=== ZMove_SetActionFieldDispatch @ 0x23c2e28 ===")
for ins in cs.disasm(f36[0x23c2e28-OV36:0x23c2e28-OV36+0x80], 0x23c2e28):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# Scan for stores to pending flag - find literal pool addresses used with strb
print("\n=== search strb to flag-like addresses near ZMovePending ===")
# From IsRoomChargeMove: ldr r1,[pc,#0x428] at 0x23c2a54 -> pool
pc=0x23c2a54
imm=0x428
pool=pc+8+imm
w=struct.unpack_from("<I", f36, pool-OV36)[0]
print(f"PendingFlag ptr from IRC hook pool @ {pool:#x} = {w:#x}")

# Get all unique low WRAM/ov36 static addrs from pools in z_move cave
cave_start=0x23c27f4
cave_end=0x23c47f4
addrs=set()
for off in range(cave_start-OV36, cave_end-OV36, 4):
    w=struct.unpack_from("<I", f36, off)[0]
    if 0x023C0000 <= w <= 0x023E0000 or 0x022B0000 <= w <= 0x022C0000:
        addrs.add(w)
print("static-ish literals in z_move cave:")
for a in sorted(addrs):
    print(f"  {a:#x}")
