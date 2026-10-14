"""User-approved ordinary evolutions, keeping all existing form IDs stable."""
import json
from pathlib import Path
MODULE=Path(__file__).resolve().parent

def load():
    source=json.loads((MODULE/'data/phase5_new_species_source.json').read_text(encoding='utf-8'))
    by_id={s['id']:s for s in source['species']}
    result=[]
    for dex,parent,first,en,ko,types,old_stats,name,learn,portrait in (
        (982,233,2269,'Dudunsparce','노고고치',[1,0],[100,70,70,65,65,45],20624,553,2048),
        (899,261,2271,'Wyrdeer','신비록',[1,11],[73,95,62,85,65,85],20625,554,2049)):
        s=by_id[dex]
        result.append(dict(dex=dex,parent=parent,species=[first,first+1],
                           target=f'md{parent:04d}:custom',en=en,ko=ko,types=types,
                           stats=s['stats'],old_stats=old_stats,name_index=name,
                           learnset_index=learn,portrait_id=portrait,level=20,moves=s['moves']))
    return result

def scaled_stats(item,old_mega):
    # Exact rational multiplication and round half up, without float drift.
    return [(base*mega*2+old)//(old*2)
            for base,mega,old in zip(item['stats'],old_mega,item['old_stats'])]

def header():
    rows=[]
    for item in load():
        for gender,species in enumerate(item['species']):
            rows.append('{'+','.join(map(str,(species,item['parent']+600*gender,
                item['name_index'],item['learnset_index'],item['portrait_id'],gender)))+'}')
    return ('typedef struct { unsigned short species,parent,name,learn,portrait,gender; } MENewSpecies;\n'
            'static const MENewSpecies me_new_species[4]={'+','.join(rows)+'};\n')
