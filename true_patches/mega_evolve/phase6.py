"""Spring progression, branch labels and bilingual strings; no inferred IDs."""
import json
from pathlib import Path
from .phase4 import load as forms
from .phase5_routes import build as routes
MODULE=Path(__file__).resolve().parent
STRINGS=[
 ('mega_confirm','Proceed with Mega Evolution?','메가 진화를 진행하시겠습니까?'),
 ('shiny_confirm','Proceed with Shiny Mega Evolution?','이로치 메가 진화를 진행하시겠습니까?'),
 ('mega_select','Choose a Mega Evolution.','메가 진화 분기를 선택하십시오.'),
 ('shiny_select','Choose a Shiny Mega Evolution.','이로치 메가 진화를 선택하십시오.'),
 ('mega_success','Mega Evolution is complete!','메가 진화가 완료되었습니다!'),
 ('shiny_success','Shiny Mega Evolution is complete!','이로치 메가 진화가 완료되었습니다!'),
 ('branch_mega','Mega','메가'),('branch_x','Mega X','메가 X'),
 ('branch_y','Mega Y','메가 Y'),('branch_z','Mega Z','메가 Z'),
 ('branch_primal','Primal Reversion','원시회귀'),('branch_origin','Origin Form','오리진폼'),
]

def build():
    data=forms();contract=routes()
    entries=[dict(key=k,index=20626+i,en=en,ko=ko) for i,(k,en,ko) in enumerate(STRINGS)]
    names={r['key']:r['index']+1 for r in entries}
    branch={'Mega':'branch_mega','Mega-X':'branch_x','Mega-Y':'branch_y',
            'Mega-Z':'branch_z','Primal':'branch_primal','Origin':'branch_origin'}
    by_id={r['species']:r for r in data['rows']}
    edges=[dict(r,label=0 if r['target_stage']==2 else
                names[branch[by_id[r['target']]['branch']]] if r['target_stage']==1 else 0)
           for r in contract['routes']]
    # A shiny legacy Primal/Origin regresses to its canonical Mega record.
    # That record must be able to awaken again, without being an additional
    # forward Mega choice from the already-Mega legacy origin.
    for species in contract['compatibility_only_mega_ids']:
        edges.append(dict(source=species,target=by_id[species]['shiny'],source_stage=1,
                          target_stage=2,level=None,items=[],label=0))
    edges.sort(key=lambda r:(r['source'],r['target']))
    if any(sum(r['source']==source for r in edges)>8 for source in {r['source'] for r in edges}):
        raise ValueError('Spring eight-choice capacity exceeded')
    return dict(schema=1,total_species=data['total_species'],routes=edges,
                compatibility_only_mega_ids=contract['compatibility_only_mega_ids'],strings=entries)

def load():
    saved=json.loads((MODULE/'data/phase6.json').read_text(encoding='utf-8'))
    if saved!=build():raise ValueError('stale phase6 Spring data')
    return saved

if __name__=='__main__':
    data=build();(MODULE/'data/phase6.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('phase6:',len(data['routes']),'routes,',len(data['strings']),'bilingual strings')
