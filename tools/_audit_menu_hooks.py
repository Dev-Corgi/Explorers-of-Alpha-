import sys, struct, json
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV31 = 0x02382820
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
van31 = van.loadArm9Overlays()[31].data
full31 = full.loadArm9Overlays()[31].data
van29 = van.loadArm9Overlays()[29].data
full29 = full.loadArm9Overlays()[29].data
OV29 = 0x022DC240

# Diff ov31 entirely - count changed words
changed = []
for off in range(0, min(len(van31), len(full31)), 4):
    vw = struct.unpack_from("<I", van31, off)[0]
    fw = struct.unpack_from("<I", full31, off)[0]
    if vw != fw:
        changed.append((OV31+off, vw, fw))
print(f"ov31 changed words: {len(changed)}")
for addr, vw, fw in changed[:40]:
    kind = hook_word_kind(fw)
    tgt = hex(branch_target(addr, fw)) if kind in ("b","bl") else ""
    print(f"  {addr:#x}: {vw:#010x} -> {fw:#010x} {kind} {tgt}")

# GetSubMenuStringId area - critical for B/menu
print("\n=== GetSubMenuStringId region van vs full ===")
# 0x22EB2xx from hooks
for addr in range(0x22EB2C0, 0x22EB320, 4):
    vw = struct.unpack_from("<I", van29, addr-OV29)[0]
    fw = struct.unpack_from("<I", full29, addr-OV29)[0]
    mark = " *" if vw!=fw else ""
    print(f"  {addr:#x}: van={vw:#010x} full={fw:#010x}{mark}")

print("\n=== full GetSubMenuStringId disasm ===")
for ins in cs.disasm(full29[0x22EB280-OV29:0x22EB380-OV29], 0x22EB280):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# Follow z_move submenu hook target
tgt = 0x23c2a9c
OV36=0x023A7080
full36 = full.loadArm9Overlays()[36].data
print(f"\n=== Z/TM submenu hook @ {tgt:#x} ===")
for ins in cs.disasm(full36[tgt-OV36:tgt-OV36+0x80], tgt):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
