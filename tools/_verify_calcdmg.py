import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target

rom=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV29,OV36=0x022DC240,0x023A7080
f29=rom.loadArm9Overlays()[29].data
f36=rom.loadArm9Overlays()[36].data
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)

w=struct.unpack_from("<I", f29, 0x230bca8-OV29)[0]
tgt=branch_target(0x230bca8, w)
print(f"CalcDamage beq -> {tgt:#x}")
print("target disasm:")
for ins in cs.disasm(f36[tgt-OV36:tgt-OV36+0x40], tgt):
    print(f"  {ins.address:#x}: {ins.mnemonic} {ins.op_str}")
