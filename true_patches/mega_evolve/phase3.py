"""Phase3 source extraction and shared normal/enhanced effect inventory.
The workbook is presentation data; established gameplay overrides stay authoritative.
"""
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from .phase0 import normalize_ability
from .phase2 import load as identities
MODULE=Path(__file__).resolve().parent
WORKBOOK=Path(r"C:/Users/82106/Downloads/포켓몬_특성_설명_업데이트.xlsx")
NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
def rows(path):
    with zipfile.ZipFile(path) as z:
        strings=[]
        if "xl/sharedStrings.xml" in z.namelist():
            strings=["".join(t.text or "" for t in s.findall(".//m:t",NS)) for s in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si",NS)]
        result=[]
        for row in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).findall("m:sheetData/m:row",NS):
            cells={}
            for c in row:
                if c.find("m:f",NS) is not None:raise ValueError("description source contains formula")
                t=c.attrib.get("t");v=c.find("m:v",NS)
                value=strings[int(v.text)] if t=="s" else "".join(x.text or "" for x in c.findall(".//m:t",NS)) if t=="inlineStr" else v.text if v is not None else ""
                cells[re.sub(r"[0-9]","",c.attrib["r"])]=value
            if cells.get("A","").isdigit():result.append((int(row.attrib["r"]),[cells.get(k,"") for k in "ABCDEFG"]))
        return result

def family(row):
    s=row["normal"]
    if "weather_set" in row:return "weather_source"
    if any(x in s for x in ("타입으로 변경","피해 ×","피해 계수","피해계수","피해 배율","공격 계산값","방어 계산값","공격 계산단계","방어 계산단계","보정","위력 계산값")):return "calculation"
    if any(x in s for x in ("층 입장","플로어 시작","다음 층","층당")):return "floor_entry"
    if any(x in s for x in ("쓰러지","쓰러뜨","처치")):return "faint"
    if any(x in s for x in ("턴 종료","매 처리","자연 회복","자연 HP 회복")):return "turn_tick"
    if any(x in s for x in ("피해를 받으면","공격을 받으면","공격을 받","급소에 맞","부여되면")):return "received_event"
    if any(x in s for x in ("지속시간","상태","저하","능력 변화")):return "status_or_stage"
    if any(x in s for x in ("열매","도구","트래져백")):return "item"
    if any(x in s for x in ("이동","함정","무게","대상","행동 횟수")):return "action_or_world"
    return "native_behavior"

def expected_profiles(reg, ident):
    ids={a["key"]:a for a in ident["entries"]}
    profiles={}
    def add(species, pair):
        key=str(species)
        if not 0<species<reg["audit"]["rom_evidence"]["md_entries"]:
            raise ValueError("base profile species out of range")
        if key in profiles and profiles[key]!=pair:
            raise ValueError("conflicting base profile "+key)
        profiles[key]=pair[:]
    for target in reg["targets"]:
        add(target["source_rom_id"], [ids[k]["id"] for k in target["base_abilities"]])
    for row in reg["audit"]["legacy_counterparts"]:
        if row["classification"]=="gender_counterpart_candidate":
            add(row["plus600_id"], profiles[str(row["source_id"])])
    return profiles

def build():
    reg=json.loads((MODULE/"data/registry.json").read_text(encoding="utf-8"))
    ident=identities();ids={a["key"]:a for a in ident["entries"]}
    source=rows(WORKBOOK);by_number={int(v[0]):(n,v) for n,v in source}
    if len(by_number)!=len(source):raise ValueError("duplicate workbook effect number")
    result=[]
    for a in reg["abilities"]:
        if a["key"]=="Omniscience":
            display={"name_en":"Omniscience","name_ko":"전지전능","normal_en":a["normal"],"normal_ko":"공격·방어에 유리한 타입으로 변화하며 피해를 강화·경감한다. 능력 저하와 급소를 막는다.","enhanced_en":"Base effect; Judgment uses the holder's current primary-type Z-Move power and effects without requiring, consuming or resetting the Z gauge.","enhanced_ko":a["enhanced"],"workbook_row":None}
        else:
            n,v=by_number[a["effect_table_number"]]
            if normalize_ability(v[2])!=a["key"]:raise ValueError("workbook identity mismatch "+a["key"])
            if not all(v[1:]):raise ValueError("missing workbook presentation")
            display=dict(zip(("name_en","name_ko","normal_en","normal_ko","enhanced_en","enhanced_ko"),v[1:]));display["workbook_row"]=n
        result.append({"key":a["key"],"id":ids[a["key"]]["id"],"legacy_effect_id":ids[a["key"]]["legacy_effect_id"],
                       "family":family(a),"normal":a["normal"],"enhanced":a["enhanced"],"display":display})
    profiles=expected_profiles(reg, ident)
    return {"schema":1,"workbook":{"path":str(WORKBOOK),"sha256":hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(),"sheet":"특성 설명","total_rows":len(source),"matched":205,"omni":"prior_user_definition"},
            "authority":"Workbook presentation only; registry normal/enhanced and user overrides govern gameplay.","abilities":result,"base_profiles":profiles}

def validate(data):
    reg=json.loads((MODULE/"data/registry.json").read_text(encoding="utf-8"))
    expected={a["key"]:a for a in reg["abilities"]}
    current={a["key"]:a for a in data["abilities"]}
    identity_data=identities()
    ident={a["key"]:a for a in identity_data["entries"]}
    if data.get("schema")!=1:raise ValueError("phase3 schema mismatch")
    if data["base_profiles"]!=expected_profiles(reg, identity_data):
        raise ValueError("phase3 base profiles mismatch")
    if set(current)!=set(expected) or len(current)!=len(data["abilities"]):raise ValueError("phase3 scope mismatch")
    for key,row in current.items():
        if row["id"]!=ident[key]["id"] or row["legacy_effect_id"]!=ident[key]["legacy_effect_id"] or row["normal"]!=expected[key]["normal"] or row["enhanced"]!=expected[key]["enhanced"]:raise ValueError("phase3 identity/effect mismatch")
        if row["family"]!=family(expected[key]):raise ValueError("phase3 family mismatch")
        if not all(row["display"].get(k) for k in ("name_en","name_ko","normal_en","normal_ko","enhanced_en","enhanced_ko")):raise ValueError("missing presentation")
    return data

def load():
    return validate(json.loads((MODULE/"data/phase3.json").read_text(encoding="utf-8")))
def header(data):
    lines=[]
    for a in data["abilities"]:lines.append(f"#define A_{a['display']['name_en'].upper().replace(' ', '_').replace('-', '_').replace(chr(39),'')} {a['id']}")
    lines.append("typedef struct { unsigned short species,ability[2]; } BaseProfile;")
    lines.append("static const BaseProfile base_profiles[]={"+",".join("{"+str(k)+",{"+",".join(map(str,v))+"}}" for k,v in sorted(data["base_profiles"].items(),key=lambda kv:int(kv[0])))+"};")
    return "#ifndef ME_PHASE3_DATA\n#define ME_PHASE3_DATA\n"+"\n".join(lines)+"\n#endif\n"
if __name__=="__main__":
    (MODULE/"data/phase3.json").write_text(json.dumps(build(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
