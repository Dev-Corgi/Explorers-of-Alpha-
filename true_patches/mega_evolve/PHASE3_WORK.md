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
- patch_engine/mega_evolve_loader.py / runtime/loader.c: 별도 실행 파일 로더.
  기존 25104바이트 분산 배치는 폐기했다. 특성 배정표는 16비트 원래 형식이며
  ID 상대값 압축과 섹션 정렬 여백 축소로 공간을 확보하지 않는다.
  `/MEGA/runtime.bin`에 비압축 코드·데이터·초기 BSS·재배치 표를 저장한다.
  기존 FAT ID와 오버레이 RAM 크기는 바꾸지 않고 새 파일/디렉터리만 끝에 추가한다.
  ov36에는 동적으로 검증/예약한 8192바이트 bootstrap만 둔다.
  첫 호출 시 LoadFileFromRom(0x02008c3c, flags=0)의 기본 heap 할당을 사용한다.
  실제 코드 RAM 주소는 할당 결과로 결정되고, 내부 ABS32만 재배치한다.
  내부 ARM branch/REL32는 위치 독립이며 외부 상대 branch/미지원 재배치는 거부한다.
  컴파일러가 만든 section 밖의 biased anchor도 원래 addend를 보존한다.
  외부 native 호출은 절대 주소 ldr/blx이고 기존 훅 소유자를 보존한다.
  모든 연결 코드는 r0–r12/LR, CPSR flags, 원래 SP/stack 인자를 복원한다.
  로딩 후 D-cache clean/write-buffer drain/I-cache invalidate/prefetch flush한다.
  DungeonFree payload가 기존 해제와 효과 heap 해제를 마치고 bootstrap으로 돌아오면
  코드 파일 heap까지 해제한다. 다음 호출에서는 새 주소로 다시 로드한다.
  실행 이미지 빌드 상한은 256KiB이며 현재 약 25KiB다. 상한은 RAM 확보 보장이 아니다.
  파일·재배치 메타데이터 검증 실패나 IRQ/FIQ/reentry는 fault 번호 기록 후 중단한다.
  native allocator는 부족할 때 null을 반환하지 않고 중단할 수 있으므로,
  실제 던전 최대 부하의 heap 여유/파일 IO/캐시 동작은 ROM 실행 검증이 남아 있다.
  verify_loader.py는 실제 ARM loader/연결 코드를 실행하고 파일 IO/할당은 모델링한다.
  최초/반복 호출·모든 입력 레지스터/flags/stack·재배치·해제/새 주소 재로딩·변조 거부를 검증한다.
  효과 테스트는 별도 heap image를 재배치해 실행하며 bootstrap도 통과한다.
  파일 SHA256, BSS 상대 구간, bootstrap 동굴 hash, MD hash를 기록한다.
  페이즈 1·2의 기존 단일 동굴 형식과 public phase2 gate는 유지한다.

## 코드 확장 전 작성된 미커밋 효과 초안

아래 초안은 코드 확장 요청 전에 작성되어 있었으며 확장 작업 동안 새 특성을 추가하지 않았다.
전체 특성 인증과 phase3 활성화는 여전히 미완료다.

- 화학의힘: 같은 방/같은 편의 동료 기절을 행동별 queue에 기록한다.
  Chebyshev 거리와 entity 슬롯으로 가까운 동료를 정하고 행동 종료 시 한 슬롯만 임시 복사한다.
  최고 등급 중복 제거, 보호 특성/Receiver 제외, 중첩 행동/개체 재사용/복원 처리와 ARM 검증이 있다.
- 잠복: 실제 ExecuteMonsterAction의 성공한 걷기만 이동 epoch로 기록한다.
  다음 행동 시작 시 해제하며 첫 유효 피격에서 해당 보유자/대상 epoch를 소비한다.
  계산/빗나감/막힌 걷기/워프는 소비하거나 새 창을 만들지 않는다.
- 도주: 적의 유효 피격 후 HP 1/4 이하에서 층당 한 번 안전한 타일로 이동한다.
  가까운 동료 주변을 먼저 찾고 불가하면 안전한 바닥을 찾는다.
  벽/계단/도구/함정/점유 타일, 치명타로 기절/아군/억제/이동 실패를 제외한다.
  기존 ID43의 도주 AI 조회 세 곳만 억제한다. 일반 특성 복사/조회는 유지한다.
  월드 외부 이동 함수/타일 서비스를 모델링한 ARM 검증이며 실기 인증은 아니다.

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

### 두 번째 진행분

- verify_phase3_actions.py는 실제 ARM의 무아지경·떠도는영혼·굳건한신념 경로를 검사한다.
- 무아지경의 물리 공격 계산값 1.5배는 BaseStats_FromMonster 결과에 적용해
  피해 최종 배율로 근사하지 않는다. 특수공격·방어에는 적용하지 않으며 천진과 틀깨기를 따른다.
  CalcDamage 문맥은 중첩 actor/target 스택으로 관리하고 해제 시 원래 문맥으로 돌아간다.
- 첫 HP 감소를 일으킨 공격 기술을 층 단위로 잠근다. 일반 공격355와 발버둥352는
  잠금 대상을 만들지 않는다. CanMonsterUseMove에서 같은 기술만 허용하며,
  잠긴 기술의 PP가 없으면 일반 공격·발버둥만 허용한다. 발버둥은 PP 검사만 생략하고
  기존 봉인/비활성 검사를 보존한다. 봉인된 무아지경은 잠금을 적용하지 않는다.
  Monster move 배열은 +0x124, 각 슬롯 ID+4/PP+6이다.
- 떠도는영혼은 피격 부가효과 처리 마지막에 슬롯 하나만 교환한다.
  자신의 떠도는영혼 슬롯과 공격자의 유효한 특성 하나를 교환하고 등급도 함께 이동한다.
  같은 특성 중복은 균등 후보에 한 번만 포함하고 높은 등급의 슬롯을 선택한다.
  영구 프로필은 변경하지 않으며 한 행동당 한 번만 교환한다.
  기존 ROM ID의 형태 전용/변경 면역 목록도 검사해 미배정 native 특성을 보호한다.
- 층 이동 시 임시 byte 투영을 원래 permanent의 호환 ID로 되돌린 뒤 은행을 비운다.
  일반형 배정표에 없는 야생 포켓몬이 임시 교환 특성을 다음 층에서 다시 읽는 문제를 막는다.
  이전 층의 entity/monster/species와 지금 개체가 모두 일치할 때만 복원한다.
- 굳건한신념은 ExecuteMoveEffect의 +0x0232e9c0에서 날따름·피뢰침·마중물의
  대상 변경 구간을 건너뛰고 +0x0232eaac의 기존 효과 처리로 이어진다.
  대상 자체의 타입·특성 면역은 제거하지 않는다. 스택/레지스터와 이전 패치 진입점도 보존한다.

1. public load_registry의 phase3 허용과 manifest 전환은 전체 일반 효과 감사 후 한다.
   현재 내부 연결 테스트 통과는 페이즈 3 전체 완료와 다르다.

### 세 번째 진행분 — 페이즈 4로 넘어가지 않음

- 사용자 요청에 따라 페이즈 4는 읽기 조사만 한 뒤 중단했다. 형태/저장 데이터 변경은 없다.
- 라이트메탈은 TryTriggerTrap의 기존 회피/IQ 검사 이후 +0x022ee1d8 경계에 연결한다.
  성공하면 기존 종료 경로 +0x022ee2f4로 이어지며 함정을 제거하지 않는다.
  실패하면 기존 위치 인자를 복구해 +0x022ee1dc로 이어진다.
  r2에서 들어온 native 강제 발동 flag(r11)가 있으면 특성 난수 판정도 하지 않는다.
  직접 ApplyTrapEffect를 호출하는 도구 경로는 수정하지 않는다.
- 헤비메탈은 TryBlowAway의 native entry +0x0231fde0에 연결한다.
  DefenderAbilityIsActive를 사용해 특성 억제와 틀깨기를 따르며,
  차단하지 않으면 원래 push{r3-r11,lr} 및 actor/target/direction 인자를 보존한다.
- verify_phase3_world.py는 실제 ARM 경계 래퍼와 모형화한 native continuation으로
  50% 인자·성공/실패·강제 발동 제외·직접 함정 함수 보존·억제·틀깨기·ABI를 검사한다.
  이 검증은 모든 함정/도구·강제 이동의 완성이나 무게 계산의 완료를 인증하지 않는다.
- GetWeightMultiplier(ARM9 +0x020528fc)는 MD 무게 값을 고정소수 피해 계수로 반환하며,
  Low Kick/Grass Knot 공통 DoMoveDamageWeightDependent는 +0x023277b8이다.
  실제 무게 값과 기술 계수의 의미를 확인한 뒤 연결해야 하므로 무게 구현은 미완으로 둔다.
2. 피해 타입은 damage_data+0xc, 분류는 +0xd다.
   하네스는 BSS section 범위만 초기화한다. Native 계산 전체 및 실제 게임
   사건 조합 검증은 개별 효과 감사와 함께 추가한다.
4. 새 피격 효과와 옛 Rough Skin/Gooey/Stamina/Berserk/charge/moxie/soul-heart
   처리가 중복되지 않도록 기존 소비자를 조사하여 교체한다.
   스피드 날씨/곡예의 옛 이동·행동 반복 효과도 숫자 스피드로 완전히 이관한다.
5. 현 common service는 일부 초안이다. 모든 206개 일반 효과의 실제 경로와
   수치를 감사하고 각 효과의 normal 구현/검증 상태를 명시적으로 기록한다.
   특히 도주, 부자유친, 잠복, 바람타기,
   화학의힘, 픽업/열매 유지, 무게/함정/강제 이동, 잠듦 판정 등의 연결이 남아 있다.
   고대활성의 새 햇살 적용 경계, 일반형 상태/계산 수치의 기존 코드 감사,
   절대안깸의 가상 수면 및 휴식 직접 쓰기, 개별 부가효과 면역도 남아 있다.
   이 목록은 완전한 미완 목록이 아니며 native 대응만으로 구현 완료로 인증하지 않는다.
6. 강화 설명/설계도 함께 조사하되 개별 강화 효과 활성화는 페이즈 7이다.
7. source reconciliation, phase1/2/3 ARM, 문자열/한국어 exact match,
   바이트/동굴/ID/상태/행동/원본 해시 검증을 수행한 뒤 커밋·푸시한다.

## 네 번째 진행분 — 아이템과 수면

- phase3_items.py/data/phase3_items.json에 실제 item_p.bin과 영어 이름을 대조한
  열매 8종 및 픽업 씨앗·열매 31종을 보관한다. item category2에는 약/회복약/비늘도
  있어 category만으로 구현하지 않는다. 부활73·행복89·황금93 씨앗은 제외한다.
  적용 전 살아 있는 ROM의 아이템 ID/이름/분류/유효성 목록이 일치하는지도 검사한다.
- 수확은 열매 소비에서 일반 날씨12%, 햇살25%, 되새김질은20%로 남긴다.
  둘을 함께 보유하면 되새김질 판정 후 실패했을 때 수확을 판정한다.
  같은 특성의 중복 슬롯은 확률을 추가하지 않는다. 소비자의 특성 억제를 따른다.
  UseSingleUseItem +0x022f53c0의 RemoveUsedItem 호출만 감싸며 실제 소비자는 r8이다.
  native stack+8의 복사된 item 구조(6byte)를 사용한다. 일반 삭제는 원래 사용자,
  action parameter와 기존 RemoveUsedItem/COT 후처리를 그대로 호출한다.
  아이템 효과는 기존 복사본으로 계속 처리된다. 투척/그 외 소비 경로의 연결은 미완이다.
- 픽업은 층 입장 ledger에서 한 번, 플레이어 팀원에만 동작한다.
  가방 공간이 있을 때 50% 판정 후31개 후보를 균등 선택해 깨끗한1개를 가방에 넣는다.
  빈 공간 없음/야생/억제 시 난수 및 아이템 생성도 하지 않는다.
  원래 +0x022fd69c..0x022fd760의 두 ability byte를 직접 읽는 픽업 블록은
  SHA-256으로 가드한 뒤 건너뛰어 기존 손에 쥐여주는 획득과 중복하지 않는다.
- 절대안깸은 꿈먹기 +0x0232bcf0의 수면 대상 검사만 별도 조회로 교체한다.
  IsMonsterSleeping +0x023007a8 자체는 보존해 가상 수면 때문에 행동이 막히지 않는다.
  Rest의 Napping +0x02311d60 기존 COT 진입점을 보존하며 수면 부여를 차단한다.
  실제 플레이어/야생 Rest 실행에서 HP 및 sleep byte가 변하지 않는지 검사했다.
  스위트베일도 Napping 수면 부여를 막는다. 기타 잠든 대상 검사 기술은 감사가 남아 있다.
- verify_phase3_items.py/verify_phase3_sleep.py는 위 경로와 native ABI,
  후보 제외·가방 공간·팀원·층당1회·억제·중복·기존 코드 가드를 실제 ARM으로 검사한다.
  모든 아이템 효과/수면 소비자 또는 전체 페이즈3의 완료를 인증하지 않는다.

## 확인된 ROM 정보

기존 영문 풀스택 131253536바이트, 헤더 카드 용량128MiB.
monster.bin / m_attack.bin / m_ground.bin은 각819개 리소스 엔트리다.
기존 비어 있지 않은 엔트리 평균 크기는 각9584 / 13163 / 43828바이트다.
스프라이트 신규 엔트리와 MD 신규 종 ID 수는 동일하다고 가정하지 않는다.
GetMoveName은 index8173+move ID를 조회한다.
확인된 ID: Struggle352, regular attack355, Judgement467,
Nightmare5, Tailwind444, Grass Knot458, Low Kick92, Z-Move559.

외부 원본 XLSX/CSV/SpriteCollab는 읽기만 했다. 원본 XLSX는 Git에 넣지 않는다.
