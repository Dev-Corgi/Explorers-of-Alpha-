import sys, struct, json
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

rom = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
OV29, OV36 = 0x022DC240, 0x023A7080
LoadOverlay, OverlayIsLoaded, UnloadOverlay = 0x020040AC, 0x02003ED0, 0x02004868
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

def scan(blob, load, label):
    """Find mov/ldr of #0x24 within 0x30 bytes before bl LoadOverlay/OverlayIsLoaded/UnloadOverlay."""
    hits = []
    for off in range(0, len(blob)-4, 4):
        w = struct.unpack_from("<I", blob, off)[0]
        if hook_word_kind(w) not in ("bl", "b"):
            continue
        site = load + off
        dest = branch_target(site, w)
        if dest not in (LoadOverlay, OverlayIsLoaded, UnloadOverlay):
            continue
        # look back for #0x24 in registers
        window = blob[max(0,off-0x40):off+4]
        base = load + max(0,off-0x40)
        saw24 = False
        for ins in cs.disasm(window, base):
            if ins.address >= site:
                break
            if "#0x24" in ins.op_str or "#36" in ins.op_str:
                saw24 = True
        if saw24:
            api = {LoadOverlay:"LoadOverlay", OverlayIsLoaded:"OverlayIsLoaded", UnloadOverlay:"UnloadOverlay"}[dest]
            hits.append((site, api))
    print(f"{label}: {len(hits)} sites with #0x24 near overlay API")
    for site, api in hits:
        print(f"  {site:#010x} -> {api}")
        start = site - load - 0x30
        for ins in cs.disasm(blob[max(0,start):site-load+8], load+max(0,start)):
            mark = ">>>" if ins.address==site else "   "
            print(f"  {mark} {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
    return hits

for name, r in [("VANILLA", van), ("FULL", rom)]:
    print(f"\n======== {name} ========")
    ov29 = r.loadArm9Overlays([29])[29].data
    ov36 = r.loadArm9Overlays([36])[36].data if 36 in r.loadArm9Overlays() else b""
    # loadArm9Overlays returns dict-like?
    ovs = r.loadArm9Overlays()
    ov29 = ovs[29].data
    ov36 = ovs[36].data if 36 in ovs else b""
    arm9 = bytes(r.arm9)
    scan(arm9, 0x02000000, "arm9")
    scan(ov29, OV29, "ov29")
    if ov36:
        scan(ov36, OV36, "ov36")

# Check RunDungeon + leftover stub region
print("\n======== RunDungeon / stub region FULL ========")
ov29 = rom.loadArm9Overlays()[29].data
for addr in [0x022DEF38, 0x0231C3D4, 0x0231C404, 0x0231C428]:
    off = addr - OV29
    if 0 <= off < len(ov29)-4:
        w = struct.unpack_from("<I", ov29, off)[0]
        print(f"{addr:#x}: {w:#010x}")
        for ins in cs.disasm(ov29[off:off+0x20], addr):
            print(f"  {ins.address:#010x}: {ins.mnemonic} {ins.op_str}")

# Who xrefs 0x231C3D4 / 0x231C404 in ov29?
print("\n======== xrefs to old EnsureOv36 stubs ========")
for target in [0x0231C3D4, 0x0231C404, 0x0231C428]:
    refs = []
    for off in range(0, len(ov29)-4, 4):
        w = struct.unpack_from("<I", ov29, off)[0]
        if hook_word_kind(w) not in ("bl","b"):
            continue
        site = OV29+off
        if branch_target(site, w) == target:
            refs.append(site)
    print(f"refs to {target:#x}: {len(refs)} {[hex(x) for x in refs[:10]]}")

# Check LOADED_OVERLAY_GROUP_0 pointer used by LoadOverlay case
print("\n======== group0 store ptr in LoadOverlay ========")
# at 0x2004174: ldr r0,[pc,#0x634] ; pc+8+0x634
pc = 0x2004174
pool = pc + 8 + 0x634
w = struct.unpack_from("<I", bytes(rom.arm9), pool-0x02000000)[0]
print(f"group ptr literal @ {pool:#x} = {w:#x}")
