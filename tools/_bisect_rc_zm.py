import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

# Bisect: compare full vs no_rc_zm for hooks that affect menus/actions
full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
norc = NintendoDSRom(Path(r"Export Rom/_full_stack_no_rc_zm.nds").read_bytes())
van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
OV29=0x022DC240
f29, n29, v29 = full.loadArm9Overlays()[29].data, norc.loadArm9Overlays()[29].data, van.loadArm9Overlays()[29].data
f31, n31 = full.loadArm9Overlays()[31].data, norc.loadArm9Overlays()[31].data

# Count ov29 diffs full vs norc, full vs van
def diff_count(a,b):
    n=0
    for off in range(0, min(len(a),len(b)), 4):
        if struct.unpack_from("<I", a, off)[0] != struct.unpack_from("<I", b, off)[0]:
            n += 1
    return n
print("ov29 changed words: full-van", diff_count(f29,v29), "full-norc", diff_count(f29,n29), "norc-van", diff_count(n29,v29))
print("ov31 changed words: full-van", diff_count(f31, van.loadArm9Overlays()[31].data), "full-norc", diff_count(f31,n31), "norc-van", diff_count(n31, van.loadArm9Overlays()[31].data))

# List ov29 sites different in full but same in norc vs van = introduced by rc+zm
print("\n=== ov29 sites only in full (rc/zm related) sample ===")
cs=Cs(CS_ARCH_ARM, CS_MODE_ARM)
only_full=[]
for off in range(0, min(len(f29),len(n29),len(v29)), 4):
    fw=struct.unpack_from("<I", f29, off)[0]
    nw=struct.unpack_from("<I", n29, off)[0]
    vw=struct.unpack_from("<I", v29, off)[0]
    if fw != nw and nw == vw:
        only_full.append((OV29+off, vw, fw))
print(f"count={len(only_full)}")
for addr,vw,fw in only_full[:50]:
    kind=hook_word_kind(fw)
    tgt=hex(branch_target(addr,fw)) if kind in ("b","bl") else ""
    print(f"  {addr:#x}: {vw:#010x}->{fw:#010x} {kind} {tgt}")
