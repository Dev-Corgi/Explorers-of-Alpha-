# 턴제 로그라이크 기믹몹·보스 패턴 자료집

조사일: 2026-10-16 · 용도: 시련의 탑 기획 참고

## 1. 범위와 읽는 방법

Dungeon Crawl Stone Soup(이하 DCSS)와 Shattered Pixel Dungeon(이하 Shattered)의 기존 적을 대상으로 한다. **포켓몬으로의 변환안이나 구현 계획은 포함하지 않는다.** 우리 저장소의 게임 코드는 분석하지 않았으며, 웹에 공개된 각 게임의 공식 자료와 소스를 조사했다.

- **버전 기준:** DCSS 0.34.1, Shattered v3.3.8. 최신 개발판 전체를 포괄한다는 뜻은 아니며, 재확인 가능한 공개 태그에 기준을 고정했다.
- **선정 기준:** 능력치 차이보다 전투 방식이 달라지는 적을 우선했다. 전체 몬스터 도감의 전수 목록은 아니며, 단순 속성·수치 변형은 일부 통합했다.
- **이름:** 검색과 원문 대조를 위해 영문 고유명을 사용한다. 역할명은 이 문서에서 붙인 분류다.
- **사실과 해석:** ‘행동·조건·전환’은 원작의 동작 요약이다. ‘대응·판단’과 마지막의 패턴 분류는 이를 바탕으로 한 기획 관점의 해석이다. 유일한 공략법을 뜻하지 않는다.
- **수치:** 피해량·확률·세부 턴 수는 대부분 생략했다. 보스의 큰 단계와 일반적인 전환 조건을 중심으로 읽는다.
- **난이도:** Shattered 보스 본문은 기본 난이도 기준이다. Badder Bosses 도전의 변경은 별도로 적었다. 다른 Pixel Dungeon 변형판의 동작과 섞지 않는다.
- **보스의 차이:** Shattered에는 층별 정규 보스전이 있다. DCSS의 네임드는 대부분 고정 순서의 패턴 보스가 아니라, 고유 기술·장비·동행 적을 가진 유니크다. HP에 따른 단계 전환이 없는 적에게 임의의 페이즈를 붙이지 않았다.

## 2. 먼저 보는 기믹 유형

| 유형 | 전투에서 달라지는 판단 | 대표 사례 |
|---|---|---|
| 사선 저격 | 어느 사선에 노출될 것인가 | Scorpio, centaur |
| 근접 회피 | 어떻게 거리를 좁힐 것인가 | Gnoll Trickster, Nessos |
| 예고 공격 | 공격 대신 언제 이동할 것인가 | Evil Eye, Ripper Demon, Goo |
| 돌진 | 돌진 경로를 어떻게 비울 것인가 | boulder beetle |
| 강타 후 빈틈 | 어느 순간에 반격할 것인가 | bunyip |
| 끌어오기·밀치기 | 현재 위치가 유지될 것인가 | Guard, swamp worm, elephant |
| 도주로 봉쇄 | 전투 전에 퇴로를 확보했는가 | vault warden, thorn hunter |
| 지형 의존 공격 | 벽·물·풀 중 무엇을 피할 것인가 | ironbound frostheart, Yog의 주먹 |
| 지연 상태이상 | 상태가 완성되기 전에 빠질 수 있는가 | basilisk, catoblepas |
| 시야 내 오라 | 직접 공격하지 않는 적도 우선 제거할 것인가 | torpor snail |
| 집단 임계점 | 적 수가 늘기 전에 줄일 것인가 | dream sheep, starcursed mass |
| 강화·치유 지원 | 앞의 적과 지원가 중 누구부터 잡을 것인가 | moth of wrath, Necromancer |
| 피해 분담 | 공격 대상의 피해가 어디로 전달되는가 | ironbound preserver, Dwarf King |
| 소환·증원 | 지금 싸움이 길어져도 되는가 | Boggart, ironbound convoker |
| 분열·부활 | 한 번 쓰러뜨리는 것으로 끝나는가 | Swarm, Ghoul, Blorkula |
| 죽음 직전 반격 | 마무리와 후퇴 중 무엇이 안전한가 | Gnoll Brute |
| 처치 시 폭발 | 어디에서 마지막 타격을 넣을 것인가 | Skeleton, bloated husk |
| 자원·빌드 훼손 | 이번 전투 이후에도 손해가 남는가 | Thief, Warlock, orb of fire |
| 수단별 방어 | 다른 공격 수단이 필요한가 | Sewer snake, Slime, Monk, hydra |
| 전장 목표 전환 | 보스 대신 장치·부하를 쳐야 하는가 | DM-300, Dwarf King, Yog-Dzewa |
| 분신·모방 | 무엇이 본체이며 누구의 힘이 복제되는가 | Mara |
| 강제 변신·기능 봉인 | 평소 빌드를 사용할 수 있는가 | Kirke, Mennas |

## 3. Shattered — 일반 기믹몹

### 3.1 하수도: 기본 전투 규칙을 가르치는 적

| ID | 몬스터 | 핵심 행동·조건 | 요구하는 대응·판단 |
|---|---|---|---|
| SP-N01 | [Sewer snake][sp-Snake] | 회피가 높아 정면 무기 공격이 잘 빗나간다. | 문·모서리에서 기습하거나 마법 등 다른 수단을 쓴다. |
| SP-N02 | [Slime][sp-Slime] | 단발 피해에 상한이 있다. | 큰 한 방만 강화한 빌드의 효율이 떨어진다. |
| SP-N03 | [Swarm of flies][sp-Swarm] | 피해를 받으면 체력을 나누어 분열한다. 공간이 늘면 개체 수가 증가한다. | 좁은 곳으로 유도하거나 범위 공격을 사용한다. |
| SP-N04 | [Sewer crab][sp-Crab] | 빠르게 접근하는 근접 적이다. | 이동만 반복하는 후퇴로 해결하기 어렵다. |

### 3.2 감옥: 도주·당기기·처치 위치

| ID | 몬스터 | 핵심 행동·조건 | 요구하는 대응·판단 |
|---|---|---|---|
| SP-N05 | [Crazy thief][sp-Thief] | 아이템을 훔치면 도주 상태로 전환한다. 훔친 물건은 처치 시 회수할 수 있다. | 추격 경로와 주변 위험을 계산한다. |
| SP-N06 | [Skeleton][sp-Skeleton] | 죽을 때 주변에 뼛조각 폭발을 일으킨다. | 마지막 타격을 넣는 위치·거리·방어를 고려한다. |
| SP-N07 | [Prison guard][sp-Guard] | 사슬로 대상을 끌어당겨 근접전을 강요한다. | 원거리에서 안전하다고 가정하지 않는다. |
| SP-N08 | [Necromancer][sp-Necromancer] | 해골을 소환하고 자신의 해골을 회복·강화하며 전투를 유지한다. | 부하를 반복해서 잡을지, 소환자를 먼저 노릴지 결정한다. |
| SP-N09 | [Spectral necromancer][sp-SpectralNecromancer] | 일반 강령술사의 희귀 변형으로, 유령 계열 소환을 사용한다. | 같은 ‘소환자 우선’ 원칙에서도 상대할 소환물의 방어 특성이 달라진다. |

### 3.3 동굴: 지연 피해·사망 유예·지형

| ID | 몬스터 | 핵심 행동·조건 | 요구하는 대응·판단 |
|---|---|---|---|
| SP-N10 | [Gnoll brute][sp-Brute] | 치명상을 받으면 임시 보호막과 강화된 공격을 얻어 잠시 생존한다. 보호막은 시간으로도 줄어든다. | 즉시 추가 공격할지, 물러나 분노가 끝나기를 기다릴지 판단한다. |
| SP-N11 | [Armored brute][sp-ArmoredBrute] | 물리 방어와 사망 유예가 강화된 희귀 변형이다. | 평타로 밀어붙이기보다 다른 피해 수단이나 시간 벌기를 고려한다. |
| SP-N12 | [Cave spinner][sp-Spinner] | 독을 걸고 물러나며 거미줄로 이동을 방해한다. | 독 피해가 누적되는 추격을 피하고 해독·원거리 공격을 준비한다. |
| SP-N13 | [Gnoll shaman][sp-Shaman] | 원거리 마법에 색상별 약화 효과가 붙는다. 공격력, 받는 피해, 명중·회피에 서로 다른 압박을 준다. | 색과 상태를 읽고 전투 지속 여부를 정한다. |
| SP-N14 | [Vampire bat][sp-Bat] | 빠른 이동과 흡혈 회복을 가진다. | 작은 피해로 오래 싸우기보다 안정적으로 마무리한다. |
| SP-N15 | [DM-200][sp-DM200] | 큰 몸 때문에 좁은 공간 이동이 제한된다. 접근하기 어려운 적에게 독성 가스를 사용한다. | 통로 활용과 가스 회피를 함께 고려한다. |
| SP-N16 | [DM-201][sp-DM201] | 이동하지 않는 변형이며, 원거리에서 공격받으면 부식성 가스로 반격한다. | 단순 원거리 포격이 안전한 해법인지 다시 판단한다. |

### 3.4 드워프 도시: 처치 순서와 빌드 방해

| ID | 몬스터 | 핵심 행동·조건 | 요구하는 대응·판단 |
|---|---|---|---|
| SP-N17 | [Dwarf ghoul][sp-Ghoul] | 함께 나타나는 구울이 쓰러진 동료를 되살릴 수 있다. | 한 마리만 반복해서 쓰러뜨리지 말고 무리를 정리한다. |
| SP-N18 | [Dwarf monk / Senior monk][sp-Monk] | 집중 상태에서 다음 물리 공격을 막는다. 이동 중 집중이 더 빨리 쌓인다. | 값싼 공격으로 방어를 소모시키거나 마법을 사용한다. |
| SP-N19 | [Dwarf warlock][sp-Warlock] | 원거리 마법과 장비 강화 효과를 일시적으로 약화시키는 디버프를 사용한다. | 강화 수치에 의존하는 빌드일수록 우선 처치 가치가 커진다. |
| SP-N20 | [Golem][sp-Golem] | 순간이동과 대상을 가까이 옮기는 능력으로 거리를 무너뜨린다. | 지형을 이용한 안전거리 유지에 별도 대책이 필요하다. |

### 3.5 악마의 전당·공통 특수 적

| ID | 몬스터 | 핵심 행동·조건 | 요구하는 대응·판단 |
|---|---|---|---|
| SP-N21 | [Succubus][sp-Succubus] | 순간이동으로 접근하고 매혹을 건다. 매혹된 대상을 공격하면 자신을 회복·보호한다. | 매혹 중 정면 교환을 계속할지 판단한다. |
| SP-N22 | [Evil Eye][sp-Eye] | 광선을 충전하면서 피해를 덜 받는다. 충전한 사선을 향해 강한 관통 광선을 발사한다. | 충전 중 공격보다 사선 이탈·엄폐를 우선한다. |
| SP-N23 | [Scorpio][sp-Scorpio] | 근접전을 피하며 원거리 가시로 공격하고 이동을 둔화시킨다. | 직선 추격보다 사선 차단·유인·이동 수단을 쓴다. |
| SP-N24 | [Ripper demon][sp-RipperDemon] | 도약을 준비한 뒤 지정한 위치로 뛰어들어 출혈을 가한다. | 예고된 착지점을 벗어나고 포위되지 않는다. |
| SP-N25 | [Demon spawner][sp-DemonSpawner] | 자리에 고정된 채 Ripper demon을 생성한다. 남겨두면 최종 보스의 증원 구성에도 영향을 준다. | 당장 처치 비용과 이후 보스전 부담을 함께 계산한다. |
| SP-N26 | [Mimic][sp-Mimic] | 상자로 위장해 상호작용을 유도한다. | 보상에 접근하기 전에 외형과 조사 정보를 확인한다. |
| SP-N27 | [Golden mimic][sp-GoldenMimic] | 좋은 보상을 내세우는 강화된 미믹이다. | 보상의 가치와 즉시 감당할 전투력을 비교한다. |
| SP-N28 | [Ebony mimic][sp-EbonyMimic] | 은밀한 위장과 위험한 기습을 가진 특수 변형이다. | 탐색·조사 자체를 전투 준비의 일부로 취급한다. |

### 3.6 퀘스트·미니보스·특수 장애물

| ID | 적·대상 | 핵심 패턴 | 요구하는 대응·판단 |
|---|---|---|---|
| SP-Q01 | [Fetid rat][sp-FetidRat] | 부패한 공격과 마비성 악취를 사용한다. | 가스가 있는 자리에서 오래 교환하지 않는다. |
| SP-Q02 | [Gnoll trickster][sp-GnollTrickster] | 원거리 투척을 하며 접근을 피한다. | 문·모서리를 이용해 사선을 끊고 거리를 좁힌다. |
| SP-Q03 | [Great crab][sp-GreatCrab] | 자신이 볼 수 있는 공격을 강하게 방어한다. | 기습처럼 방어 조건을 깨는 공격을 찾는다. |
| SP-Q04 | [Newborn fire elemental][sp-Elemental] | 불을 다루는 퀘스트 적이며 냉기 계열 수단이 큰 약점이다. | 힘으로만 싸우기보다 준비한 해법을 사용한다. |
| SP-Q05 | [Rot heart][sp-RotHeart] / [Rot lasher][sp-RotLasher] | 고정된 심장을 주변의 감지·공격 기관이 지킨다. 심장은 공격받으면 독성 가스를 방출한다. | 본체까지 가는 동선과 보호 기관·가스의 위험을 나누어 처리한다. |
| SP-Q06 | [Gnoll geomancer][sp-GnollGeomancer] | 암석 갑옷, 바위 공격, 낙석을 사용한다. 초기 갑옷은 곡괭이로 제거하며, 보호하는 공병이 있는 구간에는 공병을 먼저 처리해야 한다. | 도구 사용·부하 처치·낙석 회피에 따라 목표를 바꾼다. |
| SP-Q07 | [Crystal guardian][sp-CrystalGuardian] | 완전히 처치하기 어려운 수호자로, 좁은 공간에서 느려진다. | 영구 처치보다 잠재우기·우회·작업 시간 확보가 목표가 된다. |

## 4. Shattered — 정규 보스 5종

### SP-B01. Goo — 충전 강타와 물 지형

5층 보스. 평소에는 근접 교환을 하지만, 몸을 부풀리는 예고 뒤 강한 공격을 한다. 이동하면서 충전이 취소될 수 있어, 충전을 보고 자리를 바꾸는 것이 핵심이다. 물 위에서는 회복하므로 어디로 유도하느냐도 중요하다. 체력이 낮아지면 일반 전투력과 강타 압박이 커진다. [패턴 근거][sp-Goo]

**흐름:** 접근·근접전 → 충전 예고 → 범위 밖 이동 또는 엄폐 → 다시 공격. 물 위 회복이 끼어들면 전투가 길어진다.

**보스가 묻는 것:** ‘언제 공격을 멈출 것인가’, ‘보스에게 유리한 지형을 내줄 것인가’.

### SP-B02. Tengu — 이동 경로와 복합 장판

10층 보스. 전반에는 순간이동과 원거리 공격을 하며 함정 위치를 보여준 뒤 기억과 동선을 시험한다. 중간 추격 구간을 지나 후반 전장으로 이동한다. 후반에는 폭탄·전기 장치·화염 계열 위험이 더해져, 보스 추격과 안전한 경로 선택을 동시에 해야 한다. [패턴 근거][sp-Tengu]

**흐름:** 원거리 교환·위치 변경 → 전장 이동 → 여러 시간차 위험을 피해 재접근.

**보스가 묻는 것:** ‘최단 경로와 안전한 경로 중 어느 쪽을 택할 것인가’.

### SP-B03. DM-300 — 본체와 발전 장치의 목표 교대

15층 보스. 독성 가스와 예고된 낙석으로 자리를 바꾸게 한다. 일정 피해를 받으면 발전 장치의 힘으로 과충전되어 무적 상태로 추격한다. 이때는 본체 공격을 멈추고 **활성화된 발전 장치**를 찾아 부숴야 한다. 장치 주변에도 전기 위험이 있다. 기본 난이도에서는 이 전환을 두 번 거친다. [본체][sp-DM300], [발전 장치][sp-Pylon]

**흐름:** 본체 공격 → 과충전·무적 → 추격을 피해 활성 장치로 이동 → 장치 파괴 → 본체 공격 재개.

**보스가 묻는 것:** ‘지금 피해를 줄 대상은 누구인가’, ‘추격당하면서 전장을 읽을 수 있는가’.

### SP-B04. Dwarf King — 피해 연결·부하 웨이브·지연 피해

20층 보스. 첫 단계에서는 부하를 부르고 피해를 연결하거나 위치를 재배치한다. 다음 단계에서는 왕좌의 보호막과 직접 피해 무효 상태로 전환한다. 지정된 부하를 처치하면 왕의 보호막이 줄어든다. 마지막 단계에서는 증원이 계속되는 가운데 본체가 받은 피해가 즉시 적용되지 않고 시간에 걸쳐 반영된다. [패턴 근거][sp-DwarfKing]

**흐름:** 왕과 부하 동시 교전 → 본체 보호·부하 처치 목표 → 본체에 충분한 지연 피해 축적 → 증원을 버티며 마무리.

**보스가 묻는 것:** ‘처치 순서를 바꿀 수 있는가’, ‘이미 충분히 공격했는데도 무리하게 더 때리고 있지 않은가’.

### SP-B05. Yog-Dzewa — 예고 광선과 무적을 해제하는 주먹

25층 보스. 고정된 본체가 예고 광선과 증원으로 압박한다. 체력 구간마다 주먹을 불러내며, 주먹이 살아 있는 동안 본체는 무적이다. 주먹 역시 본체 근처에서는 보호받으므로 떨어뜨려 싸워야 한다. 주먹을 처리하면 본체 공격을 재개한다. 마지막에는 공격·증원 간격이 짧아진다. [본체][sp-YogDzewa], [주먹 공통 규칙][sp-YogFist]

기본 난이도에서는 불/흙, 부패/녹, 빛/어둠의 세 쌍에서 하나씩 뽑아 총 세 주먹을 사용하며 순서도 섞는다. 앞선 층에서 남겨둔 Demon spawner는 보스전 증원을 더 위험하게 만든다. [등장 구성][sp-YogDzewa]

**흐름:** 광선 회피·본체 공격 → 주먹 출현·본체 무적 → 주먹을 끌어내 처치 → 본체 공격 재개 → 최종 압박.

**보스가 묻는 것:** ‘본체와 분리 목표를 번갈아 처리할 수 있는가’, ‘이전 층의 결정이 최종전에 어떤 부담을 남겼는가’.

#### Yog의 주먹 6종

| ID | 주먹 | 고유 패턴 | 요구하는 대응·판단 |
|---|---|---|---|
| SP-F01 | Burning fist | 주변 지형을 불태우고 불을 퍼뜨린다. 물이 불 확산을 억제하지만 물 자체도 증발시킨다. | 남아 있는 물과 불이 퍼질 경로를 고려한다. |
| SP-F02 | Soiled fist | 식생을 만들고 뿌리로 붙잡는다. 주변의 높은 식생에서 방어 이득을 얻는다. | 식생이 없는 곳으로 유도하거나 지형을 정리한다. |
| SP-F03 | Rotting fist | 부식성 오물과 독성 가스를 사용한다. 받은 피해는 출혈 형태로 반영되며, 추가 타격은 출혈을 단순 누적하지 않는다. 물에서는 회복한다. | 연속 타격 효율과 물 지형을 함께 따진다. |
| SP-F04 | Rusted fist | 강한 근접 공격과 원거리 둔화를 사용한다. 피해는 지연 적용되지만 추가 피해는 계속 쌓인다. 좁은 통로에는 들어오지 못한다. | 안전한 공간을 이용하고 이미 누적한 피해를 기다린다. |
| SP-F05 | Bright fist | 원거리 광선으로 피해·실명을 주며 섬광과 순간이동으로 이탈한다. 근접에서 사용할 특별한 원거리 능력은 제한된다. | 사선을 끊거나 접근한다. |
| SP-F06 | Dark fist | 원거리 공격과 어둠으로 광원을 약화시키고 순간이동한다. | 시야 확보와 접근 경로를 관리한다. |

여섯 변형의 근거: [YogFist][sp-YogFist]. 지형·피해 반영 방식·시야 방해가 서로 다르며, 단순한 속성 교체가 아니다.

### Badder Bosses는 별도 변형

Goo의 충전 준비 단축·회복 압박 강화, Tengu의 폭탄·전기 장치에 화염 공격 추가, DM-300의 추가 발전 장치 단계, Dwarf King의 강화된 웨이브, Yog의 단계별 복수 주먹 등으로 기본 패턴을 더 어렵게 만든다. 본문의 기본 패턴과 도전 전용 구성을 같은 것으로 읽지 않는다. [Goo][sp-Goo], [Tengu][sp-Tengu], [DM-300][sp-DM300], [Dwarf King][sp-DwarfKing], [Yog][sp-YogDzewa]

## 5. DCSS — 일반 기믹몹

이 절의 ‘일반’은 비유니크라는 뜻이다. 후반의 매우 강한 적도 포함된다. 주문은 [0.34.1 몬스터 주문 구성][dc-spells], 전투 중 처리·특수 효과는 [행동 처리][dc-act], [능력 처리][dc-abilities], [주문 실행][dc-cast]를 함께 참고했다.

### 5.1 거리·공간을 바꾸는 적

| ID | 몬스터 | 핵심 행동·조건 | 요구하는 대응·판단 |
|---|---|---|---|
| DC-N01 | [Centaur][dc-centaur] | 빠른 이동과 원거리 사격을 결합한다. | 열린 곳에서 직선으로 접근할지, 엄폐로 유인할지 정한다. |
| DC-N02 | [Orc priest][dc-orc-priest] | 앞의 다른 적을 방패로 삼아도 Smiting으로 대상을 직접 압박한다. | ‘앞의 적부터’라는 처치 순서를 바꾼다. |
| DC-N03 | [Orc wizard][dc-orc-wizard] | 혼란과 투명화에 공격 마법을 섞는다. | 제어당하기 전에 제거하거나 시야를 끊는다. |
| DC-N04 | [Boulder beetle][dc-boulder-beetle] | 거리가 있으면 고속으로 굴러 강하게 충돌한다. | 돌진 경로를 비우고 재접근 시점을 잡는다. |
| DC-N05 | [Bunyip][dc-bunyip] | 이동은 빠르지만 공격한 뒤 긴 빈틈이 생긴다. | 공격 교환의 박자를 읽는다. |
| DC-N06 | [Elephant][dc-elephant] | 밀어내는 짓밟기로 위치를 무너뜨린다. | 계단·통로 입구를 안전지대로 단정하지 않는다. |
| DC-N07 | [Swamp worm][dc-swamp-worm] | Harpoon Shot으로 대상을 끌어당긴다. | 물가·위험한 지형 옆에서 교전하지 않는다. |
| DC-N08 | [Guardian serpent][dc-guardian-serpent] | 주변 동료들을 대상 주변으로 순간이동시켜 포위한다. | 뱀 혼자 보인다고 단독 전투로 판단하지 않는다. |
| DC-N09 | [Vault warden][dc-vault-warden] | 주변 문과 계단을 봉쇄한다. | 싸우기 전 퇴로와 우선 처치 대상을 정한다. |
| DC-N10 | [Thorn hunter][dc-thorn-hunter] | 가시 벽을 만들고 원거리 가시 공격을 한다. | 통로가 막히기 전에 위치를 잡는다. |
| DC-N11 | [Ironbound frostheart][dc-ironbound-frostheart] | 벽에 붙은 대상을 냉기로 공격한다. | 평소 유리한 벽·모서리 위치가 이번에도 안전한지 판단한다. |
| DC-N12 | [Orb spider][dc-orb-spider] | 거리를 유지하며 파괴의 구체를 준비해 발사한다. | 단순 추격 대신 사선·장애물·접근 경로를 활용한다. |

### 5.2 상태·오라·집단 제어

| ID | 몬스터 | 핵심 행동·조건 | 요구하는 대응·판단 |
|---|---|---|---|
| DC-N13 | [Basilisk][dc-basilisk] | 석화 과정을 시작시켜 점차 행동을 빼앗는다. | 완전히 굳기 전에 이탈하거나 해제한다. |
| DC-N14 | [Catoblepas][dc-catoblepas] | 석화성 구름을 내뿜어 위험 지대를 남긴다. | 공격을 버틸지보다 그 칸에 머물지를 판단한다. |
| DC-N15 | [Dream sheep][dc-dream-sheep] | 무리를 이루어 수면을 유발한다. | 여러 마리를 동시에 시야에 두지 않는다. |
| DC-N16 | [Torpor snail][dc-torpor-snail] | 존재 자체가 시야 내 적을 둔화시킨다. | 직접 때리는 적이 아니어도 우선 제거할 가치가 있다. |
| DC-N17 | [Merfolk siren][dc-merfolk-siren] | 노래로 매혹해 멀어지는 이동을 제한한다. | 뒤늦게 도망칠 계획이 통하는지 확인한다. |
| DC-N18 | [Starcursed mass][dc-starcursed-mass] | 분열해 늘어난 개체들이 합창으로 정신을 압박하고 마비시킬 수 있다. | 개체 수가 쌓이기 전에 정리하거나 시야를 끊는다. |
| DC-N19 | [Unseen horror][dc-unseen-horror] | 보이지 않는 상태로 빠르고 불규칙하게 움직여 공격한다. | 탐지와 지형을 이용해 위치 불확실성을 줄인다. |

### 5.3 지원·증원·피해 규칙

| ID | 몬스터 | 핵심 행동·조건 | 요구하는 대응·판단 |
|---|---|---|---|
| DC-N20 | [Moth of wrath][dc-moth-of-wrath] | 주변 동료를 광폭화한다. 접촉한 대상에게도 분노를 유발할 수 있다. | 본체보다 강화된 주변 적이 더 위험해지는 상황을 차단한다. |
| DC-N21 | [Ironbound convoker][dc-ironbound-convoker] | 준비 후 멀리 있는 동료를 전장으로 불러오고 강화한다. | 증원이 완성되기 전에 제거·방해·이탈한다. |
| DC-N22 | [Ironbound preserver][dc-ironbound-preserver] | 동료가 받을 피해 일부를 대신 받고 자신을 회복한다. | 보호받는 적과 보호자 중 무엇부터 공격할지 정한다. |
| DC-N23 | [Boggart][dc-boggart] | 그림자 생물을 소환하며 투명화·순간이동으로 생존한다. | 부하와 소모전을 벌이기보다 소환자를 찾는다. |
| DC-N24 | [Hydra][dc-hydra] | 특정 절단 공격은 머리를 잘라 추가 머리가 자라게 한다. 불꽃 무기로 상처를 지지면 재성장을 막는다. | 평소 주력 무기를 계속 써도 되는지 판단한다. |
| DC-N25 | [Bloated husk][dc-bloated-husk] | 접근하거나 파괴되면 폭발한다. | 너무 가까이서 마무리하지 않는다. |
| DC-N26 | [Flayed ghost][dc-flayed-ghost] | 직접 죽이지 않는 임시 체력 손실을 누적시킨다. 원인 제거·효과 종료로 회복되는 피해다. | 다른 적의 실제 피해와 겹치기 전에 원인을 끊는다. |

### 5.4 전투 자원·방어·장기 손실을 공격하는 적

| ID | 몬스터 | 핵심 행동·조건 | 요구하는 대응·판단 |
|---|---|---|---|
| DC-N27 | [Entropy weaver][dc-entropy-weaver] | 부식으로 공격·방어의 효율을 떨어뜨린다. | 시간이 갈수록 불리해지는 교전을 끊는다. |
| DC-N28 | [Quicksilver dragon][dc-quicksilver-dragon] | 마법 효과를 해제하는 브레스를 사용한다. | 강화 효과를 다시 걸기만 하며 자원을 낭비하지 않는다. |
| DC-N29 | [Shining eye][dc-shining-eye] | 돌연변이를 유발하는 시선으로 장기적인 손해를 준다. | 당장 HP가 넉넉해도 시야 노출을 줄인다. |
| DC-N30 | [Orb of fire][dc-orb-of-fire] | 빠르고 강한 화염 공격에 해로운 돌연변이를 결합한다. | 높은 화염 방어만으로 안전하다고 판단하지 않는다. |
| DC-N31 | [Tormentor][dc-tormentor] | Torment로 현재 체력의 큰 비율을 깎는다. | 체력이 많다는 이유로 전투를 방치하지 않는다. |
| DC-N32 | [Hellion][dc-hellion] | Damnation 계열 공격으로 일반적인 속성·방어 대책을 우회한다. | 시야 차단·우선 처치로 공격 기회 자체를 줄인다. |

## 6. DCSS — 유니크·네임드의 전투 패턴

대부분의 적은 ‘이 기술을 항상 이 순서로 사용한다’는 고정 루프가 없다. 아래의 화살표는 원작에 존재하는 조건부 변화만 나타낸다. 주문 목록 근거는 [0.34.1 주문 구성][dc-spells], 사망·재등장·쌍둥이의 변화는 [사망 처리][dc-death]를 참고했다.

### 6.1 초중반의 전술형 네임드

| ID | 네임드 | 핵심 패턴·변화 | 요구하는 대응·판단 |
|---|---|---|---|
| DC-U01 | [Sigmund][dc-sigmund] | 혼란·투명화·원거리 마법을 장병기 근접전과 섞는다. | 무작정 접근하는 동안 제어당하지 않게 한다. |
| DC-U02 | [Grinder][dc-grinder] | 순간이동으로 위치를 바꾸며 마비와 고통 마법을 사용한다. | 마비 뒤 연속 피해를 감당할 수 있는지 판단한다. |
| DC-U03 | [Menkaure][dc-menkaure] | 가속과 Torment를 결합한다. | 낮은 체력의 보스라도 장기전을 허용하지 않는다. |
| DC-U04 | [Duvessa & Dowan][dc-duvessa] | 근접 전사와 마법사 한 쌍. 한쪽이 죽으면 남은 쪽이 광폭화 또는 마법 강화 상태로 변한다. | 누구를 먼저 쓰러뜨리고 어느 강화형을 상대할지 고른다. |
| DC-U05 | [Robin][dc-robin] | 고블린 무리를 이끌며 동료를 던져 접근·포위를 만든다. | 본체까지 가는 동안 무리가 퍼지는 것을 막는다. |
| DC-U06 | [Eustachio][dc-eustachio] | 반복 소환으로 숫자를 늘리며 자신의 생존을 도모한다. | 부하를 모두 잡아야 한다는 생각에서 벗어난다. |
| DC-U07 | [Blorkula the orcula][dc-blorkula-the-orcula] | 치명상을 받으면 박쥐 무리로 분산된다. 박쥐를 정리하지 못하면 재결합해 전투를 이어간다. | 본체를 쓰러뜨린 뒤에도 분산 목표를 처리할 자원을 남긴다. |
| DC-U08 | [Jeremiah][dc-jeremiah] | 나비를 계속 만들고 거리를 벌리며 Smiting으로 압박한다. | 사격을 방해하는 나비와 본체 접근을 함께 해결한다. |
| DC-U09 | [Maggie][dc-maggie] | 매혹으로 이탈을 제한하면서 화염 마법을 사용한다. | 후퇴를 시작하기 전에 이동 제한을 고려한다. |
| DC-U10 | [Harold][dc-harold] | 끌어당기기와 표식을 사용한다. | 본체와의 일대일이 주변 적의 합류전으로 바뀌는 것을 경계한다. |

### 6.2 중후반의 제어·기동·변신형 네임드

| ID | 네임드 | 핵심 패턴·변화 | 요구하는 대응·판단 |
|---|---|---|---|
| DC-U11 | [Sonja][dc-sonja] | 순간이동·독성 원거리 수단·위험한 근접 무기를 결합하는 암살자다. 장비에 따라 위협이 달라진다. | 낮은 체력만 보고 안전하다고 판단하지 않는다. |
| DC-U12 | [Nessos][dc-nessos] | 가속하고 순간이동으로 거리를 벌리며 강한 독성 사격을 한다. | 열린 공간에서 추격전을 벌이지 않는다. |
| DC-U13 | [Aizul][dc-aizul] | 수면과 강한 독 마법을 결합한다. | 행동 불능과 지속 피해가 겹치는 상황을 막는다. |
| DC-U14 | [Rupert][dc-rupert] | 마비·혼란을 일으키는 외침과 광폭화를 사용한다. | 제어를 당한 뒤 광폭 근접 공격을 허용하지 않는다. |
| DC-U15 | [Kirke][dc-kirke] | 대상을 돼지로 변신시켜 평소 기능을 제한하고 소환·둔화·투명화로 전투를 유지한다. | 변신 중 사용할 수 있는 대안을 확보한다. |
| DC-U16 | [Nikola][dc-nikola] | 강력한 연쇄 번개와 위치 변경을 사용한다. | 전기 방어와 시야 노출 시간을 함께 관리한다. |
| DC-U17 | [Roxanne][dc-roxanne] | 움직이지 않는 강력한 포대. 대상을 가까이 끌어오는 순간이동 주문을 사용한다. | 사거리 밖에서 무시할지, 준비해서 교전할지 선택한다. |
| DC-U18 | [Jorgrun][dc-jorgrun] | 뿌리 구속·석화·굴착·대지 마법을 결합한다. | 발이 묶인 채 지형 폭발을 받지 않도록 한다. |
| DC-U19 | [Mara][dc-mara] | 자기 분신과 플레이어 또는 강한 동료의 환영을 만든다. 화염 마법과 순간이동도 사용한다. | 자기 빌드가 적에게 복제되는 위험을 계산한다. |
| DC-U20 | [Mennas][dc-mennas] | 빠른 근접 전투에 침묵·혼란·회복을 결합한다. | 주문·두루마리에 의존한 평소 대응이 막혔을 때의 수단을 준비한다. |
| DC-U21 | [Bai Suzhen][dc-bai-suzhen] | 전반의 소환 중심 전투에서, 피해를 받으면 폭풍을 두른 용 형태로 변한다. | 전반의 접근 방식이 후반에도 유효한지 다시 판단한다. |
| DC-U22 | [Vashnia][dc-vashnia] | 저격수 부대를 이끌고 자신과 동료의 순간이동으로 사격 거리를 유지한다. | 한 명을 따라가다 다른 사수들의 사선에 들어가지 않는다. |
| DC-U23 | [Boris][dc-boris] | 강력한 마법사이며 쓰러뜨려도 이후 새로 생성되는 층에서 재등장할 수 있다. | 이번 처치와 탐험 전체의 영구 제거를 구분한다. |

### 6.3 룬 수호자·최상위 보스급 유니크

이 절의 적들도 모두 단계제 보스는 아니다. 특히 ‘지옥 군주’라는 분류가 같은 패턴을 공유한다는 뜻은 아니다.

| ID | 적 | 핵심 패턴 | 요구하는 대응·판단 |
|---|---|---|---|
| DC-L01 | [The Royal Jelly][dc-royal-jelly] | 피해를 받으면 강한 젤리들을 배출하고 그 뒤로 물러설 수 있다. 생성된 젤리는 본체를 죽여도 사라지지 않는다. | 보스에게 넣는 피해량과 늘어나는 적을 함께 처리한다. |
| DC-L02 | [Geryon][dc-geryon] | 뿔피리로 Sin beast를 반복해서 소환한다. | 소환물을 잡는 소모전보다 본체 처리와 전장 분리를 고려한다. |
| DC-L03 | [Antaeus][dc-antaeus] | 거대한 내구력·근접 압박에 냉기와 번개를 결합한다. | 복잡한 페이즈보다 접근 허용 시간과 지속 전투 자원이 시험된다. |
| DC-L04 | [Asmodeus][dc-asmodeus] | 화염·Damnation과 Hellfire Court를 결합한다. | 화염 저항만으로 막을 수 없는 피해와 추가 전장 위협에 대비한다. |
| DC-L05 | [Dispater][dc-dispater] | 강한 물리성 마법·Damnation·Hell sentinel 소환을 결합한다. | 한 종류 방어에만 투자해도 되는지 판단한다. |
| DC-L06 | [Ereshkigal][dc-ereshkigal] | Torment·마비·침묵·소환·위기 시 회복을 가진다. | 생존 수단이 봉인된 상태에서 행동 불능까지 겹치는 것을 피한다. |
| DC-L07 | [Cerebov][dc-cerebov] | 강력한 근접 무기, 가속, Fire Storm과 Hellfire Court를 사용한다. | 근접·원거리 양쪽의 큰 피해와 전장 압박을 함께 감당한다. |
| DC-L08 | [Lom Lobon][dc-lom-lobon] | 구형 번개·광역 냉기·소용돌이에 회복과 거리 벌리기를 결합한다. | 추격과 순간 화력, 위험 구역 회피 사이에서 균형을 잡는다. |
| DC-L09 | [Gloorx Vloq][dc-gloorx-vloq] | 독·독성 구름·Torment·Executioner 소환을 사용한다. 언데드 상대로는 별도 강한 공격 수단이 있다. | 종족·형태에 따라 달라지는 위협과 빠른 증원을 고려한다. |
| DC-L10 | [Mnoleg][dc-mnoleg] | 여러 종류의 소환, 혼돈 강화, 지형 변경으로 전장을 복잡하게 만든다. | 부하를 전부 처리하기보다 전투가 통제 불능이 되기 전에 끝내거나 이탈한다. |

The Royal Jelly의 생성물과 후퇴에 대해서는 [0.34 기준 개별 설명](https://dcss.roguelikes.gg/wiki/TRJ)도 참고했다. DCSS 보스들의 주문 이름은 [공식 버전별 주문 구성][dc-spells]으로 대조했다.

## 7. 보스 패턴만 압축해서 비교

다음은 앞의 사실을 설계 관점에서 다시 묶은 것이다. 원작의 정식 분류명이 아니다.

| 패턴 구조 | 기존 사례 | 전환을 만드는 조건 |
|---|---|---|
| 예고 → 회피 → 공격 재개 | Goo, Evil Eye, Ripper Demon | 준비 동작과 타격 시점 |
| 돌진 → 빗나감/접촉 → 재정렬 | boulder beetle | 거리와 이동 경로 |
| 강타 → 긴 빈틈 | bunyip | 자신의 공격 직후 |
| 본체 무적 → 장치 파괴 → 본체 취약 | DM-300 | 누적 피해와 활성 발전 장치 |
| 본체 보호 → 지정 부하 처치 → 보호 해제 | Dwarf King | 단계 전환과 부하 사망 |
| 부위 출현 → 분리·처치 → 본체 공격 | Yog-Dzewa | 체력 구간과 주먹 생존 여부 |
| 전사+마법사 → 한쪽 사망 → 생존자 강화 | Duvessa & Dowan | 동료 사망 |
| 본체 치명상 → 다수의 작은 목표 → 재결합 또는 처치 | Blorkula | 치명상과 분산 개체 생존 |
| 평상형 → 다른 전투 규칙의 변신형 | Bai Suzhen | 피해·체력 상태 |
| 피격 → 적 생성 → 본체 뒤로 이동 | The Royal Jelly | 보스에게 가한 피해 |
| 분신 생성 → 플레이어 빌드가 적의 위협으로 전환 | Mara | 환영 생성 |
| 부하 소환 → 장기전일수록 전장 악화 | Geryon, Mnoleg, Necromancer | 시간과 소환 기회 |
| 평소 기능 봉인 → 대체 수단으로 생존 | Kirke, Mennas | 변신·침묵 등 상태 적용 |

## 8. 자료를 다시 확인할 때

공식 릴리스: [DCSS 0.34.1](https://github.com/crawl/crawl/releases/tag/0.34.1), [Shattered v3.3.8](https://github.com/00-Evan/shattered-pixel-dungeon/releases/tag/v3.3.8).

각 행의 몬스터 이름은 해당 버전에 고정한 공식 소스로 연결된다. DCSS의 개체 정의 파일은 종·기본 특성·주문 집합을 지정하므로, 실제 특수 동작은 주문 구성과 실행·행동·사망 처리 자료를 함께 읽어야 한다. Shattered 역시 본체와 소환물·전장 장치의 규칙이 여러 파일에 나뉘어 있다.

세부 확률·수치·특수 아이템과의 모든 상호작용은 이 문서의 범위 밖이다. 실제 기획으로 옮길 때에는 **예고의 가시성, 피할 수 있는 시간, 회피 수단, 반복 제한, 처치·철수 뒤 정리 규칙**을 각 패턴별로 다시 확인해야 한다.


[dc-abilities]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/mon-abil.cc
[dc-act]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/mon-act.cc
[dc-aizul]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/aizul.yaml
[dc-antaeus]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/antaeus.yaml
[dc-asmodeus]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/asmodeus.yaml
[dc-bai-suzhen]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/bai-suzhen.yaml
[dc-basilisk]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/basilisk.yaml
[dc-bloated-husk]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/bloated-husk.yaml
[dc-blorkula-the-orcula]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/blorkula-the-orcula.yaml
[dc-boggart]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/boggart.yaml
[dc-boris]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/boris.yaml
[dc-boulder-beetle]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/boulder-beetle.yaml
[dc-bunyip]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/bunyip.yaml
[dc-cast]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/mon-cast.cc
[dc-catoblepas]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/catoblepas.yaml
[dc-centaur]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/centaur.yaml
[dc-cerebov]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/cerebov.yaml
[dc-death]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/mon-death.cc
[dc-dispater]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/dispater.yaml
[dc-dream-sheep]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/dream-sheep.yaml
[dc-duvessa]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/duvessa.yaml
[dc-elephant]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/elephant.yaml
[dc-entropy-weaver]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/entropy-weaver.yaml
[dc-ereshkigal]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/ereshkigal.yaml
[dc-eustachio]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/eustachio.yaml
[dc-flayed-ghost]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/flayed-ghost.yaml
[dc-geryon]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/geryon.yaml
[dc-gloorx-vloq]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/gloorx-vloq.yaml
[dc-grinder]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/grinder.yaml
[dc-guardian-serpent]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/guardian-serpent.yaml
[dc-harold]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/harold.yaml
[dc-hellion]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/hellion.yaml
[dc-hydra]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/hydra.yaml
[dc-ironbound-convoker]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/ironbound-convoker.yaml
[dc-ironbound-frostheart]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/ironbound-frostheart.yaml
[dc-ironbound-preserver]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/ironbound-preserver.yaml
[dc-jeremiah]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/jeremiah.yaml
[dc-jorgrun]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/jorgrun.yaml
[dc-kirke]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/kirke.yaml
[dc-lom-lobon]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/lom-lobon.yaml
[dc-maggie]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/maggie.yaml
[dc-mara]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/mara.yaml
[dc-menkaure]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/menkaure.yaml
[dc-mennas]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/mennas.yaml
[dc-merfolk-siren]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/merfolk-siren.yaml
[dc-mnoleg]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/mnoleg.yaml
[dc-moth-of-wrath]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/moth-of-wrath.yaml
[dc-nessos]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/nessos.yaml
[dc-nikola]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/nikola.yaml
[dc-orb-of-fire]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/orb-of-fire.yaml
[dc-orb-spider]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/orb-spider.yaml
[dc-orc-priest]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/orc-priest.yaml
[dc-orc-wizard]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/orc-wizard.yaml
[dc-quicksilver-dragon]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/quicksilver-dragon.yaml
[dc-robin]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/robin.yaml
[dc-roxanne]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/roxanne.yaml
[dc-royal-jelly]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/royal-jelly.yaml
[dc-rupert]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/rupert.yaml
[dc-shining-eye]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/shining-eye.yaml
[dc-sigmund]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/sigmund.yaml
[dc-sonja]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/sonja.yaml
[dc-spells]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/mon-spell.h
[dc-starcursed-mass]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/starcursed-mass.yaml
[dc-swamp-worm]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/swamp-worm.yaml
[dc-thorn-hunter]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/thorn-hunter.yaml
[dc-tormentor]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/tormentor.yaml
[dc-torpor-snail]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/torpor-snail.yaml
[dc-unseen-horror]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/unseen-horror.yaml
[dc-vashnia]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/vashnia.yaml
[dc-vault-warden]: https://raw.githubusercontent.com/crawl/crawl/0.34.1/crawl-ref/source/dat/mons/vault-warden.yaml
[sp-ArmoredBrute]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/ArmoredBrute.java
[sp-Bat]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Bat.java
[sp-Brute]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Brute.java
[sp-Crab]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Crab.java
[sp-CrystalGuardian]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/CrystalGuardian.java
[sp-DM200]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/DM200.java
[sp-DM201]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/DM201.java
[sp-DM300]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/DM300.java
[sp-DemonSpawner]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/DemonSpawner.java
[sp-DwarfKing]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/DwarfKing.java
[sp-EbonyMimic]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/EbonyMimic.java
[sp-Elemental]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Elemental.java
[sp-Eye]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Eye.java
[sp-FetidRat]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/FetidRat.java
[sp-Ghoul]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Ghoul.java
[sp-GnollGeomancer]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/GnollGeomancer.java
[sp-GnollTrickster]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/GnollTrickster.java
[sp-GoldenMimic]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/GoldenMimic.java
[sp-Golem]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Golem.java
[sp-Goo]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Goo.java
[sp-GreatCrab]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/GreatCrab.java
[sp-Guard]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Guard.java
[sp-Mimic]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Mimic.java
[sp-Monk]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Monk.java
[sp-Necromancer]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Necromancer.java
[sp-Pylon]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Pylon.java
[sp-RipperDemon]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/RipperDemon.java
[sp-RotHeart]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/RotHeart.java
[sp-RotLasher]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/RotLasher.java
[sp-Scorpio]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Scorpio.java
[sp-Shaman]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Shaman.java
[sp-Skeleton]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Skeleton.java
[sp-Slime]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Slime.java
[sp-Snake]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Snake.java
[sp-SpectralNecromancer]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/SpectralNecromancer.java
[sp-Spinner]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Spinner.java
[sp-Succubus]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Succubus.java
[sp-Swarm]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Swarm.java
[sp-Tengu]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Tengu.java
[sp-Thief]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Thief.java
[sp-Warlock]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/Warlock.java
[sp-YogDzewa]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/YogDzewa.java
[sp-YogFist]: https://raw.githubusercontent.com/00-Evan/shattered-pixel-dungeon/v3.3.8/core/src/main/java/com/shatteredpixel/shatteredpixeldungeon/actors/mobs/YogFist.java
