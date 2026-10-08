import sys, json, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from patch_engine.cave_xref import slot_has_vanilla_xrefs, format_xref_report
from patch_engine.ov29_layout import cave_overlaps_item_start, cave_overlaps_start_mfunc
from patch_engine.cave_allocator import CaveSlot

van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
state = json.loads(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.state.json").read_text(encoding="utf-8"))
van_ov29 = van.loadArm9Overlays()[29].data
van_arm9 = bytes(van.arm9)
full_ov29 = full.loadArm9Overlays()[29].data
full_ov36 = full.loadArm9Overlays()[36].data
van_ov36 = van.loadArm9Overlays()[36].data
OV29, OV36 = 0x022DC240, 0x023A7080

print("=== applied modules / caves ===")
for m in state["applied"]:
    print(f"\n{m['id']} v{m['version']}")
    for c in m.get("caves", []):
        ov = c["overlay"]
        fo, sz, la = c["file_offset"], c["size"], c["load_address"]
        print(f"  {ov} file={fo:#x} size={sz} ram={la:#x}..{la+sz:#x}")
        if ov == "ov29":
            slot = CaveSlot(file_offset=fo, size=sz, load_address=la)
            print(f"    item_start_overlap={cave_overlaps_item_start(slot)} start_mfunc_overlap={cave_overlaps_start_mfunc(slot)}")
            ok, xrefs = slot_has_vanilla_xrefs(van_ov29, OV29, fo, sz, arm9_data=van_arm9)
            if not ok:
                print("    VANILLA XREF INVASION:")
                print(format_xref_report(xrefs, overlay_load=OV29, slot_file_offset=fo, slot_size=sz)[:800])
            else:
                print(f"    vanilla_xrefs=OK ({len(xrefs)} refs scanned clean)")
        elif ov == "ov36":
            # compare to vanilla zeros
            chunk_v = van_ov36[fo:fo+sz] if fo+sz <= len(van_ov36) else b""
            chunk_f = full_ov36[fo:fo+sz]
            nz_v = sum(1 for b in chunk_v if b)
            print(f"    vanilla_nonzero_in_slot={nz_v}/{sz} patched_nonzero={sum(1 for b in chunk_f if b)}")

# Cave pairwise overlaps
print("\n=== cave pairwise overlaps ===")
caves = []
for m in state["applied"]:
    for c in m.get("caves", []):
        caves.append((m["id"], c["overlay"], c["file_offset"], c["size"], c["load_address"]))
for i,(a_id,a_ov,a_fo,a_sz,a_la) in enumerate(caves):
    for b_id,b_ov,b_fo,b_sz,b_la in caves[i+1:]:
        if a_ov != b_ov: continue
        if a_fo < b_fo+b_sz and b_fo < a_fo+a_sz:
            print(f"OVERLAP {a_id}[{a_fo:#x}..{a_fo+a_sz:#x}) vs {b_id}[{b_fo:#x}..{b_fo+b_sz:#x}) on {a_ov}")
