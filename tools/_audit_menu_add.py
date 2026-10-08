import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

full=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
van=NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
OV29=0x022DC240
f29,v29=full.loadArm9Overlays()[29].data, van.loadArm9Overlays()[29].data
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)

# 0x22eb81c and 0x22eb408 - what are they
for addr in [0x22eb81c, 0x22eb408, 0x22eb9a0]:
    print(f"\n=== van @ {addr:#x} ===")
    for ins in cs.disasm(v29[addr-OV29:addr-OV29+0x30], addr):
        print(f"  {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# ov31 ZMoveMenuHook site context
OV31=0x02382820
f31,v31=full.loadArm9Overlays()[31].data, van.loadArm9Overlays()[31].data
print("\n=== ov31 ZMoveMenuHook 0x23859c0 van ===")
for ins in cs.disasm(v31[0x23859a0-OV31:0x2385a00-OV31], 0x23859a0):
    mark=">>>" if ins.address==0x23859c0 else "   "
    print(f"{mark} {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
print("full:")
for ins in cs.disasm(f31[0x23859a0-OV31:0x2385a00-OV31], 0x23859a0):
    mark=">>>" if ins.address==0x23859c0 else "   "
    print(f"{mark} {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

print("\n=== ov31 confirm 0x2385fc0 ===")
for ins in cs.disasm(v31[0x2385fa0-OV31:0x2385ff0-OV31], 0x2385fa0):
    mark=">>>" if ins.address==0x2385fc0 else "   "
    print(f"{mark} {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
print("full:")
for ins in cs.disasm(f31[0x2385fa0-OV31:0x2385ff0-OV31], 0x2385fa0):
    mark=">>>" if ins.address==0x2385fc0 else "   "
    print(f"{mark} {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
