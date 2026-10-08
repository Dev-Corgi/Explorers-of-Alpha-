"""Rebuild full_stack with tm_read v14 + z_move_v2 v10 export/menu fixes."""
from __future__ import annotations
import shutil
from pathlib import Path
from patch_engine.apply_module import apply_module, verify_module_applied

REPO = Path(r"C:\Working\SkyTemple")
OUT = REPO / "Export Rom" / "Explorers of Alpha_Vanilla+full_stack.nds"
STATE = OUT.with_suffix(".state.json")
BASE = REPO / "Export Rom" / "Explorers of Alpha_Vanilla+shop_sell_price+fixed_room_orbs.nds"

# Start from data patches already applied
shutil.copy2(BASE, OUT)
# Fresh state for remaining modules (data patches already in ROM bytes)
from patch_engine.state import BuildState, AppliedModule, save_state, load_state
# Prefer rebuilding state: apply fixed_room + shop first from vanilla for clean state
VANILLA = REPO / "Vanilla Rom" / "Explorers of Alpha_Vanilla.nds"
shutil.copy2(VANILLA, OUT)
if STATE.exists():
    STATE.unlink()

stack = [
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

for mid in stack:
    print(f"\n===== apply {mid} =====")
    state = apply_module(mid, OUT, OUT, state_path=STATE, force_reapply=True)
    mod = state.get_module(mid)
    print(f"OK {mid} v{mod.version if mod else '?'}")

# Verify critical exports
import json, struct
from ndspy.rom import NintendoDSRom
st = json.loads(STATE.read_text(encoding="utf-8"))
rom = NintendoDSRom(OUT.read_bytes())
f36 = rom.loadArm9Overlays()[36].data
OV36 = 0x023A7080
for m in st["applied"]:
    if m["id"] == "tm_read":
        d = m["data"][0]
        for k in ("TmRead_CheckReadString", "TmRead_TryRestoreSlot"):
            addr = int(d[k], 16)
            w = struct.unpack_from("<I", f36, addr - OV36)[0]
            print(f"verify {k}={addr:#x} word={w:#010x}", "OK" if w else "BAD ZERO")
    if m["id"] == "z_move_v2":
        d = m["data"][0]
        for k in ("PriorSubMenuStringCheck", "PriorCleanupTryRestore"):
            addr = int(d[k], 16)
            w = struct.unpack_from("<I", f36, addr - OV36)[0]
            print(f"verify {k}={addr:#x} word={w:#010x}", "OK" if w else "BAD ZERO")

print(f"\nBuilt {OUT}")
