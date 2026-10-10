# PMD 타입 아우라 합성 프로그램

`pmd_aura.py`는 SpriteCollab 원본의 불투명 픽셀을 보존하고, 캐릭터 바깥 투명 영역에만 픽셀 아우라를 합성합니다. 이미지 생성 AI, API 키, GPU, ROM은 사용하지 않습니다.

## 준비

Python 3.10 이상과 Pillow, numpy, scipy가 필요합니다.

```powershell
python -m pip install Pillow numpy scipy
```

## 최종진화 기본형 일괄 처리

`tools/data/pmd_aura_targets.csv`에는 574종의 도감 번호, 한글·영문 이름, `type1/type2`, `enabled`, 원본·이로치 경로 및 에셋 존재 여부가 있습니다. UTF-8 BOM 형식이며 번호는 4자리입니다. Excel에서 앞자리 0을 지워도 프로그램은 복원합니다. `enabled=0`으로 제외하거나 타입을 수정할 수 있습니다. 경로 열은 참고용이며 프로그램은 아래의 검증된 기본형 경로만 사용합니다. 존재 여부는 CSV 생성 시점의 참고값으로, 실행할 때 실제 파일을 다시 확인합니다.

목록 기준은 PokeAPI의 고정된 소스 버전에 있는 본가 기본형입니다. 진화가 없는 단일종·전설·환상도 포함합니다. 지역 폼에만 진화가 있는 파오리·코산호·직구리·침바루 등은 기본형에 후속 진화가 없으므로 포함합니다. 다른 폼·성별 폴더는 처리하지 않습니다. Alpha의 진화 조건 및 타입이 본가와 다르면 CSV를 수정하세요. 데이터 출처와 버전은 `pmd_aura_targets.source.json`에 기록했습니다.

저장소 루트 `C:\Working\SkyTemple`에서 실행합니다:

```powershell
python tools/pmd_aura.py --sprite-root SpriteCollab-master/SpriteCollab-master/sprite --csv tools/data/pmd_aura_targets.csv --output output/aura/final-evolutions-v1 --dry-run
python tools/pmd_aura.py --sprite-root SpriteCollab-master/SpriteCollab-master/sprite --csv tools/data/pmd_aura_targets.csv --output output/aura/final-evolutions-v1
```

배치 모드는 기본적으로 모든 실제 동작을 처리하고 미리보기는 생성하지 않습니다. `--animations Idle`로 일부만 선택하고 `--previews`로 미리보기를 켤 수 있습니다. `--only-dex 0012`는 버터플만 처리합니다.

배치 대상 색상은 `--variants normal`(원본 `AltMeta`만), `--variants shiny`(이로치 `AltMetaColor`만), `--variants both`(기본값, 둘 다)로 선택합니다.

입력과 출력 대응:

| 입력 | 출력 |
|---|---|
| `sprite/번호/` | `출력/번호/AltMeta/` |
| `sprite/번호/0000/0001/` | `출력/번호/AltMetaColor/` |

원본 디렉터리와 tracker는 수정하지 않습니다. AltMeta·AltMetaColor는 생성 패키지의 폴더 이름이며 게임 등록·ROM 적용은 별도 작업입니다. 마스크를 쓰면 `--mask-dir` 아래의 `번호/AltMeta/동작-Mask.png`, `번호/AltMetaColor/동작-Mask.png`를 준비합니다.

전체 실행이 끝나면 출력 루트의 `batch-report.json`에 생성·누락·실패 결과가 남습니다. 누락은 건너뛰고, 개별 실패 후에도 다른 포켓몬을 계속 처리합니다. 색상 여유가 없는 원본은 실패로 기록되며 원본을 줄이거나 덮어쓰지 않습니다. 종료 코드 1은 실패 항목이 있다는 뜻입니다.

실제 버터플 전체 동작 검증에서 원본은 16색 제한으로 성공했고, 이로치는 두 타입색을 추가할 슬롯이 부족했습니다. `--palette-limit 32`로 올리면 양쪽 파일을 생성할 수 있지만, 이 출력의 게임 팔레트 호환성은 별도로 확인해야 합니다. 기본 제한은 계속 16색입니다.

중단 후 같은 명령에 `--resume`을 추가하면 소스·옵션·프로그램·출력 해시가 일치하는 완료 항목만 건너뜁니다. 불완전하거나 변경된 출력은 덮어쓰지 않습니다. 옵션이나 CSV 타입을 바꾼 경우 새 출력 루트를 사용하세요. `--dry-run`은 파일을 생성하지 않고 입력의 존재만 확인하며 팔레트 등 렌더링 검증은 실제 실행에서 수행합니다.

목록 재현용 `pmd_aura_catalog.py`는 고정된 PokeAPI CSV를 캐시에 내려받아 분석 JSON을 출력합니다. 원본 데이터 파일은 커밋하지 않습니다.

## 단일 포켓몬 Idle 시험

저장소 루트 `C:\Working\SkyTemple`에서 실행합니다. 출력 폴더는 매번 새 이름을 사용합니다.

```powershell
python tools/pmd_aura.py --sprite-dir SpriteCollab-master/SpriteCollab-master/sprite/0012 --output output/aura/Butterfree-bug-flying-idle-v1 --types bug flying
```

`--types 벌레 비행`도 가능합니다. 타입을 한 개만 지정하면 같은 타입색의 밝기 단계, 두 개면 두 타입색 사이의 그라데이션을 사용합니다. 기본은 위쪽이 첫 타입색, 아래쪽이 두 번째 타입색입니다. `--gradient-axis radial`은 안쪽→바깥쪽입니다. 색은 프로그램의 시각적 기본값이며 ROM 타입 ID나 공식 색상 표준으로 취급하지 않습니다.

전체 동작을 처리하려면 다음처럼 실행합니다. 하위 폼은 읽지 않습니다.

```powershell
python tools/pmd_aura.py --sprite-dir SpriteCollab-master/SpriteCollab-master/sprite/0012 --output output/aura/Butterfree-all-v1 --types bug flying --all
```

`--animations Idle Walk Sleep`으로 일부 동작만 선택할 수도 있습니다. CopyOf 동작은 공유 대상의 실제 시트를 수정해야 합니다. 예를 들어 Strike 대신 Attack을 지정합니다.

## 모양과 색상

- `--width 3`: 기본 외곽 아우라 두께, 원본 픽셀 단위.
- `--flame-height 4`: 위쪽으로 흐르는 추가 불꽃 길이. 0이면 외곽 발광에 가까워집니다.
- `--seed 0`: 반복 가능한 공간 패턴. 프레임마다 독립 난수를 사용하지 않습니다.
- `--gradient-steps 3`: 고정 색 단계 수. 기본은 원본 색을 보존하고 남은 슬롯 안에서 최대 3단계를 선택합니다.
- `--palette-limit 16`: 투명색 포함 최대 색 수. 원본을 재색칠하거나 양자화하지 않습니다. 복합 타입에 필요한 색이 부족하면 실패합니다.
- `--type-colors colors.json`: `{ "bug": "#A8B820", "flying": "#A890F0" }` 형식으로 기본 색을 변경합니다.

아우라 모양은 알파 마스크의 거리와 위쪽 방향, 시간에 따라 연속적으로 변하는 파동으로 계산합니다. 원본 얼굴·날개·팔다리 위에는 그리지 않습니다. 공통 아우라 색을 모든 처리 동작에 사용하고, 디더링과 반투명 픽셀은 사용하지 않습니다. 원본의 반투명 알파는 지원하지 않으므로 먼저 정리해야 합니다. 완전 투명 픽셀의 보이지 않는 RGB는 출력에서 0으로 정규화합니다.

## 여백·위치·XML

기본 `--padding auto`는 두께와 불꽃 길이에 맞춰 각 프레임 사방에 같은 여백을 추가합니다. 기본 모양에서는 사방 8픽셀입니다. 버터플 Idle은 32×56에서 48×72, 전체 시트는 128×448에서 192×576이 됩니다.

AnimData.xml의 처리 동작 FrameWidth/FrameHeight를 수정하고, 그 동작의 Offsets/Shadow도 같은 여백만큼 옮깁니다. Index, CopyOf, Durations, 공격 타이밍은 보존합니다. 처리하지 않은 시트와 credits 등 직속 파일도 복사해 전체 원본 구성은 유지합니다. 원본과 출력 폴더는 겹칠 수 없고 기존 출력 폴더를 덮어쓰지 않습니다.

Offsets에 불투명 검은 점이 하나 있으면 파동의 위치 기준으로 사용합니다. 이 점의 엔진상 의미를 새로 지정하는 것은 아닙니다. 없으면 마스크의 가시 영역 중심을 사용합니다. 이 fallback은 몸 형태가 크게 변할 때 흔들릴 수 있으므로 보고서의 anchor_source를 확인합니다.

원본 크기를 유지하려면 `--padding 0`을 지정합니다. 아우라가 잘리면 기본적으로 출력 전에 실패합니다. 의도적으로 허용하려면 `--allow-clipping`을 추가해야 하며 잘린 픽셀 수를 보고서에 남깁니다. 프레임 확대는 새 디자인용 파일 처리일 뿐, 실제 게임 메모리·지상 sprite·부유 위치까지 검증한 결과가 아닙니다.

## 캐릭터만 선택하는 마스크

Hurt에는 땀/충격 효과처럼 캐릭터가 아닌 불투명 픽셀이 있습니다. 기본 알파 마스크는 이 효과도 둘러싸며 경고를 남깁니다. 자동으로 떨어진 픽셀을 지우면 더듬이·발도 잃을 수 있어 임의로 제거하지 않습니다.

`--mask-dir masks`를 주면 처리할 각 동작과 같은 크기의 `Idle-Mask.png`, `Hurt-Mask.png` 등을 읽습니다. 흰색(128 이상)은 아우라의 캐릭터 영역, 검은색은 제외 영역입니다. 투명 마스크 PNG는 알파로 선택할 수도 있습니다. 선택 픽셀은 원본의 불투명 영역 안에 있어야 합니다. 마스크에서 제외한 기존 효과 픽셀은 보존하지만 그 주변에는 독립 아우라를 만들지 않습니다.

## 출력 및 검수

- `*-Anim.png`: 투명 인덱스 0과 공통 팔레트를 사용하는 시트.
- `AnimData.xml`, `*-Offsets.png`, `*-Shadow.png`: 여백에 맞춰 갱신된 구성.
- `aura-report.json`: 색상, 규격, 연결 기준, 프레임별 추가/잘림 픽셀, 원본 SHA-256, 경고.
- `Preview/*-comparison.gif`: 원본(왼쪽)과 아우라(오른쪽) 동시 재생.
- `Preview/*-comparison.png`: 같은 비교의 첫 시간 프레임.

GIF는 원본 Durations를 사용하지만 초당 tick은 `--ticks-per-second 60`을 가정합니다. XML 자체에는 재생률이 없으므로 실제 게임 시간의 검증은 아닙니다. 미리보기만 최근접 확대하며 게임 시트는 확대하지 않습니다. `--no-previews`로 미리보기를 생략할 수 있습니다.

실제 ROM 적용 전에 팔레트, 확대된 프레임의 메모리, Offsets/Shadow의 엔진 해석과 장면별 잘림을 추가 검증해야 합니다. 이 도구는 ROM을 수정하거나 빌드하지 않습니다.

## 검사 실행

```powershell
python -m unittest discover -s tools -p test_pmd_aura.py -v
```

원본 픽셀 보존, 파동 반복과 위치 이동, 효과 제외 마스크, XML/CopyOf 보존, 동반 시트의 이동, 팔레트 제한과 잘림 실패 시 출력하지 않는 조건을 검사합니다.
