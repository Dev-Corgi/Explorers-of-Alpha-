"""Dispatch mega_evolve data validation and implemented runtime phases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .state import AppliedModule
from true_patches.mega_evolve.phase0 import validate


def load_registry(module_dir, manifest):
    if manifest.get("phase") not in (0,1,2,3,4,5,6):
        raise RuntimeError("requested mega_evolve runtime phase is not implemented")
    path = module_dir / "data/registry.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    metadata = validate(registry)
    bits=manifest.get('species_save_bits',11)
    if bits not in (11,12):raise RuntimeError('unsupported mega_evolve species save width')
    if manifest.get('phase',0)>=3 and bits==12:
        metadata['species_save_bits']=12
        for codec_path in (module_dir/'runtime/save12.c',Path(__file__).with_name('mega_evolve_save12.py'),
                     Path(__file__).with_name('mega_evolve_resident_slot.py'),
                     Path(__file__).with_name('mega_evolve_native_data.py')):
            metadata[codec_path.name+'_sha256']=hashlib.sha256(codec_path.read_bytes()).hexdigest()
    if manifest.get("phase",0)>=2:
        from true_patches.mega_evolve.phase2 import load
        load()
        metadata["phase2_hooks_sha256"]=hashlib.sha256((module_dir/"data/phase2_hooks.json").read_bytes()).hexdigest()
        metadata["phase2_abilities_sha256"]=hashlib.sha256((module_dir/"data/phase2_abilities.json").read_bytes()).hexdigest()
    if manifest.get("phase",0)>=3:
        from true_patches.mega_evolve.phase3 import load as phase3_data
        from true_patches.mega_evolve.audit_phase3 import build as coverage
        data=phase3_data();report=coverage()
        if len(report['abilities'])!=206 or any(a['normal_status']=='pending_implementation' for a in report['abilities']):
            raise RuntimeError('mega_evolve phase3 ordinary implementation is incomplete')
        saved=json.loads((module_dir/'data/phase3_coverage.json').read_text(encoding='utf-8'))
        if saved!=report:raise RuntimeError('mega_evolve phase3 effect coverage is stale')
        metadata['phase3_ordinary_count']=len(data['abilities'])
        for filename in ('phase3.json','phase3_strings.json','phase3_coverage.json','phase3_native_consumers.json'):
            metadata[filename.replace('.json','')+'_sha256']=hashlib.sha256((module_dir/'data'/filename).read_bytes()).hexdigest()
    if manifest.get('phase',0)>=4:
        from true_patches.mega_evolve.phase4 import load as form_data
        forms=form_data()
        if bits!=12:raise RuntimeError('phase4 requires 12-bit species saves')
        metadata['phase4_species_count']=forms['total_species']
        metadata['phase4_name_policy']='reuse_origin_except_new_ordinary_evolutions'
        for relative in ('data/phase4_forms.json','runtime/phase4.c','runtime/phase4_resident.c',
                         'runtime/phase4_resident.S','runtime/phase4_quick.c','new_species.py',
                         'data/phase5_new_species_source.json'):
            metadata[relative+'_sha256']=hashlib.sha256((module_dir/relative).read_bytes()).hexdigest()
    if manifest.get('phase',0)>=5:
        inventory=json.loads((module_dir/'data/phase5_assets.json').read_text(encoding='utf-8'))
        conversion=json.loads((module_dir/'data/phase5_conversion.json').read_text(encoding='utf-8'))
        if conversion['converted']!=conversion['total'] or conversion['total']!=len(inventory['assets']):
            raise RuntimeError('mega_evolve phase5 sprite conversion is incomplete')
        metadata['phase5_connected_forms']=len(inventory['mapping']);metadata['phase5_held_forms']=len(inventory['missing'])
        from true_patches.mega_evolve.phase5_routes import build as routes
        if json.loads((module_dir/'data/phase5_evolution_routes.json').read_text(encoding='utf-8'))!=routes():
            raise RuntimeError('mega_evolve Spring route contract is stale')
        for relative in ('data/phase5_assets.json','data/phase5_conversion.json','phase5.py','phase5_convert.py',
                         'runtime/phase5.c','runtime/phase5_hooks.S','runtime/phase5_decode.c',
                         'phase5_repair.py','data/phase5_repairs.json','phase5_routes.py',
                         'data/phase5_evolution_routes.json','phase5_reaura.py',
                         'data/phase5_shiny_palettes.json','data/phase5_aura_pose.json'):
            metadata[relative+'_sha256']=hashlib.sha256((module_dir/relative).read_bytes()).hexdigest()
    if manifest.get('phase',0)>=6:
        from true_patches.mega_evolve.phase6 import load
        phase6=load();metadata['phase6_routes']=len(phase6['routes'])
        for relative in ('phase6.py','data/phase6.json','runtime/phase6_spring.c','runtime/phase6_spring.S'):
            metadata[relative+'_sha256']=hashlib.sha256((module_dir/relative).read_bytes()).hexdigest()
    metadata["registry_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return registry, metadata


def validate_rom(rom_path, registry, expanded=False, sprites=False):
    from ndspy.rom import NintendoDSRom
    from skytemple_files.data.md.handler import MdHandler
    rom = rom_path if isinstance(rom_path,NintendoDSRom) else NintendoDSRom(Path(rom_path).read_bytes())
    md = MdHandler.deserialize(rom.getFileByName("BALANCE/monster.md"))
    expected=registry['audit']['rom_evidence']['md_entries']
    if expanded:
        from true_patches.mega_evolve.phase4 import load as forms,binary
        data=forms();expected=data['total_species']
        tail=rom.getFileByName('BALANCE/monster.md')[8+expected*68:];base=binary(data)
        if (tail[:len(base)] if sprites else tail)!=base:
            raise ValueError('mega_evolve phase4 form trailer changed')
        if sprites:
            import struct
            meta=tail[len(base):]
            if len(meta)!=16+len(data['rows'])*8 or struct.unpack_from('<4I',meta)!=(0x3550454D,1,data['first_species'],len(data['rows'])):
                raise ValueError('mega_evolve phase5 sprite metadata changed')
    if len(md.entries) != expected:
        raise ValueError("mega_evolve phase0: unexpected MD count")
    for target in registry["targets"]:
        if md.entries[target["source_rom_id"]].national_pokedex_number != target["dex"]:
            raise ValueError("mega_evolve phase0: source species identity changed")
    if md.entries[1137].ability_primary != 250:
        raise ValueError("mega_evolve phase0: story Omniscience changed")


def apply_mega_evolve_module(module_id, module_dir, manifest, rom_path, state=None):
    registry, metadata = load_registry(module_dir, manifest)
    validate_rom(rom_path, registry)
    if manifest.get("phase",0)>=1:
        from .mega_evolve_runtime import apply_phase1
        return apply_phase1(rom_path,module_dir,manifest,state,metadata)
    return AppliedModule(id=module_id, version=manifest.get("version", 1),
                         data=[{"mega_evolve": metadata}])


def verify_mega_evolve_module(rom_path, module_dir, manifest, record):
    registry, metadata = load_registry(module_dir, manifest)
    if manifest.get("phase",0)>=1:
        from .mega_evolve_runtime import verify_phase1
        verify_phase1(rom_path,module_dir,manifest,record,metadata)
        validate_rom(rom_path,registry,expanded=manifest['phase']>=4,sprites=manifest['phase']>=5)
        return
    if record is None or record.caves or record.hooks or record.data != [{"mega_evolve": metadata}]:
        raise AssertionError("mega_evolve phase0: missing/stale registry validation record")
    validate_rom(rom_path, registry)
