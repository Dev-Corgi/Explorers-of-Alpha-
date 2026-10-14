# 페이즈 5 — 스프라이트 연결

사용자의 후속 지시에 따라 기존 보류32개를 해결했다. 일반 진화체4개 성별 ID를
추가하여 총2273개 종 ID가 되며, 추가1118개 항목 모두586개 고유 이미지
패키지에 연결한다. 상세 출처와 해시는 data/phase5_assets.json 및
data/phase5_repairs.json에 있다. 처리 결과는 [PHASE5_MISSING.md](PHASE5_MISSING.md)다.

## 선택과 변환

- 공식 메가·원시·오리진의 실제 AnimData.xml이 있으면 그 스프라이트를 쓴다.
  공식 그림이 없는 메가 분기는 기본형의 일반/이로치 아우라를 쓴다.
- 공식 그림이 있는 분기의 이로치는 해당 공식 형태의 Shiny 아우라를 요구한다.
  regional 형태는 같은 지역의 아우라를 선택한다. 있는 공식 암컷 그림은 구분한다.
- source SpriteCollab 및 output/sprite-normalized를 읽기만 한다. 사용자 아우라
  생성 도구를 수정하지 않는다. 승인된 생성물은 모듈 .cache/phase5_fix에 둔다.
  노고고치·신비록은 새 이름·초상화·기술목록·타입·종족값을 가진 일반 진화체다.
  기존 성별 메가 ID는 유지하며 두 진화체 기준으로 이름/자원/종족값을 연결한다.
  두 일반 진화체는 특성1·2를 진화 전과 공유하고, 메가에서만 특성3을 추가한다.
  메가 종족값은 각 능력치의 기존 메가/기본 비율을 새 기본 종족값에 적용해
  정수 반올림한다. 종족값·지원 기술의 원출처는 PokeAPI 공식 CSV의 해시로 기록했다.
- CharaWanHandler로 XML/시트/offset/shadow를 읽고 native16색 팔레트로 변환한다.
  16색을 넘는 패키지는 SkyTemple의 팔레트 매핑을 쓴다. 원본 PNG는 바꾸지 않는다.
  프레임·방향·타이밍을 줄이지 않는다. 동일 packed pixel 조각만 공유한다.
- 기존819개 항목 뒤에 monster/m_attack/m_ground를 같은 새 인덱스로 붙인다.
  기존 파일 항목을 덮어쓰지 않는다. 포켓몬 종 ID와 이미지 인덱스는 별개다.
- .cache/phase5는 재생성 가능한 로컬 WAN 캐시이며 Git 제외다. 출처·변환 해시가
  고정된 JSON을 커밋하고 캐시가 없으면 적용 시 재생성하여 해시를 대조한다.
  전체 변환은 phase5_convert, 실패한 항목만 재개는 --retry-failed다.
  생성 아우라가 없으면 numpy/scipy가 있는 Python으로 phase5_repair를 실행한다.
  같은 프레임의 공식 일반/이로치 색상을 우선 사용한다. 무장조·다크라이 메가의
  공식 참조가 같은 색상인 경우 허용받은 임의 팔레트를 적용하고 출처를 구분한다.
  이중 타입 아우라의16색 한도 때문에 필요한 경우 가장 가까운 몸체 색상만
  캐시 복사본에서 합쳐 아우라 색상2개를 확보한다. 원본 시트는 바꾸지 않는다.

## 길이·캐시·자원 로딩

아우라의 큰 애니메이션을 기존 PKDPX의 압축 길이16비트와 MD 파일 크기8비트에
잘라 넣지 않는다. MEW5 패키지는 magic/raw size/chunk count 뒤에 크기와
PKDPX 블록을 기록한다. 블록의 원본 크기는 최대32768바이트이며 native
디코더로 순서대로 복원한다. 실행 코드는 기존 비압축 heap runtime을 유지한다.

- MD의 MEF4 뒤에 MEP5/version1/first/count 및 형태당8바이트 크기 자료를 붙인다.
  타일 슬롯과 monster WAN 실제 바이트 수를 기록한다. native 파일 크기 getter는
  새 형태에 이 uint32 값을 반환하고 이전 형태는 원래 MD byte getter로 간다.
- 기존 dungeon+0x19914의1155슬롯은 유지한다. 추가1118슬롯은 heap BSS다.
  같은 sprite_index는 한 소유 ID로 공유하며 대응은 MD별로 캐시한다.
  조회·로드·저장·삭제·swap과 전체 삭제 loop를 연결한다.
- native pack-name table020AF6A0의 순서는 monster/m_attack/m_ground다.
  새 파일 인덱스에만 별도 로딩을 사용하며 다른 archive와 기존 그림은 원래 경로다.
- 큰 파일은 기존 공용 scratch나 호출자의 기존 크기 버퍼에 복사하지 않는다.
  임시 packed buffer와 원본 크기의 buffer를 할당하고 디코딩 후 임시 buffer를 해제한다.
  원래 buffer 제공 경로도 새 그림에서는 별도 소유 buffer로 바꾼다.
- 이미지 교체는 기존 WAN cache index를 유지하면서 충분한 새 buffer를 먼저 확보한다.
  성공한 뒤 기존 소유 buffer를 해제한다. 빌린 buffer는 해제하지 않는다.
  할당 실패 시 기존 자원과 cache identity를 보존한다.
- resident ARM9 코드는 EVS1의 검증된 미사용 padding 안에서 동적으로 배치한다.
  페이즈5 형태/디코더/자원 gate 예약은1264바이트이며 기존 종 codec640바이트와
  겹치지 않는다. 실행 body는 기존8KiB ov36 bootstrap을 통해 heap에서 실행한다.
  큰 이미지의 chunk decoder도 heap body에 두며 ARM9에는 판별 gate를 둔다.
  기존 종의 이름·기술목록·초상화는 heap 호출 없이 기존 resident 경로로 처리한다.
- 자원 하나의 원본 크기는 최대2MiB다. 실제 최대 RAM 부하·여러 큰 이미지의
  동시 로딩은 페이즈8 검증 대상이다. 기기 실행을 통과한 것으로 간주하지 않는다.

## 검증과 용량

verify_phase5_runtime은 실제 ARM chunk decoder/크기 조회/SIR0 초기화를 실행한다.
픽셀 bytes와 output canary, 기존 cache 뒤 canary, 공유·삭제·교체·할당 실패,
공용/빌린 buffer 보존과 임시 buffer 해제를 검증한다. pack I/O·allocator·manager
slot 선택만 RAM 모델이다. 전체 패키지는 변환 시 native Rust 디코더와 WAN reader로
왕복하며 대표적인 일반 아우라·공식 메가·이로치 아우라의 WAN 렌더도 확인한다.

전체 애니메이션 용량에 대응하도록 card capacity 선택은128/256/512MiB다.
실제 크기로 선택하며 padding하거나 이미 선택한 용량을 줄이지 않는다.
512MiB 초과는 거부한다. ROM_CAPACITY.md와 검증 결과를 함께 확인한다.
ROM 직렬화 검증은 메모리에서만 수행하며 NDS·세이브·풀스택 출력은 만들지 않는다.

verify_new_species는 실제 레벨 판정 훅과 기존 개체 변환 코드를 실행하여
19/20/80/100레벨·양쪽 성별·진화 이력/경험치 보존을 확인한다. 로스터 I/O만
모델링한다. 기존2047개 초상화의 압축 데이터/팔레트, 기존553개 기술목록과
기술 효과를 보존하며 신규 자원 변조도 거부한다.

노고치→노고고치, 노라키→신비록의 레벨20 샘 진화는 이번에 연결했다.
메가·이로치 메가 샘 진화는 페이즈6에서 기존 진화 메뉴에 연결했다. phase5_evolution_routes.json은
기존 원시회귀·오리진을 이미 메가 단계로 취급하며 바로 해당 이로치로 각성시킨다.
기존 원시회귀 원점용 메가 복제 ID1917/1923은 호환 자료만 유지하고 추가
진화 선택지로 노출하지 않는다. 개별 강화 특성은 페이즈7, 기기 검증은 페이즈8이다.
