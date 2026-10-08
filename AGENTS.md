# Explorers of Alpha 작업 지시

US 탐험대 하늘(Explorers of Sky) 롬에 Explorers of Alpha 패치를 모듈 단위로 쌓는 저장소다. 패치 내용은 `true_patches/`에만 있고, 적용·빌드·동굴 배치는 `patch_engine/`에 있다. 완성품은 모듈을 순서대로 적용한 롬 하나다. 배포용 xdelta는 그 완성 롬에 대해 한 번만 만든다. 모듈마다 xdelta를 만들어 쌓지 않는다.

## 기준 롬과 결과

입력은 `PatchTesting/Explorers of Alpha/Explorers of Alpha.nds`다. 영문 풀스택은 `PatchTesting/Export Rom/Explorers of Alpha+.nds`, 한글 풀스택은 `PatchTesting/Export Rom/Explorers of Alpha+_kor.nds`다.

`Explorers of Alpha_Vanilla.nds`, `Vanilla Rom/`, 저장소 루트의 `Export Rom/`은 쓰지 않는다. `*.nds`와 `Export Rom/`은 git에 올리지 않는다.

## 빌드

저장소 루트에서 실행한다.

```bash
.venv\Scripts\python.exe patch_engine\build_korean.py --rebuild-full
```

이 명령이 영문 풀스택을 기준 롬부터 다시 만든 뒤 한글을 얹는다. 5분 안팎이 정상이다. 롬 옆에 `.state.json`이나 미번역 xlsx를 남기지 않는다. 사용자가 빌드하지 말라고 하면 빌드하지 않는다.

## 모듈

적용 순서는 `patch_engine/build_full_stack.py`의 `FULL_STACK_MODULES`가 기준이다. 새 기능은 `true_patches/<이름>/`에 `manifest.yaml`을 두고, `patch_engine/catalog.yaml`과 이 목록에 넣는다. 동굴 주소는 적용 시점에 비어 있는 구간을 잡는다. 주소를 소스에 고정하지 않는다.

`team_push`의 몸체는 PC 상대 주소라 오버레이36 파일 `0xE00`–`0x1100`(RAM `0x023A7E80`)에 둔다. 그 구간과, 동굴 체인이 시작되는 `0x1A578` 앞쪽은 다른 모듈이 쓰지 않는다.

## 문자열

`LogMessageById`에 넘기는 번호는 `text_e.str` 인덱스보다 1 크다. 새 문장은 이미 쓰인 인덱스를 덮어쓰지 않고 비어 있는 인덱스에 넣는다.

## 한글

`korean`은 항상 마지막이다. 영어 원문이 예전 하늘 탐험대 문장과 같을 때만 번역이 붙는다. 패치가 만든 문장은 `true_patches/korean/data/translations.json.gz`에 문자열 인덱스와 영어·한글을 같이 적는다. 이름 입력 키 조합은 `korean_assemble`이 담당한다.

## 손대지 말 것

`PatchTesting (don't touch here)`, `true_patches (don't touch here)`, `melonDS-master`는 참고용 복사본이다. 롬, 세이브, 압축을 푼 데이터는 커밋하지 않는다.

## 작업 절차

해당 모듈과 그 모듈을 호출하는 `patch_engine`만 수정한다. 적용 순서와 문자열 번호 오프셋을 확인한다. 사용자가 빌드를 요청했을 때만 풀스택을 다시 만든다. 검증이 실패한 채 커밋하지 않는다.
