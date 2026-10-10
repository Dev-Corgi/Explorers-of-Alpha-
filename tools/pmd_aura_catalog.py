"""Build reproducible base-form terminal evolution catalog as JSON for CSV export.

Source: pinned PokeAPI data; no SpriteCollab assets are changed.
"""
import argparse
import csv
import io
import json
from pathlib import Path
import urllib.request

SNAPSHOT = 'c80757193bd0889054e36f4209762360bdaa4b95'
BASE = f'https://raw.githubusercontent.com/PokeAPI/pokeapi/{SNAPSHOT}/data/v2/csv/'


def catalog(data, sprite_root):
    species = {int(r['id']): r for r in data['pokemon_species']}
    defaults = {int(r['species_id']): int(r['id']) for r in data['pokemon'] if r['is_default'] == '1'}
    default_forms = {int(r['id']) for r in data['pokemon_forms']
                     if r['is_default'] == '1' and int(r['pokemon_id']) in defaults.values()}
    parents_with_evolution = set()
    covered = set()
    for r in data['pokemon_evolution']:
        child = int(r['evolved_species_id'])
        covered.add(child)
        parent = species[child]['evolves_from_species_id']
        if not parent:
            raise ValueError(f'Evolution record has no parent: {child}')
        form = r['required_pokemon_form_id']
        if not form or int(form) in default_forms:
            parents_with_evolution.add(int(parent))
    missing = {i for i, r in species.items() if r['evolves_from_species_id']} - covered
    if missing:
        raise ValueError(f'Missing evolution conditions: {sorted(missing)}')
    languages = {r['identifier']: r['id'] for r in data['languages']}
    names = {(int(r['pokemon_species_id']), r['local_language_id']): r['name']
             for r in data['pokemon_species_names']}
    type_names = {r['id']: r['identifier'] for r in data['types']}
    types = {}
    for r in sorted(data['pokemon_types'], key=lambda r: int(r['slot'])):
        types.setdefault(int(r['pokemon_id']), []).append(type_names[r['type_id']])
    tracker = json.loads((sprite_root.parent / 'tracker.json').read_text(encoding='utf-8'))
    rows = []
    for i, r in sorted(species.items()):
        dex = f'{i:04d}'
        if i in parents_with_evolution or dex not in tracker:
            continue
        ts = types[defaults[i]]
        if len(ts) not in (1, 2):
            raise ValueError(f'Unsupported types: {i}: {ts}')
        rows.append(dict(dex_id=dex, name=names.get((i, languages['ko']), r['identifier']),
                         name_en=names.get((i, languages['en']), r['identifier']),
                         type1=ts[0], type2=ts[1] if len(ts) == 2 else '', enabled='1',
                         normal_form_path=dex, shiny_form_path=f'{dex}/0000/0001',
                         normal_available=str(int((sprite_root / dex / 'AnimData.xml').is_file())),
                         shiny_available=str(int((sprite_root / dex / '0000/0001/AnimData.xml').is_file())),
                         source_pokemon_id=str(defaults[i])))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sprite-root', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output-json', type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    data = {}
    for name in ['pokemon_species', 'pokemon', 'pokemon_forms', 'pokemon_types', 'types',
                 'pokemon_species_names', 'languages', 'pokemon_evolution']:
        path = args.cache / SNAPSHOT / f'{name}.csv'
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            request = urllib.request.Request(BASE + name + '.csv', headers={'User-Agent': 'PMD-aura-catalog'})
            with urllib.request.urlopen(request, timeout=60) as response:
                path.write_bytes(response.read())
        data[name] = list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8'))))
    rows = catalog(data, args.sprite_root.resolve())
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(dict(rows=rows, source=BASE,
                                              basis='Terminal evolution of default form across mainline games, including single-stage species'),
                                          ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(rows)} terminal base-form species')


if __name__ == '__main__':
    main()
