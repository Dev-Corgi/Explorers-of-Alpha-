import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom

van=NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
full=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV29=0x022DC240
v29=van.loadArm9Overlays()[29].data
f29=full.loadArm9Overlays()[29].data
cs=Cs(CS_ARCH_ARM,CS_MODE_ARM)

# GetSubMenuStringId uses a table - ldrh r6,[r0,r2] where r0 is table ptr from pool
# at 0x22eb2d0: ldr r0,[pc,#0x88]
print("=== GetSubMenuStringId table ===")
for ins in cs.disasm(v29[0x22eb2c8-OV29:0x22eb370-OV29], 0x22eb2c8):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

# pool at end
pool_site=0x22eb2d0
imm=0x88
table=pool_site+8+imm
print(f"\naction->string table ptr literal @ {table:#x}")
w=struct.unpack_from("<I", v29, table-OV29)[0]
print(f"table addr = {w:#x}")

# Each entry 8 bytes? lsl r2,r5,lsl#3 so 8-byte entries indexed by action?
# ldrh r6,[r0,r2] - r2 = action*8, loads halfword at start of entry - maybe string id or action field
print("\nSample table entries for actions 0x14-0x32:")
for action in list(range(0x10, 0x35))+[0x2a,0x29,0x26,0x28]:
    off=w-OV29+action*8
    if 0<=off<len(v29)-8:
        a,b,c,d=struct.unpack_from("<HHHH", v29, off)
        print(f"  action {action:#x} ({action}): {a:5} {b:5} {c:5} {d:5}")
