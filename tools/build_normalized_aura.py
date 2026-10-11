"""Add <form>_Aura beside every normalized form, preserving Normal/Shiny leaves.

Form types use pinned PokeAPI overrides when available; unmapped display-only
forms inherit the species types from the final-stage targets CSV.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
import hashlib
import json
from pathlib import Path
import sys
import uuid

import pmd_aura


def hashes(directory: Path, marker: str = 'normalized-aura-job.json') -> dict[str, str]:
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file() and p.name != marker}


def load_species_types(path: Path) -> dict[str, list[str]]:
    result = {}
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not {'dex_id', 'type1', 'type2', 'enabled'} <= set(reader.fieldnames or []):
            raise ValueError('Targets CSV needs dex_id, type1, type2, enabled.')
        for row in reader:
            dex = str(int(row['dex_id'])).zfill(4)
            if row['enabled'] == '1':
                result[dex] = [t for t in (row['type1'], row['type2']) if t]
    return result


def plan(args: argparse.Namespace) -> tuple[list[dict], dict]:
    root = args.normalized_root.resolve()
    if not root.is_dir():
        raise ValueError(f'Normalized root does not exist: {root}')
    species_types = load_species_types(args.csv)
    overrides = json.loads(args.form_types.read_text(encoding='utf-8'))['types']
    only = {str(int(x)).zfill(4) for x in args.only_dex or []}
    if only - species_types.keys():
        raise ValueError(f'Unknown or disabled target IDs: {sorted(only - species_types.keys())}')
    jobs = []
    counts = dict(form_type_override=0, base_type_fallback=0)
    for species in sorted(root.iterdir()):
        if not species.is_dir() or species.name not in species_types:
            continue
        if only and species.name not in only:
            continue
        for form in sorted(species.iterdir()):
            if not form.is_dir() or form.name.endswith('_Aura'):
                continue
            if any(token in form.name.lower() for token in
                   ('altcolor', 'alternate', 'cutscene', 'shadow', 'skytemple',
                    'primal', 'baby', 'three')):
                raise ValueError(f'Excluded form still present: {form}')
            key = f'{species.name}/{form.name}'
            types = overrides.get(key, species_types[species.name])
            if not 1 <= len(types) <= 2 or len(set(types)) != len(types) or set(types) - pmd_aura.TYPE_COLORS.keys():
                raise ValueError(f'Invalid types for {key}: {types}')
            source_kind = 'form_type_override' if key in overrides else 'base_type_fallback'
            for color in ('Normal', 'Shiny'):
                source = form / color
                if not (source / 'AnimData.xml').is_file():
                    continue
                destination = species / f'{form.name}_Aura' / color
                jobs.append(dict(source=str(source), destination=str(destination),
                                 dex_id=species.name, form=form.name, color=color,
                                 types=types, type_source=source_kind))
                counts[source_kind] += 1
    if not jobs:
        raise ValueError('No normalized sprite packages found.')
    return jobs, counts


def run_job(job: dict, settings: dict) -> dict:
    source, destination = Path(job['source']), Path(job['destination'])
    result = {k: job[k] for k in ('dex_id', 'form', 'color', 'types', 'type_source')}
    fingerprint = dict(source_hashes=hashes(source),
                       settings={k: v for k, v in settings.items() if k != 'resume'}, types=job['types'],
                       aura_code=hashlib.sha256(Path(pmd_aura.__file__).read_bytes()).hexdigest())
    marker = destination / 'normalized-aura-job.json'
    try:
        if destination.exists():
            if not settings['resume']:
                raise ValueError('Aura output already exists; rerun with --resume.')
            if not marker.is_file():
                raise ValueError('Existing aura package lacks completion marker.')
            saved = json.loads(marker.read_text(encoding='utf-8'))
            if saved.get('fingerprint') != fingerprint or saved.get('output_hashes') != hashes(destination):
                raise ValueError('Existing aura package differs from source, settings or recorded output.')
            result['status'] = 'already_present'
            return result
        stage_root = Path(settings['staging_root'])
        stage_root.mkdir(parents=True, exist_ok=True)
        staged = stage_root / f"{job['dex_id']}-{uuid.uuid4().hex}"
        arguments = ['--sprite-dir', str(source), '--output', str(staged), '--types', *job['types'],
                     '--palette-limit', str(settings['palette_limit']), '--width', str(settings['width']),
                     '--flame-height', str(settings['flame_height']), '--seed', str(settings['seed'])]
        if settings['animations']:
            arguments += ['--animations', *settings['animations']]
        else:
            arguments += ['--all']
        if not settings['previews']:
            arguments += ['--no-previews']
        if settings['allow_clipping']:
            arguments += ['--allow-clipping']
        aura_args = pmd_aura.parser().parse_args(arguments)
        pmd_aura.build(aura_args)
        (staged / marker.name).write_text(
            json.dumps(dict(fingerprint=fingerprint, output_hashes=hashes(staged),
                            type_source=job['type_source']), ensure_ascii=False, indent=2),
            encoding='utf-8')
        destination.parent.mkdir(parents=True, exist_ok=True)
        staged.rename(destination)
        result['status'] = 'created'
    except (ValueError, OSError, KeyError) as exc:
        result.update(status='failed', error=str(exc))
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--normalized-root', type=Path, required=True)
    p.add_argument('--csv', type=Path, required=True)
    p.add_argument('--form-types', type=Path, required=True)
    p.add_argument('--only-dex', nargs='+')
    p.add_argument('--animations', nargs='+', help='Default: all real animations.')
    p.add_argument('--palette-limit', type=int, default=32)
    p.add_argument('--width', type=float, default=3)
    p.add_argument('--flame-height', type=float, default=4)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--allow-clipping', action='store_true')
    p.add_argument('--previews', action='store_true')
    p.add_argument('--workers', type=int, default=2)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    try:
        if args.workers < 1:
            raise ValueError('Workers must be positive.')
        jobs, counts = plan(args)
        existing = sum(Path(job['destination']).exists() for job in jobs)
        if existing and not args.resume and not args.dry_run:
            raise ValueError(f'{existing} aura packages already exist; use --resume.')
        print(json.dumps(dict(packages=len(jobs), existing=existing, **counts), ensure_ascii=False), flush=True)
        if args.dry_run:
            return 0
        staging_root = args.normalized_root.resolve().parent / 'sprite-aura-staging'
        if staging_root == args.normalized_root.resolve() or args.normalized_root.resolve() in staging_root.parents:
            raise ValueError('Staging root must be outside normalized sprites.')
        settings = dict(palette_limit=args.palette_limit, width=args.width, flame_height=args.flame_height,
                        seed=args.seed, animations=args.animations, previews=args.previews,
                        allow_clipping=args.allow_clipping, staging_root=str(staging_root), resume=args.resume)
        totals = {'created': 0, 'already_present': 0, 'failed': 0}
        if args.workers == 1:
            results = (run_job(job, settings) for job in jobs)
            for result in results:
                totals[result['status']] += 1
                print(f"{result['dex_id']}/{result['form']}/{result['color']}: {result['status']}" +
                      (f" — {result['error']}" if result['status'] == 'failed' else ''), flush=True)
        else:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                futures = [pool.submit(run_job, job, settings) for job in jobs]
                for future in as_completed(futures):
                    result = future.result()
                    totals[result['status']] += 1
                    print(f"{result['dex_id']}/{result['form']}/{result['color']}: {result['status']}" +
                          (f" — {result['error']}" if result['status'] == 'failed' else ''), flush=True)
        print(json.dumps(totals, ensure_ascii=False))
        return int(bool(totals['failed']))
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
