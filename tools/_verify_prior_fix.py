import json, struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

s=json.loads(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.state.json").read_text(encoding="utf-8"))
for m in s["applied"]:
    if m["id"]=="z_move_v2":
        print("z_move", m["version"])
        for d in m.get("data",[]):
            for k,v in d.items():
                if "prior" in k.lower() or "room_charge" in k.lower() or "integration" in k.lower():
                    print(f"  {k}: {v}")

rom=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV36=0x023A7080
f36=rom.loadArm9Overlays()[36].data
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)
# Find PriorGetRoomChargeState target from TryRestoreSlot - bl after pending checks
# Disassemble IsRoomChargeMove original path
print("\n=== IsRoomChargeMove hook ===")
OV29=0x022DC240
f29=rom.loadArm9Overlays()[29].data
for ins in cs.disasm(f29[0x231c3d0-OV29:0x231c3d0-OV29+4], 0x231c3d0):
    print(f"{ins.address:#x}: {ins.mnemonic} {ins.op_str}")
# follow to hook and original
for ins in cs.disasm(f36[0x23c2a54-OV36:0x23c2a54-OV36+0x30], 0x23c2a54):
    print(f"{ins.address:#x}: {ins.mnemonic} {ins.op_str}")
