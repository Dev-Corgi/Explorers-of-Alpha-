import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
OV29, OV36, ARM9 = 0x022DC240, 0x023A7080, 0x02000000
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

def find_refs(blob, load, target, label):
    refs = []
    for off in range(0, len(blob)-4, 4):
        w = struct.unpack_from("<I", blob, off)[0]
        # branch
        if hook_word_kind(w) in ("b","bl"):
            if branch_target(load+off, w) == target:
                refs.append((load+off, "branch"))
        # literal pointer
        if w == target:
            refs.append((load+off, "literal"))
    print(f"{label} refs to {target:#x}: {len(refs)}")
    for a,k in refs[:30]:
        print(f"  {a:#x} {k}")
    return refs

full29 = full.loadArm9Overlays()[29].data
full36 = full.loadArm9Overlays()[36].data
full31 = full.loadArm9Overlays()[31].data
arm9 = bytes(full.arm9)
van29 = van.loadArm9Overlays()[29].data

for t in [0x0231C3D0, 0x0231C3D4]:
    print(f"\n===== target {t:#x} =====")
    find_refs(full29, OV29, t, "ov29")
    find_refs(full36, OV36, t, "ov36")
    find_refs(full31, 0x02382820, t, "ov31")
    find_refs(arm9, ARM9, t, "arm9")
    find_refs(van29, OV29, t, "van29")

# Disassemble ZMove_IsRoomChargeMoveHook
print("\n=== ZMove_IsRoomChargeMoveHook @ 0x23c2a54 ===")
for ins in cs.disasm(full36[0x23c2a54-OV36:0x23c2a54-OV36+0x40], 0x23c2a54):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# What is at PriorIsRoomChargeMove pool value in z_move cave
# search for 0x231C3D4 literal in ov36
print("\n=== literals 0x231C3D0/D4 in ov36 ===")
for off in range(0, len(full36)-4, 4):
    w = struct.unpack_from("<I", full36, off)[0]
    if w in (0x0231C3D0, 0x0231C3D4):
        print(f"  {OV36+off:#x}: {w:#x}")

# Compare no_rc_zm IsRoomChargeMove site
norc = NintendoDSRom(Path(r"Export Rom/_full_stack_no_rc_zm.nds").read_bytes())
norc29 = norc.loadArm9Overlays()[29].data
w = struct.unpack_from("<I", norc29, 0x231c3d0-OV29)[0]
print(f"\nno_rc_zm @ 0x231c3d0: {w:#010x}")
# does no_rc have z_move? no - so should be zero
# Check only-zmove ROM if exists
