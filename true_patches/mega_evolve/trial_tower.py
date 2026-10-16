"""Trial Tower's declarative encounter contract (IDs are Alpha ROM IDs)."""
import json
from pathlib import Path

DATA = Path(__file__).with_name('data') / 'trial_tower.json'


def load():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    assert len(data['bosses']) == 9
    assert len({r['species'] for r in data['bosses']}) == 9
    assert data['levels'] == [12, 24, 30, 36, 41, 44, 47, 49, 51]
    assert all(len(r['moves']) == 4 for r in data['bosses'] + data['final'])
    food = data['floor_food_weights']
    assert sum(food.values()) == 10000 and all(0 < w < 65535 for w in food.values())
    assert set(map(int, food)) == {109, 110, 137, *range(119, 136)}
    return data


def header():
    d = load()
    out = f"#define TT_DUNGEON {d['dungeon_id']}\n#define TT_ROOM_FIRST {d['room_first']}\n"
    out += 'static const unsigned char tt_levels[]={'+','.join(map(str,d['levels']))+'};\n'
    out += 'typedef struct {unsigned short species,moves[4];} TTBoss;\n'
    for name,rows in (('tt_bosses',d['bosses']),('tt_final',d['final'])):
        out += f'static const TTBoss {name}[]={{'+','.join(
            '{'+str(r['species'])+',{'+','.join(map(str,r['moves']))+'}}' for r in rows)+'};\n'
    return out
