import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_rom_profile, resolve_symbol
from patch_engine.hook_registry import branch_target, hook_word_kind
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

rom = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
arm9 = bytes(rom.arm9)
ov29 = rom.loadArm9Overlays([29])[29].data
ov36 = rom.loadArm9Overlays([36])[36].data
OV29, OV36 = 0x022DC240, 0x023A7080
prof = load_rom_profile(Path("true_patches/engine"), "us_vanilla")
LoadOverlay = resolve_symbol(prof, "LoadOverlay")
UnloadOverlay = None
for name in ["UnloadOverlay", "UnloadOverlayInRam", "DeleteOverlay"]:
    try:
        print(name, hex(resolve_symbol(prof, name)))
        UnloadOverlay = resolve_symbol(prof, name)
    except Exception as e:
        print(name, "missing", e)

# Overlay table: ndspy
# rom.arm9OverlayTable is raw bytes; use loadOverlayTable
from ndspy.code import loadOverlayTable
table = loadOverlayTable(rom.arm9OverlayTable, lambda i, n: b"")
for i in [29, 31, 34, 35, 36]:
    e = table[i]
    # Overlay attributes
    attrs = [a for a in dir(e) if not a.startswith("_")]
    print(f"ov{i}: { {a: getattr(e,a) for a in attrs if not callable(getattr(e,a))} }")

# Search LOADED_OVERLAY_GROUP symbols in arm9.yml via known addresses from pmdsky-debug
import urllib.request, re
text = urllib.request.urlopen("https://raw.githubusercontent.com/UsernameFodder/pmdsky-debug/master/symbols/arm9.yml", timeout=30).read().decode("utf-8","replace")
for name in ["LOADED_OVERLAY_GROUP_0", "LOADED_OVERLAY_GROUP_1", "LOADED_OVERLAY_GROUP_2", "LoadOverlay", "UnloadOverlay"]:
    m = re.search(rf"name: {name}\n(?:.*\n){{0,12}}", text)
    if m:
        print(m.group()[:300])
        print("---")

# Disassemble LoadOverlay briefly to see group logic
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
print("=== LoadOverlay start ===")
for ins in cs.disasm(arm9[LoadOverlay-0x02000000:LoadOverlay-0x02000000+0x80], LoadOverlay):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
