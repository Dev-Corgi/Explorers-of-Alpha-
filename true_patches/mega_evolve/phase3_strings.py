"""Build only assigned bilingual ability strings; workbook is never modified."""
from __future__ import annotations
import json,textwrap
from pathlib import Path
from .phase3 import load
from .phase2 import load as identities
MODULE=Path(__file__).resolve().parent
START=19800

def presentation(row):
    """Apply explicit user corrections over the workbook's older wording."""
    d=dict(row['display'])
    for label in ('normal','enhanced'):
        d[label+'_en']=d[label+'_en'].replace('hail','snow').replace('Hail','Snow')
        d[label+'_ko']=d[label+'_ko'].replace('싸라기눈','설경')
    if row['key']=='가뭄':
        d['normal_en']='Makes the floor sunny.';d['normal_ko']='층 입장 시 쾌청을 만든다.'
        d['enhanced_en']='Makes the floor harsh sunlight.';d['enhanced_ko']='층 입장 시 큰가뭄을 만든다.'
    if row['key']=='가속':
        for label in ('normal','enhanced'):
            d[label+'_en']=d[label+'_en'].replace('Speed +','Movement speed +')
    if row['key']=='불굴의마음':
        for label in ('normal','enhanced'):
            d[label+'_ko']=d[label+'_ko'].replace('이동속도','스피드')
    if row['key']=='고대활성':
        for label,step in (('normal',1),('enhanced',2)):
            d[label+'_en']=f'Highest stat +{step} stage(s) when sunlight is newly applied or your attack defeats a foe. Once per attack action.'
            d[label+'_ko']=f'햇살이 새로 적용되거나 자신의 공격으로 적을 처치하면 가장 높은 능력 +{step}단계. 처치 효과는 한 공격 행동당 1회.'
    if row['key']=='눈치우기':
        d['enhanced_en']='Speed +3 stages in snow.'
        d['enhanced_ko']='설경에서 스피드 계산단계 +3단계.'
    return d

def english(value):
    value=value.replace("−","-").replace("≤","<=").replace("≥",">=")
    value.encode("cp1252")
    return value

def description(name,text):
    # Original Omniscience already contains its name and control tags.
    if text.startswith("[CS:E]"):return english(text)
    return "[CS:E]"+name+"[CR]:\n"+"\n".join(textwrap.wrap(english(text),width=32,break_long_words=False))

def build():
    data=load();by_id={a["id"]:a for a in data["abilities"]};entries=[]
    for row in data["abilities"]:
        d=presentation(row);base=START+(row["id"]-256)*4
        for grade in (0,1):
            label="enhanced" if grade else "normal"
            en=english(d["name_en"])+( " II" if grade else "")
            ko=d["name_ko"]+("Ⅱ" if grade else "")
            text=d[label+"_en"]
            entries.extend([{"index":base+grade*2,"en":en,"ko":ko,"new":True},
                {"index":base+grade*2+1,"en":description(en,text),"ko":"[CS:E]"+ko+"[CR]:\n"+d[label+"_ko"],"new":True}])
    for legacy,runtime in identities()["legacy_import"].items():
        row=by_id[runtime];d=presentation(row);legacy=int(legacy)
        en=english(d["name_en"]);text=d["normal_en"]
        entries.extend([{"index":18451+legacy,"en":en,"ko":d["name_ko"],"new":False},
                        {"index":18707+legacy,"en":description(en,text),"ko":"[CS:E]"+d["name_ko"]+"[CR]:\n"+d["normal_ko"],"new":False}])
    if len({x["index"] for x in entries})!=len(entries):raise ValueError("overlapping ability string indices")
    return {"schema":1,"start":START,"entries":entries}

def load_strings():
    data=json.loads((MODULE/"data/phase3_strings.json").read_text(encoding="utf-8"))
    if data!=build():raise ValueError("stale phase3 strings")
    return data
if __name__=="__main__":
    (MODULE/"data/phase3_strings.json").write_text(json.dumps(build(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
