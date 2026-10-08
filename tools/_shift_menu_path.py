import sys, struct, json
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

# GetSubMenuStringId: what string IDs can the chain return?
# Also check z_move STRING_ID and wrong returns
rom=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV36=0x023A7080
f36=rom.loadArm9Overlays()[36].data
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)

# ZMove_GetSubMenuStringIdHook and ReturnZMoveString pools
print("=== submenu string path ===")
for addr in [0x23c2aa8, 0x23c2ab4, 0x23c1f20, 0x23c1b08]:
    print(f"\n--- {addr:#x} ---")
    for ins in cs.disasm(f36[addr-OV36:addr-OV36+0x50], addr):
        print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# Search string id literals near z_move / tm / orb in caves
s=json.loads(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.state.json").read_text(encoding="utf-8"))
# look for STRING_ID in z_move asm
from pathlib import Path as P
for p in P(r"true_patches/z_move_v2").rglob("*.asm"):
    t=p.read_text(encoding="utf-8",errors="replace")
    for i,l in enumerate(t.splitlines(),1):
        if "STRING" in l or "1910" in l or "Shift" in l:
            print(f"{p.name}:{i}: {l.strip()}")
