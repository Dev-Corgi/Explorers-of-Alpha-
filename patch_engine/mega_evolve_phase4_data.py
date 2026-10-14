"""Prepare cloned MD rows and a separate uint16 permanent-form trailer.

This is deliberately separate from public activation: native consumers must
all be connected before the expanded monster.md can be installed.
"""
from __future__ import annotations
import copy
from skytemple_files.data.md.handler import MdHandler
from true_patches.mega_evolve.phase4 import load,binary
from true_patches.mega_evolve.phase2 import load as load_abilities
from true_patches.mega_evolve.new_species import load as new_species


def prepare(rom):
    data=load()
    raw=rom.getFileByName('BALANCE/monster.md')
    md=MdHandler.deserialize(raw)
    if len(md.entries)!=data['first_species']:
        raise ValueError('phase4 source MD size mismatch')
    effects={a['id']:a['legacy_effect_id'] for a in load_abilities()['entries']}
    for row in data['rows']:
        entry=copy.deepcopy(md.entries[row.get('template',row['origin'])])
        entry.md_index=row['species']
        # Preserve entid and resource/growth provenance. Do not accidentally
        # add clones to the origin's old pre-evolution candidates: phase6
        # will enable only the explicit spring path/level80 gate.
        entry.pre_evo_index=0
        entry.evo_method=0
        entry.evo_param1=0
        entry.evo_param2=0
        entry.can_evolve=False
        if row['official'] or 'template' in row:entry.type_primary,entry.type_secondary=row['types']
        if 'dex' in row:entry.national_pokedex_number=row['dex']
        if row['stage']==0:
            entry.pre_evo_index=row['parent'];entry.evo_method=1;entry.evo_param1=20
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


def prepare_files(rom):
    from .korean_codec import parse_str_file,build_str_file,decode_english
    from skytemple_files.common.types.file_types import FileType
    from skytemple_files.data.waza_p._model import MoveLearnset,LevelUpMove
    from PIL import Image
    from pathlib import Path
    files={'BALANCE/monster.md':prepare(rom)}
    text=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    waza=FileType.WAZA_P.deserialize(rom.getFileByName('BALANCE/waza_p.bin'))
    kao=FileType.KAO.deserialize(rom.getFileByName('FONT/kaomado.kao'))
    if len(waza.learnsets)!=553 or kao.n_entries()!=2047:
        raise ValueError('new species learnset/portrait source count changed')
    kao.expand(2049)
    repo=Path(__file__).resolve().parents[1]
    for item in new_species():
        index=item['name_index']
        if index<len(text) and decode_english(text[index]).strip():
            raise ValueError('new species name index occupied')
        text.extend([b'']*max(0,index+1-len(text)));text[index]=item['en'].encode('ascii')
        moves=item['moves']
        levels=[LevelUpMove(m['rom_id'],m['level']) for m in moves if m['method']==1]
        machines=sorted({m['rom_id'] for m in moves if m['method'] in (3,4)})
        eggs=sorted({m['rom_id'] for m in moves if m['method']==2})
        if len(waza.learnsets)!=item['learnset_index']:raise ValueError('learnset append order')
        waza.learnsets.append(MoveLearnset(levels,machines,eggs))
        root=repo/f"SpriteCollab-master/SpriteCollab-master/portrait/{item['dex']:04d}"
        portrait=Image.open(root/'Normal.png').convert('RGB')
        # New forms reuse the ordinary evolution's portrait. Only Normal is
        # required; fallback emotions reuse that portrait rather than blanks.
        for emotion in range(20):kao.set_from_img(item['portrait_id']-1,emotion,portrait)
    files.update({'MESSAGE/text_e.str':build_str_file(text),
                  'BALANCE/waza_p.bin':bytes(FileType.WAZA_P.serialize(waza)),
                  'FONT/kaomado.kao':bytes(FileType.KAO.serialize(kao))})
    return files
