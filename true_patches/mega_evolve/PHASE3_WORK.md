# 페이즈 3 작업 기록 — 진행 중

페이즈 3은 아직 완료/활성화하지 않았다. manifest는 phase 2, version 4다.
용량 자동 확장 정책은 커밋 1a6a52d로 별도 푸시했다.
현재 NDS/세이브 출력은 변경하지 않았다.

## 준비한 자료와 구현 초안

- phase3.py / data/phase3.json: 새 XLSX에서 실제 배정된 205개 특성의
  영/한 이름과 일반/강화 설명을 추출했다. Omniscience는 기존 확정 정의 유지.
  효과 정의는 registry.json과 사용자 규칙이 우선하고 XLSX는 표시 문구 자료다.
  원본 320개 + 확인된 암컷 대응 226개 = 일반형 프로필 546개, 표 크기 3276바이트.
- phase3_strings.py / data/phase3_strings.json: 배정 대상만 문자열 생성.
  새 일반/강화 이름/설명은 index19800부터 종류마다 4개다.
  기존 슬롯은 phase2 legacy_import로 선택된 특성만 업데이트한다.
  내부 phase3 적용기와 한국어 exact-match 파이프라인에 연결했다.
  기존 175개 ID의 이름/설명 350개 + 확장 슬롯 824개 = 1174개다.
  XLSX의 이전 문구보다 사용자의 쾌청/설경, 숫자 스피드,
  부스트에너지 제외 규칙을 우선하는 presentation()을 적용한다.
- runtime/phase3.c: 공통 프로필 조회/계산/층/턴/피격/처치/상태 서비스 초안.
  phase1.c/phase2.c에서 ME_PHASE3 조건부로 연결한다.
  일반형 초기 프로필은 원래 종(m+4)로 조회하고 기존 두 바이트는 호환 ID만 투영한다.
  특성 은행은 phase3에서 별도 heap 소유 메모리로 바꿔 코드 동굴을 절약한다.
  DungeonFree의 기존 Spinda 해제를 먼저 실행하고 두 소유 heap을 해제한다.
  할당 실패 시 행동·특성 조회·ResetMonster가 null을 역참조하지 않는다.
- runtime/phase3_hooks.S: 실제 사건 연결용 ARM 래퍼 초안.
  기존 UseMove/CalcDamage/MoveType/Faint/DungeonFree의 기존 패치 진입점을 보존한다.
  피해 계산 끝의 이동 ID는 원래 sp+0xf4이며 래퍼 sp+0x124로 읽는다.
  ApplyDamage의 HP 반영 이후 0x02309a28 호출 경계에서 피격 이벤트를 연결하는 방식.
  Native frame은 push40+sub0x64, damage source는 원래 sp+0x90이다.
  내부 phase3 적용기에 훅을 설치하고 실제 ARM 인자/스택 경로를 검증했다.
  기존 balance 피해 tail 전체를 보존한 뒤 새 보정을 연결하며,
  Punk Rock 방어만 4/5에서 1/2로 바꾼다. 별도의 aura 4/5는 보존한다.
- patch_engine/mega_evolve_phase3_runtime.py: 함수/데이터 단위 분산 링커 초안.
  기존 최대 빈 구간을 찾고 예약/참조된 16바이트 블록을 제외한 뒤
  ELF32의 ALLOC 섹션을 맞춰 넣는다. 새 코드 주소는 고정하지 않는다.
  현재 입력에서 8400+16704=25104바이트를 확보하고 링크 자체는 통과한다.
  예전 적용기/검증기와 연결했다. 각 동굴 해시, BSS 구간 및 MD 파일 해시를 기록한다.
  페이즈 1·2의 단일 동굴 hash 형식도 보존한다.

## 이번 연결 및 검증

- verify_phase3.py는 public phase3 gate를 우회하는 내부 테스트다.
  실제 NDS/세이브를 생성하지 않고 메모리 ROM에서 테스트한다.
- 546개 일반형 모두 실제 ARM bank 조회로 16비트 두 특성을 확인했다.
  원래 두 바이트에는 legacy_effect_id만 투영하며 없는 효과는 0이다.
  배정 외 MD 개체·스토리 1137·사용 중 문자열 슬롯은 보존한다.
- 스킨은 GetMoveTypeForMonster의 해석된 노말 타입만 변환한다.
  특성 슬롯 순서가 우선이고 행동 토큰·기술 ID·실제 타입이 같을 때만 1.2배다.
  웨더볼·다른 기술·중첩 행동에 보정이 새지 않는지 검사한다.
- status_hooks.py에 12개 상태 부여 함수 ABI를 고정했다.
  절대안깸의 7개 면역, 스위트베일의 수면/하품,
  아로마베일의 헤롱헤롱/도발/앵콜/기술 봉인을 연결했다.
  봉인은 TrySealMove이며 Muzzled가 아니다. 허용 시 원래 처리로 이어진다.
- 불굴의마음·속보·전기엔진은 기존 사건/메시지/조건을 보존하고
  이동속도 API 호출만 숫자 스피드 변경으로 교체했다.
- 철가시/컬리헤어의 피격 ledger 및 치명타격 경계를 검사했다.
  고정 피해 래퍼는 실제 ARM을 실행해 스택 인자 7개를 확인한다.
  문서에 생략된 응답 flag 두 개도 0으로 명시하여 재귀 접촉 반응을 막는다.
- 전기로바꾸기는 계산에서 충전을 소모하지 않는다. 실제 HP 감소 시 소비하며
  같은 행동의 다른 대상/다단히트에는 보정을 유지한다.
- data/phase3_coverage.json은 206개 모두 normal 구현/감사 상태와 검증 경로를 기록한다.
  native ID가 있다는 이유로 일반 효과가 완성됐다고 표시하지 않는다.
  강화 기능의 개별 활성화는 여전히 페이즈 7이다.

## 우선 해결할 사항

1. public load_registry의 phase3 허용과 manifest 전환은 전체 일반 효과 감사 후 한다.
   현재 내부 연결 테스트 통과는 페이즈 3 전체 완료와 다르다.
2. 피해 타입은 damage_data+0xc, 분류는 +0xd다.
   하네스는 BSS section 범위만 초기화한다. Native 계산 전체 및 실제 게임
   사건 조합 검증은 개별 효과 감사와 함께 추가한다.
4. 새 피격 효과와 옛 Rough Skin/Gooey/Stamina/Berserk/charge/moxie/soul-heart
   처리가 중복되지 않도록 기존 소비자를 조사하여 교체한다.
   스피드 날씨/곡예의 옛 이동·행동 반복 효과도 숫자 스피드로 완전히 이관한다.
5. 현 common service는 일부 초안이다. 모든 206개 일반 효과의 실제 경로와
   수치를 감사하고 각 효과의 normal 구현/검증 상태를 명시적으로 기록한다.
   특히 도주, 부자유친, 무아지경, 잠복, 굳건한신념, 바람타기, 떠도는영혼,
   화학의힘, 픽업/열매 유지, 무게/함정/강제 이동, 잠듦 판정 등의 연결이 남아 있다.
   고대활성의 새 햇살 적용 경계, 일반형 상태/계산 수치의 기존 코드 감사,
   절대안깸의 가상 수면 및 휴식 직접 쓰기, 개별 부가효과 면역도 남아 있다.
   이 목록은 완전한 미완 목록이 아니며 native 대응만으로 구현 완료로 인증하지 않는다.
6. 강화 설명/설계도 함께 조사하되 개별 강화 효과 활성화는 페이즈 7이다.
7. source reconciliation, phase1/2/3 ARM, 문자열/한국어 exact match,
   바이트/동굴/ID/상태/행동/원본 해시 검증을 수행한 뒤 커밋·푸시한다.

## 확인된 ROM 정보

기존 영문 풀스택 131253536바이트, 헤더 카드 용량128MiB.
monster.bin / m_attack.bin / m_ground.bin은 각819개 리소스 엔트리다.
기존 비어 있지 않은 엔트리 평균 크기는 각9584 / 13163 / 43828바이트다.
스프라이트 신규 엔트리와 MD 신규 종 ID 수는 동일하다고 가정하지 않는다.
GetMoveName은 index8173+move ID를 조회한다.
확인된 ID: Struggle352, regular attack355, Judgement467,
Nightmare5, Tailwind444, Grass Knot458, Low Kick92, Z-Move559.

외부 원본 XLSX/CSV/SpriteCollab는 읽기만 했다. 원본 XLSX는 Git에 넣지 않는다.
