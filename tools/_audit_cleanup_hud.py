import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.hook_registry import branch_target, hook_word_kind

full = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
OV29, OV36, OV31 = 0x022DC240, 0x023A7080, 0x02382820
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
f29, v29 = full.loadArm9Overlays()[29].data, van.loadArm9Overlays()[29].data
f36 = full.loadArm9Overlays()[36].data
f31, v31 = full.loadArm9Overlays()[31].data, van.loadArm9Overlays()[31].data

print("=== CalcDamageJudgmentTypeHook van vs full ===")
for addr in range(0x230bc90, 0x230bcd0, 4):
    vw=struct.unpack_from("<I", v29, addr-OV29)[0]
    fw=struct.unpack_from("<I", f29, addr-OV29)[0]
    mark=" *" if vw!=fw else ""
    print(f"  {addr:#x}: {vw:#010x} -> {fw:#010x}{mark}")
print("van:")
for ins in cs.disasm(v29[0x230bc90-OV29:0x230bcd0-OV29], 0x230bc90):
    print(f"  {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
print("full:")
for ins in cs.disasm(f29[0x230bc90-OV29:0x230bcd0-OV29], 0x230bc90):
    print(f"  {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
# decode beq target
w=struct.unpack_from("<I", f29, 0x230bca8-OV29)[0]
print(f"patched word {w:#010x} kind={hook_word_kind(w)} tgt={branch_target(0x230bca8,w):#x}")

print("\n=== ZMove_Cleanup2Return @ 0x23c2f40 ===")
for ins in cs.disasm(f36[0x23c2f40-OV36:0x23c2f40-OV36+0x80], 0x23c2f40):
    print(f"  {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

print("\n=== DungeonMenuZGaugeHud site van vs full ===")
addr=0x23828f8
print("van:")
for ins in cs.disasm(v31[addr-OV31-0x20:addr-OV31+0x30], addr-0x20):
    mark=">>>" if ins.address==addr else "   "
    print(f"{mark} {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
print("full:")
for ins in cs.disasm(f31[addr-OV31-0x20:addr-OV31+0x30], addr-0x20):
    mark=">>>" if ins.address==addr else "   "
    print(f"{mark} {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

print("\n=== ZMove_DrawThenGetMoney @ 0x23c2994 ===")
for ins in cs.disasm(f36[0x23c2994-OV36:0x23c2994-OV36+0x50], 0x23c2994):
    print(f"  {ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# ACTION_Z_MOVE value
from pathlib import Path as P
types = P(r"true_patches/z_move_v2/asm/common/typesUS.asm").read_text(encoding="utf-8", errors="replace")
for line in types.splitlines():
    if "ACTION" in line or "Z_MOVE" in line or "0x2a" in line.lower():
        print(line)
