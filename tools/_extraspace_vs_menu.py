import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

rom = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
arm9f, arm9v = bytes(rom.arm9), bytes(van.arm9)
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
LoadOverlay, OverlayIsLoaded = 0x020040AC, 0x02003ED0

# Diff arm9 around LoadOverlay / OverlayIsLoaded / NitroMain
print("arm9 size", len(arm9f), len(arm9v))
diff_regions = []
i = 0
while i < min(len(arm9f), len(arm9v)):
    if arm9f[i] != arm9v[i]:
        j = i
        while j < min(len(arm9f), len(arm9v)) and arm9f[j] != arm9v[j]:
            j += 1
        # extend a bit
        diff_regions.append((0x02000000+i, 0x02000000+j, j-i))
        i = j
    else:
        i += 1
print(f"arm9 diff regions: {len(diff_regions)}")
# show diffs near overlay APIs or large ones
for start, end, sz in diff_regions:
    if sz >= 16 or (0x02003E00 <= start <= 0x02005000) or (0x020AF200 <= start <= 0x020AF300):
        print(f"  {start:#x}..{end:#x} ({sz}B)")

# Check if LoadOverlay itself patched
print("\nLoadOverlay identical?", arm9f[0x40AC:0x40AC+0x200]==arm9v[0x40AC:0x40AC+0x200])
print("OverlayIsLoaded identical?", arm9f[0x3ED0:0x3ED0+0x180]==arm9v[0x3ED0:0x3ED0+0x180])

# Search both for 0x23A7080 and overlay id 36 in ExtraSpace boot
for label, arm9 in [("full", arm9f), ("van", arm9v)]:
    hits36 = [0x02000000+o for o in range(0,len(arm9)-4,4) if struct.unpack_from("<I",arm9,o)[0]==0x023A7080]
    print(f"{label} literals 0x23A7080:", [hex(h) for h in hits36[:10]], "count", len(hits36))

# Compare ov36 content start - is ExtraSpace payload present?
ov36f = rom.loadArm9Overlays()[36].data
ov36v = van.loadArm9Overlays()[36].data
print(f"ov36 size full={len(ov36f)} van={len(ov36v)}")
print(f"ov36 full first32", ov36f[:32].hex())
print(f"ov36 van first32", ov36v[:32].hex())
# nonzero in van?
print("van ov36 nonzero bytes", sum(1 for b in ov36v if b))
print("full ov36 nonzero", sum(1 for b in ov36f if b))

# Z-move dungeon menu HUD - does it live in ov36 and get called from ov31?
# If ov31 BL to ov36, and something wrong with inter-overlay calls after menu load...
print("\n=== ov31 BL targets into ov36 range ===")
ov31 = rom.loadArm9Overlays()[31].data
OV31 = 0x02382820
refs = []
for off in range(0, len(ov31)-4, 4):
    w = struct.unpack_from("<I", ov31, off)[0]
    if hook_word_kind(w) not in ("bl","b"):
        continue
    dest = branch_target(OV31+off, w)
    if 0x023A7080 <= dest < 0x023E0000:
        refs.append((OV31+off, dest))
print(f"ov31->ov36 branches: {len(refs)}")
for s,d in refs[:20]:
    print(f"  {s:#x} -> {d:#x}")
