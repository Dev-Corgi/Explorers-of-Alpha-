# 스프라이트 코드 훼손 추적 — 2026-10-15

작성자를 찾거나 최신 ROM의 기기 증상을 해결한 결과가 아니다.
기존 상태 파일의 코드 차이가 실제 픽셀 오류를 만드는지 재현하고,
현재 ROM과 비교 가능한 자료인지 구분한 조사다. 런타임/이미지는 수정하지 않았다.

## 재현한 경로

`trace_sprite_corruption.py`는 현재 ROM의 native `0201AB0C`를 실행한다.
type 2 업로드는 `0201AB74` → ITCM `01FF80B0`으로 진행한다.
입출력/descriptor/stack은 테스트 메모리지만, 픽셀 변환 코드는 원래 ARM 코드다.
특성 코드, 메가 로더, WAN 디코더, allocator는 이 재현에서 호출하지 않는다.

ITCM `01FF80D8`의 정상 명령은 `E1A04204` (`LSL r4,r4,#4`)다.
이를 기존 상태 파일에서 발견한 값 `00000004`로 바꾸면, 같은 입력에서
다음 결과가 나온다. 이는 원인 추적용 에뮬레이션 안에서만 바꾸며 ROM은 수정하지 않는다.

| 입력 4bpp | 정상 8bpp | 훼손된 코드의 8bpp |
| --- | --- | --- |
| `D4 21` | `04 0D 01 02` | `D4 00 01 02` |

0–255 전체 입력값과 출력 양끝 canary를 검증했다. 16비트 입력의 앞쪽
바이트에 해당하는 두 픽셀이 잘못 변환되고 뒤쪽 두 픽셀은 정상이다.
일정 간격의 세로줄과 부합하는 오류이며 메가 전용 그림 없이도 재현된다.
단, 실제 화면의 모든 세로줄이 이 원인이라는 뜻은 아니다.

## 확보된 상태 파일

무시되는 `.cache/dungeon_debug/state0.bin`–`state3.bin`을 읽기만 했다.
파일 크기 5,690,006, main RAM 시작 328,231, ITCM 시작 4,522,535인
기존 expanded Complete 형식에만 적용한다. 코드 anchor도 검사한다.

| 파일 | 16KiB ITCM의 현재 ROM 대비 차이 | native 업로드 결과 |
| --- | --- | --- |
| state0 | `01FF80D8` 한 명령만 `00000004` | 오류 재현 |
| state1 | 동일 | 오류 재현 |
| state2 | 없음 | 정상 |
| state3 | 없음 | 정상 |

**훼손된 state0/1의 이미지 자료는 현재 ROM과 다르다.** 실제 WAN manager의
pack 0/index 959는 state0에서 91,568바이트인데 현재 ROM에서는 26,160바이트다.
index 1289도 상태 파일의 20,048바이트와 현재 ROM의 26,160바이트가 다르다.
따라서 이 자료로 현재 포즈 공유 아우라의 새 실행에서도 같은 훼손이
발생했다고 단정할 수 없다. state2/3에는 이 비교 대상의 새 그림이 없으므로
이미지 크기 비교만으로 두 파일의 ROM 버전을 확정하지 않는다.

현재 영문 ROM SHA256은 `7b27346a80e265346e14166ef23de71bdd7968a585c477a0cab90bb5cb4631cc`,
한글은 `44fed2763f3fee267d3dff136a3c16b03cafad46689cf8756bb38d7d7ff86b32`다.

## 메모리와 작성자 추적

native allocator의 block+4 내부 flags bit 0을 기준으로 실제 arena를 읽었다.
block+0의 content flags로 빈 블록을 판정하면 일반 할당도 빈 공간으로 세므로 잘못된다.

| 파일 | 기본 arena 빈 공간 | 최대 연속 빈 공간 |
| --- | ---: | ---: |
| state0 | 282,668 | 262,756 |
| state1 | 266,600 | 266,188 |
| state2 | 58,004 | 54,620 |
| state3 | 21,720 | 18,748 |

state3의 별도 ground arena에는 381,480바이트의 연속 빈 공간이 있었다.
기본 arena만 부족하고 다른 arena에는 여유가 있을 수 있으므로, 전체 빈 RAM의
합이나 ROM 파일 크기만으로 할당 성공을 판단하면 안 된다. 이 값들은 과거
한 시점의 값이고, 최신 ROM의 최대 사용량/할당 실패/메모리 누수를 증명하지 않는다.
정지 화면에서 스프라이트가 새는 현상도 heap 누수가 입증됐다는 뜻은 아니다.

ITCM 복사 명령의 위치는 main RAM이 아니다. `020B3380`의 ROM 원본은 부팅 시
ITCM으로 복사된 후 그 RAM 자리가 allocator 자료로 재사용된다. 상태 파일에서
그 RAM을 실행 코드와 직접 비교하면 정상적인 allocator 쓰기를 코드 훼손으로
오인한다. 실제 비교는 별도로 저장된 ITCM 16KiB에 대해 수행했다.

다음 실행의 watchpoint는 **ITCM 미러 전체**를 포함해야 한다.
`address < 02000000`이고 `(address & 7FFF)`가 `00D8`–`00DB`에 해당하는
쓰기를 잡고, 작성 명령의 PC/LR/주소/값/레지스터와 직전 호출을 기록해야 한다.
`000000D8`이나 `000080D8`에 대한 잘못된 포인터 쓰기도 같은 ITCM을 덮을 수 있다.
이는 후보 경로이며 null pointer 쓰기를 실제로 잡았다는 주장은 아니다.
이미 훼손된 상태 파일에는 과거의 작성 명령/호출 기록이 남아 있지 않다.
새 진단의 native 업로드 실행 중에는 해당 위치에 쓰기가 발생하지 않았다.

현재 ADB 기기 목록은 비어 있었다. 최신 ROM을 새로 시작한 후 재현하는 실행이나
문제 전후의 최신 상태 파일은 확보하지 못했다. 임의로 복사 명령을 매 프레임
복구하거나 다른 코드로 우회하면 작성자 추적을 방해하므로 추가하지 않았다.

## 실행과 검증

```powershell
.venv\Scripts\python.exe -B -m true_patches.mega_evolve.trace_sprite_corruption
.venv\Scripts\python.exe -B -m true_patches.mega_evolve.trace_sprite_corruption --state true_patches/mega_evolve/.cache/dungeon_debug/state0.bin --state true_patches/mega_evolve/.cache/dungeon_debug/state1.bin --state true_patches/mega_evolve/.cache/dungeon_debug/state2.bin --state true_patches/mega_evolve/.cache/dungeon_debug/state3.bin --report true_patches/mega_evolve/.cache/dungeon_debug/corruption_report.json
```

`--rom`으로 영문 ROM도 검사했다. 양쪽의 native 256값 변환과 훼손 재현,
상태 파일 4개의 코드/arena/실제 이미지 크기 비교가 통과했다.
기존 `verify_actor_sprite_cache`, `verify_aura_loading`도 통과했다. 후자의
동시 sprite 351,980바이트는 allocator 모델의 값이며 전체 게임 RAM 실측이 아니다.
ROM/세이브/상태 파일 출력 및
풀스택 빌드는 하지 않았다. 최신 게임 플레이 정상화와 작성자 특정은 미완료다.

## 추가 제공된 Complete_0.dss 조사

이 절은 위의 "최신 상태 파일 미확보" 이후 사용자가 추가 제공한 파일의 결과다.
원본 DSS SHA256은 `3907ebe92595273e0528d7404c72698f54a4ced6bf5539c23390e7a0d50de354`,
압축 해제 데이터 SHA256은 `d9ccfc7f3ca8e5804ed6c9788c046d91336bbba117c2f6d4d0271e5e0b0ac41c`다.
원본은 1,516,106바이트, 버전15 헤더68바이트 뒤의 zlib 자료다.
도구가 DSS를 직접 읽도록 확장했고 원본과 ROM의 실행 전후 바이트를 비교한다.

이번 파일에도 ITCM의 차이는 `01FF80D8 = 00000004` 한 명령이다.
native 업로드 결과는 다시 `D4 00 01 02`로 깨진다. 이전 파일과 달리 현재 ROM과
MD 전체 199,324바이트가 일치하며, 현재 runtime 파일의 헤더도 RAM에서 찾았다.
파일의 마지막 비영 워드까지 재배치한 앞부분36,784바이트가 RAM과 일치한다.
그 뒤의 zero-filled 상태 영역은 게임 중 바뀌므로 코드 훼손으로 세지 않는다.
이 비교는 초기화된 prefix 비교이며 ELF section 경계 판독을 대신하지 않는다.

현재 ROM의 pack을 풀고, 실제 RAM 주소에 native SIR0 초기화를 실행한 뒤
그 결과를 상태 파일의 버퍼와 전부 비교했다.

| apparent 종 ID | WAN 슬롯 | pack/index | 버퍼 크기 | 현재 ROM 복원 결과 |
| --- | ---: | --- | ---: | --- |
| 2065 | 76 | 0/1289 | 26,160 | 전체 바이트 일치 |
| 1421 | 77 | 0/959 | 26,160 | 전체 바이트 일치 |
| 1625 | 78 | 0/1069 | 20,096 | 전체 바이트 일치 |

세 메가와 적 개체4마리 모두 entity의 슬롯, animation_control의 슬롯,
해당 슬롯의 sprite index와 MD가 일치한다. 이 순간에는 메가 WAN 버퍼의
손상이나 잘못된 캐시 슬롯 연결이 검출되지 않았다.

기본 arena는 총301,496바이트, 최대 연속300,268바이트가 비어 있다.
따라서 이 스냅샷만으로 당장의 메모리 고갈을 깨짐의 원인으로 설명할 수 없다.
이전 순간의 부족이나 다른 맵의 최대 부하까지 배제하는 결과는 아니다.

`--replay-cache`는 이 파일의 복사된 RAM에서 실제 던전 삭제/로딩 함수로
2065/1421/1625를 해제하고 다시 읽은 뒤 native actor refresh를 실행한다.
이번에는 기존 검증의 가상 allocator 대신 **상태 파일의 실제 arena 자료와
native 할당/해제 코드**를 실행했다. pack I/O와 allocator의 lock/unlock만
모델링했다. 실행 후 캐시는80/81/82에 다시 연결됐고 low-memory 쓰기는 없었다.
세 그림의 로드에는 각각 임시13,132/13,204/10,872바이트와 원본
26,160/26,160/20,096바이트 할당이 발생했고 임시 버퍼는 해제됐다.
이 한 경로에서 최초 작성자를 재현하지 못했으며, IRQ/스케줄러/맵 전환/VRAM
실행 전체를 재현한 것은 아니다. 이미 훼손된 명령을 자동으로 고치지도 않는다.

```powershell
.venv\Scripts\python.exe -B -m true_patches.mega_evolve.trace_sprite_corruption --state "C:/Users/82106/AppData/Local/Temp/Complete_0.dss" --replay-cache --report true_patches/mega_evolve/.cache/dungeon_debug/latest_report.json
```

이 자료로는 최신 자원/실행 이미지가 로드된 상태에서도 훼손된 공용 복사 명령이
존재함을 확인할 수 있다. 다만 이전 상태 파일에서 훼손을 물려받았는지, 새 실행
중 다시 훼손됐는지는 현재 상태 하나로 구별할 수 없다. 에뮬레이터 재시작 후 일반
세이브로 연 입장 전 상태와 비교해야 최초 훼손 구간을 좁힐 수 있다.
