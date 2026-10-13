"""Small audited move catalogue for effect classifiers, shared with phase7."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from patch_engine.korean_codec import parse_str_file,decode_english
from skytemple_files.data.waza_p.handler import WazaPHandler
MODULE=Path(__file__).resolve().parent
REPO=MODULE.parents[1]
SHOWDOWN=REPO/'true_patches/base_stats_speed/data/showdown_moves.json'

def build(rom):
    source=json.loads(SHOWDOWN.read_text(encoding='utf-8'))
    normalize=lambda s:re.sub('[^a-z0-9]','',s.lower())
    wind={normalize(v['name']) for v in source.values() if v.get('flags',{}).get('wind')}
    strings=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    moves=WazaPHandler.deserialize(rom.getFileByName('BALANCE/waza_p.bin')).moves
    rows=[];target_rules=[];global_status=[]
    for i,move in enumerate(moves):
        name=decode_english(strings[8173+i])
        target_rules.append({'id':i,'category':int(move.category),'range':int(move.settings_range.range)})
        if normalize(name) in {'sunnyday','raindance','sandstorm','hail','snowscape','electricterrain','grassyterrain','mistyterrain','psychicterrain'}:
            global_status.append(i)
        if normalize(name) in wind:
            rows.append({'id':i,'name':name,'category':int(move.category),
                         'chained_hits':move.number_chained_hits,'power':move.base_power})
    return {'schema':1,'classifier':'local_showdown_flags_wind',
            'source_sha256':hashlib.sha256(SHOWDOWN.read_bytes()).hexdigest(),
            'wind_moves':rows,'target_rules':target_rules,'global_status_moves':global_status,
            'scope':'Wind immunity, move-native player range and weather/terrain exclusions for targeted guards.'}

def load():
    data=json.loads((MODULE/'data/phase3_moves.json').read_text(encoding='utf-8'))
    if data['schema']!=1 or len({r['id'] for r in data['wind_moves']})!=len(data['wind_moves']):
        raise ValueError('mega_evolve move catalogue invalid')
    return data

def validate_rom(rom):
    if build(rom)!=load():raise RuntimeError('mega_evolve audited wind move catalogue changed')

def header():
    ids=[r['id'] for r in load()['wind_moves'] if r['category']!=2]
    data=load()
    return ('static const unsigned short wind_damage_moves[]={'+','.join(map(str,ids))+'};\n'
            'static const unsigned char player_move_ranges[]={'+','.join(str(r['range']) for r in data['target_rules'])+'};\n'
            'static const unsigned short global_status_moves[]={'+','.join(map(str,data['global_status_moves']))+'};\n')

if __name__=='__main__':
    from ndspy.rom import NintendoDSRom
    rom=NintendoDSRom((REPO/'PatchTesting/Export Rom/Explorers of Alpha+.nds').read_bytes())
    (MODULE/'data/phase3_moves.json').write_text(json.dumps(build(rom),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
