"""Build one-patch-on-vanilla ROMs for bisection."""
from __future__ import annotations
import shutil
import traceback
from pathlib import Path

from patch_engine.apply_module import apply_module

REPO = Path(r"C:\Working\SkyTemple")
VANILLA = REPO / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
OUT_DIR = REPO / "Export Rom" / "test_rom"

# Same order / set as full_stack
PATCHES = [
    "fixed_room_orbs",
    "shop_sell_price",
    "room_charge_v4",
    "orb_charges_v2",
    "berry_boost",
    "tm_read",
    "z_move_v2",
    "spinda_ev_v2",
    "iq_change",
    "overlay36_loader",
]

if not VANILLA.is_file():
    raise SystemExit(f"vanilla missing: {VANILLA}")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Clear previous one-patch outputs (keep folder)
for old in OUT_DIR.glob("*.nds"):
    old.unlink()
for old in OUT_DIR.glob("*.state.json"):
    old.unlink()

results = []
for mid in PATCHES:
    rom_out = OUT_DIR / f"Vanilla+{mid}.nds"
    state_out = OUT_DIR / f"Vanilla+{mid}.state.json"
    print(f"\n===== {mid} =====")
    shutil.copy2(VANILLA, rom_out)
    if state_out.exists():
        state_out.unlink()
    try:
        state = apply_module(
            mid,
            rom_out,
            rom_out,
            state_path=state_out,
            force_reapply=True,
        )
        mod = state.get_module(mid)
        ver = mod.version if mod else "?"
        size = rom_out.stat().st_size
        print(f"OK {mid} v{ver} -> {rom_out.name} ({size} bytes)")
        results.append((mid, "OK", ver, rom_out.name))
    except Exception as e:
        print(f"FAIL {mid}: {e}")
        traceback.print_exc()
        results.append((mid, "FAIL", str(e), rom_out.name if rom_out.exists() else ""))
        # leave partial file for inspection but mark fail

print("\n===== SUMMARY =====")
for mid, status, info, name in results:
    print(f"  {status:4} {mid}: {info} ({name})")
print(f"\nOutput dir: {OUT_DIR}")
