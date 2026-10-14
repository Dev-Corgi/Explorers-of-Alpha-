"""Explicit permanent-form identities. Uses the persisted phase0/2 inventory.

No +600/mod600 inference is applied to newly allocated identities. Existing
story/alternate entries are distinct origins even when their sprites match.
"""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path
from .phase2 import load as load_abilities
from .new_species import load as new_species,scaled_stats

MODULE=Path(__file__).resolve().parent


def build():
    registry=json.loads((MODULE/'data/registry.json').read_text(encoding='utf-8'))
    identities={a['key']:a['id'] for a in load_abilities()['entries']}
    sexes={r['source_id']:r['plus600_id'] for r in registry['audit']['legacy_counterparts']
           if r['classification']=='gender_counterpart_candidate'}
    start=registry['audit']['rom_evidence']['md_entries']
    rows=[]
    for target in registry['targets']:
        origins=[target['source_rom_id']]
        if origins[0] in sexes:origins.append(sexes[origins[0]])
        for origin in origins:
            mega=start+len(rows);shiny=mega+1
            for stage,species,parent in ((1,mega,origin),(2,shiny,mega)):
                rows.append(dict(species=species,origin=origin,target=target['key'],
                                 branch=target['official_form'] or 'Mega',stage=stage,
                                 parent=parent,mega=mega,shiny=shiny,
                                 abilities=[identities[k] for k in target['abilities']],
                                 grade=stage-1,types=(target['types']+[0])[:2],stats=target['mega_stats'],
                                 asset_source=target['special_existing_target'] or origin,
                                 portrait_source=origin,learnset_source=origin,
                                 name_source=origin,official=bool(target['official_form'])))
    for item in new_species():
        for gender,new_id in enumerate(item['species']):
            origin=item['parent']+gender*600
            pair=[r for r in rows if r['target']==item['target'] and r['origin']==origin]
            if len(pair)!=2:raise ValueError('new evolution form pair missing')
            for row in pair:
                row.update(template=origin,origin=new_id,name_source=new_id,
                           learnset_source=new_id,portrait_source=new_id,types=item['types'],
                           stats=scaled_stats(item,row['stats']),dex=item['dex'])
                if row['stage']==1:row['parent']=new_id
            rows.append(dict(species=new_id,origin=new_id,template=origin,target=item['target'],
                             branch='Ordinary',stage=0,parent=origin,mega=pair[0]['species'],
                             shiny=pair[1]['species'],abilities=pair[0]['abilities'][:2]+[0],
                             grade=0,types=item['types'],stats=item['stats'],asset_source=origin,
                             portrait_source=new_id,learnset_source=new_id,name_source=new_id,
                             official=False,dex=item['dex']))
    result=dict(schema=1,first_species=start,total_species=start+len(rows),
                save_bits=12,stat_bits=16,stats_order=['HP','Atk','Def','SpA','SpD','Spe'],
                registry_sha256=hashlib.sha256((MODULE/'data/registry.json').read_bytes()).hexdigest(),
                rows=rows)
    validate(result)
    return result


def validate(data):
    if data['schema']!=1 or data['save_bits']!=12 or data['stat_bits']!=16:
        raise ValueError('phase4 storage schema mismatch')
    first=data['first_species'];rows=data['rows'];total=data['total_species']
    if total!=first+len(rows) or total>4096 or len(rows)%2:
        raise ValueError('phase4 species capacity/pair mismatch')
    seen=set()
    for index,row in enumerate(rows):
        if row['species']!=first+index or not 0<row['origin']<total:
            raise ValueError('phase4 noncontiguous identities or invalid origin')
        if len(row['stats'])!=6 or any(not 0<v<=65535 for v in row['stats']):
            raise ValueError('phase4 stat width mismatch')
        if len(row['types'])!=2 or any(not 0<=v<=18 for v in row['types']):
            raise ValueError('phase4 type mismatch')
        if len(row['abilities'])!=3 or any(not (256<=v<462 or (row['stage']==0 and i==2 and v==0)) for i,v in enumerate(row['abilities'])):
            raise ValueError('phase4 ability identity mismatch')
        if row['stage'] not in (0,1,2) or row['grade']!=max(0,row['stage']-1):
            raise ValueError('phase4 stage mismatch')
        key=(row['origin'],row['target'],row['stage'])
        if key in seen:raise ValueError('phase4 duplicate origin/branch/stage')
        seen.add(key)
    evolved=[r for r in rows if r['stage']]
    for mega,shiny in zip(evolved[::2],evolved[1::2]):
        if (mega['stage'],shiny['stage'])!=(1,2):raise ValueError('phase4 pair order')
        if mega['parent']!=mega['origin'] or shiny['parent']!=mega['species']:
            raise ValueError('phase4 devolution mismatch')
        for key in ('origin','target','types','stats','abilities','mega','shiny'):
            if mega[key]!=shiny[key]:raise ValueError('phase4 incompatible pair')
    return data


def load():
    data=json.loads((MODULE/'data/phase4_forms.json').read_text(encoding='utf-8'))
    if data!=build():raise ValueError('stale phase4 form mapping')
    return data


def header(data):
    return ('#define ME_FORM_FIRST '+str(data['first_species'])+'\n'
            '#define ME_FORM_COUNT '+str(len(data['rows']))+'\n'
            'typedef struct { unsigned short species,origin,parent,mega,shiny,stage; '
            'unsigned short stats[6],ability[3],grade; } MEForm;\n')


def binary(data):
    """MD trailer: versioned fixed records, not repurposed native MD fields."""
    records=b''.join(struct.pack('<16H',*[r[k] for k in ('species','origin','parent','mega','shiny','stage')],
                                *r['stats'],*r['abilities'],r['grade']) for r in data['rows'])
    return struct.pack('<4I',0x3446454D,1,data['first_species'],len(data['rows']))+records


if __name__=='__main__':
    data=build()
    (MODULE/'data/phase4_forms.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"phase4 forms: {len(data['rows'])} new rows; {data['total_species']} total IDs")
