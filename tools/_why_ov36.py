import sys, json, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable

full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
state = json.loads(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.state.json").read_text(encoding="utf-8"))
table = loadOverlayTable(full.arm9OverlayTable, lambda i,n: b"")
ov36 = full.loadArm9Overlays()[36].data
OV36 = 0x023A7080

print("=== ov36 overlay table ===")
e = table[36]
print(f"ram={e.ramAddress:#x} ramSize={e.ramSize:#x} end={e.ramAddress+e.ramSize:#x}")
print(f"file size={len(ov36):#x} bssSize={e.bssSize:#x}")
print(f"staticInit {e.staticInitStart:#x}..{e.staticInitEnd:#x}")

print("\n=== packed ov36 caves (from state) ===")
caves=[]
for m in state["applied"]:
    for c in m.get("caves",[]):
        if c["overlay"]=="ov36":
            caves.append((m["id"], c["file_offset"], c["size"], c["load_address"]))
caves.sort(key=lambda x: x[1])
for i,(mid,fo,sz,la) in enumerate(caves):
    end=la+sz
    nz=sum(1 for b in ov36[fo:fo+sz] if b)
    gap=""
    if i+1 < len(caves):
        nfo=caves[i+1][1]
        gap_bytes=nfo-(fo+sz)
        gap=f" gap_to_next={gap_bytes}"
        if gap_bytes < 0:
            gap=" OVERLAP!"
    # check trailing bytes of allocation that are still zero (slack)
    slack=0
    for j in range(sz-1,-1,-1):
        if ov36[fo+j]==0: slack+=1
        else: break
    print(f"{mid:16} file={fo:#x} ram={la:#x}..{end:#x} used~{nz} slack_tail={slack}{gap}")

# Check if any module's code has bl/b targets landing in ANOTHER module's cave
from patch_engine.hook_registry import branch_target, hook_word_kind
print("\n=== cross-cave branches inside ov36 ===")
ranges=[(mid,la,la+sz) for mid,fo,sz,la in caves]
for mid,fo,sz,la in caves:
    blob=ov36[fo:fo+sz]
    cross=[]
    for off in range(0,len(blob)-4,4):
        w=struct.unpack_from("<I", blob, off)[0]
        if hook_word_kind(w) not in ("b","bl"): continue
        site=la+off
        dest=branch_target(site,w)
        if not (OV36 <= dest < OV36+len(ov36)):
            continue
        owner=None
        for om,ol,oh in ranges:
            if ol <= dest < oh:
                owner=om
                break
        if owner and owner!=mid:
            cross.append((site, dest, owner))
    if cross:
        print(f"{mid}: {len(cross)} branches into other caves")
        for s,d,o in cross[:15]:
            print(f"  {s:#x} -> {d:#x} ({o})")
