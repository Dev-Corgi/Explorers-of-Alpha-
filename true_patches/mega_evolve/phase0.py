"""Build a deterministic phase-0 registry from user sources; never write a ROM.

External assets are read-only and are not copied into Git. Normalized gameplay
definitions and provenance hashes are the patch's maintained input data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import gzip
import json
import re
import sys
import struct
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

MODULE = Path(__file__).resolve().parent
REPO = MODULE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

ASSIGNMENTS = "메가특성_본가기준_전체 - 특성 배정.csv"
EFFECTS = "포켓몬_특성_강화완성 - 포켓몬 특성.csv"
STATS = "한글풀스택_최종진화형_메가종족값.xlsx"
BASE_ROM = REPO / "PatchTesting/Explorers of Alpha/Explorers of Alpha.nds"
ALIASES = {
    "과학의힘": "화학의힘", "시간끌기": "시간벌기",
    "에널라이즈": "애널라이즈", "짖궂은마음": "짓궂은마음",
    "페어스킨": "페어리스킨", "날카로운발톱": "단단한발톱",
    "전지전능": "Omniscience", "Omnisense": "Omniscience",
    "일렉트릭메이커": "일렉트릭스킨", "서핑테일": "쓱쓱",
}
OFFICIAL_SPECIAL = {
    382: ("Primal", 555, 414), 383: ("Primal", 556, 415),
    483: ("Origin", 552, 525), 484: ("Origin", 551, 526),
    487: ("Origin", 536, 529),
}
ORIGIN_STATS = [100, 130, 130, 160, 130, 130]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_ability(value):
    key = re.sub(r"[\sⅡ]", "", value)
    return ALIASES.get(key, key)


def ids(value):
    if not re.fullmatch(r"\s*\d+(\s*,\s*\d+)*\s*", str(value)):
        raise ValueError(f"invalid ROM ID list: {value!r}")
    result = [int(x.strip()) for x in str(value).split(",")]
    if len(result) != len(set(result)):
        raise ValueError("duplicate ID within a source row")
    return result


def assignments(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    header = next(i for i, row in enumerate(rows) if row and row[0] == "이름")
    result = []
    for number, cells in enumerate(rows[header + 1:], header + 2):
        row = dict(zip(rows[header], cells))
        if not row.get("ROM ID", "").strip():
            continue  # title/footer/reference rows are not assignments
        result.append({"source_record": number, "name": row["이름"],
                       "source_rom_ids": ids(row["ROM ID"]),
                       "abilities": [normalize_ability(row[f"특성{i} Ⅱ"])
                                     for i in (1, 2, 3)],
                       "original_abilities": [row[f"특성{i} Ⅱ"] for i in (1, 2, 3)],
                       "notes": row["비고"], "original_row": row["원본 행"]})
    return result


def workbook_stats(path):
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ["".join(t.text or "" for t in node.findall(".//m:t", ns))
                      for node in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", ns)]
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        result = []
        for row in root.findall("m:sheetData/m:row", ns):
            values = {}
            for cell in row:
                value = cell.find("m:v", ns)
                if cell.attrib.get("t") == "s":
                    text = shared[int(value.text)]
                elif cell.attrib.get("t") == "inlineStr":
                    text = "".join(t.text or "" for t in cell.findall(".//m:t", ns))
                else:
                    text = value.text if value is not None else ""
                values[re.sub(r"\d", "", cell.attrib["r"])] = text
            if int(row.attrib["r"]) <= 5 or not values.get("L"):
                continue
            stats = [int(values[key]) for key in "DEFGHI"]
            result.append({"name": values["A"], "dex": int(values["B"]),
                           "method": values["C"], "stats": stats,
                           "rom_ids": ids(values["L"]), "sheet_row": int(row.attrib["r"])})
    return result


def normalized_name(value):
    value = re.sub(r"\[ROM[^\]]*\]", "", value)
    value = re.sub(r"\([^)]*보류[^)]*\)", "", value)
    return re.sub(r"\s", "", value)


def match_stats(assignment, species, rows):
    candidates = [r for r in rows if species in r["rom_ids"]]
    exact = [r for r in candidates if normalized_name(r["name"]) == normalized_name(assignment["name"])]
    if len(exact) == 1:
        return exact[0]
    if len(candidates) == 1:
        return candidates[0]
    raise ValueError(f"ambiguous/missing stats: {assignment['name']} / {species}")


def rom_evidence(rom_path=BASE_ROM):
    from ndspy.rom import NintendoDSRom
    from skytemple_files.common.util import get_ppmdu_config_for_rom
    from skytemple_files.data.md.handler import MdHandler
    from skytemple_files.data.str.handler import StrHandler
    rom = NintendoDSRom(rom_path.read_bytes())
    config = get_ppmdu_config_for_rom(rom)
    md = MdHandler.deserialize(rom.getFileByName("BALANCE/monster.md"))
    strings = StrHandler.deserialize(rom.getFileByName("MESSAGE/text_e.str"),
                                    string_encoding=config.string_encoding).strings
    starts = [i for i in range(len(strings) - 512)
              if strings[i] == "Unknown" and strings[i+1] == "Stench"
              and strings[i+125] == "Illusion"]
    if len(starts) != 1:
        raise ValueError("ambiguous Alpha ability name block")
    start = starts[0]
    if strings[start+250] != "Omniscience" or md.entries[1137].ability_primary != 250:
        raise ValueError("Omniscience / story Arceus evidence changed")
    codecs = []
    for offset, service in ((0x59358, 0x020509C0), (0x59480, 0x02050A40)):
        words = struct.unpack_from("<4I", rom.arm9, offset)
        branch = words[3] & 0xFFFFFF
        if branch & 0x800000:
            branch -= 0x1000000
        destination = 0x02000000 + offset + 12 + 8 + branch * 4
        if words[:3] != (0xE1A00005, 0xE2841004, 0xE3A0200B) or destination != service:
            raise ValueError("stock species serialization evidence changed")
        codecs.append({"instruction_address": 0x02000000+offset,
                       "record_species_offset": 4, "bits": 11, "stream_service": service})
    evidence = {"rom_sha256": digest(rom_path), "md_entries": len(md.entries),
                "stock_species_codec": codecs, "stock_species_max_id": 2047,
                "ability_name_start": start, "legacy_ability_slots": 2,
                "legacy_ability_id_bits": 8,
                "omnisense": {"canonical_name": "Omniscience", "rom_ability_id": 250,
                              "name_index": start+250, "description_index": start+506,
                              "normal_description": strings[start+506],
                              "normal_arceus_id": 537, "story_arceus_id": 1137,
                              "enhanced_status": "user_judgment_z_effect_override"}}
    return md.entries, strings, config, evidence


def effects(path, assigned, omni):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["번호"].isdigit()]
    by_name = {re.sub(r"\s", "", r["특성명"]): r for r in rows}
    result = []
    for name in sorted(assigned):
        if name == "Omniscience":
            result.append({"key": name, "rom_ability_id": 250, "effect_table_number": None,
                           "normal": omni["normal_description"],
                           "enhanced": "기존 Omniscience 효과 유지. 심판(467)을 현재 보유자의 주 타입 Z-Move 위력·효과로 처리한다. Z 게이지 요구·소모·초기화 없음.",
                           "status": "specified_user_override_not_implementation_certified",
                           "judgment_z": {"move_id": 467, "legacy_z_shell_id": 559,
                               "type": "holder_current_primary_type", "capture": "action_start_before_attack_type_rewrite",
                               "requires_active_enhanced_ability": True,
                               "normal_power": 360, "other_type_power": 180,
                               "secondary_effects": "reuse_existing_z_move_type_effects",
                               "gauge_requirement": False, "gauge_consumption": False,
                               "gauge_reset": False, "ordinary_gauge_gains": "unchanged",
                               "temporary_move_slot_replacement": False,
                               "effect_frequency": "same_as_existing_z_move_per_action",
                               "pp": "ordinary_Judgment_pp_rules",
                               "runtime_state": "separate_action_context_not_manual_z_pending_flag"}})
            continue
        if name not in by_name:
            raise ValueError(f"unmapped assigned ability: {name}")
        row = by_name[name]
        normal, enhanced = row["불가사의"], row["강화"]
        overrides = []
        if name == "불굴의마음":
            normal, enhanced = normal.replace("이동속도", "스피드 저장단계"), enhanced.replace("이동속도", "스피드 저장단계")
            overrides.append("user: speed rank, not movement speed")
        if name == "가뭄":
            normal, enhanced = "층 입장 시 쾌청을 만든다.", "층 입장 시 큰가뭄(강한 쾌청)을 만든다."
            overrides.append("user: ordinary sun / strong sun")
        if name == "고대활성":
            common = "공격·방어·특수공격·특수방어·스피드 중 가장 높은 능력의 저장단계. 동률은 공격→방어→특공→특방→스피드. 햇살 새 적용 시 한 번, 적 처치 시 한 공격 행동당 한 번. 부스트에너지 조건 없음."
            normal, enhanced = "최고 능력 저장단계 +1. " + common, "최고 능력 저장단계 +2. " + common
            overrides.append("user: remove Booster Energy; retain sunlight/kill triggers")
        if "싸라기눈" in normal+enhanced:
            overrides.append("user: hail becomes snow; no periodic hail damage")
            normal, enhanced = normal.replace("싸라기눈", "설경"), enhanced.replace("싸라기눈", "설경")
        result.append({"key": name, "effect_table_number": int(row["번호"]),
                       "normal": normal, "enhanced": enhanced,
                       "status": "specified_not_implementation_certified", "overrides": overrides})
    return result


def legacy_ability_candidates(ability_rows, strings, evidence):
    """Record evidence, not new ID allocations. Alpha IDs differ from table IDs."""
    from true_patches.balance_change.patch_ability_names import RENAMES
    translation_path = REPO / "true_patches/korean/data/translations.json.gz"
    translations = json.loads(gzip.decompress(translation_path.read_bytes()))["text_e"]
    english_to_korean = {}
    for pair in translations.values():
        if isinstance(pair, dict) and "en" in pair and "ko" in pair:
            if "\n" not in pair["en"] and "[" not in pair["en"]:
                english_to_korean.setdefault(pair["en"], set()).add(normalize_ability(pair["ko"]))
    start = evidence["ability_name_start"]
    for row in ability_rows:
        candidates = []
        for ability_id in range(1, 255):
            original = strings[start+ability_id]
            current = RENAMES.get(ability_id, (original, original))[1]
            korean_names = english_to_korean.get(original, set()) | english_to_korean.get(current, set())
            if row["key"] in korean_names or row["key"] == current:
                candidates.append({"rom_id": ability_id, "alpha_name": original,
                                   "full_stack_name": current})
        row["legacy_rom_candidates"] = candidates
        row["runtime_id_status"] = "candidate_effect_audit_required" if candidates else "extended_registry_or_name_mapping_required"


def sprite_candidates(dex, forme, source_name, sprite_root, normalized_root, tracker):
    # Inventory, not a claim that every XML/package is ROM-ready.
    species = tracker.get(f"{dex:04d}", {})
    regional = next((v for k, v in (("알로라", "Alola"), ("가라르", "Galar"), ("히스이", "Hisui"))
                     if k in source_name), None)
    candidates = []
    for form_id, meta in species.get("subgroups", {}).items():
        if not forme:
            continue
        name = meta.get("name", "")
        want = re.sub(r"[^a-z]", "", forme.lower())
        if want and re.sub(r"[^a-z]", "", name.lower()) != want:
            continue
        if form_id == "0000":
            continue
        base = sprite_root / f"{dex:04d}" / form_id
        leaves = [base, base/"0000/0001", base/"0000/0002"]
        for leaf in leaves:
            if (leaf/"AnimData.xml").is_file():
                candidates.append({"path": leaf.relative_to(REPO).as_posix(),
                                   "kind": "official_form_normal", "tracker_name": name})
    species_dir = normalized_root / f"{dex:04d}"
    if species_dir.is_dir():
        for form_dir in sorted(species_dir.iterdir()):
            if not form_dir.is_dir():
                continue
            label = form_dir.name
            if forme:
                want = re.sub(r"[^a-z]", "", forme.lower())
                if want not in re.sub(r"[^a-z]", "", label.lower()):
                    continue
            elif regional and regional.lower() not in label.lower():
                continue
            elif not regional and not label.startswith("Base"):
                continue
            for color in ("Normal", "Shiny"):
                leaf = form_dir / color
                if (leaf/"AnimData.xml").is_file():
                    candidates.append({"path": leaf.relative_to(REPO).as_posix(),
                                       "kind": f"{'aura' if label.endswith('_Aura') else 'sprite'}_{color.lower()}",
                                       "form": label})
    return {"status": "candidates_only_phase5_must_validate",
            "source_region": regional,
            "candidates": candidates,
            "required_shiny": "official_form_shiny_aura" if forme else "base_shiny_aura",
            "portrait_policy": "reuse_existing_if_missing"}


def rules():
    weather = {}
    for family, targets in (("sun", ["fire_move"]), ("rain", ["water_move"]),
                            ("sand", ["rock_def_spdef", "ground_def_spdef", "steel_def_spdef"]),
                            ("snow", ["ice_def_spdef"])):
        for strength, fraction in (("normal", [6, 5]), ("strong", [3, 2])):
            weather[f"{family}_{strength}"] = {"family": family, "strength": strength,
                "factor": fraction, "targets": targets, "calculation_only": True,
                "can_be_replaced_by": ["strong"] if strength == "strong" else ["normal", "strong"]}
    weather["wind_strong"] = {"family": "wind", "strength": "strong", "factor": None,
                             "targets": [], "preserve_legacy_effects": True,
                             "can_be_replaced_by": ["strong"]}
    return {"phase": 0, "runtime_gameplay_enabled": False,
            "progression": {"mega": {"minimum_level": 80, "location": "Luminous Spring", "item": None},
                            "shiny_mega": {"requires_stage": "mega", "additional_level": None, "item": None},
                            "regression": {"shiny_mega": "same_branch_mega", "mega": "original_final_form"},
                            "branch_selection": "on_mega_evolution", "later_branch_switch": "not_enabled"},
            "abilities": {"normal": [1, 2], "mega": [1, 2, 3], "shiny_mega": ["1_II", "2_II", "3_II"],
                          "scope": "all_assigned_normal_and_enhanced_only", "trace_II_extra_candidate_filter": False,
                          "identical_ability_stacking": "once_per_unique_ability",
                          "effect_table_numbers_are_rom_ids": False},
            "speed": {"neutral": 10, "stored_min": 4, "stored_max": 16,
                      "movement_speed_separate": True, "stage_multiplier": "phase1_engine_audit_required"},
            "weather": weather, "weather_extra": {"snow_chip_damage": False,
                "strong_sun_alias": "Desolate Land", "strong_rain_alias": "Primordial Sea",
                "strong_wind_is_strong_weather": True,
                "trigger_checks": "family_not_exact_strength", "dual_type_bonus_stacks": False,
                "strong_replaces_normal_bonus": True, "weather_source_tracked_separately": True,
                "strong_priority": "most_recent_valid_strong_weather",
                "source_loss_or_suppression": "reevaluate_weather_sources_do_not_erase_unrelated_weather",
                "strong_sun_and_rain": "retain_existing_cataclysm_features"},
            "forms": {"temporary_changes_do_not_overwrite_permanent_stage": True,
                      "existing_roster_migration": "separate_not_applied_phase0",
                      "story_entities": "preserve_separate_not_migrated",
                      "evolution_history_bytes": "retain_existing_two_bytes_for_ordinary_lineage",
                      "mega_lineage_rate": "1.0_do_not_extend_ordinary_evolution_graph"},
            "excluded_systems": ["Electric Terrain", "Strong Electric Terrain", "Booster Energy"],
            "allocation": {"logical_form_ids_only_phase0": True, "physical_species_ids": None,
                "strategy": "explicit_extended_md_lookup_and_versioned_save_codec",
                "legacy_plus600_is_not_new_form_arithmetic": True,
                "caves": "allocate_at_apply_time_preserve_team_push_reservations"}}


def build(assets=None):
    assets = assets or REPO / "assets"
    assignment_rows = assignments(assets / ASSIGNMENTS)
    stat_rows = workbook_stats(assets / STATS)
    entries, strings, config, evidence = rom_evidence()
    names_start = config.string_index_data.string_blocks["Pokemon Names"].begin
    forms = json.loads((REPO / "true_patches/base_stats_speed/data/forms.json").read_text(encoding="utf-8"))
    sprite_root = REPO / "SpriteCollab-master/SpriteCollab-master/sprite"
    normalized_root = REPO / "output/sprite-normalized"
    tracker_path = sprite_root.parent / "tracker.json"
    tracker = json.loads(tracker_path.read_text(encoding="utf-8")) if tracker_path.exists() else {}
    source_ids = {i for r in assignment_rows for i in r["source_rom_ids"]}
    if source_ids != {i for r in stat_rows for i in r["rom_ids"]}:
        raise ValueError("assignment/stat source ID coverage differs")
    targets = []
    missing_official = []
    for row in assignment_rows:
        for species in row["source_rom_ids"]:
            stat_row = match_stats(row, species, stat_rows)
            entry = entries[species]
            dex = entry.national_pokedex_number
            if dex != stat_row["dex"]:
                raise ValueError(f"dex mismatch at {species}")
            forme = ""
            special = OFFICIAL_SPECIAL.get(dex)
            if special:
                forme = special[0]
            elif stat_row["method"] == "공식":
                branch = re.search(r"메가\s*([XYZ])(?:\s|$)", row["name"])
                forme = "Mega-" + branch.group(1) if branch else "Mega"
            official = next((f for f in forms if f["num"] == dex and f["forme"] == forme), None) if forme else None
            if forme and official is None:
                missing_official.append({"name": row["name"], "dex": dex, "forme": forme})
            base_stats = ORIGIN_STATS if special and forme == "Origin" else official["stats"] if official else stat_row["stats"]
            types = official["types"] if official else [t for t in (int(entry.type_primary), int(entry.type_secondary)) if t]
            branch_key = re.sub(r"[^a-z0-9]+", "_", forme.lower()) or "custom"
            original_class = "existing_official_mega_stage" if special and species == special[1] else "source_form_requires_runtime_classification"
            key = f"md{species:04d}:{branch_key}"
            targets.append({"key": key, "source_rom_id": species, "source_name": strings[names_start+species],
                "assignment_name": row["name"], "source_record": row["source_record"],
                "dex": dex, "official_form": forme or None, "source_class": original_class,
                "special_existing_target": special[1] if special else None,
                "special_base_source": special[2] if special else None,
                "abilities": row["abilities"], "base_abilities": row["abilities"][:2],
                "mega_stats": base_stats, "shiny_mega_stats": base_stats,
                "stats_order": ["HP", "Atk", "Def", "SpA", "SpD", "Spe"],
                "types": types, "stats_source": "user_origin_override" if special and forme == "Origin" else "local_official_forms" if official else "user_workbook",
                "workbook_reference": {"sheet": "메가 종족값", "row": stat_row["sheet_row"], "name": stat_row["name"]},
                "logical_mega": key+":mega", "logical_shiny": key+":shiny_mega",
                "runtime_mega_id": None, "runtime_shiny_id": None,
                "notes": row["notes"],
                "sprites": sprite_candidates(dex, forme, row["name"], sprite_root, normalized_root, tracker)})
    ability_rows = effects(assets / EFFECTS, {a for r in targets for a in r["abilities"]}, evidence["omnisense"])
    weather_setters = {"잔비": ("rain_normal", "rain_strong"),
                       "가뭄": ("sun_normal", "sun_strong"),
                       "모래날림": ("sand_normal", "sand_strong"),
                       "눈퍼뜨리기": ("snow_normal", "snow_strong"),
                       "시작의바다": ("rain_strong", "rain_strong"),
                       "끝의대지": ("sun_strong", "sun_strong"),
                       "델타스트림": ("wind_strong", "wind_strong")}
    for ability in ability_rows:
        if ability["key"] in weather_setters:
            normal, enhanced = weather_setters[ability["key"]]
            ability["weather_set"] = {"normal": normal, "enhanced": enhanced,
                                      "priority_and_effects": "rules.weather_and_weather_extra_override_source_wording"}
    legacy_ability_candidates(ability_rows, strings, evidence)
    collisions = []
    for species in sorted(source_ids):
        other = species+600
        if other < len(entries):
            a, b = entries[species], entries[other]
            role = "gender_counterpart_candidate" if int(b.gender) == 2 else "alternate_or_story_entry_do_not_auto_migrate"
            collisions.append({"source_id": species, "plus600_id": other, "classification": role,
                               "secondary_gender": int(b.gender), "secondary_base_form": int(b.base_form_index)})
    source_hashes = {name: digest(assets/name) for name in (ASSIGNMENTS, EFFECTS, STATS)}
    audit = {"assignment_rows": len(assignment_rows), "stat_rows": len(stat_rows),
        "source_rom_ids": len(source_ids), "expanded_targets": len(targets),
        "assigned_abilities": len(ability_rows), "rom_evidence": evidence,
        "legacy_counterparts": collisions,
        "missing_local_official_forms": missing_official,
        "pending_specifications": [],
        "asset_candidates_without_matching_shiny_aura": [r["key"] for r in targets
            if not any(c["kind"] == "aura_shiny" for c in r["sprites"]["candidates"])],
        "legacy_stat_max": 255, "required_stat_max": max(max(r["mega_stats"]) for r in targets),
        "new_stat_storage": "uint16_per_stat",
        "naive_clone_entry_count": len(entries)+2*len(targets)+2*sum(
            any(c["source_id"] == r["source_rom_id"] and c["classification"] == "gender_counterpart_candidate"
                for c in collisions) for r in targets),
        "special_form_profile_reuse_constraints": [
            {"existing_target": r["special_existing_target"], "incoming_key": r["key"],
             "incoming_abilities": r["abilities"], "existing_form_abilities": old["abilities"],
             "decision": "retain_source_profile_do_not_reuse_one_md_with_incompatible_ability_profiles"}
            for r in targets if r["special_existing_target"] and r["source_rom_id"] != r["special_existing_target"]
            for old in targets if old["source_rom_id"] == r["special_existing_target"]
            and old["abilities"] != r["abilities"]],
        "phase4_requirements": ["Audit all MD/name/learnset/sprite bounds and story exceptions before assigning physical IDs.",
            "Replace mega-specific +600/%600 lookups with explicit maps within mega_evolve hooks.",
            "Hook existing CalcStat/summary/initialization consumers; new IDs must not fall through to species zero.",
            "Stock roster stream stores species in 11 bits (verified ARM write/read instructions). Widen or version the codec; quicksave width remains a required execution audit.",
            "Existing EVS1 save tail spans 0xB700..0xC644; never reuse or overwrite it.",
            "Keep ordinary evolution history and doping; use explicit stage/regression mapping.",
            "Remove Giratina Origin from unrestricted form changes when mega gating is enabled."],
        "asset_requirements": ["Inventory contains candidates only; no pixel/ROM-conversion certification in phase0.",
            "Normalized aura generator excludes Primal; inspect original assets and resolve Primal shiny aura explicitly in phase5.",
            "New official Mega branches may lack sprites: normal aura fallback permitted; shiny official-form aura availability must be reported."]}
    return {"schema": 1, "module": "mega_evolve", "phase": 0,
            "provenance": {"assets_relative": assets.relative_to(REPO).as_posix() if assets.is_relative_to(REPO) else str(assets),
                "sha256": source_hashes, "official_forms_sha256": digest(REPO / "true_patches/base_stats_speed/data/forms.json"),
                "ability_translation_sha256": digest(REPO / "true_patches/korean/data/translations.json.gz")},
            "rules": rules(), "targets": targets, "abilities": ability_rows, "audit": audit}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, indent=2)+"\n"


def validate(registry):
    if registry["module"] != "mega_evolve" or registry["phase"] != 0:
        raise ValueError("unsupported phase-0 registry")
    targets = registry["targets"]
    keys = [r["key"] for r in targets]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate logical form keys")
    abilities = {r["key"] for r in registry["abilities"]}
    assigned = {a for r in targets for a in r["abilities"]}
    if assigned != abilities:
        raise ValueError("ability implementation scope differs from assignments")
    if "일렉트릭메이커" in abilities or "서핑테일" in abilities:
        raise ValueError("excluded terrain abilities still assigned")
    for row in targets:
        if len(row["abilities"]) != 3 or not all(row["abilities"]):
            raise ValueError("missing ability slot")
        if row["mega_stats"] != row["shiny_mega_stats"] or len(row["mega_stats"]) != 6:
            raise ValueError("shiny stat mismatch")
        if not all(isinstance(value, int) and 0 < value <= 65535 for value in row["mega_stats"]):
            raise ValueError("invalid uint16 base stat")
        if row["official_form"] == "Origin" and row["dex"] in (483, 484, 487) and row["mega_stats"] != ORIGIN_STATS:
            raise ValueError("Origin override lost")
        if row["runtime_mega_id"] is not None or row["runtime_shiny_id"] is not None:
            raise ValueError("physical species IDs must not be allocated in phase0")
    if registry["audit"]["missing_local_official_forms"]:
        raise ValueError("missing official type/stat definitions")
    return {"registry_sha256": hashlib.sha256(encoded(registry).encode()).hexdigest(),
            "phase": 0, "gameplay_changes": 0, "targets": len(targets), "abilities": len(abilities)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="update module registry from read-only local sources")
    args = parser.parse_args()
    data = build()
    validate(data)
    path = MODULE / "data/registry.json"
    if args.refresh:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded(data), encoding="utf-8")
    elif path.read_text(encoding="utf-8") != encoded(data):
        raise SystemExit("Phase-0 source/asset inventory changed; review and run --refresh.")
    print(json.dumps(validate(data), ensure_ascii=False))


if __name__ == "__main__":
    main()
