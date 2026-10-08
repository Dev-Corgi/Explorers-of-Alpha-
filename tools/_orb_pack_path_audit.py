#!/usr/bin/env python3
"""Exhaustive audit of dungeon orb/pack use paths in EoS US ov29."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from ndspy.rom import NintendoDSRom
from skytemple_files.data.data_cd.handler import DataCDHandler
from skytemple_files.data.item_p.handler import ItemPHandler

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost_orbdummies.nds"
)
BASE = ROOT / (
    "4273 - Pokemon Mystery Dungeon - Explorers of Sky (US)(XenoPhobia)"
    "-patched_orbs_roomcharge_nodarkness_berryboost.nds"
)

OV29_LOAD = 0x022DC240
CS = Cs(CS_ARCH_ARM, CS_MODE_ARM)

HOOKS = {
    "ApplyItemEffect_ItemCdLoader": 0x0231B9A8,
    "TryWarp_Type5_PreItemEffect": 0x02321010,
    "ItemEffectClearSlot1": 0x022FB2F0,
    "ItemEffectClearSlot2": 0x022FB3A8,
    "BerryBoostCode": 0x02330100,
    "FEBAC_action49": 0x022FEBAC,
    "FED54_EnsureStand": 0x022FED54,
    "TryWarp": 0x02320D08,
    "ApplyItemEffect": 0x0231B68C,
    "UseSingleUseItem": 0x022F52F8,
}


def disasm_at(ov: bytes, addr: int, size: int = 12) -> list[str]:
    off = addr - OV29_LOAD
    return [
        f"{i.address:08X}: {i.mnemonic} {i.op_str}"
        for i in CS.disasm(ov[off : off + size], addr)
    ]


def find_bl_callers(ov: bytes, target: int) -> list[int]:
    callers: list[int] = []
    for base in range(OV29_LOAD, OV29_LOAD + len(ov), 4):
        off = base - OV29_LOAD
        if off + 4 > len(ov):
            break
        w = int.from_bytes(ov[off : off + 4], "little")
        if (w >> 24) & 0xFF != 0xEB:
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        dest = base + 8 + imm * 4
        if dest == target:
            callers.append(base)
    return callers


def find_b_branches(ov: bytes, target: int) -> list[int]:
    sites: list[int] = []
    for base in range(OV29_LOAD, OV29_LOAD + len(ov), 4):
        off = base - OV29_LOAD
        if off + 4 > len(ov):
            break
        w = int.from_bytes(ov[off : off + 4], "little")
        cond = (w >> 28) & 0xF
        if cond == 0xE:  # unconditional b
            imm = w & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            dest = base + 8 + imm * 4
            if dest == target:
                sites.append(base)
    return sites


def scan_mov_r2_before(ov: bytes, call_addr: int, window: int = 40) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    start = call_addr - OV29_LOAD - window * 4
    end = call_addr - OV29_LOAD
    for ins in CS.disasm(ov[start:end], call_addr - window * 4):
        if ins.mnemonic == "mov" and "r2" in ins.op_str.split(",")[0]:
            hits.append((ins.address, ins.op_str))
    return hits


def main() -> None:
    rom = NintendoDSRom(ROM.read_bytes())
    ov = rom.loadArm9Overlays([29])[29].data
    base_ov = NintendoDSRom(BASE.read_bytes()).loadArm9Overlays([29])[29].data

    print("=" * 70)
    print("PATCH SITE VERIFICATION")
    print("=" * 70)
    for name, addr in HOOKS.items():
        patched = disasm_at(ov, addr, 16)
        vanilla = disasm_at(base_ov, addr, 16)
        changed = patched != vanilla
        print(f"\n{name} @ {addr:08X} {'[CHANGED]' if changed else '[UNCHANGED]'}")
        for line in patched[:4]:
            print(f"  {line}")

    print("\n" + "=" * 70)
    print("ITEM DATA (pack vs real)")
    print("=" * 70)
    cd = DataCDHandler.deserialize(rom.getFileByName("BALANCE/item_cd.bin"))
    item_p = ItemPHandler.deserialize(rom.getFileByName("BALANCE/item_p.bin"))
    for iid, label in [(313, "Blowback pack"), (323, "Cleanse pack"), (1411, "Blowback real"), (1419, "Cleanse real")]:
        it = item_p.item_list[iid]
        print(
            f"  {label} id={iid}: effect={cd.get_item_effect_id(iid)}, "
            f"category={it.category}, buy={it.buy_price}, sell={it.sell_price}"
        )

    print("\n" + "=" * 70)
    print("ALL CALLERS OF KEY FUNCTIONS")
    print("=" * 70)
    for name, target in [
        ("TryWarp", 0x02320D08),
        ("EnsureCanStandCurrentTile", 0x02321104),
        ("ApplyItemEffect_ItemCdLoader", 0x0231B9A8),
        ("UseSingleUseItem", 0x022F52F8),
        ("UseSingleUseItemWrapper", 0x022F52CC),
        ("ApplyItemEffect", 0x0231B68C),
        ("ItemEffectClearSlot (ItemZInit hook site)", 0x022FB2F0),
    ]:
        callers = find_bl_callers(ov, target)
        print(f"\n{name} ({target:08X}): {len(callers)} bl callers")
        for c in callers[:15]:
            ctx = disasm_at(ov, c - 16, 20)
            print(f"  from {c:08X}:")
            for line in ctx:
                print(f"    {line}")

    print("\n" + "=" * 70)
    print("TryWarp CALLERS WITH r2 VALUE (mov r2, #N before bl)")
    print("=" * 70)
    by_r2: dict[str, list[int]] = defaultdict(list)
    for c in find_bl_callers(ov, 0x02320D08):
        movs = scan_mov_r2_before(ov, c)
        key = movs[-1][1] if movs else "unknown"
        by_r2[key].append(c)
    for key, addrs in sorted(by_r2.items(), key=lambda x: x[0]):
        print(f"  r2 setup '{key}': {len(addrs)} sites -> {[hex(a) for a in addrs[:8]]}")

    print("\n" + "=" * 70)
    print("BRANCHES TO TryWarp type-5 item-effect block (23221008)")
    print("=" * 70)
    for site in find_b_branches(ov, 0x02321008):
        print(f"  b -> 23221008 from {site:08X}")
        for line in disasm_at(ov, site - 8, 16):
            print(f"    {line}")

    print("\n" + "=" * 70)
    print("BRANCHES TO OrbPackTryWarpHook (23301B0 approx)")
    print("=" * 70)
    hook_target = int(disasm_at(ov, 0x02321010, 4)[0].split()[1].replace("#0x", "0x"), 16)
    print(f"  TryWarp hook branches to: {hook_target:08X}")
    for line in disasm_at(ov, hook_target, 48):
        print(f"  {line}")

    print("\n" + "=" * 70)
    print("EFFECT 86 ITEM IDS IN item_cd (pack range 301-359)")
    print("=" * 70)
    packs_with_86 = [i for i in range(301, 360) if cd.get_item_effect_id(i) == 86]
    packs_with_0 = [i for i in range(301, 360) if cd.get_item_effect_id(i) == 0]
    print(f"  packs still effect 86: {packs_with_86}")
    print(f"  packs with effect 0: {len(packs_with_0)} ids")

    print("\n" + "=" * 70)
    print("OVERLAY DIFF SUMMARY vs berry-boost base")
    print("=" * 70)
    diffs = [OV29_LOAD + i for i in range(min(len(ov), len(base_ov))) if ov[i] != base_ov[i]]
    print(f"  total byte diffs: {len(diffs)}")
    regions: dict[int, int] = defaultdict(int)
    for a in diffs:
        regions[a >> 12] += 1
    for page, count in sorted(regions.items()):
        print(f"  page {page << 12:08X}: {count} bytes changed")


if __name__ == "__main__":
    main()
