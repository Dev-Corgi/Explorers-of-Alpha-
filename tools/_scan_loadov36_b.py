import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_rom_profile, resolve_symbol
from patch_engine.hook_registry import branch_target, hook_word_kind

rom = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
ov29 = rom.loadArm9Overlays([29])[29].data
ov36 = rom.loadArm9Overlays([36])[36].data
arm9 = bytes(rom.arm9)
OV29, OV36 = 0x022DC240, 0x023A7080
prof = load_rom_profile(Path("true_patches/engine"), "us_vanilla")
LoadOverlay = resolve_symbol(prof, "LoadOverlay")
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

print("=== ov29 BL LoadOverlay sites + context ===")
for off in range(0, len(ov29)-4, 4):
    w = struct.unpack_from("<I", ov29, off)[0]
    if hook_word_kind(w) != "bl":
        continue
    site = OV29 + off
    if branch_target(site, w) != LoadOverlay:
        continue
    print(f"\n--- site {site:#x} ---")
    start = max(0, off-0x40)
    for ins in cs.disasm(ov29[start:off+0x20], OV29+start):
        mark = ">>>" if ins.address == site else "   "
        print(f"{mark} {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# Check LOADED_OVERLAY_GROUP / overlay info for 36
print("\n=== overlay table entry 36 vs 29/31 ===")
from ndspy.code import loadOverlayTable
# parse from ROM
table = rom.arm9OverlayTable
# ndspy NintendoDSRom has overlays
info = {}
for i, ov in enumerate(rom.loadArm9Overlays()):
    if ov is None: continue
    if i in (10, 29, 31, 34, 35, 36):
        print(f"ov{i}: ram={ov.ramAddress:#x} size={ov.ramSize:#x} bss={ov.bssSize:#x} fileID={ov.fileID}")

# Search for mov r0,#0x24 (36) near LoadOverlay in arm9+ov29 via different patterns
print("\n=== mov/mvn r0,#36 then nearby LoadOverlay ===")
for label, blob, load in [("arm9", arm9, 0x02000000), ("ov29", ov29, OV29), ("ov36", ov36, OV36)]:
    for off in range(0, len(blob)-4, 4):
        w = struct.unpack_from("<I", blob, off)[0]
        # mov r0, #36 = E3A00024
        if w in (0xE3A00024, 0xE3A01024, 0xE3A02024):
            # search forward 0x30 for bl LoadOverlay
            for j in range(off, min(len(blob)-4, off+0x40), 4):
                wj = struct.unpack_from("<I", blob, j)[0]
                if hook_word_kind(wj)=="bl" and branch_target(load+j, wj)==LoadOverlay:
                    print(f"{label} mov#36 @{load+off:#x} bl LoadOverlay @{load+j:#x}")
