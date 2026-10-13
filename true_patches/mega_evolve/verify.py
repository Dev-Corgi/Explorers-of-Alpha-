"""Phase-0 source reconciliation, regression cases and byte-preserving engine gate.

No full-stack build, NDS output, state output or source-asset edits.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parent
REPO = MODULE.parents[1]
sys.path.insert(0, str(REPO))

from patch_engine.apply_mega_evolve import load_registry, validate_rom, verify_mega_evolve_module, apply_mega_evolve_module
from patch_engine.manifest import load_module_manifest, load_yaml
from patch_engine.build_full_stack import FULL_STACK_MODULES
from true_patches.mega_evolve.phase0 import BASE_ROM, MODULE, build, digest, ids, normalize_ability, validate


def rejected(function, *args):
    try:
        function(*args)
    except (ValueError, AssertionError, RuntimeError):
        return
    raise AssertionError("invalid input was accepted")


def main():
    registry_path = MODULE / "data/registry.json"
    saved = json.loads(registry_path.read_text(encoding="utf-8"))
    manifest = load_module_manifest(MODULE)
    catalog = load_yaml(REPO / "patch_engine/catalog.yaml")
    assert manifest["phase"] in (0,1,2) and manifest["kind"] == "mega_evolve"
    assert FULL_STACK_MODULES.count("mega_evolve") == 1
    assert all(FULL_STACK_MODULES.index(dep) < FULL_STACK_MODULES.index("mega_evolve")
               for dep in manifest["requires"])
    assert catalog["modules"]["mega_evolve"]["kind"] == manifest["kind"]
    assert catalog["recommended_order"].index("mega_evolve") < catalog["recommended_order"].index("korean")
    rebuilt = build()
    assert saved == rebuilt, "registry/source/asset inventory changed"
    assert (saved["audit"]["assignment_rows"], saved["audit"]["stat_rows"],
            saved["audit"]["source_rom_ids"], saved["audit"]["expanded_targets"]) == (322, 308, 320, 326)
    assert ids("383, 384") == [383, 384]
    rejected(ids, "383, 383")
    rejected(ids, "383;384")
    assert normalize_ability("날카로운 발톱 Ⅱ") == "단단한발톱"
    assert normalize_ability("전지전능") == "Omniscience"
    assert normalize_ability("일렉트릭메이커 Ⅱ") == "일렉트릭스킨"
    assert normalize_ability("서핑테일 Ⅱ") == "쓱쓱"
    targets = saved["targets"]
    assert {r["official_form"] for r in targets if r["source_rom_id"] == 6} == {"Mega-X", "Mega-Y"}
    assert all(r["mega_stats"] == [100,130,130,160,130,130]
               for r in targets if r["dex"] in (483,484,487))
    assert all(r["types"] == [9,2] or set(r["types"]) == {9,2}
               for r in targets if r["dex"] == 383), "Primal Groudon typing"
    assert saved["audit"]["required_stat_max"] > 255
    assert saved["audit"]["naive_clone_entry_count"] > 2048
    assert saved["audit"]["rom_evidence"]["stock_species_max_id"] == 2047
    assert any(r["plus600_id"] == 1137 and r["classification"] != "gender_counterpart_candidate"
               for r in saved["audit"]["legacy_counterparts"])
    abilities = {r["key"]: r for r in saved["abilities"]}
    assert len(abilities) == 206
    assert "이동속도" not in abilities["불굴의마음"]["normal"] + abilities["불굴의마음"]["enhanced"]
    assert "부스트에너지 조건 없음" in abilities["고대활성"]["normal"]
    omni = abilities["Omniscience"]["judgment_z"]
    assert omni["move_id"] == 467 and omni["normal_power"] == 360 and omni["other_type_power"] == 180
    assert not omni["gauge_requirement"] and not omni["gauge_consumption"] and not omni["gauge_reset"]
    assert not omni["temporary_move_slot_replacement"]
    assert omni["requires_active_enhanced_ability"] and omni["type"] == "holder_current_primary_type"
    assert not saved["audit"]["pending_specifications"]
    weather = saved["rules"]["weather"]
    for family in ("sun", "rain", "sand", "snow"):
        assert weather[family+"_normal"]["factor"] == [6,5]
        assert weather[family+"_strong"]["factor"] == [3,2]
        assert weather[family+"_strong"]["can_be_replaced_by"] == ["strong"]
    assert not saved["rules"]["weather_extra"]["snow_chip_damage"]
    for mutation in ("duplicate", "missing_ability", "shiny_stats", "physical_id", "origin_stats", "scope"):
        broken = copy.deepcopy(saved)
        if mutation == "duplicate": broken["targets"].append(broken["targets"][0])
        if mutation == "missing_ability": broken["targets"][0]["abilities"][0] = ""
        if mutation == "shiny_stats": broken["targets"][0]["shiny_mega_stats"] = [1]*6
        if mutation == "physical_id": broken["targets"][0]["runtime_mega_id"] = 1200
        if mutation == "origin_stats":
            row = next(r for r in broken["targets"] if r["dex"] == 483)
            row["mega_stats"] = row["shiny_mega_stats"] = [1]*6
        if mutation == "scope": broken["abilities"].append({"key": "unassigned"})
        rejected(validate, broken)
    # The phase-0 handler stays available beside the new phase-1 runtime.
    before = digest(BASE_ROM)
    phase0_manifest=dict(manifest,phase=0)
    record=apply_mega_evolve_module("mega_evolve",MODULE,phase0_manifest,BASE_ROM)
    verify_mega_evolve_module(BASE_ROM,MODULE,phase0_manifest,record)
    assert digest(BASE_ROM) == before
    rejected(verify_mega_evolve_module, BASE_ROM, MODULE, phase0_manifest, None)
    stale = copy.deepcopy(record)
    stale.data[0]["mega_evolve"]["registry_file_sha256"] = "stale"
    rejected(verify_mega_evolve_module, BASE_ROM, MODULE, phase0_manifest, stale)
    rejected(load_registry, MODULE, {"phase": 3})
    for filename in ("Explorers of Alpha+.nds", "Explorers of Alpha+_kor.nds"):
        existing = REPO / "PatchTesting/Export Rom" / filename
        if existing.exists():
            before_existing = digest(existing)
            validate_rom(existing, saved)
            assert digest(existing) == before_existing
    print("PASS: source reconciliation, aliases, branching, official overrides, stat/save limits,")
    print("      assigned ability scope, weather, Omniscience II spec, rejection cases and engine gate.")
    print("No ROM, save, build-state or source assets were written.")


if __name__ == "__main__":
    main()
