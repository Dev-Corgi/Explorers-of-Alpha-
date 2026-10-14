# 페이즈 4 — 형태 데이터와 저장

## 확정·구현한 저장 폭

사용자 요청에 따라 종 ID 저장 폭을 12비트로 확장한다. 일반 저장의 실제
555개 길드 동료 및 도장 교환 4개 레코드를 그대로 유지한다. 포켓몬 수와
길드 슬롯 수는 별개다. 물리 형태 ID 0..4095를 표현할 수 있다.

- 기존 monster stream: 202510비트, 25314바이트.
- 신규 monster stream: 203069비트, 25384바이트. 증가량 559비트, 70바이트.
- 기존 예약 구간 0x7F6B(32619)바이트를 늘리지 않는다.
- 구간 상대 0x7F58..0x7F68에 little-endian uint32 네 개를 기록한다:
  `0x3231454D`(ME12), 버전1, 폭12, 레코드559.
- main block에서 구간 시작은 0x464, 표시 위치는 0x83BC다. 원래 세이브의
  InitBitstream이 구간 전체를 0으로 지우므로 이전 형식은 표시가 없다.
- 표시 없음 → 11비트 읽기. 새 표시 → 12비트 읽기. 미지원 표시/버전/폭/개수는
  레코드를 읽기 전에 실패한다. 체크섬은 표시도 포함한다.
- ID 외 모든 native 필드 순서를 유지한다. 일반 진화 이력, 도핑 V를 재사용하지 않는다.
- EVS1 표시 main[0x35..0x37], main 0xB65C, tail 0xB700..0xC644,
  이중 슬롯 시작 페이지0/200과 기존 체크섬 처리는 그대로 유지한다.

`runtime/save12.c`는 resident ARM9 코드로 링크한다. dungeon heap runtime의
로딩 여부에 의존하지 않는다. 배치는 동적으로 찾고 빌드 상태에 예약을 남긴다.
직접 xref 검사 외 spinda_ev_speed가 기록한 live cache/상태 금지 구간을 공유한다.
ITCM 원본 구간 이후에는 새 코드를 배치하지 않는다.

쓰기 훅은 WriteMonsterInfoToSave의 native 프롤로그를 trampoline으로 유지한다.
읽기 훅은 기존 EvSave_ReadMonsters로 체인하여 영구/임시 V 복원을 보존한다.
두 종 ID BL만 공통 native bit codec의 폭을 선택하도록 바꾼다. 폭은 roster
호출 안에서만 바뀌며 반환 때 이전 상태로 복원된다. 다른 스트림은 11비트를 유지한다.

현재 공개 phase3/version6에는 이 저장 준비가 포함된다. 페이즈4 전체를
완료로 표시하거나 미완성 형태를 활성화하지 않는다.

## 주소·실행 검증

- ARM9 WriteMonsterInfoToSave 0x02059118, ReadMonsterInfoFromSave 0x02059224.
- 종 ID bit codec 호출: write 0x02059364, read 0x0205948C.
- 두 native bit codecs: 0x020509C0, 0x02050A40.
- 해당 개별 record 호출자는 각 roster loop 둘뿐임을 ARM9/전체 overlay에서 확인했다.
- overlay30 quicksave는 bit stream과 별개의 byte stream이다.
  apparent ID: write 0x0238330C..0x02383324, read 0x02384EDC..0x02384EF8.
  original ID: write 0x02383324..0x0238333C, read 0x02385138..0x0238514C.
  각각 2바이트이며 byte write/read 0x02385C54/0x02385CA4를 사용한다.
  이 경로는 변경하지 않고 적용·검증 때 폭과 byte codec 명령을 guard한다.

`python -B -X utf8 -m true_patches.mega_evolve.verify_save12`:

- 실제 native roster/record/bit 코드를 실행하여 559개 전부 왕복한다.
  경계 ID0/1154/1155/2047/2048/2268/4095를 포함한다.
- 기존11비트 버퍼를 새 reader로 읽는다. 새12비트 버퍼를 다시 읽고
  ID·능력치·이름·ABI·호출 뒤 폭 복원·미지원 버전 거부를 확인한다.
- 기존 EVS1 main write/read와 tail 체크섬을 실행한다. flash I/O만 메모리 모델이다.
  슬롯0/200 모두 새 형식 표시를 보존하며 main 손상은 native 체크섬에서 실패한다.
- 옆 저장 구간/도핑 tail canary를 침범하지 않는다.
- quicksave 두 ID의 실제 native 쓰기/읽기 조각과 byte codecs를 실행한다.
  영구 ID와 임시 외형 ID가 서로 달라도 높은 ID가 각각 보존된다.

검증은 기존 ROM을 읽어 메모리에서만 수행한다. NDS·세이브·풀스택 출력은 만들지 않는다.
실제 플래시 I/O·기기 RAM 부하·전체 던전 재개 과정은 페이즈8 통합 검증에 남는다.

## 페이즈 4에서 남은 작업

물리 MD ID와 성별/분기/단계 대응표, MD 복제와 uint16 종족값의 내부 연결은
아래 두 번째 진행분에서 구현했다. 이름/기술/초상화 조회와 생성·요약·팀 복사
소비자의 ID 범위 연결 및 공개 활성화가 남았다. 기존 스토리 개체는
신규 진화 프로필에 합치지 않는다. 스프라이트 변환은 페이즈5, 샘 진화는 페이즈6,
개별 강화 효과는 페이즈7이다. 저장 폭 확장만으로 이 작업들이 완료된 것은 아니다.

## 두 번째 진행분 — 신규 물리 대응표와 내부 런타임

- phase4_forms.json에 기존1155 이후1155..2268을 확정적으로 배정했다.
  326개 대상 분기와 성별 대응으로557쌍, 새 MD1114개다. 기존 원시/오리진/
  대체/스토리 ID를 신규 ID에 합치지 않는다. 각 origin은 자기 분기와 단계의
  별도 부모를 가진다. 이로치 → 해당 메가 → 해당 origin이다.
- mega_evolve_phase4_data.prepare는 기존 MD 바이트를 보존하고 신규 행을
  복제한다. 공식 타입만 바꾸고 비공식 타입은 실제 입력 MD에서 유지한다.
  sprite index는 현재 이용 가능한 기존 리소스를 가리킨다. 신규 에셋은 phase5다.
  복제 행의 기존 진화 조건은 비활성화하여 원래 전진화형의 후보에 메가가
  끼어들지 않게 한다. 샘의 level80/단계 진화는 phase6의 명시적 조회로 활성화한다.
- MD 끝에 MEF4/version1/first1155/count1114 헤더와32바이트 행을 붙인다.
  행은16개의 uint16: species/origin/parent/mega/shiny/stage, 6종족값,
  특성3개와grade다. 기존 MD 필드를 저장 공간으로 전용하지 않는다.
- 실제 MD 로더0x02052358은 파일 전체를 읽은 뒤020B09B4에 file+8을 저장한다.
  개별 native MD getter는 그 포인터와 ID×68로 행을 읽는다. 새 trailer 조회는
  MD 헤더 count와 trailer 헤더를 검증한 뒤에만 수행한다.
- 내부 phase4 runtime은 이 원래 MD ID(+2)로 세 영구 특성을 초기화한다.
  메가grade0, 이로치grade1이다. 임시 외형(+4)과 특성 교환은 영구 프로필을
  변경하지 않는다. 개별 강화 효과를 전부 구현한 것으로 간주하지 않는다.
- 기존 base_stats_speed의 동적 CalcStat/EvoRate 두 진입점은 신규 종의
  uint16 종족값/진화배율1.0을 조회하도록 연결했다. 기존 종은 원래 함수 몸체로
  인자·스택을 보존하여 돌아간다. 기존600종 표로 신규 ID를 보내지 않는다.
- verify_phase4_forms는1114개 전체에서 단계/부모/성별/타입/3슬롯 복원과
  종족값277을 확인했다. 각 행24개의 레벨·도핑 경계 사례를 실행하고,
  실제 CalcStat/EvoRate 진입점 및 원래 종의 native continuation도 실행한다.

아직 공개 phase4를 활성화하지 않는다. 내부 fixture에서만 새 MD를 사용한다.
town/요약의 별도 계산 복사본, 이름·기술·초상화의 기존 %600/+600 경로,
생성·팀 복사와 종 수 제한 소비자를 추가 연결해야 한다. 이 항목들이 완료되기
전에는 확장 MD를 실제 모듈 출력에 설치하지 않는다.
