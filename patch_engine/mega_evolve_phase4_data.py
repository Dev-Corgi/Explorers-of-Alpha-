"""Prepare cloned MD rows and a separate uint16 permanent-form trailer.

This is deliberately separate from public activation: native consumers must
all be connected before the expanded monster.md can be installed.
"""
from __future__ import annotations
import copy
from skytemple_files.data.md.handler import MdHandler
from true_patches.mega_evolve.phase4 import load,binary
from true_patches.mega_evolve.phase2 import load as load_abilities


def prepare(rom):
    data=load()
    raw=rom.getFileByName('BALANCE/monster.md')
    md=MdHandler.deserialize(raw)
    if len(md.entries)!=data['first_species']:
        raise ValueError('phase4 source MD size mismatch')
    effects={a['id']:a['legacy_effect_id'] for a in load_abilities()['entries']}
    for row in data['rows']:
        entry=copy.deepcopy(md.entries[row['origin']])
        entry.md_index=row['species']
        # Preserve entid and resource/growth provenance. Do not accidentally
        # add clones to the origin's old pre-evolution candidates: phase6
        # will enable only the explicit spring path/level80 gate.
        entry.pre_evo_index=0
        entry.evo_method=0
        entry.evo_param1=0
        entry.evo_param2=0
        entry.can_evolve=False
        if row['official']:entry.type_primary,entry.type_secondary=row['types']
        entry.ability_primary,entry.ability_secondary=[effects[a] for a in row['abilities'][:2]]
        entry.sprite_index=md.entries[row['asset_source']].sprite_index
        # The native uint8 fields are not a place to truncate >255 stats.
        # Their old values remain compatibility data; the uint16 trailer is
        # authoritative for the connected CalcStat paths.
        md.entries.append(entry)
    result=bytes(MdHandler.serialize(md))
    if result[:8]!=b'MD\0\0'+data['total_species'].to_bytes(4,'little'):
        raise AssertionError('phase4 MD header mismatch')
    if result[8:8+data['first_species']*68]!=raw[8:8+data['first_species']*68]:
        raise AssertionError('phase4 changed existing MD entries')
    return result+binary(data)
