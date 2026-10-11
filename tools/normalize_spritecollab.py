"""Copy SpriteCollab sprites into species/form/Normal-or-Shiny leaf folders.

The original tree and tracker.json are read-only. Select exactly one package per
form/color, preferring Male, then shared, then Female.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys


def has_sprite(directory: Path) -> bool:
    return (directory / 'AnimData.xml').is_file()


def choose_sprite(base: Path, color_group: Path) -> tuple[Path | None, str]:
    male = color_group / '0001'
    if has_sprite(male):
        return male, 'male'
    if has_sprite(base):
        return base, 'shared'
    female = color_group / '0002'
    if has_sprite(female):
        return female, 'female_fallback'
    return None, 'missing'


def safe_form_name(value: str) -> str:
    cleaned = re.sub(r'[^\w.-]+', '_', value, flags=re.UNICODE).strip(' ._')
    return cleaned or 'Unnamed'


def plan(sprite_root: Path, tracker_path: Path) -> tuple[list[dict], list[dict]]:
    tracker = json.loads(tracker_path.read_text(encoding='utf-8'))
    jobs: list[dict] = []
    omitted: list[dict] = []
    for species_id, species in sorted(tracker.items()):
        if not re.fullmatch(r'\d{4}', species_id) or species_id == '0000':
            continue
        species_dir = sprite_root / species_id
        forms = species.get('subgroups', {})
        entries = [('Base', species_dir, forms.get('0000', {}), '0000')]
        for form_id, form in sorted(forms.items()):
            if form_id == '0000':
                continue
            name = str(form.get('name', ''))
            if 'altcolor' in re.sub(r'[^a-z]', '', name.lower()):
                omitted.append(dict(dex_id=species_id, form_id=form_id, form=name,
                                    reason='altcolor_excluded'))
                continue
            entries.append((f'{form_id}-{safe_form_name(name)}', species_dir / form_id, form, form_id))
        for label, normal_base, form_meta, form_id in entries:
            # Base-form normal assets live at the species root. Other forms live
            # in their own first-level directory. 0000 is a metadata container.
            normal_group = normal_base / '0000' if form_id != '0000' else species_dir / '0000/0000'
            shiny_base = species_dir / '0000/0001' if form_id == '0000' else normal_base / '0001'
            shiny_group = shiny_base
            for color, base, group in [('Normal', normal_base, normal_group),
                                       ('Shiny', shiny_base, shiny_group)]:
                selected, gender = choose_sprite(base, group)
                entry = dict(dex_id=species_id, form=label, form_id=form_id, color=color,
                             source=str(selected) if selected else None, gender_source=gender)
                if selected:
                    jobs.append(entry)
                else:
                    # The tracker may contain placeholders for forms with no
                    # sprite assets. Record the absence instead of inventing data.
                    omitted.append({**entry, 'reason': 'sprite_missing'})
    return jobs, omitted


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def copy_leaf(source: Path, destination: Path) -> str:
    files = sorted(p for p in source.iterdir() if p.is_file())
    if not files or not has_sprite(source):
        raise ValueError(f'Source package missing: {source}')
    destination.mkdir(parents=True, exist_ok=True)
    copied = False
    for source_file in files:
        target = destination / source_file.name
        if target.exists():
            if not target.is_file() or sha256(target) != sha256(source_file):
                raise ValueError(f'Existing file differs from source: {target}')
        else:
            shutil.copy2(source_file, target)
            copied = True
    unexpected = {p.name for p in destination.iterdir()} - {p.name for p in files}
    if unexpected:
        raise ValueError(f'Unexpected files in destination: {destination}: {sorted(unexpected)}')
    return 'copied' if copied else 'already_present'


def run(args: argparse.Namespace) -> dict:
    root, output = args.sprite_root.resolve(), args.output.resolve()
    tracker = args.tracker.resolve()
    report_path = args.report.resolve()
    if not root.is_dir() or not tracker.is_file():
        raise ValueError('Sprite root and tracker.json must exist.')
    if root == output or root in output.parents or output in root.parents:
        raise ValueError('Input and output trees must not overlap.')
    if output == report_path or output in report_path.parents:
        raise ValueError('Report must be outside the normalized tree.')
    jobs, omitted = plan(root, tracker)
    if output.exists() and not args.resume and not args.dry_run:
        raise ValueError('Output exists; use --resume or choose a new output directory.')
    results = []
    for job in jobs:
        source = Path(job['source']).resolve()
        if root not in source.parents:
            raise ValueError(f'Source escapes sprite root: {source}')
        destination = output / job['dex_id'] / job['form'] / job['color']
        result = {**job, 'destination': str(destination)}
        if args.dry_run:
            result['status'] = 'ready'
        else:
            try:
                result['status'] = copy_leaf(source, destination)
            except (OSError, ValueError) as exc:
                result.update(status='failed', error=str(exc))
        results.append(result)
    summary = dict(Counter(r['status'] for r in results))
    summary['altcolor_excluded'] = sum(r['reason'] == 'altcolor_excluded' for r in omitted)
    summary['sprite_missing'] = sum(r['reason'] == 'sprite_missing' for r in omitted)
    summary['female_fallback'] = sum(r['gender_source'] == 'female_fallback' for r in results)
    report = dict(source_root=str(root), tracker=str(tracker), output_root=str(output),
                  rule='Exactly one package per form/color: Male, then shared, then Female fallback',
                  summary=summary, jobs=results, omitted=omitted)
    if not args.dry_run:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sprite-root', type=Path, required=True)
    parser.add_argument('--tracker', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    try:
        result = run(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result['summary'], ensure_ascii=False))
    return int(bool(result['summary'].get('failed')))


if __name__ == '__main__':
    raise SystemExit(main())
