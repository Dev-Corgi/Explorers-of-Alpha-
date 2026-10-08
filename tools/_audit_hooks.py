import sys, json, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_rom_profile, resolve_symbol
from patch_engine.hook_registry import branch_target, hook_word_kind

van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
state = json.loads(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.state.json").read_text(encoding="utf-8"))
prof = load_rom_profile(Path("true_patches/engine"), "us_vanilla")
OV29 = 0x022DC240
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
van29 = van.loadArm9Overlays()[29].data
full29 = full.loadArm9Overlays()[29].data
van31 = van.loadArm9Overlays()[31].data
full31 = full.loadArm9Overlays()[31].data

# Collect all hooks from state
print("=== hook sites: vanilla word vs patched ===")
for m in state["applied"]:
    hooks = m.get("hooks") or []
    if not hooks:
        continue
    print(f"\n-- {m['id']} ({len(hooks)} hooks) --")
    for h in hooks:
        site = int(h.get("site") or h.get("address") or 0)
        if not site:
            # try symbol
            sym = h.get("symbol") or h.get("name")
            try:
                site = resolve_symbol(prof, h.get("symbol", sym))
            except Exception:
                print(f"  skip {h}")
                continue
        binary = h.get("binary", "ov29")
        if binary == "ov29":
            vb, fb, load = van29, full29, OV29
        elif binary == "ov31":
            vb, fb, load = van31, full31, 0x02382820
        elif binary == "arm9":
            vb, fb, load = bytes(van.arm9), bytes(full.arm9), 0x02000000
        else:
            print(f"  unknown binary {binary} for {h.get('name')}")
            continue
        off = site - load
        if not (0 <= off < len(vb)-4):
            print(f"  OUT OF RANGE {h.get('name')} @ {site:#x} binary={binary}")
            continue
        vw = struct.unpack_from("<I", vb, off)[0]
        fw = struct.unpack_from("<I", fb, off)[0]
        expected = h.get("vanilla_word")
        if isinstance(expected, str):
            expected = int(expected, 16)
        ok_van = (expected is None) or (vw == expected)
        kind = hook_word_kind(fw)
        tgt = None
        if kind in ("b", "bl"):
            tgt = branch_target(site, fw)
        flag = ""
        if not ok_van:
            flag += " VANILLA_MISMATCH"
        if vw == fw:
            flag += " UNCHANGED?"
        print(f"  {h.get('name')}: {site:#x} van={vw:#010x} full={fw:#010x} kind={kind} tgt={tgt and hex(tgt)} exp_van={expected and hex(expected)}{flag}")
