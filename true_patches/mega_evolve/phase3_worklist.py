"""Definition-based work candidates, distinct from verified effect coverage.
Keep the agreed 92/87/27 split reproducible instead of re-reading all effects.
"""
from .phase3 import load

def classify(row):
    if not row['legacy_effect_id']:return 'new_handler'
    if (row['normal'].startswith('[기존') or row['key']=='Omniscience') and row['key'] not in {
        '불굴의마음','점착','픽업'}:return 'reuse_candidate'
    return 'modify_or_connect'

def build():
    rows=load()['abilities']
    return {kind:[row['key'] for row in rows if classify(row)==kind]
            for kind in ('reuse_candidate','modify_or_connect','new_handler')}
