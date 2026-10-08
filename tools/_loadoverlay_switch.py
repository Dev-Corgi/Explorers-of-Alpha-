import sys, struct
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_rom_profile, resolve_symbol

rom = NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
van = NintendoDSRom(Path(r"Vanilla Rom/Explorers of Alpha_Vanilla.nds").read_bytes())
arm9 = bytes(rom.arm9)
arm9v = bytes(van.arm9)
LoadOverlay = 0x020040AC
cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)

print("=== LoadOverlay full switch (patched) ===")
for ins in cs.disasm(arm9[LoadOverlay-0x02000000:LoadOverlay-0x02000000+0x180], LoadOverlay):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")

print("\n=== compare LoadOverlay jump table van vs full (words) ===")
# Jump table starts at 0x20040c4, entries for id 0..0x24
base = 0x20040C4
for gid in list(range(0x20, 0x25)) + [0, 1, 0x1F]:
    off = (base + gid*4) - 0x02000000
    wp = struct.unpack_from("<I", arm9, off)[0]
    wv = struct.unpack_from("<I", arm9v, off)[0]
    # decode B target
    def bt(site, w):
        imm = w & 0xFFFFFF
        if imm & 0x800000: imm -= 0x1000000
        return site + 8 + imm*4
    site = base + gid*4
    print(f"gid {gid:02x}: van->{bt(site,wv):#x} pat->{bt(site,wp):#x} same={wv==wp}")

# Also OverlayIsLoaded jump for 0x24
OverlayIsLoaded = 0x02003ED0
print("\n=== OverlayIsLoaded start ===")
for ins in cs.disasm(arm9[OverlayIsLoaded-0x02000000:OverlayIsLoaded-0x02000000+0x100], OverlayIsLoaded):
    print(f"{ins.address:#010x}: {ins.mnemonic:8} {ins.op_str}")
