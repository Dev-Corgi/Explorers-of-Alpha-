import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

# Compare: does ExtraSpace ov36 static init / BSS zero the patch region at runtime?
# Check static init pointers and whether patched caves sit in BSS

full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
from ndspy.code import loadOverlayTable
table = loadOverlayTable(full.arm9OverlayTable, lambda i,n: b"")
e=table[36]
print(f"ov36 ram={e.ramAddress:#x} size={e.ramSize:#x} bss={e.bssSize:#x}")
print(f"file image len={len(full.loadArm9Overlays()[36].data):#x}")
# In NDS, BSS is typically after file image in RAM
file_len=len(full.loadArm9Overlays()[36].data)
bss_start=e.ramAddress+file_len  # often
print(f"approx file-backed RAM [{e.ramAddress:#x}..{e.ramAddress+file_len:#x})")
print(f"approx BSS [{e.ramAddress+file_len:#x}..{e.ramAddress+e.ramSize:#x})" if e.ramSize>file_len else "bss within/after?")
print(f"ramSize-fileLen={e.ramSize-file_len:#x}")

# Our caves start at 0x23c15f8 - is that in file-backed region?
caves_start=0x23c15f8
print(f"caves_start in file-backed? {e.ramAddress <= caves_start < e.ramAddress+file_len}")
print(f"offset in file: {caves_start-e.ramAddress:#x}")

# static init - disassemble
OV36=0x023A7080
ov36=full.loadArm9Overlays()[36].data
cs=Cs(CS_ARCH_ARM, CS_MODE_ARM)
print(f"\nstaticInit {e.staticInitStart:#x}..{e.staticInitEnd:#x}")
if e.staticInitStart and e.staticInitEnd > e.staticInitStart:
    off=e.staticInitStart-OV36
    for ins in cs.disasm(ov36[off:off+0x80], e.staticInitStart):
        print(f"  {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# Check c-of-time / ExtraSpace common area vs caves
COT_COMMON=0x023D7FF0
print(f"\ncaves vs COT common 0x23D7FF0: last cave end 0x23c4af4, common={COT_COMMON:#x}")
print(f"overlap caves/common? {0x23c15f8 < COT_COMMON+0x8010 and COT_COMMON < 0x23c4af4}")
