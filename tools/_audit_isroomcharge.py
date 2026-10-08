import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_rom_profile, resolve_symbol
from patch_engine.hook_registry import branch_target, hook_word_kind

van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
prof = load_rom_profile(Path("true_patches/engine"), "us_vanilla")
OV29 = 0x022DC240
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
van29 = van.loadArm9Overlays()[29].data
full29 = full.loadArm9Overlays()[29].data
full36 = full.loadArm9Overlays()[36].data
OV36 = 0x023A7080

# Resolve symbols
for name in ["IsRoomChargeMove", "GetSubMenuStringId", "GetSubMenuStringIdReadSite", "GetSubMenuStringId_Continue",
             "ExecuteMonsterAction", "ExecuteMonsterActionCleanup2Return"]:
    try:
        print(f"{name}: {resolve_symbol(prof, name):#x}")
    except Exception as e:
        print(f"{name}: ERR {e}")

print("\n=== vanilla around 0x231c3d0 (IsRoomChargeMoveHook) ===")
for addr in range(0x231c300, 0x231c500, 4):
    w = struct.unpack_from("<I", van29, addr-OV29)[0]
    if w != 0:
        print(f"  van {addr:#x}: {w:#010x}")
print("nonzero count in 0x231c300-500 van", sum(1 for a in range(0x231c300,0x231c500,4) if struct.unpack_from("<I", van29, a-OV29)[0]))
print("nonzero count in 0x231c300-500 full", sum(1 for a in range(0x231c300,0x231c500,4) if struct.unpack_from("<I", full29, a-OV29)[0]))

print("\n=== full IsRoomChargeMoveHook ===")
for ins in cs.disasm(full29[0x231c3c0-OV29:0x231c3e0-OV29], 0x231c3c0):
    print(f"{ins.address:#010x}: {ins.mnemonic} {ins.op_str}")

# Find real IsRoomChargeMove in vanilla - search pmdsky or string
import urllib.request, re
text = urllib.request.urlopen("https://raw.githubusercontent.com/UsernameFodder/pmdsky-debug/master/symbols/overlay29.yml", timeout=30).read().decode()
m = re.search(r"name: IsRoomChargeMove\n.*?NA: (0x[0-9A-Fa-f]+)", text, re.S)
print("pmdsky IsRoomChargeMove NA:", m.group(1) if m else "missing")
if m:
    addr = int(m.group(1), 16)
    print(f"\n=== vanilla IsRoomChargeMove @ {addr:#x} ===")
    for ins in cs.disasm(van29[addr-OV29:addr-OV29+0x40], addr):
        print(f"{ins.address:#010x}: {ins.mnemonic} {ins.op_str}")
    print(f"\n=== full @ {addr:#x} ===")
    for ins in cs.disasm(full29[addr-OV29:addr-OV29+0x40], addr):
        print(f"{ins.address:#010x}: {ins.mnemonic} {ins.op_str}")

# Who calls IsRoomChargeMove in vanilla?
irc = int(m.group(1), 16) if m else None
if irc:
    refs = []
    for off in range(0, len(van29)-4, 4):
        w = struct.unpack_from("<I", van29, off)[0]
        if hook_word_kind(w) not in ("bl","b"): continue
        if branch_target(OV29+off, w) == irc:
            refs.append(OV29+off)
    print(f"\nvanilla callers of IsRoomChargeMove: {len(refs)}")
    for r in refs[:20]:
        print(f"  {r:#x}")
    # full callers of hook site 0x231c3d0
    refs2 = []
    for off in range(0, len(full29)-4, 4):
        w = struct.unpack_from("<I", full29, off)[0]
        if hook_word_kind(w) not in ("bl","b"): continue
        if branch_target(OV29+off, w) == 0x231c3d0:
            refs2.append(OV29+off)
    print(f"full callers of 0x231c3d0: {len(refs2)} {[hex(x) for x in refs2[:20]]}")
    # full callers of real irc
    refs3 = []
    for off in range(0, len(full29)-4, 4):
        w = struct.unpack_from("<I", full29, off)[0]
        if hook_word_kind(w) not in ("bl","b"): continue
        if branch_target(OV29+off, w) == irc:
            refs3.append(OV29+off)
    print(f"full callers of real IsRoomChargeMove {irc:#x}: {len(refs3)} {[hex(x) for x in refs3[:20]]}")
