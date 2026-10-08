import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

# What are tm_read stubs at 0x23C1EF8?
full=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV36=0x023A7080
f36=full.loadArm9Overlays()[36].data
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)
print("=== tm_read room_charge stubs ===")
for ins in cs.disasm(f36[0x23c1ef8-OV36:0x23c1f24-OV36], 0x23c1ef8):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# What's at 0x231C47C in full?
OV29=0x022DC240
f29=full.loadArm9Overlays()[29].data
print("\n=== ov29 @ 0x231C3D0..0x231C4A0 ===")
for off in range(0x231c3d0, 0x231c4a0, 4):
    w=struct.unpack_from("<I", f29, off-OV29)[0]
    if w:
        print(f"{off:#x}: {w:#010x}")
