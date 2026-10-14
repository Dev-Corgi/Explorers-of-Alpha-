"""Regenerate assigned aura packages without per-action runtime loading.

Use system Python (Pillow/numpy/scipy). Original packages remain read-only.
Only metadata/provenance belongs in git; generated images stay in .cache.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
import argparse, hashlib, json, shutil, sys

MODULE=Path(__file__).resolve().parent
REPO=MODULE.parents[1]
CACHE=MODULE/'.cache/phase5_pose'
DATA=MODULE/'data/phase5_aura_pose.json'
sys.path.insert(0,str(REPO/'tools'))


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def hashes(directory):
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.iterdir()) if p.is_file()}


def package(directory):
    names=['AnimData.xml',*(p.name for pattern in ('*-Anim.png','*-Offsets.png','*-Shadow.png')
                            for p in directory.glob(pattern))]
    files={name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in sorted(names)}
    return dict(path=directory.relative_to(REPO).as_posix(),files=files,sha256=digest(files))


def prepare_input(job,directory):
    """Reproduce the authorized palette edits, independently of old aura files."""
    from PIL import Image
    source=REPO/job['source']
    if hashes(source)!=job['source_hashes']:raise ValueError('Source changed: '+str(source))
    mapping=job.get('palette')
    budget=job.get('body_palette_budget')
    if not mapping and not budget:return source
    target=directory/'input';target.mkdir(exist_ok=True)
    for p in source.iterdir():
        if p.is_file():shutil.copyfile(p,target/p.name)
    if mapping:
        convert={tuple(bytes.fromhex(a)):tuple(bytes.fromhex(b)) for a,b in mapping.items()}
        for p in target.glob('*-Anim.png'):
            image=Image.open(p).convert('RGBA')
            used={px[:3] for px in image.getdata() if px[3]}
            if used-convert.keys():raise ValueError('Unmapped body color in '+str(p))
            image.putdata([convert[px[:3]]+(px[3],) if px[3] else px for px in image.getdata()]);image.save(p)
    if budget:
        colors=Counter()
        for p in target.glob('*-Anim.png'):
            colors.update(px[:3] for px in Image.open(p).convert('RGBA').getdata() if px[3])
        replacement={c:c for c in colors}
        while len(colors)>budget:
            a,b=min(((a,b) for a in colors for b in colors if a<b),
                    key=lambda pair:(sum((pair[0][i]-pair[1][i])**2 for i in range(3)),pair))
            if colors[a]>colors[b]:a,b=b,a
            colors[b]+=colors.pop(a)
            replacement={c:b if v==a else v for c,v in replacement.items()}
        for p in target.glob('*-Anim.png'):
            image=Image.open(p).convert('RGBA')
            image.putdata([replacement[px[:3]]+(px[3],) if px[3] else px for px in image.getdata()]);image.save(p)
    return target


def run(job):
    import pmd_aura
    directory=CACHE/digest(job);output=directory/'aura';marker=directory/'provenance.json'
    if marker.is_file():
        saved=json.loads(marker.read_text('utf-8'))
        if saved['job']!=job or saved['output_hashes']!=hashes(output):raise ValueError('Aura output drift')
        return saved
    directory.mkdir(parents=True,exist_ok=True)
    source=prepare_input(job,directory)
    args=pmd_aura.parser().parse_args(['--sprite-dir',str(source),'--output',str(output),
         '--types',*job['types'],'--all','--no-previews','--palette-limit',str(job['palette_limit']),
         '--width',str(job['width']),'--flame-height',str(job['flame_height']),
         '--gradient-steps',str(job['gradient_steps']),'--seed',str(job['seed'])])
    pmd_aura.build(args)
    result=dict(job=job,output_hashes=hashes(output),asset=dict(index=job['index'],policy=job['policy'],**package(output)))
    marker.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def plan():
    if DATA.is_file():
        jobs=[r['job'] for r in json.loads(DATA.read_text('utf-8'))['packages']]
        tool_hash=hashlib.sha256((REPO/'tools/pmd_aura.py').read_bytes()).hexdigest()
        palettes=json.loads((MODULE/'data/phase5_shiny_palettes.json').read_text('utf-8'))['palettes']
        for job in jobs:
            job['tool_sha256']=tool_hash
            if job.get('palette'):
                dex=str(int(job['source'].split('/sprite/')[1].split('/')[0]))
                job.update(palette=palettes[dex]['colors'],palette_style=palettes[dex]['style'])
        return jobs
    assets=json.loads((MODULE/'data/phase5_assets.json').read_text('utf-8'))
    forms=json.loads((MODULE/'data/phase4_forms.json').read_text('utf-8'))['rows']
    by_species={r['species']:r for r in forms}
    types=['none','normal','fire','water','grass','electric','ice','fighting','poison',
           'ground','flying','psychic','bug','rock','ghost','dragon','dark','steel','fairy']
    tool_hash=hashlib.sha256((REPO/'tools/pmd_aura.py').read_bytes()).hexdigest()
    palettes=json.loads((MODULE/'data/phase5_shiny_palettes.json').read_text('utf-8'))['palettes']
    jobs=[]
    for asset in assets['assets']:
        if asset['policy']=='new_ordinary_species':continue
        old=REPO/asset['path'];row=by_species[next(m['species'] for m in assets['mapping'] if m['asset']==asset['index'])]
        report=json.loads((old/'aura-report.json').read_text('utf-8')) if (old/'aura-report.json').is_file() else {}
        job=dict(index=asset['index'],previous_path=asset['path'],previous_sha256=asset['sha256'],
                 policy='official_aura' if asset['policy']=='official_sprite' else asset['policy'],
                 types=report.get('types') or list(dict.fromkeys(types[t] for t in row['types'] if t)),
                 palette_limit=report.get('palette_limit',32),width=3,flame_height=4,
                 gradient_steps=report.get('gradient_steps',3),seed=report.get('seed',0),tool_sha256=tool_hash)
        if asset['policy']=='user_requested_derived_aura':
            settings=json.loads((old.parent/'provenance.json').read_text('utf-8'))['settings']
            source=REPO/'SpriteCollab-master/SpriteCollab-master/sprite'/f"{settings['dex']:04d}"/settings['suffix']
            job['body_palette_budget']=settings['body_palette_budget']
            if settings.get('reference'):
                selected=palettes[str(settings['dex'])]
                job.update(palette=selected['colors'],palette_style=selected['style'])
        elif report:
            source=old.parent.parent/old.parent.name.removesuffix('_Aura')/old.name
        else:source=old
        if not (source/'AnimData.xml').is_file():raise ValueError('Missing original input: '+str(source))
        job.update(source=source.relative_to(REPO).as_posix(),source_hashes=hashes(source))
        jobs.append(job)
    return jobs


def overlay(inventory):
    if not DATA.is_file():return inventory
    pinned=json.loads(DATA.read_text('utf-8'))
    replacements={r['job']['index']:r for r in pinned['packages']}
    for i,asset in enumerate(inventory['assets']):
        if i not in replacements:continue
        r=replacements[i]
        if asset['sha256'] not in (r['job']['previous_sha256'],r['asset']['sha256']):
            raise ValueError('Aura inventory source drift')
        inventory['assets'][i]=r['asset']
    return inventory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ensure',action='store_true');parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args()
    jobs=[r['job'] for r in json.loads(DATA.read_text('utf-8'))['packages']] if args.ensure else plan()
    if any(j['tool_sha256']!=hashlib.sha256((REPO/'tools/pmd_aura.py').read_bytes()).hexdigest() for j in jobs):
        raise ValueError('Aura generator changed; regenerate pinned inventory')
    results=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(run,job):job for job in jobs}
        for future in as_completed(futures):
            results.append(future.result())
            if len(results)%25==0:print(f'Aura packages {len(results)}/{len(jobs)}',flush=True)
    results.sort(key=lambda r:r['job']['index'])
    report=dict(schema=1,policy='canonical source pose; waves only on one-shot groups; all Mega forms have aura',packages=results)
    if args.ensure:
        if report!=json.loads(DATA.read_text('utf-8')):raise ValueError('Regenerated aura provenance drift')
    else:DATA.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Aura packages ready:',len(results),flush=True)


if __name__=='__main__':main()
