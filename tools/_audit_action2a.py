import sys, struct, urllib.request, re
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

# Find action 0x2a handling in ExecuteMonsterAction
van=NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
OV29=0x022DC240
v29=van.loadArm9Overlays()[29].data
cs=Cs(CS_ARCH_ARM, CS_MODE_ARM)

# Search cmp rX, #0x2a near ExecuteMonsterAction
ema=0x22fe4bc
print("=== search cmp #0x2a / #42 in ov29 ===")
hits=[]
for off in range(0, len(v29)-4, 4):
    w=struct.unpack_from("<I", v29, off)[0]
    # cmp rn, #0x2a = E35X002A or similar
    if (w & 0xFFF0FFFF) == 0xE350002A or (w & 0xFFF0FFFF) == 0xE350002A:
        hits.append(OV29+off)
    if w in (0xE356002A, 0xE355002A, 0xE354002A, 0xE353002A, 0xE352002A, 0xE351002A, 0xE350002A,
             0xE3560026, 0xE3500028, 0xE3500029):
        hits.append((OV29+off, w))
print("direct hits", len(hits))
for h in hits[:40]:
    if isinstance(h, tuple):
        addr,w=h
        print(f"  {addr:#x} {w:#010x}")
        for ins in cs.disasm(v29[addr-OV29-8:addr-OV29+24], addr-8):
            mark=">>>" if ins.address==addr else "   "
            print(f"  {mark} {ins.address:#010x}: {ins.mnemonic} {ins.op_str}")

# pmdsky action descriptions
text=urllib.request.urlopen("https://raw.githubusercontent.com/UsernameFodder/pmdsky-debug/master/headers/types/dungeon_mode/enums.h", timeout=30).read().decode("utf-8","replace")
# get enum action block
idx=text.find("ACTION_UNK_2A")
print(text[max(0,idx-400):idx+400])
