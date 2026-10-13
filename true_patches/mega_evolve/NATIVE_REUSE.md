# 일반 효과 재사용 검증 기록

## 완료 기준과 공통 경계

기존 이름/ID 대응만으로 효과 완료를 선언하지 않는다. 기존 효과 유지 후보는
실제 소비자의 거부/계산/상태 쓰기 경로를 실행하고, 특성이 없는 대조 사례와
세 번째 슬롯·억제·위액·틀깨기를 같은 fixture에서 비교한다.
전체 전투 인증은 별도이며 각 경로의 검증 범위를 coverage에 명시한다.

`phase3_worklist.py`는 사용자와 정리한 작업 후보 분류를 고정한다.
효과 정의의 기존/변경 태그와 legacy 효과 ID, 불굴의마음·점착·픽업의
확인된 변경을 반영해 유지 후보92 / 수정·연결87 / 신규 처리27로 구분한다.
후보 분류는 구현 완료 판정이 아니다. 이후에는 효과표 전체를 재독하지 않고
이 목록과 `phase3_coverage.json`에서 해당 경로만 선택한다.

## 첫 묶음: 기존 상태 면역

공통 함수 DefenderAbilityIsActive의 상태 부여용 사본은 +0x02311b94다.
인자는 actor(r0), target(r1), legacy ability ID(r2), Mold Breaker 적용 flag(r3)다.
actor와 target이 다르고 flag가 켜지면 공격자의 ID83을 먼저 검사하고,
그다음 대상의 AbilityIsActiveVeneer(+0x02301d78)를 호출한다.
확장 특성 은행을 연결한 기존 공통 조회를 재사용하며 특성별 새 코드는 추가하지 않는다.

| 특성 | 실제 상태 부여 entry | 상태 byte | 부여 값 |
|---|---|---|---|
| 면역 | 0x02312664 / 0x0231293c | monster+0xbf | 독2 / 맹독3 |
| 수의베일 | 0x02312338 | monster+0xbf | 화상1 |
| 유연 | 0x02314544 | monster+0xbf | 마비4 |
| 마이페이스 | 0x02314f38 | monster+0xd0 | 혼란2 |
| 마그마의무장 | 0x02312bf8 | monster+0xc4 | 기존 동결 entry1 |
| 불면 / 의기양양 | 0x023118d8 | monster+0xbd | 수면1 |

`verify_phase3_native_status.py`는 기존 wrapper 하네스에서 모델링하던
STATUS_TARGET continuation을 실제로 실행한다. 각 경로마다 특성 없음,
slot1/2/3, 도구 억제, 위액, 공격자 틀깨기 총7조건을 비교한다(56사례).
막히면 원래 거부 경로가 반환하는지, 허용되면 실제 해당 byte 쓰기가
발생하는지를 검사한다. 쓰기를 발견한 시점에 실행을 멈추므로
그 뒤의 상태 반응/화면/애니메이션/추가 특성 효과는 인증하지 않는다.
다른 전역 방어, 정상 바닥 terrain, UI/이름 포맷/RNG/부수 서비스를 모델링한다.

주의: Poison/BadPoison의 r3은 check-only flag이며 0이어야 실제 부여된다.
Burn의 추가 stack check-only flag도0으로 둔다. Sleep은 r2가 지속시간이다.
이 계약을 다음 상태 묶음에서도 재사용하고 효과별 가정으로 다시 추측하지 않는다.

마그마의무장의 BF=5 동상 경로, 불면/의기양양의 다른 수면 계열 경로,
다른 보호 특성과의 조합은 별도 미검증 범위다. 일괄 완료로 표시하지 않는다.
이 작업에서 ROM/세이브/외부 원본을 생성하거나 수정하지 않는다.

## 두 번째 묶음: 기술 면역과 급소 판정

`verify_phase3_native_immunity.py`는 기존 처리기를 다시 작성하지 않고
아래 ARM 소비자의 원래 조건 분기를 실행한다. 공통 세 슬롯 조회 연결을 사용한다.

| 특성 | 실행 범위 / ABI | 확인 경계 |
|---|---|---|
| 부유 | 0x0230b1dc..0x0230b248, r8=type, r9=target, r10=actor, r7=damage_info, r11=multiplier | Ground9에서 damage_info+8=0, 중력·틀깨기 시 허용 |
| 방음 | 0x0232f220..0x0232f270 또는 0x023c1244, r4=target, r8=move, r9=actor | 소리 기술 거부 시 r11=0, 비소리 기술 허용 |
| 전투무장 / 조가비갑옷 | 0x0230cd50..0x0230ce14 또는 0x0230ce38, r9=target, r10=actor | 급소 판정 성공/거부 분기, 공통 legacy19 양쪽 이름 대응 |
| 대운 | 위 급소 판정, 원래 임계값 stack+0xe8 | 기준10→20, 난수9/10/19/20 경계 비교 |

부유 helper0x02301e18은 실제 Gravity0x02338390(DUNGEON+0x12afc)를 먼저
읽은 뒤 ID55를 조회한다. 땅 면역 소비자는 공격자의 ID83 틀깨기를 먼저
조회한다. Magnet Rise는 별도 보호이며 이 테스트에서는 없는 것으로 모델링한다.
면역 시 float zero 변환 서비스만 모델링하며 damage_info 쓰기는 실제 실행한다.

방음 소비자에서 DefenderAbilityIsActive 사본0x02332a0c(actor,target,ID60,flag1)와
실제 IsSoundMove0x02013d5c를 실행한다. 현재 ROM의 소리 ID15개는
217,112,284,83,34,84,171,424,27,241,25,26,446,530,555다.
이 목록은 기존 ROM 분류의 검증 기준이며 이후 새 기술의 분류 인증은 아니다.

급소 면역은 DefenderAbilityIsActive 사본0x0230a940을 사용한다.
대운은 공격자 ID88 조회 뒤 r4 임계값을 왼쪽으로1비트 이동한다.
아이템/IQ 보너스와 성별 보정은 중립으로 모델링하고 RNG값을 지정한다.
대운은 공격자 특성이므로 자신의 틀깨기로 억제되는 것으로 테스트하지 않는다.

총178사례: 부유28, 방음112, 급소 면역14, 대운24.
특성 없음·슬롯1/2/3·도구 억제·위액, 방어 특성의 틀깨기를 비교한다.
급소 결과 뒤의 피해 배율, 앞선 Lucky Chant 등 다른 급소 보호,
전체 기술 실행/UI/피격 반응, 부유의 바닥 이동/함정은 이 범위에 포함하지 않는다.

## 세 번째 묶음: 새 이벤트의 숫자 단계 변화

ME_ChangeStat(actor,target,stat,delta)의 stat4/5/6(숫자 스피드/명중/회피)을
공통 처리로 묶었다. 이전 스피드 경로와 명중/회피 경로는 plain ability 조회를
사용해 틀깨기를 누락했고, 실제 하락 후 오기/승기 반응도 없었다.
이제 DefenderAbilityIsActive0x022f96cc(actor,target,id,1)로 대상의
심술꾸러기129→하락 방지15/명중 전용30→단순97을 순서대로 처리한다.
그 뒤 4..16으로 제한하고 실제 저장 값이 변한 경우만 성공으로 반환한다.

숫자 단계가 실제로 내려가고 살아 있는 적이 원인일 때만 holder의
오기150/승기151을 조회하여 ME_ChangeStat(holder,holder,Atk/SpAtk,+2)를 호출한다.
이는 별도 자기 효과이므로 원인 공격자의 틀깨기가 반응 자체를 억제하지 않는다.
UI/특수공격 처리 등은 기존 IncreaseAttackStage0x0231399c에 위임한다.
verify_phase3_numeric_stats.py는 이 native writer 경계를 모델링하며,
actor=target, physical/special index, amount2 및 stack 인자를 기록한다.
최종 물리/특수 저장 값과 기존 native 반응 UI까지 인증하는 테스트는 아니다.

기존 효과가 이 API로 들어오는 경로에 한정한다. 기존 기술의 별도
명중/회피 native 함수, 공격/방어 감소 함수, phase1/2 ME_ChangeSpeed API까지
한꺼번에 바꾼 것으로 표시하지 않는다. 강화 차이와 신규 native 연결은 후속 범위다.
