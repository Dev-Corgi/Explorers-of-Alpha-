# true_patches JIT 정적 분석 — 2026-10-06

현재 결론: true_patches의 특정 모듈을 Android melonDS JIT 크래시 원인으로 확정하지 못했다.
이전 한글 v5 변경으로 사용자가 보고한 크래시는 해결되지 않았다. ARM 명령 결과가 같다는
검증과 실제 melonDS JIT에서 게임이 정상 동작한다는 검증은 서로 다르다.

## 분석 대상과 범위

- 사용자 갱신 extracted와 일치하는 최신 full_stack+korean ROM에서 만든 jit_compat ROM.
- 적용 모듈 26개. 글리프 데이터 영역을 제외한 코드 cave 25개.
- 직접 분기 및 hook을 통해 도달할 가능성이 있는 ARM 명령 6,286개.
- 코드 cave를 가진 모듈 21개가 집계됨. 데이터 위주 모듈은 ARM cave 분석 대상이 아님.
- overlay 원시 데이터의 분기처럼 보이는 값도 진입점에 포함될 수 있는 보수적 분석이다.
- 간접 분기, 동적 포인터, 모든 호출의 레지스터 보존, 게임 상태, IRQ/타이밍,
  item_cd/waza_cd에서 실행 중 생성하는 코드를 완전히 증명하는 분석은 아니다.

## 패치 코드 점검 결과

이번 범위에서는 해석 불가능한 명령, PC 상대 비정렬 읽기, PC 상대 쓰기,
빈 레지스터 목록 및 비정상적인 block-transfer writeback 패턴을 발견하지 못했다.
제한적인 상수 주소 추적에서는 가변 쓰기 위치를 직접 PC 상대 리터럴로 읽는
중복 패턴도 발견하지 못했다. 따라서 한글과 같은 수정안을 모든 모듈에 일괄 적용할
근거는 현재 없다. 이 결과가 모든 메모리 접근이나 JIT 실행의 안전성을 보증하지 않는다.

상수 주소로 추적된 쓰기는 56곳/주소 39개이며, base_stats_speed, belly_union,
better_equipment, control_mode_enhance, orb_charges_v2, spinda_ev_speed,
tm_read, z_move_v2 등에 분포한다. 주소를 리터럴로 로드한 뒤 그 주소의 데이터를
레지스터를 통해 읽는 패턴은 데이터 자체를 상수로 읽는 것과 다르다.
코드와 데이터가 같은 메모리 페이지에 존재한다는 사실만으로 잘못된 코드라고 볼 수 없다.

## Android 2.0.1 PS와 공개 소스의 관계

공개 2.0.1 태그: https://github.com/rafaelvcaetano/melonDS-android/releases/tag/2.0.1
앱 commit: 5ec3648d68382dea9c17d6fbf02544e5c2c0afed
고정 라이브러리 commit: 654270ec019d7311366c5efc09bb1359e8c6223e

이 태그에 고정된 공개 코어를 따로 내려받아 대조했다. 사용자 Play Store APK 자체를
추출/검증한 것은 아니다. ARM64 ALU, 컴파일러, LoadStore와 ARMJIT.cpp는 로컬 master와
저작권 연도를 제외하면 동일했다. Memory.cpp에는 VRAM 동기화 등의 차이가 있으며,
명령 디코더에는 Thumb PC-relative load에 대한 한 가지 변경이 있었다. 우리 cave는 ARM이다.

## melonDS 코어에서 별도로 확인한 구현 문제

1. src/ARMJIT.cpp:943–967, InvalidateByAddr의 mask 변수 가림.
   외부 mask는 쓰기 위치의 16바이트 구간인데, 내부에서 block의 mask로 다시 선언한다.
   실제 판정은 blockMask & blockMask가 되어 같은 512바이트 범위의 무관한 block도
   무효화한다. 보수적인 과잉 무효화이므로 이것만으로 잘못된 게임 실행이나 현재
   크래시가 발생한다고 확정할 수 없다.

2. src/ARMJIT_A64/ARMJIT_LoadStore.cpp:214, FastMemory 정적 주소의 비정렬 word load.
   동적 주소에는 ARM의 rotate 동작을 적용하지만, 정적으로 알려진 주소에는 그 처리가
   빠져 있다. x64 구현에는 이 처리가 있다. 예를 들어 정렬 주소 word가 0x11223344이고
   주소+1을 읽으면 ARM9의 기대값은 0x44112233인데 이 ARM64 경로는 회전을 생략한다.
   이 감사의 상수 주소 분석에서는 우리 patch가 해당 비정렬 조건을 사용하는 위치를
   찾지 못했다. 따라서 현재 크래시의 원인으로 연결하지 않았다.

JIT_review_fixes.patch는 위 두 구현 문제에 대한 검토용 수정안이다. 원본 melonDS 소스나
APK에는 적용하지 않았다. C++ 컴파일 및 실제 JIT 실행을 검증한 패치도 아니다.

## 코드만으로 확정할 수 있는 것과 남는 것

코드만으로 명령 인코딩, 정렬, 상수 포인터, 특정 JIT 처리 누락은 찾을 수 있다.
현재처럼 JIT OFF는 정상이고 ON에서 여러 지점이 실패하는 문제는, 정적 코드 목록만으로
첫 잘못된 분기나 포인터를 확정할 수 없다. 하나의 선행 오류가 여러 후속 크래시를
만들 수도 있다. 필요할 때 실제 코어에서 최초 interpreter/JIT 상태 차이를 자동 기록해
원인을 좁히면 되며, 모든 크래시 장면을 사용자에게 나열하도록 요구할 필요는 없다.

사용자는 현재 코드 분석만 요청했다. 연결 기기는 ADB unauthorized였으며 휴대폰의
크래시 로그나 앱 데이터는 읽지 않았다. 이번 분석으로 추가 ROM 수정은 하지 않았다.

기계 판독 결과: ../true_patches_jit_audit.json
재실행 도구: ../audit_true_patches_jit.py
소스 버전 증거: provenance.json, source_comparison.json
