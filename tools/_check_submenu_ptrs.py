import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

# Verify DungeonSubMenu pointers used by z_move against vanilla AddDungeonSubMenuOption
van=NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
OV29=0x022DC240
v29=van.loadArm9Overlays()[29].data
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)

print("=== AddDungeonSubMenuOption 0x22eb81c ===")
for ins in cs.disasm(v29[0x22eb81c-OV29:0x22eb81c-OV29+0x80], 0x22eb81c):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# pools after function
print("\nliterals near end:")
for off in range(0x22eb890-OV29, 0x22eb8b0-OV29, 4):
    w=struct.unpack_from("<I", v29, off)[0]
    print(f"  {OV29+off:#x}: {w:#010x}")
