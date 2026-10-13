"""Stable 16-bit identities; grades are independent. No effect certification."""
from __future__ import annotations
import json
from pathlib import Path
MODULE=Path(__file__).resolve().parent
# Explicit Alpha name correspondence, including replacements whose translated
# source names still point at Electric Surge / Surge Surfer.
NATIVE_TEXT="""가뭄:49 가속:11 갈지자걸음:98 개미지옥:5 건조피부:85 게으름:42 곡예:84 괴력집게:9 근성:17 급류:16 기분파:37 까칠한피부:18 나이트메어:105 날씨부정:45 날카로운눈:30 내열:95 노가드:106 노말스킨:107 눈숨기:119 눈퍼뜨리기:120 다운로드:96 단순:97 대운:88 도주:43 독가시:39 돌머리:7 두꺼운지방:2 둔감:41 리프가드:123 마그마의무장:65 마이너스:63 마이페이스:64 마중물:122 매직가드:115 맹화:70 먹보:89 모래날림:28 모래숨기:29 발광:46 방음:60 배짱:87 벌레의알림:67 변색:59 분노의경혈:79 불가사의부적:53 불굴의마음:112 불꽃몸:62 색안경:80 선파워:90 속보:109 수의베일:66 순수한힘:34 스나이퍼:93 스킬링크:91 슬로스타트:94 습기:21 시간벌기:78 심록:26 싱크로:25 쓱쓱:27 아이스바디:77 악취:1 엽록소:74 예지몽:121 옹골참:13 위험예지:86 위협:6 유연:22 유폭:118 의기양양:73 의욕:48 이상한비늘:52 이판사판:92 인분:76 일찍기상:47 자력:23 자연회복:20 잔비:4 저수:36 적응력:99 전기엔진:102 전투무장:19 점착:44 정신력:31 정전기:32 젖은접시:3 천진:103 천하장사:34 철주먹:101 촉촉바디:81 축전:35 타오르는불꽃:72 탈피:33 테크니션:100 통찰:82 투쟁심:104 트레이스:40 틀깨기:83 포이즌힐:114 포자:61 프레셔:57 플라워기프트:113 플러스:56 피뢰침:50 픽업:71 하늘의은총:38 해감액:58 헤롱헤롱바디:68 흡반:14"""
# Same legacy effect need not mean the same identity (Pure/Huge Power, armor).
EFFECT_ALIASES={"순수한힘":34,"조가비갑옷":19,"하얀연기":15,"하드록":110}
# Non-legacy identities remain valid for copy/enhancement before their effects
# are implemented in phases 3/7. They are never truncated into byte IDs.
def build():
    source=json.loads((MODULE/"data/registry.json").read_text(encoding="utf-8"))
    explicit={k:int(v) for k,v in (x.split(":") for x in NATIVE_TEXT.split())}
    explicit.update({"일렉트릭스킨":0,"부유":55,"컬리헤어":180,"화학의힘":196,"면역":69,"복안":51})
    entries=[]
    for index,row in enumerate(source["abilities"]):
        candidates=[r["rom_id"] for r in row["legacy_rom_candidates"]]
        legacy=explicit.get(row["key"],candidates[0] if candidates else 0)
        if row["key"] in EFFECT_ALIASES: legacy=EFFECT_ALIASES[row["key"]]
        entries.append({"key":row["key"],"id":256+index,"legacy_effect_id":legacy,
                        "effect_status":"phase3_normal_phase7_enhanced"})
    imported={}
    for entry in entries:
        legacy=entry["legacy_effect_id"]
        if legacy and entry["key"] not in EFFECT_ALIASES: imported.setdefault(legacy,entry["id"])
    # Duplicate legacy names alone do not prove identical effects. Preserve
    # non-selected IDs24/251 as separate existing identities (including story).
    return {"schema":1,"grade":{"normal":0,"enhanced":1},"entries":entries,
            "legacy_import":{str(k):v for k,v in sorted(imported.items())},
            "legacy_unassigned":"preserve_1_to_254_no_candidate_filter"}
def load():
    expected=build()
    actual=json.loads((MODULE/"data/phase2_abilities.json").read_text(encoding="utf-8"))
    if actual!=expected: raise ValueError("stale phase2 identity mapping")
    return actual
def header(data):
    effects=[0]*462; imports=list(range(255))+[0]
    for e in data["entries"]:effects[e["id"]]=e["legacy_effect_id"]
    for k,v in data["legacy_import"].items():imports[int(k)]=v
    return "static const unsigned short ability_import[256]={"+",".join(map(str,imports))+"};\n"+"static const unsigned char ability_effect[462]={"+",".join(map(str,effects))+"};\n"
if __name__=="__main__":
    (MODULE/"data/phase2_abilities.json").write_text(json.dumps(build(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
