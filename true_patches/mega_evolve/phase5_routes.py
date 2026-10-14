"""Explicit Spring routing contract; phase6 must consume this, not infer IDs.

Stored/story-origin profiles retain separate physical IDs. Existing Primal
origins are already Mega and awaken directly; their allocated Mega clone IDs
remain compatibility records, never an additional evolution choice.
"""
import json
from .phase4 import load as forms
from .new_species import load as new_species
from .phase5 import MODULE

def build():
    registry=json.loads((MODULE/'data/registry.json').read_text(encoding='utf-8'))
    targets={t['key']:t for t in registry['targets']}
    routes=[];compatibility=[]
    for row in forms()['rows']:
        if row['stage']!=1:continue
        t=targets[row['target']]
        if t['official_form'] in ('Primal','Origin') and row['origin']==t['special_existing_target']:
            routes.append(dict(source=row['origin'],target=row['shiny'],
                               source_stage=1,target_stage=2,level=None,items=[]))
            compatibility.append(row['species'])
        else:
            routes.append(dict(source=row['origin'],target=row['species'],
                               source_stage=0,target_stage=1,level=80,items=[]))
            routes.append(dict(source=row['species'],target=row['shiny'],
                               source_stage=1,target_stage=2,level=None,items=[]))
    for item in new_species():
        for gender,species in enumerate(item['species']):
            routes.append(dict(source=item['parent']+gender*600,target=species,
                               source_stage=0,target_stage=0,level=20,items=[]))
    return dict(schema=1,activation_phase=6,ordinary_level20_activation_phase=5,
                routes=routes,compatibility_only_mega_ids=compatibility)

def main():
    data=build()
    (MODULE/'data/phase5_evolution_routes.json').write_text(
        json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Evolution routes:',len(data['routes']),'Primal compatibility IDs:',data['compatibility_only_mega_ids'])

if __name__=='__main__':main()
