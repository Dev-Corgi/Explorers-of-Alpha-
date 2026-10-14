"""Read-only sprite selection and provenance; never alter SpriteCollab packages."""
from __future__ import annotations
import hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
from .phase4 import load as forms
MODULE=Path(__file__).resolve().parent
REPO=MODULE.parents[1]
ROOT=REPO/'SpriteCollab-master/SpriteCollab-master'
NORMALIZED=REPO/'output/sprite-normalized'

def token(value):return re.sub('[^a-z0-9]','',value.lower())

def package(path):
    if not (path/'AnimData.xml').is_file():return None
    files=sorted([path/'AnimData.xml',*path.glob('*-Anim.png'),*path.glob('*-Offsets.png'),*path.glob('*-Shadow.png')])
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    return dict(path=path.relative_to(REPO).as_posix(),files=hashes,
                sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest())

def build():
    registry=json.loads((MODULE/'data/registry.json').read_text(encoding='utf-8'))
    tracker=json.loads((ROOT/'tracker.json').read_text(encoding='utf-8'))
    assets=[];mapping=[];keys={};missing=[]
    targets={t['key']:t for t in registry['targets']}
    repairs=json.loads((MODULE/'data/phase5_repairs.json').read_text(encoding='utf-8'))['packages']
    derived={(p['settings']['dex'],p['settings']['color']):p for p in repairs}
    for row in forms()['rows']:
        t=targets[row['target']];dex=f"{row.get('dex',t['dex']):04d}";official=None
        for formid,meta in tracker.get(dex,{}).get('subgroups',{}).items():
            if t['official_form'] and token(meta.get('name',''))==token(t['official_form']):
                p=ROOT/'sprite'/dex/formid
                if (p/'AnimData.xml').is_file():official=p
        candidates=t['sprites']['candidates'];color='Normal' if row['stage']<=1 else 'Shiny'
        selected=None;policy=None
        if row['stage']==1 and official:
            # Prefer an explicit female animation package when available.
            female=official/'0000/0002'
            selected=female if row['origin']>=600 and (female/'AnimData.xml').is_file() else official
            policy='official_sprite'
        else:
            region=t['sprites']['source_region']
            dirs=[]
            species=NORMALIZED/dex
            if species.is_dir():
                for p in sorted(species.iterdir()):
                    if not p.name.endswith('_Aura'):continue
                    matches=(token(t['official_form']) in token(p.name)) if official else (
                        token(region) in token(p.name) if region else p.name.startswith('Base'))
                    if matches and (p/color/'AnimData.xml').is_file():dirs.append(p/color)
            if dirs:selected=dirs[0];policy='official_shiny_aura' if official else 'base_aura_fallback' if t['official_form'] else 'base_aura'
        replacement=derived.get((int(dex),color))
        if replacement:
            selected=REPO/replacement['path'];policy='user_requested_derived_aura'
            if not selected.is_dir():raise ValueError('Regenerate missing derived auras with phase5_repair')
        if row['stage']==0:
            selected=ROOT/'sprite'/dex;policy='new_ordinary_species'
        incomplete=selected is not None and not {0,7}<=set(int(a.findtext('Index','-1')) for a in ET.parse(selected/'AnimData.xml').findall('./Anims/Anim'))
        if selected is None or incomplete:
            missing.append(dict(species=row['species'],target=t['key'],dex=t['dex'],color=color,
                                required='official_sprite_complete' if incomplete else 'official_shiny_aura' if official else 'base_aura',
                                available_sprite=(selected if incomplete else official/'0001' if official and color=='Shiny' else ROOT/'sprite'/dex/('0000/0001' if color=='Shiny' else '')).relative_to(REPO).as_posix(),
                                reason='Walk/Idle animation missing' if incomplete else 'package absent'))
            continue
        key=selected.relative_to(REPO).as_posix()
        if key not in keys:
            keys[key]=len(assets);assets.append(dict(index=len(assets),policy=policy,**package(selected)))
        mapping.append(dict(species=row['species'],asset=keys[key]))
    return dict(schema=1,total_forms=len(forms()['rows']),assets=assets,mapping=mapping,missing=missing,
                tracker_sha256=hashlib.sha256((ROOT/'tracker.json').read_bytes()).hexdigest())

def main():
    data=build();(MODULE/'data/phase5_assets.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"sprite inventory: {len(data['assets'])} unique packages, {len(data['mapping'])}/{data['total_forms']} forms selected")
    seen=set()
    for m in data['missing']:
        k=(m['target'],m['color'])
        if k in seen:continue
        seen.add(k);print('MISSING',m['target'],m['color'],m['required'])
if __name__=='__main__':main()
