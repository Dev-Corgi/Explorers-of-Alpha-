"""All available images through the public dispatcher; memory-only serialization."""
import hashlib,json,struct
from ndspy.rom import NintendoDSRom
from .verify_phase1 import SOURCE,MODULE
from patch_engine.manifest import load_module_manifest
from patch_engine.apply_mega_evolve import apply_mega_evolve_module,verify_mega_evolve_module
from patch_engine.state import BuildState,AppliedModule,CaveAllocation
from patch_engine.apply_module import _serialize_rom
from skytemple_files.common.types.file_types import FileType
from skytemple_files.data.md.handler import MdHandler

def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest();rom=NintendoDSRom(SOURCE.read_bytes())
    inventory=json.loads((MODULE/'data/phase5_assets.json').read_text(encoding='utf-8'))
    original={p:[bytes(v) for v in FileType.BIN_PACK.deserialize(rom.getFileByName(p))]
              for p in ('MONSTER/monster.bin','MONSTER/m_attack.bin','MONSTER/m_ground.bin')}
    old_md=rom.getFileByName('BALANCE/monster.md')
    prerequisite=load_module_manifest(MODULE.parent/'spinda_ev_speed');caves=[]
    for name,c in prerequisite.items():
        if name.startswith('arm9_') and isinstance(c,dict):caves.append(CaveAllocation('arm9',c['preferred'],c['estimated_bytes'],0x02000000+c['preferred']))
    state=BuildState('us_vanilla',0x022DC240,[AppliedModule('spinda_ev_speed',1,caves)])
    manifest=dict(load_module_manifest(MODULE),phase=5)
    record=apply_mega_evolve_module('mega_evolve',MODULE,manifest,rom,state)
    verify_mega_evolve_module(rom,MODULE,manifest,record);state.upsert_module(record)
    for path,old in original.items():
        pack=FileType.BIN_PACK.deserialize(rom.getFileByName(path));assert len(pack)==819+len(inventory['assets'])
        assert all(bytes(pack[i])==b for i,b in enumerate(old))
        assert all(bytes(pack[i])[:4]==b'MEW5' for i in range(819,len(pack)))
    md=MdHandler.deserialize(rom.getFileByName('BALANCE/monster.md'))
    for row in inventory['mapping']:assert md.entries[row['species']].sprite_index==819+row['asset']
    for row in inventory['missing']:
        # Held images retain phase4's old sprite reference.
        assert md.entries[row['species']].sprite_index<819
    output=_serialize_rom(rom,state)
    assert output[0x14]==12 and 256*1024*1024<len(output)<=512*1024*1024
    restored=NintendoDSRom(output);verify_mega_evolve_module(restored,MODULE,manifest,record)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    report=dict(schema=1,connected_forms=len(inventory['mapping']),held_forms=len(inventory['missing']),
                packages=len(inventory['assets']),additional_bytes=record.data[0]['sprites']['additional_bytes'],
                serialized_rom_bytes=len(output),card_capacity_mib=512,
                runtime_bytes=record.data[0]['runtime_size'],resident_bytes=record.data[0]['form_consumers']['cave']['size'],
                scope='Public apply/verify and all-pack memory serialization; no NDS/save outputs. Hardware/RAM integration deferred to phase8.')
    (MODULE/'data/phase5_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS public phase5:',report)
    print('Original sprite entries retained, all available forms connected, explicit holds, guards and512MiB FAT/FNT roundtrip. No ROM/save output.')
if __name__=='__main__':main()
