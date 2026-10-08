import sys, struct, json
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from ndspy.rom import NintendoDSRom

full=NintendoDSRom(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.nds").read_bytes())
OV36=0x023A7080
f36=full.loadArm9Overlays()[36].data
# PendingFlag was at 0x23c280c from earlier pool
for addr in [0x23c2800,0x23c2804,0x23c2808,0x23c280c,0x23c2810,0x23c2814,0x23c2818,0x23c281c,0x23c2820]:
    off=addr-OV36
    print(f"{addr:#x}: {f36[off:off+4].hex()}")

# Also verify generated prior in last apply - from state
s=json.loads(Path(r"Export Rom/Explorers of Alpha_Vanilla+full_stack.state.json").read_text(encoding="utf-8"))
for m in s["applied"]:
    if m["id"]=="z_move_v2":
        for d in m.get("data",[]):
            for k in ["prior_is_room_charge_move","prior_get_room_charge_state","room_charge_integration","PriorSubMenuStringCheck"]:
                if k in d: print(k, d[k])
