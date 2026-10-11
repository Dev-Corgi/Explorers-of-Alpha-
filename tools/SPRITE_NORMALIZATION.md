# SpriteCollab 작업용 폴더 정리

`normalize_spritecollab.py`는 원본 `sprite/`와 `tracker.json`을 읽어, 각 포켓몬의 폼과 색상별 스프라이트 패키지를 별도 폴더로 복사합니다. 원본 파일과 메타데이터는 수정하지 않습니다.

```text
output/sprite-normalized/0012/
├─ Base/
│  ├─ Normal/  (AnimData.xml, PNG, credits.txt 등)
│  └─ Shiny/
└─ 0001-Gigantamax/
   └─ Normal/
```

- `Base`는 기본 폼입니다. 다른 폼은 SpriteCollab 폼 번호와 메타데이터 이름을 함께 사용합니다. 같은 이름의 폼도 번호로 구분합니다.
- 이름에 `Altcolor`가 포함된 폼은 그 하위 색상과 성별까지 모두 제외합니다.
- 각 폼의 `Normal`과 `Shiny`는 실제 `AnimData.xml`이 있을 때만 만듭니다. 파일이 없으면 빈 폴더를 만들지 않습니다.
- 한 폼·색상에는 스프라이트 세트 하나만 선택합니다. 수컷 전용 파일을 우선하고, 없으면 성별 공통 파일을, 둘 다 없으면 암컷 전용 파일을 사용합니다. 암컷을 선택한 항목은 보고서의 `gender_source: female_fallback`으로 표시합니다.
- 스프라이트 파일은 `Normal` 또는 `Shiny` 최하위 폴더에만 복사합니다. 원본 폴더의 숫자 계층을 해석한 대응 관계, 누락 사유와 복사 상태는 별도의 JSON 보고서에 남깁니다.

저장소 루트 `C:\Working\SkyTemple`에서 실행합니다.

```powershell
python tools/normalize_spritecollab.py --sprite-root SpriteCollab-master/SpriteCollab-master/sprite --tracker SpriteCollab-master/SpriteCollab-master/tracker.json --output output/sprite-normalized --report output/sprite-normalized-report.json --dry-run
python tools/normalize_spritecollab.py --sprite-root SpriteCollab-master/SpriteCollab-master/sprite --tracker SpriteCollab-master/SpriteCollab-master/tracker.json --output output/sprite-normalized --report output/sprite-normalized-report.json
```

중단된 복사를 같은 경로에서 이어갈 때는 `--resume`을 붙입니다. 이미 있는 파일은 원본과 SHA-256이 같을 때만 건너뛰고, 다르면 오류로 기록합니다. `--dry-run`은 대상 선정만 확인하며 파일을 복사하지 않습니다.

이 구조는 작업용 에셋 복사본입니다. SpriteCollab의 `tracker.json` 형식이나 게임 등록 형식은 아니므로, 실제 패치에 넣으려면 별도 변환이 필요합니다.
