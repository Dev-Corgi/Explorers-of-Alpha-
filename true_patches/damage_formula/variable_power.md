# 가변 위력 기술의 실제 계산

Explorers of Sky(US) `overlay29` 핸들러가 넣는 숫자다. `damage_formula` v8이 Psywave, Present, Magnitude, Natural Gift의 아래 숫자를 바꾼다. 그 네 기술 외에는, `waza_p` 기본 위력을 Natural Gift만 읽는다.

숫자는 두 갈래로 들어간다.

- **고정 대미지.** `CalcDamageFixed`에 넘어가는 값이다. 공격÷방어 공식을 타지 않는다. 기술의 타입은 같이 전달된다.
- **공식에 넣는 위력.** 공격÷방어 공식(`CalcDamage`)의 위력 자리에 들어가는 값이다.

HP는 몬스터 구조체 `+0x10`, 레벨은 `+0x0A`(바이트), IQ는 `+0x0E`(부호 있는 16비트)다. 최대 HP는 `+0x12`와 `+0x16`을 더한 값이고, 999를 넘기면 999다.

## 고정 대미지

| 기술 | 대미지 |
|---|---|
| Sonic Boom | 20 |
| Dragon Rage | 30 |
| Seismic Toss | 사용자의 레벨 |
| Night Shade | 사용자의 레벨 |
| Super Fang | 대상의 현재 HP ÷ 2. 결과가 0이면 실패한다 |
| Endeavor | 대상 HP − 사용자 HP. 0 미만이면 0. 그 앞의 판정이 참이면 맞는 대상을 사용자로 바꾼다 |
| Fissure, Guillotine, Horn Drill, Sheer Cold | 명중 판정을 통과하면 9999 |
| Self-Destruct, Explosion | 반경 2. 반경별 고정 표가 40, 40, 80이라 반경 2는 80이다. 전용 도구 경감은 이 함수 안에서 따로 빠질 수 있다 |
| Bide, Revenge, Avalanche | 사용 순간에는 충전 상태만 건다. 풀릴 때 맞아 쌓인 값(`+0xB8`)의 2배, 상한 999 |

### Return (IQ가 낮을수록 작은 값)

기본값은 1이다. IQ가 처음 만족하는 칸의 대미지를 쓰고 멈춘다.

| IQ 미만 | 대미지 |
|---|---|
| 50 | 5 |
| 100 | 10 |
| 200 | 15 |
| 300 | 20 |
| 400 | 25 |
| 500 | 30 |
| 600 | 35 |
| 700 | 40 |
| 800 | 45 |
| 1000 | 45 |
| 10000 | 9999 |

IQ가 10000 이상이면 표가 끝나고 기본값 1이 남는다.

### Frustration (IQ가 낮을수록 큰 값)

| IQ 미만 | 대미지 |
|---|---|
| 0 | 9999 |
| 50 | 45 |
| 100 | 40 |
| 200 | 35 |
| 300 | 30 |
| 400 | 25 |
| 500 | 20 |
| 600 | 15 |
| 700 | 10 |
| 1000 | 5 |
| 10000 | 1 |

IQ는 0 미만이 되지 않으므로 첫 칸(9999)은 쓰이지 않는다. 0이면 45다.

## 공식에 넣는 위력

### Psywave

`x`는 1 이상 10 이하의 난수다. 나눗셈은 정수다. 레벨이 10 미만이면 위력은 0이다.

```
위력 = (x + 5) × (레벨 / 10)
```

### Magnitude

미리 굴려 둔 인덱스 0~6이 위력을 고른다.

| 인덱스 | 위력 |
|---|---|
| 0 | 10 |
| 1 | 30 |
| 2 | 50 |
| 3 | 70 |
| 4 | 90 |
| 5 | 110 |
| 6 | 150 |

대상 몬스터 `+0xD2` 바이트가 10이면 이 위력을 2배한다.

### Present

0~99 난수.

| 난수 | 결과 |
|---|---|
| 0–9 | 위력 120 |
| 10–29 | 회복. (최대 HP) ÷ 4 |
| 30–59 | 위력 80 |
| 60–99 | 위력 40 |

### Natural Gift

나무열매(또는 같은 표의 씨앗)를 들고 있으면

```
위력 = waza_p 기본 위력 + 표의 가산값
타입 = 표의 타입
배율 = 1.0
```

지금 빌드의 기본 위력은 80이다. Alpha 원본은 1이었다. 해당 도구가 없으면 가산 없이 기본 위력만 쓰고 타입도 바꾸지 않는다.

| 도구 | 타입 | 가산 |
|---|---|---|
| Heal Seed | Grass | 10 |
| Oran Berry | Poison | 10 |
| Sitrus Berry | Psychic | 30 |
| Eyedrop Seed | Ghost | 20 |
| Reviver Seed | Ground | 10 |
| Blinker Seed | Dark | 20 |
| Doom Seed | Steel | 10 |
| X-Eye Seed | Dark | 20 |
| Life Seed | Fighting | 30 |
| Rawst Berry | Grass | 20 |
| Hunger Seed | Rock | 50 |
| Quick Seed | Flying | 20 |
| Pecha Berry | Electric | 20 |
| Cheri Berry | Fire | 20 |
| Totter Seed | Ghost | 20 |
| Sleep Seed | Ice | 20 |
| Plain Seed | Normal | 70 |
| Warp Seed | Psychic | 20 |
| Blast Seed | Dragon | 50 |
| Joy Seed | Normal | 30 |
| Chesto Berry | Water | 20 |
| Stun Seed | Bug | 20 |
| Golden Seed | Dragon | 70 |
| Vile Seed | Poison | 50 |
| Pure Seed | Water | 50 |
| Violent Seed | Fighting | 50 |
| Vanish Seed | Bug | 50 |
| Dropeye Seed | Ghost | 20 |
| Reviser Seed | Ground | 70 |
| Slip Seed | Ice | 20 |
| Via Seed | Poison | 20 |
| Oren Berry | Poison | 50 |
| Dough Seed | Steel | 10 |

## 위력 숫자가 없는 것

- **Pain Split.** 둘의 현재 HP를 더해 2로 나눈 값으로 맞춘다. 각자의 최대 HP, 상한 999를 넘기지 않는다.
- **Nature Power.** 던전 번호(0 미만은 0, 199 이상이면 198)가 기술을 고르고, 그 기술의 핸들러가 실행된다. 번호별 횟수는 이렇다. Earthquake 44, Rock Slide 64, Tri Attack 24, Hydro Pump 6, Blizzard 3, Ice Beam 21, Seed Bomb 31, Mud Bomb 6.
- **Beat Up.** 대미지를 계산하지 않는다. 조건에 맞는 동료를 대상 위치로 워프한다.
- **Knock Off.** `DealDamage`를 부르지 않는다. 대상이 든 도구를 떨어뜨린다.
- **Counter, Mirror Coat, Metal Burst, Pursuit, Payback.** 사용 함수는 되받아치는 상태만 건다. 위력 숫자는 여기 없다.
- **Fling.** 효과 함수 목록에 전용 핸들러가 없고, 기본 위력은 0 그대로다.
