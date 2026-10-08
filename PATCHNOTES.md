# 패치노트

## damage_formula v5

탐험대 데미지·기술 위력·던지기 아이템을 9세대 본편 기준에 맞춘 통합 패치입니다.

### 시스템 변경

- 데미지 기본 공식 | 탐험대 전용 공식 → 본편식 `((2×레벨/5+2)×위력×공격÷방어÷50)+2` 후, 타입·STAB·급소·랜덤(±12.5%)은 기존과 동일하게 적용
- 적 포켓몬 공격 | 추가 보정 없음 → 아군이 아닌 공격자는 ×64/85 패널티
- **일반 공격** | 고정 데미지 처리 → 해당 포켓몬 기본 공격 위력의 **25%**로 계산
- **투사체** 데미지 | 계산 후 ×0.5 → ×1.0
- **급소·날씨 보정** | 일반 급소, 맑음+불꽃, 비+물 타입 | ×1.25 → ×1.5
- 기술 설명 **위력 별표** | 구간별 별 개수 → **20 위력당 ★1**, **10 위력당 ★½** (IQ와 같은 반별 표시)
- **돌멩이·자갈·희귀한 화석** | 고정 데미지 → 본편 데미지 공식을 거치는 투사체로 변경

### v5 추가 조정 (v4 대비)

- **Thrash** | 위력 120 → 50
- **Outrage** | 위력 120 → 50
- **Petal Dance** | 위력 120 → 50
- **Raging Fury** | 위력 120 → 50
- **Self-Destruct** | (고정 데미지) → 위력 **120**
- **Explosion** | 위력 250 → **150**

### 던지기·폭탄땅콩

| 아이템 | 변경 전 | 변경 후 |
| --- | --- | --- |
| 나뭇가지 | 1 | 20 |
| 철 가시 | 4 | 40 |
| 은 가시 | 8 | 60 |
| 선인장 가시 | 10 | 80 |
| 코산호 가지 | 15 | 100 |
| 금니 | 16 | 120 |
| 금 가시 | 16 | 120 |
| 돌멩이 | 10 | 20 |
| 자갈 | 20 | 40 |
| 희귀한 화석 | 80 | 120 |
| 폭탄땅콩 | 25 | 80 |

- **폭탄땅콩** | 고정 25 데미지 → 위력 80 투사체(본편 공식 적용)

---

## 밸런스

전투 IQ·방 전체 기술·상태이상·랭크 상한 등 던전 밸런스를 조정하는 패치 묶음입니다.

### iq_change v17

IQ 스킬·경험치 보너스·위협(IQ) 동작을 개편합니다.

- **Nonsleeper** → **Status-Resistence** | 수면 면역 → 상태이상에 걸리면 공격·특공·방어·특방 중 **랜덤 1종 +2단계**
- **Critical Dodger** | 급소 피해 배율 그대로 → 급소를 **일반 데미지의 120%**만 받음 (급소 배율·스나이퍼 무시)
- **Counter Basher** | 물리 반격(전액) → **물리 반격 없음**; 특수 공격을 맞으면 **반격 타격가와 같은 확률**로 받은 데미지의 **1/4** 반격
- **Intimidator** | 근접 기술 12% 위협 → **HP 1/4 미만**일 때만 근접 기술 **20%** 위협
- **Exp. Elite** | 경험치 받는 포켓몬만 → **파티 전원**에게 IQ 보너스 적용
- **Wonder Chest / Miracle Chest** | 지닌 포켓몬만 → **파티 전원**에게 가슴 보너스 적용
- **전용 아이템 경험치 부스트** | 개별 적용 → **파티 전원**에게 적용

### room_charge_pending v4

방 전체 2턴 기술(차지 → 발동)의 동작을 정리합니다.

- **1턴째(차지)** | 기술 효과 실행(0 데미지·빗나감 판정) → **준비만 하고 효과·데미지·부가효과 생략** (Wary Fighter 등 미발동)
- **2턴째(발동)** | (기존과 동일) → 저장된 기술로 **방 전체 정상 데미지**, PP는 **실질 −1**

### status_adjust v22

방어·견제 기술과 능력치 랭크 상한을 본편에 가깝게 맞춥니다.

- **Protect / Detect** | 지속 턴 랜덤 → **정확히 1턴**
- **Endure** | 지속 턴 랜덤 → **정확히 1턴**
- **Spite** | 마지막 기술 PP **0** → **절반(내림)**
- **Grudge** | 마지막 기술 PP **0** → **절반(내림)**
- **Reflect** | 받는 물리 데미지 **약 79.7%** → **33.3% (×1/3)**
- **Light Screen** | 받는 특수 데미지 **약 79.7%** → **33.3% (×1/3)**
- **능력치 랭크 상·하한** | ±10단계 (0~20) → **±6단계 (4~16, 본편 ±6)**

---

## 아이템

던전 아이템·구슬·베리·기술머신·포켓·지닌 도구 동작을 개편하는 패치 묶음입니다.

### 구슬

#### fixed_room_orbs v1

- **고정 방(이벤트·보스 방 등)** | 구슬 사용·워프·Trawl 불가 → **모든 고정 방에서 사용 가능**

#### orb_charges_v2 v14

- **다회 사용 구슬** | 1회 소모 → **최대 3회** (`Use(3)` / `Use(2)` / `Use(1)` 표시)

| 횟수 | 구슬 |
| --- | --- |
| **3회** | Aim Orb, Baton Orb, Blowback Orb, Charge Orb, Cure Orb, Decoy Orb, Evasion Orb, Gravity Orb, Hail Orb, Hurl Orb, Lure Orb, Mimic Orb, One-Shot Orb, Pounce Orb, Quick Orb, Radar Orb, Rainy Orb, Rollcall Orb, Safe Orb, Sandy Orb, Scanner Orb, See-Trap Orb, Shocker Orb, Slow Orb, Stayaway Orb, Sunny Orb, Switcher Orb, Terastal Orb, Transfer Orb, Trapbust Orb, Warp Orb, Wish Orb |
| **1회** | Cleanse Orb, Decay Orb, Diet Orb, Escape Orb, Heal Orb, Invisify Orb, Luminous Orb, Mobile Orb, One-Room Orb, PP-Save Orb, Petrify Orb, Poison Orb, Premier Gift, Protect Orb, Rebound Orb, Refresh Orb, Slumber Orb, Stairs Orb, Totter Orb, Trawl Orb, Weakness Orb |

- **세이브 프롬프트** | (변경 없음) → 가방·지닌 **충전 구슬 전부 최대 충전**
- **Rocky Orb** → **Baton Orb** | 같은 방 포켓몬 위치 교환
- **Snatch Orb** → **Decay Orb** | 같은 방 적 **방어·특방 −6**
- **Mug Orb** → **Refresh Orb** | 같은 방 아군 **상태이상 치료**
- **Lob Orb** → **Terastal Orb** | **Counter + Mirror Coat** 부여
- **Two-Edge Orb** → **Charge Orb** | **다음 턴 기술 위력 ×3**
- **Silence Orb** → **Protect Orb** | 같은 방 **팀 전체 Protect**
- **Drought Orb** → **PP-Save Orb** | **이 층 PP 소모 없음**
- **Identify Orb** → **Poison Orb** | **층 전체 적 독**
- **Sizebust Orb** → **Weakness Orb** | 같은 방 적 **공격·특공 −6** (이름만 변경)
- **Grudge Orb** → **Diet Orb** | 1회 사용, **이 층 포켓몬 배 고정**(걸음 소모 없음)
- **Longtoss Orb** → **Wish Orb** | 같은 방 아군 **HP 회복 가속**
- **Pierce Orb** → **Mimic Orb** | 앞 적 **마지막 기술 복사**
- **Health Orb** → **Heal Orb** | **날씨에 따라 HP 회복**(Moonlight)

### 베리

#### berry_boost v8

먹으면 상태이상 치료(또는 예방)와 함께 능력치가 오릅니다.

| 베리 | 변경 전 | 변경 후 |
| --- | --- | --- |
| Cheri Berry | 마비 치료 | 마비 치료 + **특공 +2** |
| Pecha Berry | 독 치료 | 독 치료 + **방어·특방 +2** |
| Rawst Berry | 화상 치료 | 화상 치료 + **공격 +2** |
| Chesto Berry | 수면 방지 | 수면 방지 + **회피 +2** |
| Aspear Berry | 동상 치료 | 동상 치료 + **명중 +2**, **급소율 상승** |

### 기술머신

#### tm_read v16

- **Read 메뉴** | (없음) → **Read(3) / Read(2) / Read(1)** 잔여 횟수 표시
- **TM 사용** | 1회 소모 → **최대 3회 Read** 후 소모
- **세이브 프롬프트** | (변경 없음) → 가방·지닌 **TM Read 충전 전부 회복**
- **Read 중** | (없음) → 임시 슬롯으로 기술 사용, 종료 후 원래 슬롯 복구

### 포켓

#### better_poke v1

- **바닥 Poke 줍기** | 배만 채움 → 줍은 포켓몬 **배 +5** (리더·동료 모두)

### 장비아이템

#### better_equipment v4

**팀 전체 보호** (파티원 1명만 지녀도 전원 적용)

- No-Stick Cap, Pecha Scarf, Persim Band, Weather Band, Insomniscope, Sneak Scarf, Trap Scarf, Twist Band
- Twist Band | 공격·특공 하락만 막음 → **방어·특방 하락도 추가 차단**
- Ability Monitor | (변경 없음) → **지닌 포켓몬 특성 발동 중지**

**스탯 밴드** (고정 수치 보너스 → **랭크 +2**, 기술 +6 상한 넘어서도 계산에 반영)

- Power Band | → **공격 +2랭크**
- Def. Band | → **방어 +2랭크**
- Special Band | → **특공 +2랭크**
- Zinc Band | → **특방 +2랭크**
- Lens Scarf | → **명중 +2랭크**
- Bright Ribbon | → **회피 +2랭크**

**지닌 도구 개편** (이름·효과 교체, 구 효과 제거)

| 변경 전 | 변경 후 | 효과 |
| --- | --- | --- |
| Lockon Specs | Life Band | 위력 ×1.5, 공격마다 **최대 HP 10%** 소모 |
| No-Aim Scope | Lens Scarf | 명중 +2랭크 |
| Bounce Band | Focus Scarf | **2배 이상** 데미지 → **70%**만 받음 |
| Gold Ribbon | Bright Ribbon | 회피 +2랭크 |
| Joy Ribbon | PP Scarf | **층 시작** 랜덤 기술 PP +1 |
| Whiff Specs | Wish Scarf | 공격 시 준 **데미지의 1/8 HP** 회복 |
| Patsy Band | Expert Band | **2배 효과** 기술 위력 ×1.5 |
| Curve Band | Z-Scarf | **Z 게이지 획득 ×2** (팀 전체) |
| Racket Band | Rhythm Scarf | 같은 공격 기술 반복 시 **+25%**, 최대 **×2** |
| Munch Belt | Consistent Band | **별효과 데미지 최소 보통**, 배 빨리 닳음 **없음** |

#### boost_ribbon v4

가방에서 **Boost** 메뉴로 지닌 도구를 소모해, Ingest와 같은 **팀원 선택** 후 해당 능력치 **+3** (세이브 프롬프트까지 유지).

| Boost | 대상 지닌 도구 |
| --- | --- |
| Hp Up | Diet Ribbon, Heal Ribbon, Friend Bow, Bright Ribbon, PP Scarf, Mobile Scarf, Ability Monitor, Stamina Band, Tight Belt, Wish Scarf |
| Atk Up | Power Band, Pass Scarf, Expert Band, Pierce Band, Scope Lens, X-Ray Specs, Lens Scarf |
| Def Up | Def. Band, No-Stick Cap, Pecha Scarf, Persim Band, Warp Scarf, Weather Band, Insomniscope |
| SpA Up | Special Band, Z-Scarf, Consistent Band, Rhythm Scarf, Sneak Scarf, Life Band |
| SpD Up | Zinc Band, Focus Scarf, Detect Band, Dodge Scarf, Trap Scarf, Twist Band, Goggle Specs |

---

## 기타 패치

상점·난이도·스토리·던전 편의·조작·특별 에피소드 등 주변 시스템을 다루는 패치 묶음입니다.

### shop_sell_price v1

- **케클론 상점 판매가** | (바닐라 고정값) → **구매가 ÷ 4** (유효숫자 2자리 내림)

### difficulty_unlock v1

- **Expert / Hardcore 난이도** | 다크라이 클리어 후 해금 → **처음부터 자유롭게 변경 가능**

### level_scaling_guest_fix v4

- **Level Scaling** | 게스트 포켓몬도 파티 최고 레벨에 맞춰 스케일 → **게스트는 스케일 대상에서 제외** (스토리 동반 포켓몬 레벨 오류 방지)

### no_immediate_house v1

- **층 입장 시 몬스터하우스** | 리더 스폰 위치가 몬스터하우스면 **즉시 발동** → **해당 방 몬스터하우스 비활성화**
- **도적 아지트** | (변경 없음) → 몬스터하우스 **정상 발동**
- **다른 방 몬스터하우스** | (변경 없음) → 들어가면 **정상 발동**

### cutscene_bug_fix v3

- **스토리 구간(8-1~8-3) 저녁 식사** | Team Skull 식사 **미표시** → **정상 재생**
- **일일 컷신 ON/OFF와 저녁 식사** | 플래그 반대로 동작 → **컷신 ON이면 식사 재생, OFF면 생략** (Sky와 동일)

### balance_change v1

**Bidoof's Wish** 특별 에피소드 기술 구성을 조정합니다 (배우 목록·습득 테이블은 그대로).

| 대상 | 변경 전 | 변경 후 |
| --- | --- | --- |
| 비두프 (주인공) | Tackle, Growl | **Quick Attack, Iron Tail, Dig, Swagger** |
| 눈쓰 (동반·보스) | Powder Snow, Icy Wind, Grass Whistle, Swagger | **Ice Beam, Razor Leaf, Icy Wind, Grass Whistle** |

### control_mode_enhance v4

- **수동 조작 모드 + Select** | 카메라 모드만 → **비리더 턴에 Select** 누르면 **그 포켓몬이 리더** (`"<이름> is now leader"` 메시지)
- **수동 모드 Select** | 카메라 열림 → **카메라 비활성** (자동 모드에서만 카메라)
- **턴 순서** | Select로 리더 변경 시 순서 바뀜 → **라운드 시작 리더는 유지**, 해당 턴만 Select 리더로 조작 후 복귀

### belly_union v1

- **팀 배(Belly)** | 포켓몬마다 개별 → **팀 공유 1개** (리더 값 기준, 전원 동기화)
- **음식·배 관련 아이템** | 개별 적용 → **공유 배에 반영**
- **턴마다 걸음 소모** | 멤버마다 각각 → **리더(수동 모드에선 Select 리더)만** 1회
- **배 소모 지닌 도구** | 개별 계산 → **파티 전원 지닌 도구 합산** 후 1회 적용
- **Diet Orb 사용 층** | (없음) → **공유 걸음 소모 없음**

---

## Spinda EV (spinda_ev_v2 v8)

Spinda Cafe의 **EV(추가 스탯)** 시스템과 던전 일시 강화·초기화 규칙을 개편합니다.

### EV 상한 (레벨 연동)

- **스탯당 EV 상한** | (바닐라 고정) → **`⌊레벨÷10⌋ × 5`**
- **총 Earn EV 상한** | (바닐라 고정) → **`⌊레벨÷10⌋ × 13`**

| 레벨 | 스탯당 상한 | 총 EV 상한 |
| --- | --- | --- |
| 10 | 5 | 13 |
| 20 | 10 | 26 |
| 30 | 15 | 39 |
| 50 | 25 | 65 |
| 100 | 50 | 130 |

### Spinda Drink (카페)

- **스탯 선택 메뉴** | HP / Atk … | → **HP(0), Atk(3)**처럼 **현재 EV(V) 표시**
- **포켓몬 요약 화면** | 스탯만 표시 | → 각 스탯 옆 **(V숫자)** 표시
- **드링크 재료** | 전 종류 | → **타입별 Gummi만** (White~Silver, Mystic Gummi). **Wonder Gummi(136) 제외**
- **Miracle Drink 특수 결과** | IQ↑·배↑·랜덤 스탯↑ 등 | → **일반 드링크만** (포켓몬 영입·비밀 장소 등 **3·4·5번 결과는 유지**)

### 던전·세이브

- **Wonder Gummi (던전)** | IQ·배·랜덤 1스탯 | → 기존 효과 + **HP·공격·특공·방어·특방 +3** (해당 탐험 한정)
- **Life Seed / Protein / Iron / Calcium / Zinc / Wonder Gummi** | 탐험 후 유지 | → **세이브 프롬프트 시 제거**
- **Spinda Drink EV·레벨업 스탯** | (변경 없음) → **영구 유지**
- **Gummi IQ·배 효과** | (변경 없음) → **유지**

### 연동

- **boost_ribbon** Boost +3 | 세이브까지 유지 | → Spinda EV와 동일하게 **세이브 프롬프트에서 초기화**
