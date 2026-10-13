"""Persistent effect coverage, deliberately distinct from native ID matching."""
from __future__ import annotations
import json
from pathlib import Path
from .phase3 import load
MODULE=Path(__file__).resolve().parent

VERIFIED={
    '쓱쓱':['numeric_weather_speed','movement_query_context'],
    '엽록소':['numeric_weather_speed','movement_query_context'],
    '모래헤치기':['numeric_weather_speed','movement_query_context'],
    '눈치우기':['numeric_weather_speed','movement_query_context'],
    '불굴의마음':['native_event_numeric_speed'],
    '속보':['native_event_numeric_speed'],
    '전기엔진':['native_event_numeric_speed'],
    '일렉트릭스킨':['resolved_type_conversion','action_scoped_multiplier','slot_priority'],
    '프리즈스킨':['resolved_type_conversion','slot_priority'],
    '절대안깸':['seven_native_status_immunities','dream_eater_virtual_sleep','player_enemy_rest_guard','global_action_sleep_unchanged'],
    '스위트베일':['native_sleep_yawn_room_aura','rest_napping_guard'],
    '아로마베일':['native_infatuation_taunt_encore_seal_room_aura'],
    '철가시':['once_per_action','fatal_hit','native_fixed_damage_wrapper_abi'],
    '컬리헤어':['once_per_action','numeric_speed_drop'],
    '전기로바꾸기':['calculation_does_not_consume','consume_on_successful_hit','same_action_multitarget_bonus'],
    '무아지경':['physical_attack_stat_multiplier','unaware_and_nested_calculations','first_successful_hit_move_lock',
                'native_move_permission','exhausted_pp_regular_attack_struggle','suppression_and_floor_reset'],
    '떠도는영혼':['one_slot_grade_transfer','highest_grade_unique_candidates','protected_profiles','once_per_action',
                  'contact_only_dispatch','permanent_restore','non_target_native_floor_restore'],
    '굳건한신념':['native_redirect_block_bypass','original_target_retained','target_immunity_retained','suppression'],
    '라이트메탈':['floor_trap_boundary_50_percent','forced_activation_exclusion','direct_trap_entry_preserved','suppression',
                  'native_weight_move_lookup','composed_weight_modifiers_and_mold_breaker'],
    '헤비메탈':['native_blow_away_guard','suppression_and_mold_breaker','native_continuation_abi',
                'native_weight_move_lookup','composed_weight_modifiers_and_mold_breaker'],
    '수확':['eight_actual_berry_identities','ordinary_sun_12_25_percent','single_use_consumption_boundary','stacking_and_suppression'],
    '되새김질':['eight_actual_berry_identities','20_percent_retention','single_use_consumption_boundary','stacking_and_duplicates'],
    '픽업':['audited_31_seed_berry_pool','reviver_joy_golden_exclusions','bag_capacity_team_and_50_percent',
            'once_per_floor','replace_raw_byte_legacy_block'],
    '화학의힘':['action_end_nearest_same_room_ally_copy','grade_dedup_protected_candidates',
                'nested_actions_reset_death_and_temporary_restore'],
    '잠복':['successful_walk_epoch','next_action_expiry','first_successful_holder_hit',
             'miss_calculation_suppression_and_reuse'],
    '도주':['quarter_hp_enemy_hit','closest_ally_safe_floor_destination','floor_once',
             'failed_destination_suppression_and_legacy_ai_queries'],
    '고대활성':['accepted_native_sunlight_boundary','quiet_weather_update_no_repeat','weather_ability_suppression',
                 'sunny_entry_once','highest_stat_and_tie_priority','own_ko_once_per_action'],
    '치유의마음':['50_percent_eligible_adjacent_ally','one_uniform_target','seven_status_class_cures_native_arm',
                   'other_statuses_preserved','sleep_five_argument_abi_no_napping_heal'],
    '감미로운꿀':['floor_wide_foes_only_evasion_drop','floor_once_and_regrant','next_floor_reapply'],
    '슬로스타트':['numeric_speed_minus_three','floor_once'],
    '변덕쟁이':['uniform_distinct_stats','numeric_speed_and_accuracy','floor_once'],
    '소울하트':['same_room_faint_once_per_action'],
    '자기과신':['own_opponent_ko_each_target'],
    '바람타기':['audited_damaging_wind_ids','post_redirection_resolved_target_guard','once_per_action_attack_raise',
                 'suppression_and_mold_breaker','tailwind_first_application','speed_counter_ownership_refresh_expiry_reuse',
                 'native_speed_increase_argument_stack_return_abi'],
}


def build():
    data=load()
    return {'schema':1,'phase':3,'activation':'not_enabled',
            'test':'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3',
            'additional_tests':['python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_actions',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_world',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_items',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_sleep',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_faint',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_movement',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_escape',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_loader',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_events',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_weight_wind',
                                'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_tailwind'],
            'boundary':'Verified paths are not whole-ability certification. Native ID matches are not proof of correct normal effects.',
            'shared_phase7_research':['status_hooks.py','phase3.json','phase3_status_generated.S generated at link time','runtime/phase3_hooks.S'],
            'abilities':[{'key':row['key'],'id':row['id'],'legacy_effect_id':row['legacy_effect_id'],
                          'family':row['family'],'normal_status':'partial' if row['key'] in VERIFIED else 'pending_audit',
                          'verified_paths':VERIFIED.get(row['key'],[]),'enhanced_status':'phase7'}
                         for row in data['abilities']]}


if __name__=='__main__':
    (MODULE/'data/phase3_coverage.json').write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
