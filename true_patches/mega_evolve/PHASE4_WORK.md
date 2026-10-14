# 페이즈 4 — 형태 데이터와 저장 완료

페이즈4 완료 당시 manifest는 phase4/version7이었다. 신규 형태 데이터, 종족값·특성 조회,
이름·기술·초상화·기존 이미지 조회, 일반 저장과 던전 중간 저장을 연결했다.
입력 ROM을 메모리에서만 적용·검증했다. NDS·세이브·풀스택 출력은 만들지 않았다.
실제 기기와 전체 게임 흐름 검증은 페이즈8이다.

## 형태와 영구 프로필

- data/phase4_forms.json: 기존1155 이후 ID1155..2268, 신규1114행, 총2269행.
  326개 대상 분기와 성별 대응을 펼친557쌍이다.
- origin/parent/mega/shiny/stage를 명시한다. 이로치 → 같은 분기 메가 →
  해당 원본이다. 기존 원시·오리진·대체·스토리 개체를 자동 변환하지 않는다.
- 기존 MD1155행은 페이즈3 특성 배정을 유지하고 새 행만 복제한다.
  공식 형태 타입만 변경하고 비공식 형태는 입력 MD 타입을 유지한다.
  복제된 native 진화 조건은 끄며 샘의 별도 진화 경로는 페이즈6이다.
- MD 뒤 MEF4/version1/first1155/count1114 헤더와 행당32바이트를 붙인다.
  행은 species/origin/parent/mega/shiny/stage, uint16 종족값6개,
  특성3개와grade다. 종족값277도 잘리지 않는다.
- MD 로더02052358은 전체 파일을 읽고020B09B4에 file+8을 둔다.
  새 조회는 MD count와 trailer를 검증한다. 기존 MD 필드를 전용하지 않는다.
- original ID(monster+2)로 영구 특성3개를 복원한다. 메가grade0,
  이로치grade1이다. apparent ID(+4), 일시 특성 교환과 타입 변경은
  영구 종과 프로필을 덮어쓰지 않는다.
- base_stats_speed의 동적 CalcStat/EvoRate 루트를 연결한다. 새 형태는
  uint16 종족값과 진화배율1.0, 기존 형태는 원래 native 몸체를 사용한다.
  마을/요약도 이 공통 루트를 사용하며 별도 ARM9 계산 복사본은 없다.

## 이름·기술·초상화와 이미지 캐시

포켓몬 이름은 origin의 기존 이름을 그대로 쓴다. 새 이름 문자열을 만들지 않는다.
resident ARM9 조회는 던전 heap runtime의 로딩에 의존하지 않는다.

- 이름의 %600 호출5개, 분류·성장·리소스 관련 ARM9/ov10/ov29 조회는
  explicit origin으로 연결한다. 신규 ID%600으로 다른 종을 읽지 않는다.
- 기술 목록 getter02013884/38F4/3940의 단회600 감산 전에 origin을 연결한다.
- 초상화 LoadPortrait0204D8CC는 조회할 때만 origin을 쓴다.
- IsMonsterValid0205476C는 검증된 trailer의 새 종을 인정한다.
  GetBaseForm은 신규 영구 ID를 그대로 유지한다.
- 기존 dungeon sprite cache는1155슬롯이다. getter022F7388,
  load022F74E0, store022F7414, delete022F7770, swap022F75D4를 기존
  이미지의 소유 ID로 연결한다. 영구 종 ID는 바꾸지 않는다.
  같은 이미지를 공유하는 형태끼리의 swap은 자신의 캐시를 지우지 않는다.
- 신규 메가/아우라/shiny 이미지와 서로 다른 이미지용 캐시 확장은 페이즈5다.

## 일반 저장: 12비트

555개 길드 동료와 도장 교환4개, 총559레코드의 종 ID만12비트로 바꾼다.
종 수와 동료 슬롯 수는 별개이며 ID0..4095를 표현한다.

- monster stream202510비트/25314바이트 →203069비트/25384바이트.
  증가559비트/70바이트는 기존 예약0x7F6B(32619)바이트 안에 들어간다.
- 상대0x7F58에 uint32 네 개: ME12(0x3231454D), 버전1, 폭12, 레코드559.
  main의 구간 시작0x464, 표시 위치0x83BC다. 표시도 native 체크섬에 포함한다.
- 표시 없음은 기존11비트로 읽고 미지원 버전·폭·개수는 읽기 전에 거부한다.
- write02059118/read02059224의 roster 진입에서만 폭을 바꾸고 반환 시
  복원한다. ID codec BL02059364/0205948C만 연결한다.
  읽기는 기존 EVS1 reader를 체인하며 나머지 native 필드 순서를 유지한다.
- EVS1 main0xB65C, tail0xB700..0xC644, 슬롯 페이지0/200,
  체크섬·도핑 V·진화 이력을 유지한다.
- stock quicksave original/apparent 종 ID는 각각16비트다. ov30의 실제
  byte codec 명령과 폭을 guard하며 이 ID 경로를 다시 압축하지 않는다.

ARM9 resident 코드 두 개는 EVS1의 실제 trampoline을 찾아 동적으로 배치한다.
마지막 trampoline 끝+0x888부터 codec 시작+0x1000 사이의 확인된 미사용
padding만 명시적으로 공유한다. 종 codec640바이트, 형태 소비자1024바이트가
서로 겹치지 않게 예약된다. EVS1 실행 코드·상태·버퍼·캐시는 제외하며
다른 모듈 예약과 직접 xref도 검사한다. 새 ov36 할당은 보호 prefix와
team_push 구간을 침범하지 않는다.

## 중간 저장: MEK4 자동 복원

stock main의 page400/0x5800바이트와 native 체크섬은 그대로 둔다.
미사용 flash tail page488(0x1E800)에 MEK4/version1/0x1400바이트를 기록하며
끝0x1FC00 이후0x400바이트도 보존한다. 일반 저장 슬롯과 EVS1 tail은
이 영역에 닿지 않는다.

- ARM9 quicksave write BL02049264/read BL02049644를 연결한다.
  기존 EVS1/native wrapper를 먼저 호출한다.
- header는 main 전체의 FNV 해시와 sidecar 체크섬을 포함한다.
  표시 없는 기존 중간 저장은 native 방식으로 읽고 표시 있는 손상·불일치는 거부한다.
- 1024바이트 상태 컴포넌트는 스피드 저장단계, 날씨 강도·발생원·순서를 보존한다.
- 슬롯+original 종으로20개 actor를 대응한다. 특성3개의 영구/현재 값과
  층 입장 발동 상태를 복원한다. 포인터는 기록하지 않는다.
- 층 입장 전에 actor 상태를 복원하여 슬로스타트 등의 중복 발동을 막고,
  actor 생성 후 첫 턴 앞에서 전체 상태와 발동 serial을 복원한다.
  이전 행동 토큰은 새 행동 장부에 연결하지 않는다.
- 일반 저장은 형태 ID로 영구 프로필을 재구성한다. 층 내부 상태는 중간 저장에서만 유지한다.

## 검증 결과와 경계

- verify_phase4_forms:1114행의 성별·분기·부모·타입·특성3슬롯,
  행당24개 레벨/도핑 경계 계산, 실제 CalcStat/EvoRate 루트와 기존 종
  continuation, 이름·기술·초상화·validity·캐시 native 소비자 실행.
  팀/도장 halfword 복사와 캐시 뒤 canary, 동일 이미지 swap도 확인했다.
- verify_phase4_public: 공개 dispatcher apply/verify, 실제 EVS1 부모 예약과
  padding 공유, JSON record 왕복, 기존 이름/MD 보존과 drift 거부.
  ROM 직렬화는 메모리에서만 수행했다.
- verify_save12:559개 실제 native roster/record/bit codec 왕복,
  ID0/1154/1155/2047/2048/2268/4095, 기존11비트 읽기,
  ABI·폭 복원·미지원 형식 거부·이웃 영역 canary·EVS1 이중 슬롯 체크섬.
  native 중간 저장의 서로 다른 original/apparent16비트 ID도 보존했다.
- verify_phase4_quick: 실제 native main/checksum wrapper와 자동 sidecar,
  cold runtime 재생성 후 스피드·강한 날씨·영구/임시 특성3개 복원,
  층 입장 효과 중복 방지, 기존 저장 읽기·손상 거부·flash 경계 보존.
- 페이즈3 회귀39개 결과도 모두 통과 상태다. 최종 수정에 해당하는 공개
  게이트/기반 검증은 다시 실행했으며 나머지 효과별 기존 통과 결과는 유지했다.

외부 flash I/O·할당·일부 native 서비스는 RAM 모델이다. 실제 기기 RAM 부하,
전체 던전 재개·전투 화면 검증은 페이즈8이다. 페이즈4 완료는 새 그림,
샘 진화 메뉴, 개별 강화 효과 구현까지 완료했다는 의미가 아니다.
