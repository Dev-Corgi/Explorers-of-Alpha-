"""Add deterministic, palette-limited aura layers to SpriteCollab sprite sheets.

Dependencies: Pillow, numpy, scipy. No image-generation service or ROM required.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt


# Editable visual defaults, not a ROM type-ID table or an official color standard.
TYPE_COLORS = {
    'normal': '#A8A878', 'fire': '#F08030', 'water': '#6890F0',
    'electric': '#F8D030', 'grass': '#78C850', 'ice': '#98D8D8',
    'fighting': '#C03028', 'poison': '#A040A0', 'ground': '#E0C068',
    'flying': '#A890F0', 'psychic': '#F85888', 'bug': '#A8B820',
    'rock': '#B8A038', 'ghost': '#705898', 'dragon': '#7038F8',
    'dark': '#705848', 'steel': '#B8B8D0', 'fairy': '#EE99AC',
}
TYPE_ALIASES = dict(zip(
    '노말 불꽃 물 전기 풀 얼음 격투 독 땅 비행 에스퍼 벌레 바위 고스트 드래곤 악 강철 페어리'.split(),
    TYPE_COLORS,
))


def rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.removeprefix('#')
    if len(value) != 6:
        raise ValueError(f'Expected a six-digit RGB color, got {hex_color!r}')
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError as exc:
        raise ValueError(f'Invalid RGB color {hex_color!r}') from exc


def color_ramp(colors: list[tuple[int, int, int]], steps: int) -> np.ndarray:
    if len(colors) == 2 and steps < 2:
        raise ValueError('Dual types need at least two free palette colors.')
    if steps < 1:
        raise ValueError('No free palette color remains for the aura.')
    if len(colors) == 1:
        # Light inner glow -> saturated outside, without adding per-frame colors.
        a = np.asarray(colors[0], dtype=float)
        b = a * .55 + 255 * .45
    else:
        a, b = (np.asarray(c, dtype=float) for c in colors)
    return np.array([np.rint(a * (1 - t) + b * t) for t in np.linspace(0, 1, steps)], dtype=np.uint8)


def render_frame(
    source: np.ndarray, body_mask: np.ndarray, ramp: np.ndarray,
    phase: float, width: float, flame_height: float, padding: int,
    axis: str = 'vertical', seed: int = 0,
    anchor: tuple[float, float] | None = None,
) -> tuple[np.ndarray, dict]:
    """Render on a guard canvas, then measure any aura lost by the requested crop."""
    if source.ndim != 3 or source.shape[2] != 4 or body_mask.shape != source.shape[:2]:
        raise ValueError('RGBA frame and body mask dimensions must match.')
    if not np.isin(source[:, :, 3], [0, 255]).all():
        raise ValueError('Source alpha must be binary (0 or 255); clean it first.')
    if np.any(body_mask & (source[:, :, 3] == 0)):
        raise ValueError('Body mask includes pixels outside the source character/effects.')
    guard = math.ceil(width + flame_height) + 2
    border = padding + guard
    src = np.pad(source, ((border, border), (border, border), (0, 0)))
    mask = np.pad(body_mask.astype(bool), border)
    result = src.copy()
    if not mask.any():
        return result[guard:-guard, guard:-guard], {'empty_mask': True, 'clipped_aura_pixels': 0}
    distance, nearest = distance_transform_edt(~mask, return_indices=True)
    yy, xx = np.indices(mask.shape)
    sy, sx = np.where(body_mask)
    if anchor is None:
        anchor = ((float(sx.min()) + float(sx.max())) / 2,
                  (float(sy.min()) + float(sy.max())) / 2)
    ax, ay = anchor[0] + border, anchor[1] + border
    # Coordinates follow the source anchor; no independent random frame noise.
    wave = .5 + .5 * np.sin((xx - ax) * .72 - (yy - ay) * .29 + phase * math.tau + seed * .618)
    up = np.clip((nearest[0] - yy) / np.maximum(distance, 1), 0, 1)
    reach = width * (.8 + .2 * wave) + flame_height * up * wave ** 3
    aura = (distance > 0) & (distance <= reach) & (src[:, :, 3] == 0)
    if axis == 'vertical':
        low, high = sy.min() + border, sy.max() + border
        t = np.clip((yy - low) / max(1, high - low), 0, 1)
    else:
        t = np.clip(distance / np.maximum(reach, 1e-6), 0, 1)
    ids = np.rint(t * (len(ramp) - 1)).astype(int)
    result[aura, :3] = ramp[ids[aura]]
    result[aura, 3] = 255
    inside = np.zeros(mask.shape, dtype=bool)
    inside[guard:-guard, guard:-guard] = True
    clipped = int(np.count_nonzero(aura & ~inside))
    # A source foreground/effect pixel is never recolored or alpha-composited.
    assert np.array_equal(result[src[:, :, 3] > 0], src[src[:, :, 3] > 0])
    return result[guard:-guard, guard:-guard], {
        'empty_mask': False, 'clipped_aura_pixels': clipped,
        'anchor': list(anchor), 'added_pixels': int(np.count_nonzero(aura & inside)),
    }


def sheet_palette(sheet: np.ndarray) -> list[tuple[int, int, int]]:
    opaque = sheet[sheet[:, :, 3] > 0, :3]
    return [tuple(map(int, c)) for c in np.unique(opaque, axis=0)]


def indexed_image(rgba: np.ndarray, palette: list[tuple[int, int, int]]) -> Image.Image:
    colors = [(0, 0, 0)] + palette
    indices = np.zeros(rgba.shape[:2], dtype=np.uint8)
    for i, color in enumerate(palette, 1):
        indices[(rgba[:, :, :3] == color).all(axis=2) & (rgba[:, :, 3] > 0)] = i
    im = Image.fromarray(indices, mode='P')
    im.putpalette([v for c in colors for v in c] + [0] * (768 - len(colors) * 3))
    im.info['transparency'] = 0
    return im


def padded_sheet(image: Image.Image, fw: int, fh: int, padding: int) -> Image.Image:
    cols, rows = image.width // fw, image.height // fh
    out = Image.new('RGBA', (cols * (fw + 2 * padding), rows * (fh + 2 * padding)))
    for r in range(rows):
        for c in range(cols):
            tile = image.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
            out.paste(tile, (c * (fw + 2 * padding) + padding, r * (fh + 2 * padding) + padding))
    return out


def save_preview(path: Path, source: np.ndarray, result: np.ndarray,
                 fw: int, fh: int, padding: int, durations: list[int],
                 ticks_per_second: float, scale: int) -> None:
    cols, rows = source.shape[1] // fw, source.shape[0] // fh
    nw, nh = fw + 2 * padding, fh + 2 * padding
    tiles_per_row = min(rows, 4)
    tw, th = nw * 2 * scale + 12, nh * scale + 20
    frames = []
    for c in range(cols):
        canvas = Image.new('RGB', (tw * tiles_per_row, th * math.ceil(rows / tiles_per_row)), (35, 39, 47))
        draw = ImageDraw.Draw(canvas)
        for r in range(rows):
            pair = Image.new('RGB', (nw * 2, nh), (65, 69, 80))
            old = Image.new('RGBA', (nw, nh))
            old.paste(Image.fromarray(source[r * fh:(r + 1) * fh, c * fw:(c + 1) * fw]), (padding, padding))
            new = Image.fromarray(result[r * nh:(r + 1) * nh, c * nw:(c + 1) * nw])
            pair.paste(old, (0, 0), old); pair.paste(new, (nw, 0), new)
            x, y = r % tiles_per_row * tw, r // tiles_per_row * th
            draw.text((x + 4, y + 3), f'R{r + 1} F{c} original | aura', fill='white')
            canvas.paste(pair.resize((nw * 2 * scale, nh * scale), Image.Resampling.NEAREST), (x + 6, y + 20))
        frames.append(canvas)
    ms = [max(10, round(t * 1000 / ticks_per_second / 10) * 10) for t in durations]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms, loop=0, disposal=2)
    frames[0].save(path.with_suffix('.png'))


def build(args: argparse.Namespace) -> dict:
    src, out = args.sprite_dir.resolve(), args.output.resolve()
    if not src.is_dir():
        raise ValueError(f'Sprite directory does not exist: {src}')
    if out.exists():
        raise ValueError('Output already exists; choose a new directory (no overwrite).')
    if src == out or src in out.parents or out in src.parents:
        raise ValueError('Input and output directory trees must not overlap.')
    if not 2 <= args.palette_limit <= 256:
        raise ValueError('Palette limit must be between 2 and 256, including transparency.')
    if not math.isfinite(args.width) or args.width <= 0:
        raise ValueError('Width must be finite and positive.')
    if not math.isfinite(args.flame_height) or args.flame_height < 0:
        raise ValueError('Flame height must be finite and nonnegative.')
    if not math.isfinite(args.ticks_per_second) or args.ticks_per_second <= 0 or args.preview_scale < 1:
        raise ValueError('Preview rate and scale must be positive.')
    padding = math.ceil(args.width + args.flame_height) + 1 if args.padding == 'auto' else int(args.padding)
    if padding < 0:
        raise ValueError('Padding must be nonnegative.')
    defaults = TYPE_COLORS.copy()
    if args.type_colors:
        supplied = json.loads(args.type_colors.read_text(encoding='utf-8'))
        defaults.update({TYPE_ALIASES.get(k, k.lower()): v for k, v in supplied.items()})
    types = [TYPE_ALIASES.get(t, t.lower()) for t in args.types]
    if len(types) not in [1, 2] or len(set(types)) != len(types):
        raise ValueError('Specify one type or two different types.')
    unknown = set(types) - defaults.keys()
    if unknown:
        raise ValueError(f'Unknown type(s): {sorted(unknown)}')
    colors = [rgb(defaults[t]) for t in types]
    tree = ET.parse(src / 'AnimData.xml')
    anims = tree.findall('./Anims/Anim')
    by_name = {a.findtext('Name'): a for a in anims}
    selected = [a.findtext('Name') for a in anims if a.find('CopyOf') is None] if args.all else (args.animations or ['Idle'])
    if len(set(selected)) != len(selected):
        raise ValueError('Duplicate animation names.')
    for name in selected:
        if name not in by_name:
            raise ValueError(f'Unknown animation: {name}')
        if by_name[name].find('CopyOf') is not None:
            raise ValueError(f'{name} uses CopyOf; process {by_name[name].findtext("CopyOf")} instead.')
    # Copy complete direct files only; never mix in child forms or overwrite input.
    source_files = [p for p in src.iterdir() if p.is_file()]
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    loaded = {}
    original_colors = set()
    for name in selected:
        a = by_name[name]
        fw, fh = int(a.findtext('FrameWidth')), int(a.findtext('FrameHeight'))
        image = np.array(Image.open(src / f'{name}-Anim.png').convert('RGBA'))
        if fw <= 0 or fh <= 0 or image.shape[1] % fw or image.shape[0] % fh:
            raise ValueError(f'{name}: image does not fit XML frame dimensions.')
        if not np.isin(image[:, :, 3], [0, 255]).all():
            raise ValueError(f'{name}: nonbinary source alpha is unsupported.')
        # Invisible RGB values are not sprite pixels; normalize for indexed export.
        image[image[:, :, 3] == 0] = 0
        ds = [int(d.text) for d in a.findall('./Durations/Duration')]
        if len(ds) != image.shape[1] // fw or not ds or min(ds) <= 0:
            raise ValueError(f'{name}: Durations must match columns and be positive.')
        companions = {}
        for suffix in ['Offsets', 'Shadow']:
            p = src / f'{name}-{suffix}.png'
            if not p.exists():
                raise ValueError(f'Missing companion sheet: {p.name}')
            im = Image.open(p).convert('RGBA')
            if im.size != (image.shape[1], image.shape[0]):
                raise ValueError(f'{name}: {suffix} sheet dimensions differ.')
            companions[suffix] = im
        mask = image[:, :, 3] > 0
        if args.mask_dir:
            p = args.mask_dir / f'{name}-Mask.png'
            m = Image.open(p)
            if m.size != (image.shape[1], image.shape[0]):
                raise ValueError(f'{name}: mask dimensions differ.')
            m = m.getchannel('A') if 'A' in m.getbands() and m.getchannel('A').getextrema() != (255, 255) else m.convert('L')
            mask = np.array(m) >= 128
            if np.any(mask & (image[:, :, 3] == 0)):
                raise ValueError(f'{name}: mask selects transparent source pixels.')
        original_colors.update(sheet_palette(image))
        loaded[name] = (image, mask, fw, fh, ds, companions)
    available = args.palette_limit - 1 - len(original_colors)
    steps = min(3, available) if args.gradient_steps is None else args.gradient_steps
    if steps > available or steps < 1:
        raise ValueError(f'Palette has {len(original_colors)} source colors; {available} free slots. Cannot fit aura steps={steps}.')
    ramp = color_ramp(colors, steps)
    palette = sorted(original_colors | {tuple(map(int, c)) for c in ramp})
    plans = {}
    report = {'types': types, 'type_colors': [defaults[t] for t in types], 'palette_limit': args.palette_limit,
              'opaque_source_colors': len(original_colors), 'gradient_steps': steps, 'aura_colors': ramp.tolist(),
              'padding_per_side': padding, 'gradient_axis': args.gradient_axis, 'seed': args.seed,
              'preview_ticks_per_second_assumption': args.ticks_per_second, 'animations': {}, 'warnings': [],
              'rom_validated': False, 'source_hashes': hashes}
    for name, (image, mask, fw, fh, ds, companions) in loaded.items():
        cols, rows = image.shape[1] // fw, image.shape[0] // fh
        nw, nh = fw + padding * 2, fh + padding * 2
        result = np.zeros((rows * nh, cols * nw, 4), np.uint8)
        metrics = []
        elapsed = 0
        offsets = np.array(companions['Offsets'])
        for c, duration in enumerate(ds):
            phase = elapsed / sum(ds)
            elapsed += duration
            for r in range(rows):
                old = image[r * fh:(r + 1) * fh, c * fw:(c + 1) * fw]
                body = mask[r * fh:(r + 1) * fh, c * fw:(c + 1) * fw]
                tile = offsets[r * fh:(r + 1) * fh, c * fw:(c + 1) * fw]
                yy, xx = np.where((tile[:, :, :3] == 0).all(axis=2) & (tile[:, :, 3] > 0))
                anchor = (float(xx[0]), float(yy[0])) if len(xx) == 1 else None
                new, metric = render_frame(old, body, ramp, phase, args.width, args.flame_height,
                                          padding, args.gradient_axis, args.seed, anchor)
                metric.update(row=r + 1, frame=c, phase=phase,
                              anchor_source='offsets_black_marker' if anchor else 'mask_bbox')
                if metric['clipped_aura_pixels'] and not args.allow_clipping:
                    raise ValueError(f'{name} row {r + 1} frame {c}: aura would clip. Use --padding auto or explicitly --allow-clipping.')
                preserved = new[padding:padding + fh, padding:padding + fw]
                assert np.array_equal(preserved[old[:, :, 3] > 0], old[old[:, :, 3] > 0])
                result[r * nh:(r + 1) * nh, c * nw:(c + 1) * nw] = new
                metrics.append(metric)
        plans[name] = result
        a = by_name[name]
        a.find('FrameWidth').text = str(nw); a.find('FrameHeight').text = str(nh)
        report['animations'][name] = dict(source_frame_size=[fw, fh], output_frame_size=[nw, nh],
                                          rows=rows, columns=cols, durations=ds, frames=metrics,
                                          original_foreground_pixels_preserved=True,
                                          clipping_pixels=sum(m['clipped_aura_pixels'] for m in metrics))
        if name == 'Hurt' and not args.mask_dir:
            report['warnings'].append('Hurt uses all opaque pixels, including hit/sweat effects; supply Hurt-Mask.png to exclude them.')
    for p in source_files:
        if hashlib.sha256(p.read_bytes()).hexdigest() != hashes[p.name]:
            raise ValueError(f'Source changed during processing: {p.name}')
    # All preflight and rendering checks complete before writing the output package.
    out.mkdir(parents=True)
    for p in source_files:
        shutil.copy2(p, out / p.name)
    for name, result in plans.items():
        im = indexed_image(result, palette)
        im.save(out / f'{name}-Anim.png', transparency=0)
        # Indexed round-trip also checks every original foreground RGB/alpha value.
        assert np.array_equal(np.array(Image.open(out / f'{name}-Anim.png').convert('RGBA')), result)
        image, _, fw, fh, ds, companions = loaded[name]
        for suffix, companion in companions.items():
            padded_sheet(companion, fw, fh, padding).save(out / f'{name}-{suffix}.png')
        if not args.no_previews:
            preview = out / 'previews'; preview.mkdir(exist_ok=True)
            save_preview(preview / f'{name}-comparison.gif', image, result, fw, fh, padding,
                         ds, args.ticks_per_second, args.preview_scale)
    tree.write(out / 'AnimData.xml', encoding='utf-8', xml_declaration=True)
    report['output_opaque_palette_colors'] = len(palette)
    report['output_palette_colors_including_transparency'] = len(palette) + 1
    report['source_unchanged'] = all(hashlib.sha256(p.read_bytes()).hexdigest() == hashes[p.name] for p in source_files)
    report['clipping_allowed'] = args.allow_clipping
    (out / 'aura-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def file_hashes(directory: Path) -> dict:
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file() and p.name != 'batch-job.json'}


def batch(args: argparse.Namespace) -> dict:
    root, output = args.sprite_root.resolve(), args.output.resolve()
    if not root.is_dir() or root == output or root in output.parents or output in root.parents:
        raise ValueError('Input must exist and output must be outside the input tree.')
    if not args.csv or args.types:
        raise ValueError('Batch mode requires --csv and reads types from CSV, not --types.')
    jobs = []
    seen = set()
    only = {str(int(x)).zfill(4) for x in args.only_dex or []}
    with args.csv.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'dex_id', 'type1', 'type2', 'enabled'}
        if not required <= set(reader.fieldnames or []):
            raise ValueError(f'CSV needs columns: {sorted(required)}')
        for row in reader:
            dex = str(int(row['dex_id'])).zfill(4)
            if not 1 <= int(dex) <= 1025 or dex in seen:
                raise ValueError(f'Invalid or duplicate dex_id: {dex}')
            seen.add(dex)
            types = [TYPE_ALIASES.get(t.strip(), t.strip().lower()) for t in (row['type1'], row['type2']) if t.strip()]
            if not types or len(types) != len(set(types)) or set(types) - TYPE_COLORS.keys():
                raise ValueError(f'{dex}: invalid types {types}')
            if row['enabled'].strip() not in {'0', '1'}:
                raise ValueError(f'{dex}: enabled must be 0 or 1')
            if row['enabled'].strip() == '0' or (only and dex not in only):
                continue
            variants = [('AltMeta', dex), ('AltMetaColor', f'{dex}/0000/0001')]
            if args.variants == 'normal':
                variants = variants[:1]
            elif args.variants == 'shiny':
                variants = variants[1:]
            for variant, relative in variants:
                source = (root / relative).resolve()
                if root not in source.parents:
                    raise ValueError(f'Source path escapes root: {source}')
                jobs.append((dex, variant, source, types))
    if only - seen:
        raise ValueError(f'IDs not in CSV: {sorted(only - seen)}')
    if output.exists() and not args.resume and not args.dry_run:
        raise ValueError('Batch output already exists; choose a new root or --resume.')
    results = []
    for dex, variant, source, types in jobs:
        item = dict(dex_id=dex, variant=variant, source=str(source))
        if not (source / 'AnimData.xml').is_file():
            item['status'] = 'skipped_missing'
        elif args.dry_run:
            item['status'] = 'ready'
        else:
            job = argparse.Namespace(**vars(args))
            job.sprite_dir, job.output, job.types = source, output / dex / variant, types
            job.all = args.all or args.animations is None
            job.no_previews = not args.previews or args.no_previews
            job.mask_dir = args.mask_dir / dex / variant if args.mask_dir else None
            settings = {k: str(v) if isinstance(v, Path) else v for k, v in vars(job).items()
                        if k not in {'resume', 'dry_run', 'only_dex', 'csv', 'sprite_root'}}
            source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir() if p.is_file()}
            fingerprint = dict(settings=settings, source_hashes=source_hashes,
                               program_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               mask_hashes=file_hashes(job.mask_dir) if job.mask_dir else {},
                               colors_hash=hashlib.sha256(args.type_colors.read_bytes()).hexdigest() if args.type_colors else None)
            try:
                marker = job.output / 'batch-job.json'
                if job.output.exists():
                    saved = json.loads(marker.read_text(encoding='utf-8')) if marker.is_file() else {}
                    if saved.get('fingerprint') != fingerprint or saved.get('output_hashes') != file_hashes(job.output):
                        raise ValueError('Existing output is incomplete or source/settings/output changed; use a new output root.')
                    item['status'] = 'skipped_completed'
                else:
                    build(job)
                    marker.write_text(json.dumps(dict(fingerprint=fingerprint, output_hashes=file_hashes(job.output)),
                                                 ensure_ascii=False, indent=2), encoding='utf-8')
                    item['status'] = 'created'
            except (ValueError, OSError, ET.ParseError) as exc:
                item.update(status='failed', error=str(exc))
            print(f'{dex}/{variant}: {item["status"]}', flush=True)
        results.append(item)
    report = dict(summary=dict(Counter(x['status'] for x in results)), jobs=results, rom_validated=False)
    if not args.dry_run:
        output.mkdir(parents=True, exist_ok=True)
        (output / 'batch-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--sprite-dir', type=Path)
    source.add_argument('--sprite-root', type=Path)
    p.add_argument('--csv', type=Path)
    p.add_argument('--only-dex', nargs='+')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--resume', action='store_true')
    p.add_argument('--previews', action='store_true', help='Enable previews in batch mode.')
    p.add_argument('--variants', choices=['normal', 'shiny', 'both'], default='both',
                   help='Batch variants: normal=AltMeta, shiny=AltMetaColor, both (default).')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--types', nargs='+', help='One or two English/Korean type names (single mode).')
    select = p.add_mutually_exclusive_group()
    select.add_argument('--animations', nargs='+')
    select.add_argument('--all', action='store_true', help='All real sheets, not CopyOf aliases.')
    p.add_argument('--width', type=float, default=3, help='Aura width in native pixels.')
    p.add_argument('--flame-height', type=float, default=4, help='Extra upward flame reach.')
    p.add_argument('--padding', default='auto', help='Pixels per side, or auto (default).')
    p.add_argument('--allow-clipping', action='store_true', help='Explicitly permit and report clipped aura.')
    p.add_argument('--gradient-axis', choices=['vertical', 'radial'], default='vertical')
    p.add_argument('--gradient-steps', type=int, help='Default: up to 3 within the remaining palette budget.')
    p.add_argument('--palette-limit', type=int, default=16, help='Total colors including transparency.')
    p.add_argument('--type-colors', type=Path, help='JSON object overriding type hex colors.')
    p.add_argument('--mask-dir', type=Path, help='Full-sheet <Name>-Mask.png, white/alpha selects body only.')
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--ticks-per-second', type=float, default=60, help='Preview timing assumption only.')
    p.add_argument('--preview-scale', type=int, default=3)
    p.add_argument('--no-previews', action='store_true')
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        if args.sprite_root:
            report = batch(args)
            print(json.dumps(report['summary'], ensure_ascii=False))
            return int(bool(report['summary'].get('failed')))
        if not args.types or args.csv or args.dry_run or args.resume or args.only_dex:
            raise ValueError('Single mode requires --types; CSV/dry-run/resume/only-dex are batch options.')
        report = build(args)
    except (ValueError, OSError, ET.ParseError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print(f'Output: {args.output.resolve()}')
    print(f'Animations: {", ".join(report["animations"])}; palette: {report["output_palette_colors_including_transparency"]} colors')
    print(f'Padding: {report["padding_per_side"]} pixels/side; source unchanged: {report["source_unchanged"]}')
    for warning in report['warnings']:
        print(f'Warning: {warning}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
