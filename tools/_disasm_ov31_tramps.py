import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

full=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV36=0x023A7080
f36=full.loadArm9Overlays()[36].data
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)

# orb ov31 trampolines
for addr,name in [(0x23c1c50,"OrbSave"),(0x23c1c60,"OrbAfterAdd"),(0x23c1c88,"OrbAfterAddAlt"),
                  (0x23c2408,"TmMenu"),(0x23c23c8,"TmConfirm")]:
    print(f"\n=== {name} @ {addr:#x} ===")
    for ins in cs.disasm(f36[addr-OV36:addr-OV36+0x40], addr):
        print(f"  {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
