"""Append converted sprites and size metadata without overwriting old images."""
import hashlib,json,struct
from pathlib import Path
from skytemple_files.common.types.file_types import FileType
from skytemple_files.data.md.handler import MdHandler
from true_patches.mega_evolve.phase4 import load as forms,binary

def chunks(raw):
    from skytemple_rust.st_pkdpx import Pkdpx
    parts=[Pkdpx.compress(raw[i:i+32768]).to_bytes() for i in range(0,len(raw),32768)]
    return struct.pack('<3I',0x3557454D,len(raw),len(parts))+b''.join(
        struct.pack('<I',len(p))+p+bytes((-len(p))%4) for p in parts)

def prepare(rom,module,inventory=None,conversion=None):
    inventory=inventory or json.loads((module/'data/phase5_assets.json').read_text(encoding='utf-8'))
    conversion=conversion or json.loads((module/'data/phase5_conversion.json').read_text(encoding='utf-8'))
    if (module/'data/phase5_aura_pose.json').is_file() and any(
        '/.cache/phase5_pose/' in a['path'] and not (module.parents[1]/a['path']/'AnimData.xml').is_file()
        for a in inventory['assets']):
        import subprocess,shutil
        python=shutil.which('python')
        if not python:raise RuntimeError('Aura regeneration requires Python with numpy/scipy')
        subprocess.run([python,'-B','-X','utf8','-m','true_patches.mega_evolve.phase5_reaura','--ensure'],
                       cwd=module.parents[1],check=True)
    derived=[a for a in inventory['assets'] if a.get('policy')=='user_requested_derived_aura']
    if any(not (module.parents[1]/a['path']/'AnimData.xml').is_file() for a in derived):
        import subprocess,shutil
        expected=(module/'data/phase5_repairs.json').read_bytes()
        python=shutil.which('python')
        if not python:raise RuntimeError('Aura regeneration requires Python with numpy/scipy')
        subprocess.run([python,'-B','-X','utf8','-m','true_patches.mega_evolve.phase5_repair'],
                       cwd=module.parents[1],check=True)
        if (module/'data/phase5_repairs.json').read_bytes()!=expected:
            raise RuntimeError('Regenerated aura provenance differs')
    if conversion['converted']!=conversion['total']:raise RuntimeError('phase5 sprite conversion is incomplete')
    rows={r['asset']:r for r in conversion['assets']};paths={
        'monster':'MONSTER/monster.bin','ground':'MONSTER/m_ground.bin','attack':'MONSTER/m_attack.bin'}
    packs={k:FileType.BIN_PACK.deserialize(rom.getFileByName(p)) for k,p in paths.items()}
    if {len(p) for p in packs.values()}!={819}:raise RuntimeError('phase5 original sprite pack count changed')
    before={k:hashlib.sha256(b''.join(bytes(v) for v in p)).hexdigest() for k,p in packs.items()}
    for asset in inventory['assets']:
        row=rows[asset['index']]
        if row['source_sha256']!=asset['sha256']:raise RuntimeError('phase5 conversion source mismatch')
        directory=module/row['cache']
        if not all((directory/(k+'.wan')).is_file() for k in packs):
            from true_patches.mega_evolve.phase5_convert import convert
            restored=convert(asset)
            if restored.get('outputs')!=row['outputs']:raise RuntimeError('phase5 sprite cache regeneration differs')
        for kind,pack in packs.items():
            raw=(directory/(kind+'.wan')).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=row['outputs'][kind+'.wan']:raise RuntimeError('phase5 cached sprite drift')
            if kind=='ground':
                from true_patches.mega_evolve.phase5_convert import pack_ground
                packed=pack_ground(row);raw=(directory/'ground.mew5').read_bytes()
                if hashlib.sha256(raw).hexdigest()!=packed['sha256']:raise RuntimeError('phase5 ground encoding drift')
            pack.append(raw)
    mapping={r['species']:r['asset'] for r in inventory['mapping']}
    formdata=forms();md=MdHandler.deserialize(rom.getFileByName('BALANCE/monster.md'));metadata=[]
    for form in formdata['rows']:
        entry=md.entries[form['species']]
        if form['species'] in mapping:
            a=rows[mapping[form['species']]];entry.sprite_index=819+mapping[form['species']]
            entry.unk17=a['tile_slots'];entry.unk18=min(255,a['file_pages'])
            metadata.append((a['tile_slots'],a['raw_sizes']['monster']))
        else:metadata.append((entry.unk17,entry.unk18*512))
    trailer=struct.pack('<4I',0x3550454D,1,formdata['first_species'],len(formdata['rows']))
    trailer+=b''.join(struct.pack('<2I',*r) for r in metadata)
    files={p:bytes(FileType.BIN_PACK.serialize(packs[k])) for k,p in paths.items()}
    files['BALANCE/monster.md']=bytes(MdHandler.serialize(md))+binary(formdata)+trailer
    details=dict(sprite_first=819,sprite_count=len(inventory['assets']),connected_forms=len(mapping),
                 held_forms=inventory['missing'],original_pack_hashes=before,
                 files_sha256={p:hashlib.sha256(b).hexdigest() for p,b in files.items()},
                 additional_bytes=sum(len(b)-len(rom.getFileByName(p)) for p,b in files.items()))
    return files,details

def verify(rom,details):
    for p,h in details['files_sha256'].items():
        if hashlib.sha256(rom.getFileByName(p)).hexdigest()!=h:raise AssertionError('phase5 image/metadata file changed')
