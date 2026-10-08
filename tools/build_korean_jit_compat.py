#!/usr/bin/env python3
"""Reassemble Korean engine in an existing ROM without rebuilding game data.

Usage: python -B tools/build_korean_jit_compat.py input.nds output.nds
Dependencies: existing repository ndspy, PyYAML, capstone and armips.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path
from PIL import Image  # Load the active runtime Pillow before legacy repository packages.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '.venv/Lib/site-packages'))
from ndspy.rom import NintendoDSRom
from ndspy.code import loadOverlayTable, MainCodeFile
from patch_engine.armips_runner import run_armips_bundle
from patch_engine.apply_korean import verify_korean_module
from patch_engine.manifest import load_module_manifest
from patch_engine.state import BuildState

def assemble(rom, module, asm_dir):
    table = loadOverlayTable(rom.arm9OverlayTable, lambda i, n: b'')
    entry = table[36]
    if entry.compressed:
        raise ValueError('Compressed ov36 is not supported by this fixed-size updater')
    cave = module['caves'][0]
    if cave['overlay'] != 'ov36':
        raise ValueError('Unexpected Korean engine cave')
    with tempfile.TemporaryDirectory(prefix='korean_jit_') as temp:
        work = Path(temp)
        a, o = work / 'arm9.bin', work / 'overlay_0036.bin'
        a.write_bytes(rom.arm9)
        o.write_bytes(rom.files[entry.fileID])
        inc = work / 'generated.inc'
        inc.write_text(
            f".definelabel KoreanCaveAddress, 0x{cave['load_address']:X}\n"
            f"KoreanCaveSize equ 0x{cave['size']:X}\n"
            f".definelabel KoGlyphTable, 0x023E0000\n"
            f"KoGlyphCount equ {module['data'][0]['glyph_count']}\n", encoding='utf-8')
        run_armips_bundle(armips=ROOT / 'tools/armips.exe', asm_dir=asm_dir,
            asm_entry='main.asm', binaries={'arm9.bin': a, 'overlay_0036.bin': o},
            generated_inc=inc)
        return a.read_bytes(), o.read_bytes(), entry

def changed_ranges(before, after):
    if len(before) != len(after):
        raise ValueError('Fixed-size patch unexpectedly resized a binary')
    ranges = []
    start = None
    for i, (a, b) in enumerate(zip(before, after)):
        if a != b and start is None:
            start = i
        elif a == b and start is not None:
            ranges.append((start, i))
            start = None
    if start is not None:
        ranges.append((start, len(before)))
    return ranges

def build(source, dest, baseline):
    if source.resolve() == dest.resolve():
        raise ValueError('Use a separate output ROM')
    report_path = dest.with_suffix('.jit-report.json')
    output_state = dest.with_suffix('.state.json')
    if any(p.exists() for p in (dest, report_path, output_state)):
        raise FileExistsError('Output already exists; choose a new output name')
    raw = source.read_bytes()
    rom = NintendoDSRom(raw)
    state = json.loads(source.with_suffix('.state.json').read_text(encoding='utf-8'))
    module = next(m for m in state['applied'] if m['id'] == 'korean')
    if module['version'] != 4:
        raise ValueError('Updater expects an unmodified Korean v4 ROM')
    a0, o0, entry = assemble(rom, module, baseline)
    if a0 != bytes(rom.arm9) or o0 != bytes(rom.files[entry.fileID]):
        raise ValueError('Input Korean engine differs from the saved v4 source; refusing to replace it')
    extracted = ROOT / 'extracted/arm9/arm9.bin'
    extracted_match = MainCodeFile(rom.arm9, rom.arm9RamAddress).sections[0].data == extracted.read_bytes()
    arm9, ov36, entry = assemble(rom, module, ROOT / 'true_patches/korean/asm')
    ar = changed_ranges(bytes(rom.arm9), arm9)
    ore = changed_ranges(bytes(rom.files[entry.fileID]), ov36)
    allowed = [(int(s['address']), int(s['address']) + 4) for s in load_module_manifest(ROOT / 'true_patches/korean')['arm9_sites']]
    for s, e in ar:
        if not all(any(lo <= 0x02000000 + off < hi for lo, hi in allowed) for off in range(s, e)):
            raise ValueError(f'Unexpected ARM9 change at {s:#x}-{e:#x}')
    cave = module['caves'][0]
    for s, e in ore:
        if not cave['file_offset'] <= s <= e <= cave['file_offset'] + cave['size']:
            raise ValueError('Overlay change outside the existing Korean engine cave')
    arm9_start, arm9_size = struct.unpack_from('<I', raw, 0x20)[0], struct.unpack_from('<I', raw, 0x2C)[0]
    fat = struct.unpack_from('<I', raw, 0x48)[0]
    ov_start, ov_end = struct.unpack_from('<II', raw, fat + entry.fileID * 8)
    if arm9_size != len(arm9) or ov_end - ov_start != len(ov36):
        raise ValueError('ROM sizes do not match fixed-size replacement')
    result = bytearray(raw)
    result[arm9_start:arm9_start + arm9_size] = arm9
    result[ov_start:ov_end] = ov36
    changed = changed_ranges(raw, result)
    if any(not (arm9_start <= s <= e <= arm9_start + arm9_size or ov_start <= s <= e <= ov_end) for s, e in changed):
        raise AssertionError('Unexpected ROM change')
    new_state = copy.deepcopy(state)
    new_module = next(m for m in new_state['applied'] if m['id'] == 'korean')
    new_module['version'] = int(load_module_manifest(ROOT / 'true_patches/korean')['version'])
    new_module['data'][0]['jit_compatibility'] = 'stack glyph pointer; register-based mutable flag read; device test pending'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(result)
    output_state.write_text(json.dumps(new_state, indent=2) + '\n', encoding='utf-8')
    verify_korean_module(dest, ROOT / 'true_patches/korean',
        load_module_manifest(ROOT / 'true_patches/korean'), BuildState.from_dict(new_state).get_module('korean'))
    check = NintendoDSRom(dest.read_bytes())
    assert len(rom.files) == len(check.files)
    assert all(bytes(x) == bytes(y) for i, (x, y) in enumerate(zip(rom.files, check.files)) if i != entry.fileID)
    assert rom.arm7 == check.arm7
    assert rom.arm9OverlayTable == check.arm9OverlayTable
    report = {'source': str(source.resolve()), 'output': str(dest.resolve()),
        'source_sha256': hashlib.sha256(raw).hexdigest(), 'output_sha256': hashlib.sha256(result).hexdigest(),
        'source_matches_updated_extracted_arm9': extracted_match,
        'source_v4_reassembly_matches': True,
        'changed_bytes': sum(e-s for s,e in changed),
        'arm9_changed_ranges': [[hex(0x02000000+s), hex(0x02000000+e)] for s,e in ar],
        'ov36_changed_ranges': [[hex(entry.ramAddress+s), hex(entry.ramAddress+e)] for s,e in ore],
        'all_other_files_identical': True, 'module_verification': 'passed',
        'melonDS_android_JIT_runtime': 'not tested; experimental compatibility candidate'}
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return dest

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--baseline', type=Path, default=ROOT / 'tools/korean_jit_v4_backup/asm')
    args = parser.parse_args()
    build(args.source, args.output, args.baseline)
