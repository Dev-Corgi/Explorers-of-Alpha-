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
    '절대안깸':['seven_native_status_immunities'],
    '스위트베일':['native_sleep_yawn_room_aura'],
    '아로마베일':['native_infatuation_taunt_encore_seal_room_aura'],
    '철가시':['once_per_action','fatal_hit','native_fixed_damage_wrapper_abi'],
    '컬리헤어':['once_per_action','numeric_speed_drop'],
    '전기로바꾸기':['calculation_does_not_consume','consume_on_successful_hit','same_action_multitarget_bonus'],
    '무아지경':['physical_attack_stat_multiplier','unaware_and_nested_calculations','first_successful_hit_move_lock',
                'native_move_permission','exhausted_pp_regular_attack_struggle','suppression_and_floor_reset'],
    '떠도는영혼':['one_slot_grade_transfer','highest_grade_unique_candidates','protected_profiles','once_per_action',
                  'contact_only_dispatch','permanent_restore','non_target_native_floor_restore'],
    '굳건한신념':['native_redirect_block_bypass','original_target_retained','target_immunity_retained','suppression'],
}


def build():
    data=load()
    return {'schema':1,'phase':3,'activation':'not_enabled',
            'test':'python -B -X utf8 -m true_patches.mega_evolve.verify_phase3',
            'additional_tests':['python -B -X utf8 -m true_patches.mega_evolve.verify_phase3_actions'],
            'boundary':'Verified paths are not whole-ability certification. Native ID matches are not proof of correct normal effects.',
            'shared_phase7_research':['status_hooks.py','phase3.json','phase3_status_generated.S generated at link time','runtime/phase3_hooks.S'],
            'abilities':[{'key':row['key'],'id':row['id'],'legacy_effect_id':row['legacy_effect_id'],
                          'family':row['family'],'normal_status':'partial' if row['key'] in VERIFIED else 'pending_audit',
                          'verified_paths':VERIFIED.get(row['key'],[]),'enhanced_status':'phase7'}
                         for row in data['abilities']]}


if __name__=='__main__':
    (MODULE/'data/phase3_coverage.json').write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
