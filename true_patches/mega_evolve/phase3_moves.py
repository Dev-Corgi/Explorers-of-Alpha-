"""Small audited move catalogue for effect classifiers, shared with phase7."""
from __future__ import annotations
import hashlib,json,re,struct
from pathlib import Path
from patch_engine.korean_codec import parse_str_file,decode_english
from skytemple_files.data.waza_p.handler import WazaPHandler
from skytemple_files.container.sir0.handler import Sir0Handler
MODULE=Path(__file__).resolve().parent
REPO=MODULE.parents[1]
SHOWDOWN=REPO/'true_patches/base_stats_speed/data/showdown_moves.json'

def build(rom):
    source=json.loads(SHOWDOWN.read_text(encoding='utf-8'))
    normalize=lambda s:re.sub('[^a-z0-9]','',s.lower())
    wind={normalize(v['name']) for v in source.values() if v.get('flags',{}).get('wind')}
    strings=parse_str_file(rom.getFileByName('MESSAGE/text_e.str'))
    # MOVE_COUNT is a mutable library global (559 by default, 560 after the
    # accuracy module). Read the actual table boundaries instead of inheriting
    # the caller's import/apply order.
    container=Sir0Handler.deserialize(rom.getFileByName('BALANCE/waza_p.bin'))
    move_start,learn_start=struct.unpack_from('<II',container.content,container.data_pointer)
    count,padding=divmod(learn_start-move_start,26)
    if count<1 or padding>=16 or learn_start>len(container.content):
        raise ValueError('mega_evolve move table boundaries invalid')
    model=WazaPHandler.get_move_model()
    moves=[model(container.content[move_start+i*26:move_start+(i+1)*26]) for i in range(count)]
    overlays=rom.loadArm9Overlays();ov36=overlays[36]
    sheer_pointer=struct.unpack_from('<I',ov36.data,0x023c14ec-ov36.ramAddress)[0]
    sheer_owner=next(v for k,v in overlays.items() if k in (10,29,36) and v.ramAddress<=sheer_pointer<v.ramAddress+len(v.data))
    sheer=[]
    for i in range(len(moves)+1):
        id_=struct.unpack_from('<H',sheer_owner.data,sheer_pointer-sheer_owner.ramAddress+i*2)[0]
        if not id_:break
        if id_>=len(moves):raise ValueError('native Sheer Force move ID outside catalogue')
        sheer.append(id_)
    else:raise ValueError('native Sheer Force catalogue has no terminator')
    rows=[];target_rules=[];global_status=[];parental=[];drain=[]
    by_name={normalize(v['name']):v for v in source.values()}
    fixed_names={'counter','mirrorcoat','metalburst','bide','endeavor','superfang','naturesmadness','finalgambit','psywave','futuresight','doomdesire'}
    for i,move in enumerate(moves):
        name=decode_english(strings[8173+i])
        target_rules.append({'id':i,'category':int(move.category),'range':int(move.settings_range.range)})
        official=by_name.get(normalize(name),{});flags=official.get('flags',{})
        if official.get('drain') and int(move.category)!=2:drain.append(i)
        if (int(move.category)!=2 and move.number_chained_hits==1 and i not in (0,355,405,559)
            and not flags.get('charge') and not flags.get('noparentalbond') and not official.get('ohko')
            and not official.get('damage') and normalize(name) not in fixed_names):
            parental.append(i)
        if normalize(name) in {'sunnyday','raindance','sandstorm','hail','snowscape','electricterrain','grassyterrain','mistyterrain','psychicterrain'}:
            global_status.append(i)
        if normalize(name) in wind:
            rows.append({'id':i,'name':name,'category':int(move.category),
                         'chained_hits':move.number_chained_hits,'power':move.base_power})
    return {'schema':1,'classifier':'local_showdown_flags_wind',
            'source_sha256':hashlib.sha256(SHOWDOWN.read_bytes()).hexdigest(),
            'wind_moves':rows,'target_rules':target_rules,'global_status_moves':global_status,'parental_moves':parental,
            'sheer_force_moves':sheer,'sheer_force_source_pointer':sheer_pointer,'drain_moves':drain,
            'scope':'Wind immunity, move-native player range and weather/terrain exclusions for targeted guards.'}

def load():
    data=json.loads((MODULE/'data/phase3_moves.json').read_text(encoding='utf-8'))
    if data['schema']!=1 or len({r['id'] for r in data['wind_moves']})!=len(data['wind_moves']):
        raise ValueError('mega_evolve move catalogue invalid')
    return data

def validate_rom(rom):
    observed,expected=build(rom),load()
    if observed!=expected:
        changed=sorted(key for key in expected.keys()|observed.keys() if expected.get(key)!=observed.get(key))
        raise RuntimeError('mega_evolve audited move catalogue changed: '+json.dumps(changed,ensure_ascii=False))

def header():
    ids=[r['id'] for r in load()['wind_moves'] if r['category']!=2]
    data=load()
    return ('static const unsigned short wind_damage_moves[]={'+','.join(map(str,ids))+'};\n'
            'static const unsigned char player_move_ranges[]={'+','.join(str(r['range']) for r in data['target_rules'])+'};\n'
            'static const unsigned short global_status_moves[]={'+','.join(map(str,data['global_status_moves']))+'};\n'
            'static const unsigned short parental_moves[]={'+','.join(map(str,data['parental_moves']))+'};\n'
            'static const unsigned short sheer_force_moves[]={'+','.join(map(str,data['sheer_force_moves']))+'};\n'
            'static const unsigned short drain_moves[]={'+','.join(map(str,data['drain_moves']))+'};\n')

if __name__=='__main__':
    from ndspy.rom import NintendoDSRom
    rom=NintendoDSRom((REPO/'PatchTesting/Export Rom/Explorers of Alpha+.nds').read_bytes())
    (MODULE/'data/phase3_moves.json').write_text(json.dumps(build(rom),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
