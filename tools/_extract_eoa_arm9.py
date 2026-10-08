from pathlib import Path

from ndspy.rom import NintendoDSRom

van = NintendoDSRom.fromFile(
    r"c:\Working\SkyTemple\Vanilla Rom\Explorers of Alpha_Vanilla.nds"
)
base = Path(r"c:\Working\SkyTemple\unpacked\arm9.bin").read_bytes()
out = Path(r"c:\Working\SkyTemple\tools\_tmp_eoa_arm9.bin")
out.write_bytes(van.arm9)
print("EoA arm9", len(van.arm9), "base", len(base))
# diff regions
changes = []
start = None
for i in range(min(len(base), len(van.arm9))):
    if base[i] != van.arm9[i]:
        if start is None:
            start = i
    elif start is not None:
        changes.append((start, i))
        start = None
if start is not None:
    changes.append((start, min(len(base), len(van.arm9))))
print("changed regions in overlap:", len(changes))
for s, e in changes[:25]:
    print(f"  0x{s:X}-0x{e:X} ({e-s}B)")
if len(van.arm9) != len(base):
    print("size delta", len(van.arm9) - len(base))
