"""Install Trial Tower as part of mega_evolve, without altering shared bosses."""
from __future__ import annotations
import copy
import hashlib
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from ndspy.code import saveOverlayTable
from skytemple_files.common.types.file_types import FileType
from skytemple_files.common.util import get_ppmdu_config_for_rom
from skytemple_files.hardcoded.dungeons import HardcodedDungeons
from skytemple_files.hardcoded.fixed_floor import HardcodedFixedFloorTables
from .mega_evolve_runtime import OV29, OV36, allocate_runtime, branch, word
from .korean_codec import parse_str_file, build_str_file, decode_english
from .state import BuildState, CaveAllocation, HookRecord
from true_patches.mega_evolve.trial_tower import load


def install(rom, module, state, record):
    contract=load();config=get_ppmdu_config_for_rom(rom)
    dungeon=contract['dungeon_id'];source=contract['source_dungeon'];first=contract['room_first']
    # Alpha loads shared overlay36 during early ARM9 initialization, before
    # any ground/title string lookups can reach these resident entry points.
    if (word(rom.arm9,0x02000ca0,0x02000000)!=branch(0x02000ca0,0x020047c0,True)
            or word(rom.arm9,0x020047cc,0x02000000)!=0xe3a02024):
        raise RuntimeError('Trial Tower shared-overlay boot prerequisite changed')
    for name in ('mappa_s.bin','fixed.bin'):
        if rom.getFileByName('BALANCE/'+name)!=rom.getFileByName('UTILITY/'+name):
            raise RuntimeError('Trial Tower authoring/native banks disagree: '+name)
    mappa=FileType.MAPPA_BIN.deserialize(rom.getFileByName('BALANCE/mappa_s.bin'))
    definitions=HardcodedDungeons.get_dungeon_list(rom.arm9,config)
    group=len(mappa.floor_lists)
    if group>255:raise RuntimeError('Trial Tower mappa group u8 exhausted')
    base=definitions[source]
    if base.number_floors!=99 or base.start_after:raise RuntimeError('Zero Isle South definition changed')
    floors=copy.deepcopy(mappa.floor_lists[base.mappa_index])
    if len(floors)!=99:raise RuntimeError('Zero Isle South must have 99 floors')
    fixed=FileType.FIXED_BIN.deserialize(rom.getFileByName('BALANCE/fixed.bin'))
    original_rooms={str(n):hashlib.sha256(fixed.fixed_floors[n].to_bytes()).hexdigest() for n in (21,77)}
    used={int(f.layout.fixed_floor_id) for rows in mappa.floor_lists for f in rows}
    for i in range(10):
        n=first+i
        if n in used or fixed.fixed_floors[n].actions:raise RuntimeError(f'Trial Tower fixed room {n} occupied')
        fixed.fixed_floors[n]=copy.deepcopy(fixed.fixed_floors[21 if i<9 else 77])
        floors[(i+1)*10-1 if i<9 else 98].layout.fixed_floor_id=n
    mappa.floor_lists.append(floors)
    files={}
    for name,kind,value in (('mappa_s.bin',FileType.MAPPA_BIN,mappa),('fixed.bin',FileType.FIXED_BIN,fixed)):
        blob=bytes(kind.serialize(value))
        # Native Alpha loaders select UTILITY, while authoring APIs select BALANCE.
        for bank in ('BALANCE','UTILITY'):
            path=bank+'/'+name;rom.setFileByName(path,blob);files[path]=hashlib.sha256(blob).hexdigest()
    tables=rom.loadArm9Overlays();ov10=bytearray(tables[10].data)
    props=HardcodedFixedFloorTables.get_fixed_floor_properties(ov10,config)
    for i in range(10):
        props[first+i]=copy.deepcopy(props[21 if i<9 else 77])
        props[first+i].exit_floor_when_defeating_enemies=True
    HardcodedFixedFloorTables.set_fixed_floor_properties(ov10,props,config)
    arm9=bytearray(rom.arm9)
    restrictions=HardcodedDungeons.get_dungeon_restrictions(arm9,config)
    restrictions[dungeon]=copy.deepcopy(restrictions[source])
    HardcodedDungeons.set_dungeon_restrictions(restrictions,arm9,config)
    markers=HardcodedDungeons.get_marker_placements(arm9,config)
    marker=dungeon+1
    if markers[marker].reference_id!=233:raise RuntimeError('Trial Tower dummy map marker occupied')
    markers[marker]=copy.deepcopy(markers[source+1])
    HardcodedDungeons.set_marker_placements(markers,arm9,config)
    strings=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'));index=contract['name_index']
    name_aliases=[config.string_index_data.string_blocks['Dungeon Names ('+name+')'].begin+dungeon+1
                  for name in ('Main','Selection','SetDungeonBanner','Banner')]
    if any(decode_english(strings[n-1]).strip() not in ('','[M:D1]','[M:D1]Dummy') for n in name_aliases):
        raise RuntimeError('Trial Tower dungeon ID already has a name')
    if index<len(strings) and decode_english(strings[index]).strip() not in ('','[M:D1]'):
        raise RuntimeError('Trial Tower string index occupied')
    strings.extend([b'']*max(0,index+1-len(strings)));strings[index]=contract['en'].encode('ascii')
    rom.setFileByName('MESSAGE/text_e.str',build_str_file(strings))
    # All four native name slots alias a genuinely empty new string. Placeholder
    # strings and original dungeon names are never overwritten.
    combined=BuildState('us_vanilla',OV29,list(state.applied) if state else [])
    combined.applied.append(record)
    slot,ov36=allocate_runtime(bytearray(tables[36].data),combined,0x400)
    compiler=shutil.which('arm-none-eabi-gcc')
    if not compiler:raise RuntimeError('Trial Tower requires arm-none-eabi-gcc')
    prefix=str(Path(compiler).with_name('arm-none-eabi-'));suffix='.exe' if compiler.endswith('.exe') else ''
    menu_load=word(tables[11].data,0x022ffe08,tables[11].ramAddress)
    if menu_load!=0xe59f0058:raise RuntimeError('Trial Tower menu pointer load changed')
    # ARM literal loads use PC=instruction+8. The preceding literal is the
    # menu-kind selector, not the pointer to the allocated departure menu.
    menu_literal=0x022ffe08+8+(menu_load&0xfff)
    menu_ptr=word(tables[11].data,menu_literal,tables[11].ramAddress)
    defines=dict(TT_DUNGEON=dungeon,TT_GROUP=group,TT_MARKER=marker,
                 TT_NAME_ID=index+1,TT_MENU_PTR=menu_ptr,
                 TT_MENU_CAPACITY=(word(tables[11].data,0x022ffe60,tables[11].ramAddress)-0x1c4)//4)
    defines.update({f'TT_NAME_ALIAS_{i}':v for i,v in enumerate(name_aliases)})
    with tempfile.TemporaryDirectory(prefix='mega_tower_') as tmp:
        work=Path(tmp);(work/'tower_resident_generated.h').write_text(
            ''.join(f'#define {k} {v}\n' for k,v in defines.items()),encoding='ascii')
        (work/'tower.ld').write_text(f'SECTIONS {{ . = {slot.load_address}; .text : {{ *(.text*) }} /DISCARD/ : {{ *(.ARM.attributes) }} }}',encoding='ascii')
        elf=work/'tower.elf'
        result=subprocess.run([compiler,'-mcpu=arm946e-s','-marm','-nostdlib','-I',str(work),
            str(module/'runtime/trial_tower_resident.S'),'-Wl,-T,'+str(work/'tower.ld'),'-o',str(elf)],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        symbols={}
        for line in subprocess.check_output([prefix+'nm'+suffix,'--defined-only',str(elf)],text=True).splitlines():
            a,k,n=line.split();symbols[n]=int(a,16)
        binary=work/'tower.bin'
        subprocess.run([prefix+'objcopy'+suffix,'-O','binary',str(elf),str(binary)],check=True,capture_output=True)
        blob=binary.read_bytes()
    if len(blob)>slot.size:raise RuntimeError('Trial Tower resident cave overflow')
    ov36[slot.file_offset:slot.file_offset+slot.size]=blob.ljust(slot.size,b'\0')
    edits=[]
    def patch(binary,site,target,expected,link=False):
        b,base=(arm9,0x02000000) if binary==0 else (tables[binary].data,tables[binary].ramAddress)
        old=word(b,site,base)
        if old!=expected:raise RuntimeError(f'Trial Tower hook guard changed at {site:#x}: {old:#x}')
        value=branch(site,target,link);struct.pack_into('<I',b,site-base,value)
        edits.append(dict(binary=binary,site=site,after=value))
        record.hooks.append(HookRecord('TrialTower',site,'bl' if link else 'b','TrialTower','trial_tower'))
    for site,name,expected in ((0x0204f57c,'ME_TowerFloors',0xe35000b4),
        (0x0204f5c8,'ME_TowerGroup',0xe35000b4),(0x0204f5e0,'ME_TowerPreceding',0xe35000b4),
        (0x0204f5f8,'ME_TowerGroupFloors',0xe35000b4),(0x0206a714,'ME_TowerSwapId',0xe3a0c000),
        (0x0206a750,'ME_TowerSwapIndex',0xe3e01000),(0x0206a84c,'ME_TowerMap',0xe35000b4),
        (0x02025788,'ME_TowerName',0xe92d4038)):
        patch(0,site,symbols[name],expected)
    patch(11,0x022ffe08,symbols['ME_TowerMenu'],0xe59f0058)
    runtime=record.data[0]['symbols']
    patch(29,0x0234389c,runtime['ME_TowerSpawnHook'],branch(0x0234389c,0x023da080,True),True)
    patch(29,0x023438bc,runtime['ME_TowerStatsHook'],0xe5d80000)
    patch(29,0x02343eb8,runtime['ME_TowerSpeciesHook'],branch(0x02343eb8,0x023da090,True),True)
    rom.arm9=bytes(arm9)
    tables[10].data=ov10;tables[36].data=ov36
    for n in (10,11,29,36):
        ov=tables[n];ov.compressed=False;ov.ramSize=len(ov.data);rom.files[ov.fileID]=ov.save(compress=False)
    rom.arm9OverlayTable=saveOverlayTable(tables)
    cave=CaveAllocation('ov36',slot.file_offset,slot.size,slot.load_address);record.caves.append(cave)
    record.data[0]['cave_hashes'].append(hashlib.sha256(bytes(ov36[slot.file_offset:slot.file_offset+slot.size])).hexdigest())
    record.data[0].pop('cave_sha256',None)
    return dict(group=group,dungeon=dungeon,room_first=first,marker=marker,edits=edits,
                symbols=symbols,files=files,original_rooms=original_rooms,
                name_index=index,restriction=restrictions[dungeon].to_bytes().hex(),
                map_marker=markers[marker].to_bytes().hex(),
                properties=[p.to_bytes().hex() for p in props[first:first+10]])


def verify(rom,info):
    c=get_ppmdu_config_for_rom(rom);tables=rom.loadArm9Overlays();d=load()
    for path,digest in info['files'].items():
        if hashlib.sha256(rom.getFileByName(path)).hexdigest()!=digest:raise AssertionError('Trial Tower file drift: '+path)
    for edit in info['edits']:
        b,base=(rom.arm9,0x02000000) if not edit['binary'] else (tables[edit['binary']].data,tables[edit['binary']].ramAddress)
        if word(b,edit['site'],base)!=edit['after']:raise AssertionError('Trial Tower hook drift')
    m=FileType.MAPPA_BIN.deserialize(rom.getFileByName('BALANCE/mappa_s.bin'))
    source=HardcodedDungeons.get_dungeon_list(rom.arm9,c)[d['source_dungeon']]
    floors=m.floor_lists[info['group']];base=m.floor_lists[source.mappa_index]
    if len(floors)!=99 or len(base)!=99:raise AssertionError('Trial Tower floor count drift')
    for i,(a,b) in enumerate(zip(floors,base)):
        clone=copy.deepcopy(a)
        expected=d['room_first']+(i+1)//10-1 if (i+1)%10==0 and i<90 else d['room_first']+9 if i==98 else int(b.layout.fixed_floor_id)
        if int(a.layout.fixed_floor_id)!=expected:raise AssertionError('Trial Tower floor assignment drift')
        clone.layout.fixed_floor_id=b.layout.fixed_floor_id
        # Floor/layout model equality covers the complete spawn/item/trap data.
        if clone!=b:raise AssertionError('Trial Tower floor clone drift')
    f=FileType.FIXED_BIN.deserialize(rom.getFileByName('BALANCE/fixed.bin'))
    for n,digest in info['original_rooms'].items():
        if hashlib.sha256(f.fixed_floors[int(n)].to_bytes()).hexdigest()!=digest:raise AssertionError('original boss room changed')
    for i in range(10):
        if f.fixed_floors[d['room_first']+i].to_bytes()!=f.fixed_floors[21 if i<9 else 77].to_bytes():raise AssertionError('Trial Tower layout drift')
    p=HardcodedFixedFloorTables.get_fixed_floor_properties(tables[10].data,c)
    if [x.to_bytes().hex() for x in p[d['room_first']:d['room_first']+10]]!=info['properties']:raise AssertionError('Trial Tower victory properties drift')
    restrictions=HardcodedDungeons.get_dungeon_restrictions(rom.arm9,c)
    if restrictions[d['dungeon_id']].to_bytes().hex()!=info['restriction']:raise AssertionError('Trial Tower restrictions drift')
    markers=HardcodedDungeons.get_marker_placements(rom.arm9,c)
    if markers[info['marker']].to_bytes().hex()!=info['map_marker']:raise AssertionError('Trial Tower map marker drift')
    text=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    if decode_english(text[d['name_index']])!=d['en']:raise AssertionError('Trial Tower name drift')
