"""Build offline form-type overrides from a pinned PokeAPI CSV snapshot."""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import urllib.request

from pmd_aura_catalog import BASE, SNAPSHOT


FORM_ALIASES = {'gigantamax': 'gmax'}
FORM_SUFFIXES = {
    (128, 'Paldea'): 'paldea-combat-breed',
    (128, 'Paldea_Blaze'): 'paldea-blaze-breed',
    (128, 'Paldea_Aqua'): 'paldea-aqua-breed',
    (413, 'Sand'): 'sandy',
    (550, 'Blue'): 'blue-striped',
    (550, 'White'): 'white-striped',
    (555, 'Galar'): 'galar-standard',
    (741, 'Pa_U'): 'pau',
    (849, 'Lowkey'): 'low-key',
    (888, 'Crowned_Sword'): 'crowned',
    (889, 'Crowned_Shield'): 'crowned',
    (1017, 'Wellspring'): 'wellspring-mask',
    (1017, 'Hearthflame'): 'hearthflame-mask',
    (1017, 'Cornerstone'): 'cornerstone-mask',
    (1017, 'Wellspring_Mask'): 'wellspring-mask',
    (1017, 'Hearthflame_Mask'): 'hearthflame-mask',
    (1017, 'Cornerstone_Mask'): 'cornerstone-mask',
    (1017, 'Teal_Mask'): 'teal-mask',
}
TYPE_FORM_SPECIES = {493, 773}  # Arceus and Silvally form names are their types.
TYPE_NAMES = {'normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting',
              'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost',
              'dragon', 'dark', 'steel', 'fairy'}


def fetch_table(name: str, cache: Path) -> list[dict]:
    path = cache / SNAPSHOT / f'{name}.csv'
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(BASE + name + '.csv', headers={'User-Agent': 'PMD-aura-form-types'})
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
    return list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8'))))


def collect(root: Path, data: dict[str, list[dict]]) -> dict:
    species_ids = {int(row['id']): row['identifier'] for row in data['pokemon_species']}
    names = {row['id']: row['identifier'] for row in data['types']}
    types: dict[int, list[tuple[int, str]]] = {}
    for row in data['pokemon_types']:
        types.setdefault(int(row['pokemon_id']), []).append((int(row['slot']), names[row['type_id']]))
    by_species_name = {(int(row['species_id']), row['identifier']): int(row['id'])
                       for row in data['pokemon']}
    matched, unmatched = {}, []
    for species in sorted(root.iterdir()):
        if not species.is_dir() or not species.name.isdigit():
            continue
        dex = int(species.name)
        for form in sorted(species.iterdir()):
            if not form.is_dir() or form.name == 'Base' or form.name.endswith('_Aura'):
                continue
            label = form.name.split('-', 1)[1]
            if dex in TYPE_FORM_SPECIES and label.lower() in TYPE_NAMES:
                matched[f'{species.name}/{form.name}'] = [label.lower()]
                continue
            if dex == 1017 and label == 'Teal_Mask':
                matched[f'{species.name}/{form.name}'] = ['grass']
                continue
            suffix = FORM_SUFFIXES.get((dex, label), label.lower().replace('_', '-'))
            suffix = FORM_ALIASES.get(suffix, suffix)
            identifier = f'{species_ids[dex]}-{suffix}'
            pokemon_id = by_species_name.get((dex, identifier))
            key = f'{species.name}/{form.name}'
            if pokemon_id is None:
                unmatched.append(key)
            else:
                matched[key] = [name for _, name in sorted(types[pokemon_id])]
    return dict(source=BASE, types=matched, unmatched_forms=unmatched)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--normalized-root', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    data = {name: fetch_table(name, args.cache) for name in
            ('pokemon_species', 'pokemon', 'pokemon_types', 'types')}
    result = collect(args.normalized_root.resolve(), data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"matched={len(result['types'])} unmatched={len(result['unmatched_forms'])}")


if __name__ == '__main__':
    main()
