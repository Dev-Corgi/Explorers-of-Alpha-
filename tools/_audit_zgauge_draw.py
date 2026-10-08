import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV36=0x023A7080
f36=full.loadArm9Overlays()[36].data
cs=Cs(CS_ARCH_ARM, CS_MODE_ARM)

print("=== ZMove_DrawZGaugeHudMenuMoneyRow / draw path 0x23c2948 ===")
for ins in cs.disasm(f36[0x23c2940-OV36:0x23c29a8-OV36], 0x23c2940):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# Check GetMoney 0x200ecfc - does it need specific regs?
arm9=bytes(full.arm9)
print("\n=== GetMoney @ 0x200ecfc ===")
for ins in cs.disasm(arm9[0x200ecfc-0x2000000:0x200ecfc-0x2000000+0x40], 0x200ecfc):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# ACTION ids used by patches
print("\n=== search ACTION / menu id constants in z_move asm ===")
from pathlib import Path as P
for p in P(r"true_patches/z_move_v2/asm").rglob("*.asm"):
    t=p.read_text(encoding="utf-8", errors="replace")
    for i,l in enumerate(t.splitlines(),1):
        if "ACTION" in l or "0x2a" in l or "0x26" in l or "0x28" in l or "BAG" in l.upper() or "TREASURE" in l.upper():
            print(f"{p.name}:{i}: {l.strip()}")
