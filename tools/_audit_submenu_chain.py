import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
OV29, OV36 = 0x022DC240, 0x023A7080
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
full29 = full.loadArm9Overlays()[29].data
full36 = full.loadArm9Overlays()[36].data
van29 = van.loadArm9Overlays()[29].data

def disasm(blob, load, addr, n=0x60):
    off = addr - load
    for ins in cs.disasm(blob[off:off+n], addr):
        print(f"  {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

print("=== orb GetSubMenuStringIdUseBranch @ 0x23c1b08 ===")
disasm(full36, OV36, 0x23c1b08, 0x80)

print("\n=== tm_read CheckReadString @ 0x23c1f20 ===")
disasm(full36, OV36, 0x23c1f20, 0xA0)

print("\n=== z_move entry @ 0x23c2a9c already seen; Prior path ===")
# Trace: 0x23c2a9c cmp r6,#0x2a; beq z; b 0x23c1f20 (tm)
# tm should eventually go to continue. Find bx/b back to 0x22eb2e0 or vanilla body

print("\n=== search ov36 for branches back to GetSubMenuStringId body ===")
targets_of_interest = {0x22eb2e0, 0x22eb2e4, 0x22eb2f8, 0x22eb2dc}
for off in range(0, len(full36)-4, 4):
    w = struct.unpack_from("<I", full36, off)[0]
    if hook_word_kind(w) not in ("b","bl"): continue
    site = OV36+off
    dest = branch_target(site, w)
    if dest in targets_of_interest or (0x22eb2c8 <= dest <= 0x22eb360):
        print(f"  {site:#x} -> {dest:#x}")

# Also check what vanilla cmp r6,#0x26 meant - action 0x26
# B button treasure bag - action IDs?
print("\n=== UseItemBeforeUsedMoveMessage hooks (replaced mov r0,r6) ===")
for addr in [0x2322608, 0x2322670, 0x23226a8]:
    vw = struct.unpack_from("<I", van29, addr-OV29)[0]
    fw = struct.unpack_from("<I", full29, addr-OV29)[0]
    print(f"{addr:#x}: van={vw:#010x} full={fw:#010x} tgt={branch_target(addr,fw):#x}")
    print("  van context:")
    disasm(van29, OV29, addr-0x10, 0x30)
    print("  full:")
    disasm(full29, OV29, addr-0x10, 0x30)

print("\n=== ZMove_BeforeUsedMoveMessage @ 0x23c2dac ===")
disasm(full36, OV36, 0x23c2dac, 0x60)
