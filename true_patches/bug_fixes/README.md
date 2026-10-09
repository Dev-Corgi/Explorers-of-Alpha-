# bug_fixes

기준 Alpha 롬의 버그를 직접 수정하는 모듈이다. 풀스택의 게임플레이 모듈
뒤에 적용하며, 한글 모듈은 그 이후에 적용한다.

## v1: 싸라기눈의 일반 자연회복 가속 제거

`TickStatusAndHealthRegen`의 `0x023111F0` 명령은 Ice Body가 없는 개체도
싸라기눈에서 회복 분모에 -100을 적용한다. 이 명령만 NOP으로 바꾼다.
Ice Body의 Alpha 접촉 동상 효과, Quick Healer, Rain Dish, Dry Skin 및
나머지 회복 보정은 건드리지 않는다. 동굴과 추가 문자열은 사용하지 않는다.

HP 787, 기본 회복 분모 200, Quick Healer가 있는 Kabutops라면 싸라기눈에서
평균 회복량이 회복 처리 1회당 39.35 HP에서 7.87 HP로 줄어든다.
이는 자연회복 부분만의 값이며, 날씨 피해 등 다른 효과는 별도로 처리된다.

검증:

```powershell
.venv\Scripts\python.exe -B true_patches\bug_fixes\verify.py
```

검증은 임시 파일에 모듈만 적용하고 ARM 회복 루틴을 부분 실행한다.
풀스택 롬을 다시 빌드하거나 배포 결과물을 수정하지 않는다.
