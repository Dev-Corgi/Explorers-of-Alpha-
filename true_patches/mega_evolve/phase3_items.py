"""Item identity audit for ordinary Harvest/Cud Chew/Pickup.

Category 2 also contains drugs and elixirs. Select actual seed/berry names,
never all category-2 items. Source assets stay read-only.
"""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
MODULE=Path(__file__).resolve().parent
SOURCE=MODULE.parents[1]/'PatchTesting/Export Rom/Explorers of Alpha+.nds'
EXCLUDED=(73,89,93)

def inventory(rom):
    from skytemple_files.data.item_p.handler import ItemPHandler
    from patch_engine.korean_codec import parse_str_file,decode_english
    strings=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    entries=ItemPHandler.deserialize(rom.getFileByName('BALANCE/item_p.bin')).item_list
    rows=[]
    for index,row in enumerate(entries):
        if not row.is_valid or row.category!=2:continue
        name=re.sub(r'\[[^]]*\]','',decode_english(strings[6773+row.item_id])).strip()
        if name.endswith((' Berry',' Seed')):
            rows.append({'id':index,'name':name,'category':int(row.category)})
    return rows

def build():
    from ndspy.rom import NintendoDSRom
    rom=NintendoDSRom(SOURCE.read_bytes());rows=inventory(rom)
    overlay=rom.loadArm9Overlays()[29].data
    return {'schema':1,'source_items_sha256':hashlib.sha256(rom.getFileByName('BALANCE/item_p.bin')).hexdigest(),
            'berries':[row for row in rows if row['name'].endswith(' Berry')],
            'pickup':[row for row in rows if row['id'] not in EXCLUDED],
            'excluded':list(EXCLUDED),
            'legacy_pickup_block':{'start':0x022fd69c,'end':0x022fd760,
                                  'sha256':hashlib.sha256(overlay[0x022fd69c-0x022dc240:0x022fd760-0x022dc240]).hexdigest()}}

def load():
    data=json.loads((MODULE/'data/phase3_items.json').read_text(encoding='utf-8'))
    if data.get('schema')!=1 or data['excluded']!=list(EXCLUDED):raise ValueError('phase3 item schema/exclusions changed')
    for key in ('berries','pickup'):
        rows=data[key];ids=[row['id'] for row in rows]
        if not rows or ids!=sorted(set(ids)) or any(not 0<r['id']<65536 or r['category']!=2 for r in rows):
            raise ValueError('phase3 item identities invalid')
    if any(row['id'] in EXCLUDED for row in data['pickup']):raise ValueError('excluded Pickup item')
    if any(not row['name'].endswith(' Berry') for row in data['berries']):raise ValueError('non-berry retention item')
    if any(not row['name'].endswith((' Berry',' Seed')) for row in data['pickup']):raise ValueError('non-seed/berry Pickup item')
    block=data['legacy_pickup_block']
    if (block['start'],block['end'])!=(0x022fd69c,0x022fd760) or not re.fullmatch('[0-9a-f]{64}',block['sha256']):
        raise ValueError('invalid legacy Pickup guard')
    return data

def validate_rom(rom):
    data=load();rows=inventory(rom)
    if data['berries']!=[r for r in rows if r['name'].endswith(' Berry')] or data['pickup']!=[r for r in rows if r['id'] not in EXCLUDED]:
        raise RuntimeError('mega_evolve item identities changed')
    return data

def header(data):
    return ''.join('static const unsigned short '+name+'[]={'+','.join(str(row['id']) for row in data[key])+'};\n'
                   for name,key in (('berry_items','berries'),('pickup_items','pickup')))

if __name__=='__main__':
    (MODULE/'data/phase3_items.json').write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
