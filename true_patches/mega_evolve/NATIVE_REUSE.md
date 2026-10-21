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

숫자 스피드 랭크 연출은 공격 랭크 writer를 거치지 않는다. 기존 능력치
하강/상승 효과(일반 애니메이션 686/687, effect.bin 257)를 복제하여 파란색
팔레트의 파일 293 및 애니메이션 707/708을 추가한다. ME_ChangeStat의 스피드
분기는 실제 저장 랭크가 변한 뒤에만 대상 엔티티로 PlayEffectAnimationEntity를
호출한다. verify_phase3_visual.py가 효과 파일·테이블과 ARM 호출 인자, 공격
랭크 불변 및 상한에서 연출이 없는 경우를 검사한다.

명중·회피 숫자 랭크는 원래 Boost/LowerHitChanceStat의 연출 전용 래퍼
0x022e5258/0x022e52f8만 사용한다. 원래 writer를 재호출하지 않으므로 랭크가
이중으로 변하지 않는다. 동일 계열·강도의 날씨 소스는 타이머/우선순위를
갱신해도 native selector의 강제 연출 플래그를 내리고, 종류나 강도가 바뀌면
기존 날씨 전환 연출을 사용한다.
끝의대지·시작의바다·델타스트림의 새 강한 날씨가 실제로 적용된 경우에만
빈 문자열 인덱스19753..19755의 별도 한영 안내 메시지를 이어 표시한다.
동일 날씨 재등록에서는 이 메시지도 반복하지 않는다.
무효화된 대상 기술·상태·방어 하락·강제 이동과
라이트메탈의 함정 회피는 기존 무효 메시지를 사용한다. 메시지의 대상 이름은
SubstitutePlaceholderStringTags로 먼저 채운다. 떠도는영혼의 교환 성공은
기존 Skill Swap 메시지와 사용자 이름 태그를 재사용한다.
픽업은 가방 삽입 성공 후 원래 바닥 아이템 획득 코드의 아이템 태그 함수
0x02024fe8과 사용자 이름 태그를 써서 기존 획득 메시지(문자열 인덱스3167)를
표시한다. 가방이 찼거나 발동이 실패하면 메시지와 태그를 만들지 않는다.
화학의힘은 실제 특성 은행 교체가 성공한 경우에만 기존 트레이스의 복사
메시지(문자열 인덱스3807)를 표시한다.

델타스트림은 native 날씨0(맑음) 전환 뒤, 원래 순풍(Tailwind444)의 화면 전체
바람 연출(anim 일반471, effect 파일15)을 재생한다. 동일 강한 날씨 재등록에서는
재생하지 않는다. ARM 검증은 애니메이션 표 연결과 호출 인자·조건을 검사하며
실제 기기/에뮬레이터 렌더링까지 인증하지 않는다.

최종 물리/특수 저장 값과 기존 native 반응 UI까지 인증하는 테스트는 아니다.

기존 효과가 이 API로 들어오는 경로에 한정한다. 기존 기술의 별도
명중/회피 native 함수, 공격/방어 감소 함수, phase1/2 ME_ChangeSpeed API까지
한꺼번에 바꾼 것으로 표시하지 않는다. 강화 차이와 신규 native 연결은 후속 범위다.

## 실제 호출 경로와 추가 ABI 교정

- DealDamage0x02332b28은 실제로0x023af5e4를 호출한다. 그 안에서 r7에
  피해 계수를 보관하고0x023af81c..0x023b0430의 특성 처리를 실행한다.
  0x023d9480의 비슷한 본문은 현재 ROM에서 직접/리터럴 호출 참조가 없는 사본이다.
  사본만 수정/실행해 효과 완료로 선언하지 않는다. 이 경로 확인을 다시 조사하지 않는다.
- 활성 경로에서 통찰5/4→6/5, 옹골찬턱3/2→6/5,
  예리함·애널라이즈·메가런처·단단한발톱4/3→6/5,
  모래의힘3/2→6/5, 프렌드가드3/4→4/5를 해당 연산만 가드하고 교체한다.
  위험예지의 실제 경로는 이미3/2이므로 그대로 유지한다.
- 기존 AbilityIsActive0x02301d10은 r3를 보존한다. C 조회로 바꾼 뒤에는
  이 암묵적 ABI를 잃을 수 있어 phase2/3 native entry를 저장/복원 래퍼로 바꿨다.
  직접 C API의 AAPCS와 native 호출 계약을 분리한다.
- 필터/하드록의 native matchup3 경감은 원래Omniscience와 같은0.75 상수를 쓴다.
  0x0230b070의 factor 포인터만 교체해 필터/하드록은0.8,
  Omniscience만 있는 경우는 기존0.75를 유지한다. 공유 상수를 전역으로 바꾸지 않는다.
- 순수한힘/천하장사의 기존 core34 부스트 두 조회를 교체하고,
  실제 물리 공격 base-stat 경계에서 각각6/5를 적용한다. 특수·방어·고정 피해 제외,
  천진/틀깨기·서로 다른 두 특성의 조합을 검사한다.
- 근성은 physical category 및 기존 negative-status 판정을 보존한다.
  old numerator×2를 numerator×3 / denominator×2로 바꿔1.5를 정확히 유지한다.
- 건조피부는 기존 fire 부스트와 햇살 정기 피해의 두 조회만 제거했다.
  실제 햇살에서 fire 피해1.2를 적용하고 water 피해→회복 및 rain 회복 조회는 유지한다.
- 노가드는 MoveHitCheck의 actor/target 유효 특성을 검사해 두 accuracy pass 모두
  성공으로 처리한다. 적용되지 않으면 이전 entry와 인자/stack을 그대로 호출한다.
  별도 피해 계산·타입/기술 면역 entry를 바꾸지 않는다.

## 외형과 원래 종의 분리

SetMonsterTypeAndAbility0x022f91dc/0x022f9200은 monster+2로 MD를 조회한다.
반면 기존 일루전/괴짜의 spawn 본문은 monster+4를 외형 종으로 바꾼다.
따라서 phase3 bank 및 층 복원은 +2를 기준으로 하며 +4 변화로 새 프로필을
생성하지 않는다. 초기 문서의 +4 해석을 교정했다. phase2 저장 형식은 유지한다.
기존 네 appearance byte-reader의 가드된 명령 두 개만 세 슬롯 조회로 바꿨다.
spawn은 활성 특성을 검사하고 해제 판정은 이미 적용된 외형을 정리할 수 있도록
보유 여부를 검사한다. 기존 fixed-room/candidate 처리와 변신 본문은 유지한다.

## 추가 검증 경계

damage_rules는 ROM-derived player range와 유형/상태 배율, 전 대상 처리 건너뛰기,
아군 support/날씨 예외를 검사한다. hit_rules는 실제 HP 하락·행동/층 ledger를 검사한다.
defense_guard는 기존 방어 감소 entry의 파라미터를 그대로 넘기는지 검사한다.
mega_sol은 해당 native return site와 현재 공격자만 가상 쾌청을 반환하며
실제 Solar Beam/Morning Sun 본문을 실행한다. ambient/world/source/상대 조회는 유지한다.
원래 move table의 불변 상수를 읽기 위해 해당 fixture에 overlay10을 추가 로드한다.
sleep은 Snore/Bad Dreams/기술 status-check의 수면 조회만 교체하고 global action sleep은
보존한다. Nightmare가 실제 BD3 수면 상태를 쓰는 entry는 기존 sleep 면역으로 보호한다.
미검증 부분 및 native terminal service 모델링은 각 script docstring/출력에 명시한다.

## 페이즈 3 마무리 연결

- 부자유친은 ExecuteMoveEffect entry의 기존 balance owner를 호출한다. eligible 기술만
  같은 action ledger 안에서 다시 실행하며 두 번째 피해 1/4, 첫 실행 이후 PP로 복원한다.
  중첩 effect frame은 별개이며 원래 다단히트/고정 피해/충전 기술은 catalogue에서 제외한다.
- 우격다짐의 활성 caller 0x02332b38에서 원래 pointer/ID 혼동을 제거했다. 기존 native
  목록 128개를 그대로 추출하고 실제 호출된 기술 ID로 추가 효과와 최종 6/5 피해를 판정한다.
- 나쁜손버릇은 기존 Thief/Covet item-transfer tail 0x0232c354를 재사용한다. 6바이트 item,
  점착, 보스 고정 도구, 가방 여유, 팀 도구 등록/해제 조건을 유지한다.
- 내용물분출은 기존 유폭118의 조회에225를 연결한다. 기존 50% 판정과 폭발 처리,
  source 재귀 제한 및 틀깨기를 유지한다.
- 실제 피해 packet의 type/critical을 HitBoundary에서 넘긴다. 부활로 HP가 복원된
  타격도 양의 피해 packet으로 확인하며 분노의경혈은 공격/특공 저장+3을 요청한다.
  기존 계산단계20 강제 query는 해당 소비자에서만 제거한다.
- 급류/심록/벌레의알림/맹화의 기존 HP≤max/4 조건을 유지하고 factor2.0을1.5로
  바꾼다. 이판사판/철주먹은 기존 기술 classifier와 위력 위치에서6/5를 적용한다.
- 위협은 기존 물리 numerator4/denominator5 연산을 재사용하고 같은 방의 살아 있는
  상대 보유자를 검사한다. 자력은 인접 강철 적의 계산 방어/특방 단계−1이며,
  실제 walk action2만 pass action1로 처리한다. 별도 상태를 저장하거나 강제 이동을 막지 않는다.
- 일찍기상은 기존 duration half/min1/127 예외를 유지하고 실제 EndSleepClassStatus
  전후의 수면1/3/5→0 전환에서 최대 HP를 복원한다. 원래5인자 ABI를 보존한다.
- 해감액은 DealDamageCore의 성공한 명중 이후 0x02332d9c 경계에서만 처리한다.
  흡수 기술 피해 packet을0으로 바꾸고 절반을 기존 fixed-damage wrapper로 반사한다.
  AI 피해 계산만으로 반사하거나 이미 피해를 받은 뒤 HP를 되돌리지 않는다.
- 복안은 native accuracy bonus+1, 정의의마음은 native attack writer+3,
  저주받은바디는 native seal flag RNG threshold12로 교정한다.
- 아이스바디의 잘못된 active branch와 비활성화된 half 연산을 교정한다. native
  설경 회복 분모 half와 원래25..400 clamp를 유지한다. 젖은접시도 같은 native 경로로 검증한다.
- 두꺼운지방/내열의 공유 fire/ice factor0.8을 해당 pointer 경계에서0.5로 바꾼다.
  내열의 얼음 경로는 별도 final rule이며 틀깨기를 적용한다.
- 펑크록의 damage tail이 기술 ID를 IsSoundMove의 pointer 인자로 넘기던 ABI 오류를
  최소 move struct wrapper로 교정한다. 공격6/5를 유지하고 방어는1/2로 바꾼다.
- 천진은 최종 native attack/defense/accuracy/evasion lookup에서 단계10을 적용한다.
  공격/방어 cached scalar를256으로 처리하고 저장 단계는 바꾸지 않는다. 기존 native
  최초 neutralization 뒤의 다른 보정이 재도입되는 문제를 이 최종 경계에서 막는다.

## 기존 효과를 재사용하는 근거와 검증 한계

data/phase3_native_consumers.json은 source hash, query caller와 주변 instruction hash를
보관한다. ov29/36만 조사하면 피뢰침/마중물의 실제 소비자를 놓친다. ARM9의
0x020b3380..0x020bb380는 startup copy 후 ITCM0x01ff8000..0x02000000에서 실행하며,
그 위치에서 native AbilityIsActive 목적지를 해석한다. 원본 위치만 disassemble하면
branch destination이 다른 주소로 보이는 것도 기록한다.

verify_phase3_inherited는 실제 copied ITCM record updater0x01ffbd20의 ID50/122 query와
cache writes를 실행한다. 관련 없는 redirect eligibility는 모델링한다. 습기의21은
native Explosion0x02320788에서 r7에 보관해 floor loop query로 전달하며, 일루전/괴짜는
전용 appearance suite가 실제 소비자를 실행한다. 자동 immediate-query inventory의
빈 목록을 곧바로 기능 부재로 해석하지 않는다.

206개 전체의 세 슬롯 일반 identity/기존 native query ABI/억제는 공통 suite에서 검증한다.
그대로 재사용한 기존 효과70개를 신규 구현/전투 전체 실행 인증으로 집계하지 않는다.
수정·신규 공통 처리와 기존 효과의 연결136개는 개별 suite 및 앞선 공유 suite에 근거를
기록한다. coverage의 implementation status와 verified_paths는 서로 다른 정보다.
전체 던전 전투, 실제 file IO/RAM 최대 부하와 기기 실행은 후속 통합 검증 범위다.

마무리 weather 회귀에서는 강한 비/햇살의 native type immunity가 날씨부정 등
해당 대상의 날씨 억제를 무시하던 global flag 소비자를 교정했다. 해당 대상의
ApparentWeather/strength가 억제되면 로컬 immunity flag만0으로 처리하며 source와
세계 날씨를 지우지 않는다. 강한 햇살의 물 면역에는 누락된 damage packet miss
marker를 추가해 피해 없이 추가 효과/흡수 회복이 발동하지 않도록 했다.
verify_phase3_strong_weather는 실제 native branch와 Air Lock query를 실행하며,
팀 관계 판정과 UI는 모델링한다.
