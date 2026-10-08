import sys, struct, json
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_rom_profile, resolve_symbol
from patch_engine.hook_registry import branch_target, hook_word_kind

rom = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
state = json.loads(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.state.json").read_text(encoding="utf-8"))
ov29 = bytearray(rom.loadArm9Overlays([29])[29].data)
ov36 = rom.loadArm9Overlays([36])[36].data
arm9 = bytes(rom.arm9)
OV29, OV36, ARM9 = 0x022DC240, 0x023A7080, 0x02000000
prof = load_rom_profile(Path("true_patches/engine"), "us_vanilla")
LoadOverlay = resolve_symbol(prof, "LoadOverlay")
OverlayIsLoaded = resolve_symbol(prof, "OverlayIsLoaded")
print(f"LoadOverlay={LoadOverlay:#x} OverlayIsLoaded={OverlayIsLoaded:#x}")

cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

def find_bl_to(blob, load, target, name):
    hits = []
    for off in range(0, len(blob)-4, 4):
        w = struct.unpack_from("<I", blob, off)[0]
        if hook_word_kind(w) != "bl":
            continue
        site = load + off
        if branch_target(site, w) == target:
            hits.append(site)
    print(f"{name}: {len(hits)} BL -> {target:#x}")
    return hits

# Find literal pools that load #36 then call LoadOverlay nearby
def find_loadoverlay_36(blob, load, label):
    hits = []
    for off in range(0, len(blob)-4, 4):
        w = struct.unpack_from("<I", blob, off)[0]
        if w != 36:
            continue
        # look back for ldr that points to this literal, then nearby bl LoadOverlay
        lit_addr = load + off
        for i in range(max(0, off-0x80), off, 4):
            wi = struct.unpack_from("<I", blob, i)[0]
            if (wi & 0x0FFF0000) != 0x059F0000:  # ldr rt,[pc,#imm] approx
                continue
            # more precise: ldr rt, [pc, #imm] encoding
            if ((wi >> 16) & 0x0FFF) not in range(0x59F0, 0x59FF+1) and (wi & 0x0F7F0000) != 0x051F0000:
                # standard LDR literal: cond 0101 1001 xxxx = 0xE59Fxxxx for ldr
                if (wi & 0x0FFF0000) != 0x059F0000:
                    continue
            imm = wi & 0xFFF
            site = load + i
            pool = (site + 8) + imm  # U=1
            # also check U=0 subtract
            if (wi & (1<<23)) == 0:
                pool = (site + 8) - imm
            if pool != lit_addr:
                continue
            # scan forward for bl LoadOverlay within 0x40
            for j in range(i, min(len(blob)-4, i+0x60), 4):
                wj = struct.unpack_from("<I", blob, j)[0]
                if hook_word_kind(wj) == "bl" and branch_target(load+j, wj) == LoadOverlay:
                    hits.append((site, load+j, "ldr+#36 then bl LoadOverlay"))
                    break
                if hook_word_kind(wj) == "bl" and branch_target(load+j, wj) == OverlayIsLoaded:
                    # also note OverlayIsLoaded(36) patterns
                    hits.append((site, load+j, "ldr+#36 then bl OverlayIsLoaded"))
                    break
    print(f"{label} LoadOverlay/IsLoaded(36) patterns: {len(hits)}")
    for h in hits[:30]:
        print(f"  ldr@{h[0]:#x} bl@{h[1]:#x} {h[2]}")
    return hits

print("=== arm9 ===")
find_loadoverlay_36(arm9, ARM9, "arm9")
print("=== ov29 ===")
h29 = find_loadoverlay_36(ov29, OV29, "ov29")
print("=== ov36 ===")
h36 = find_loadoverlay_36(ov36, OV36, "ov36")

# Also BL LoadOverlay count in each
find_bl_to(arm9, ARM9, LoadOverlay, "arm9 BL LoadOverlay")
find_bl_to(ov29, OV29, LoadOverlay, "ov29 BL LoadOverlay")
find_bl_to(ov36, OV36, LoadOverlay, "ov36 BL LoadOverlay")
