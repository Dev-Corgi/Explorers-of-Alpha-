"""Reproducible derived aura packages; SpriteCollab and user tool stay read-only.

Run with the Python that provides the user aura tool's numpy/scipy dependencies.
Generated images belong in the ignored cache, with source hashes in the report.
"""
from pathlib import Path
from collections import Counter
import hashlib, json, shutil, subprocess, sys
import urllib.request
from PIL import Image

MODULE = Path(__file__).resolve().parent
REPO = MODULE.parents[1]
ROOT = REPO / 'SpriteCollab-master/SpriteCollab-master/sprite'
CACHE = MODULE / '.cache/phase5_fix'

# dex, source suffix, color, aura types, optional reference palette.
JOBS = [
    (99, '', 'Normal', ['water'], None),
    (982, '', 'Normal', ['normal'], None),
    (982, '0000/0001', 'Shiny', ['normal'], None),
    (899, '', 'Normal', ['normal', 'psychic'], None),
    (899, '0000/0001', 'Shiny', ['normal', 'psychic'], None),
    (212, '', 'Normal', ['bug', 'steel'], None),
    (227, '0001', 'Shiny', ['steel', 'flying'], 10284),
    (248, '0001', 'Shiny', ['rock', 'dark'], 10049),
    (308, '0001', 'Shiny', ['fighting', 'psychic'], 10054),
    (358, '', 'Normal', ['psychic'], None),
    (358, '0000/0001', 'Shiny', ['psychic'], None),
    (381, '0001/0001', 'Shiny', ['dragon', 'psychic'], None),
    (382, '0001/0001', 'Shiny', ['water'], None),
    (383, '0001/0001', 'Shiny', ['ground', 'fire'], None),
    (491, '0002', 'Shiny', ['dark'], 10312),
]

def hashes(path):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.iterdir()) if p.is_file()}

def palette_map(reference):
    for color in ('normal','shiny'):
        path=CACHE/f'reference/{reference}-{color}.png'
        if not path.is_file():
            path.parent.mkdir(parents=True,exist_ok=True)
            url=('https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/'
                 + ('shiny/' if color=='shiny' else '')+f'{reference}.png')
            path.write_bytes(urllib.request.urlopen(url,timeout=30).read())
    normal = Image.open(CACHE / f'reference/{reference}-normal.png').convert('RGBA')
    shiny = Image.open(CACHE / f'reference/{reference}-shiny.png').convert('RGBA')
    if normal.size != shiny.size:
        raise ValueError('Reference images must have matching geometry')
    counts = {}
    for a, b in zip(normal.getdata(), shiny.getdata()):
        if a[3] and b[3]:
            counts.setdefault(a[:3], Counter())[b[:3]] += 1
    mapping = {a: b.most_common(1)[0][0] for a, b in counts.items()}
    if all(a == b for a, b in mapping.items()):
        # These references contain no shiny colors. User authorized a suitable
        # custom palette where no official shiny reference exists.
        mapping = {a: ((a[2], a[0], a[1]) if max(a)-min(a) > 20 else a)
                   for a in mapping}
        policy = 'custom_hue_rotation_no_distinct_official_reference'
    else:
        policy = 'official_shiny_reference'
    return mapping, policy

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    results = []
    for dex, suffix, color, types, reference in JOBS:
        source = ROOT / f'{dex:04d}' / suffix
        original = hashes(source)
        if 'AnimData.xml' not in original:
            raise ValueError(f'Missing source: {source}')
        settings = dict(generator_revision=2,dex=dex, suffix=suffix, color=color, types=types,
                        body_palette_budget=15-len(types),
                        source_hashes=original,
                        tool_sha256=hashlib.sha256((REPO/'tools/pmd_aura.py').read_bytes()).hexdigest())
        if reference:
            mapping, policy = palette_map(reference)
            settings.update(reference=reference, palette_policy=policy,
                            palette={','.join(map(str, a)): list(b) for a, b in mapping.items()},
                            reference_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                              for p in (CACHE/'reference').glob(f'{reference}-*.png')})
        key = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
        directory = CACHE / key
        output = directory / 'aura'
        marker = directory / 'provenance.json'
        directory.mkdir(exist_ok=True)
        if marker.exists():
            saved = json.loads(marker.read_text(encoding='utf-8'))
            if saved['settings'] != settings or saved['output_hashes'] != hashes(output):
                raise ValueError('Derived aura drift')
        else:
            input_path = source
            colors = Counter()
            for p in source.glob('*-Anim.png'):
                colors.update(px[:3] for px in Image.open(p).convert('RGBA').getdata() if px[3])
            reduce_palette = len(colors) > settings['body_palette_budget']
            if reference or reduce_palette:
                input_path = directory / 'palette_swap'
                input_path.mkdir(exist_ok=True)
                for p in source.iterdir():
                    if p.is_file(): shutil.copyfile(p, input_path/p.name)
                for p in input_path.glob('*-Anim.png') if reference else []:
                    im = Image.open(p).convert('RGBA')
                    def swap(pixel):
                        if not pixel[3]: return pixel
                        rgb = pixel[:3]
                        nearest = min(mapping, key=lambda c: (sum((c[i]-rgb[i])**2 for i in range(3)),c))
                        delta = tuple(mapping[nearest][i]-nearest[i] for i in range(3))
                        return tuple(max(0, min(255, rgb[i]+delta[i])) for i in range(3)) + (pixel[3],)
                    im.putdata([swap(px) for px in im.getdata()])
                    im.save(p)
                if reduce_palette:
                    colors = Counter()
                    for p in input_path.glob('*-Anim.png'):
                        colors.update(px[:3] for px in Image.open(p).convert('RGBA').getdata() if px[3])
                    replacements = {c: c for c in colors}
                    while len(colors) > settings['body_palette_budget']:
                        a, b = min(((a,b) for a in colors for b in colors if a < b),
                                   key=lambda pair: (sum((pair[0][i]-pair[1][i])**2 for i in range(3)),pair))
                        if colors[a] > colors[b]: a,b = b,a
                        colors[b] += colors.pop(a)
                        replacements = {c: b if v == a else v for c,v in replacements.items()}
                    for p in input_path.glob('*-Anim.png'):
                        im = Image.open(p).convert('RGBA')
                        im.putdata([replacements[px[:3]]+(px[3],) if px[3] else px for px in im.getdata()])
                        im.save(p)
            subprocess.run([sys.executable, '-B', str(REPO/'tools/pmd_aura.py'),
                            '--sprite-dir', str(input_path), '--output', str(output),
                            '--types', *types, '--all', '--no-previews'], check=True)
            if hashes(source) != original: raise ValueError('Source modified')
            saved = dict(settings=settings, path=output.relative_to(REPO).as_posix(),
                         output_hashes=hashes(output))
            marker.write_text(json.dumps(saved, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        results.append(saved)
        print(f'{dex:04d} {color}: aura ready', flush=True)
    (MODULE/'data/phase5_repairs.json').write_text(
        json.dumps(dict(schema=1, packages=results), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__': main()
