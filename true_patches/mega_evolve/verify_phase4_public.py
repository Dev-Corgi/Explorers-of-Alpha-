"""Public dispatcher, occupied prerequisite reservations and data guards."""
import copy,hashlib,json,struct
from .verify_phase1 import SOURCE,MODULE
from .phase4 import load
from ndspy.rom import NintendoDSRom
from patch_engine.manifest import load_module_manifest
from patch_engine.state import AppliedModule,BuildState,CaveAllocation
from patch_engine.apply_mega_evolve import apply_mega_evolve_module,verify_mega_evolve_module,load_registry
from patch_engine.mega_evolve_phase3_data import prepare_data
from patch_engine.mega_evolve_runtime import word,branch
from .verify_phase4_forms import FormWorld
from patch_engine.korean_codec import parse_str_file


def main():
    before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    rom=NintendoDSRom(SOURCE.read_bytes());manifest=load_module_manifest(MODULE)
    assert manifest['phase']==4 and manifest['species_save_bits']==12
    prerequisite=load_module_manifest(MODULE.parent/'spinda_ev_speed')
    caves=[]
    for name,config in prerequisite.items():
        if name.startswith('arm9_') and isinstance(config,dict):
            caves.append(CaveAllocation('arm9',config['preferred'],config['estimated_bytes'],
                                        0x02000000+config['preferred']))
    state=BuildState('us_vanilla',0x022DC240,[AppliedModule('spinda_ev_speed',1,caves)])
    expected=prepare_data(rom)[0]
    record=apply_mega_evolve_module('mega_evolve',MODULE,manifest,rom,state)
    verify_mega_evolve_module(rom,MODULE,manifest,record)
    original_text=parse_str_file(NintendoDSRom(SOURCE.read_bytes()).getFileByName('MESSAGE/text_e.str'))
    patched_text=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    assert patched_text[8735:9335]==original_text[8735:9335]
    assert rom.getFileByName('BALANCE/monster.md')[8:8+1155*68]==expected['BALANCE/monster.md'][8:]
    # Whole-record JSON persistence is required by the existing patch engine.
    serialized=json.loads(json.dumps(record.to_dict()))
    assert len(serialized['caves'])==3
    lo=caves[-1].file_offset+0x888;hi=caves[-1].file_offset+0x1000
    for cave in record.caves[1:]:assert lo<=cave.file_offset and cave.file_offset+cave.size<=hi
    # New IDs cannot become original story Mega/Origin IDs through GetBaseForm.
    w=FormWorld(rom,record);md=0x021A0000
    w.u.mem_write(md,rom.getFileByName('BALANCE/monster.md'))
    w.u.mem_write(0x020B09B4,struct.pack('<I',md+8))
    for row in load()['rows'][::2]:
        assert w.call('',row['species'],start=0x02054024)==row['species']
    # File and instruction drift are rejected by public verification.
    altered=NintendoDSRom(SOURCE.read_bytes())
    # Serialize the patched ROM only in memory to retain its FNT/file layout.
    altered=NintendoDSRom(rom.save())
    raw=bytearray(altered.getFileByName('BALANCE/monster.md'));raw[-1]^=1
    altered.setFileByName('BALANCE/monster.md',raw)
    try:verify_mega_evolve_module(altered,MODULE,manifest,record)
    except (AssertionError,ValueError):pass
    else:raise AssertionError('phase4 modified trailer accepted')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
    print('PASS public phase4: full dispatcher, occupied EVS1 parent reservations,')
    print('  original names/MD, explicit padding subreservations, persistent IDs, JSON records and drift guards.')
    print('ROM serialization stayed in memory; no NDS/save/full-stack output.')


if __name__=='__main__':main()
