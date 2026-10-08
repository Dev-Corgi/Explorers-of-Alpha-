import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

# Count ov31 -> ov36 vs ov31 -> ov29 branches in full_stack
full=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV29,OV31,OV36=0x022DC240,0x02382820,0x023A7080
f31=full.loadArm9Overlays()[31].data
to36=to29=other=[]
to36=[]; to29=[]; other=[]
for off in range(0,len(f31)-4,4):
    w=struct.unpack_from("<I", f31, off)[0]
    if hook_word_kind(w) not in ("b","bl"): continue
    site=OV31+off
    dest=branch_target(site,w)
    if OV36 <= dest < OV36+0x40000:
        to36.append((site,dest))
    elif OV29 <= dest < OV29+0x80000:
        to29.append((site,dest))
print(f"ov31 branches to ov36: {len(to36)}")
for s,d in to36: print(f"  {s:#x} -> {d:#x}")
print(f"ov31 branches to ov29: {len(to29)}")
for s,d in to29[:10]: print(f"  {s:#x} -> {d:#x}")

# ov29 hooks to ov36 count
f29=full.loadArm9Overlays()[29].data
n=0
sites=[]
for off in range(0,len(f29)-4,4):
    w=struct.unpack_from("<I", f29, off)[0]
    if hook_word_kind(w) not in ("b","bl"): continue
    site=OV29+off
    dest=branch_target(site,w)
    if OV36 <= dest < OV36+0x40000:
        n+=1
        sites.append((site,dest))
print(f"\nov29 branches to ov36: {n}")
for s,d in sites[:25]:
    print(f"  {s:#x} -> {d:#x}")
