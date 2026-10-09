# bug_fixes

기준 Alpha 롬의 버그를 수정하는 모듈이다. 풀스택의 게임플레이 모듈 뒤에
적용하며, 한글 모듈은 그 이후에 적용한다. v2부터 보조 코드의 overlay36
동굴은 적용 시점에 동적으로 할당한다. 기존 모듈 업그레이드는 기준 롬부터
풀스택을 재구성하는 방식으로 적용한다.

## v2: Mirror Armor, Trace, Neutralizing Gas

- **Mirror Armor:** 저장해 둔 원래 엔티티 포인터로 능력치 하락의 출발점과
  대상을 뒤집는다. 특성 메시지는 Mirror Armor 소유자에게 표시하고,
  Defiant·Competitive가 사용하는 대상도 실제 반사 대상에 맞춘다.
- **Trace:** 원래 특성 슬롯을 선택하기 전에 `AbilityIsActive`를 호출한다.
  위액, 인접 Neutralizing Gas 및 특성 억제 도구가 반영된다. Trace가
  없거나 억제됐을 때도 기존 Color Change 처리로 계속 진행한다.
- **Neutralizing Gas:** 층 전체 플래그 대신 인접 8칸의 살아 있는 소유자를
  매번 검사한다. 적·아군 모두 영향을 받으며 이동·기절·억제가 즉시 반영된다.
  소유자는 스스로를 억제하지 않고, 가스 특성끼리 서로 억제하지 않는다.
  위액과 특성 억제 도구는 가스 자체를 끌 수 있다.

## v1: 싸라기눈의 일반 자연회복 가속 제거

`TickStatusAndHealthRegen`의 `0x023111F0` 명령은 Ice Body가 없는 개체도
싸라기눈에서 회복 분모에 -100을 적용한다. 이 명령만 NOP으로 바꾼다.
Ice Body의 Alpha 접촉 동상 효과, Quick Healer, Rain Dish, Dry Skin 및
나머지 회복 보정은 건드리지 않는다. 이 수정 자체는 동굴을 사용하지 않으며,
v2의 특성 수정에도 추가 문자열은 없다.

HP 787, 기본 회복 분모 200, Quick Healer가 있는 Kabutops라면 싸라기눈에서
평균 회복량이 회복 처리 1회당 39.35 HP에서 7.87 HP로 줄어든다.
이는 자연회복 부분만의 값이며, 날씨 피해 등 다른 효과는 별도로 처리된다.

검증:

```powershell
.venv\Scripts\python.exe -B true_patches\bug_fixes\verify.py
```

검증은 임시 파일에 모듈만 적용하고 실제 ARM 회복·특성·능력치 하락
루틴을 부분 실행한다. 회복·날씨·아이템 조건과 메시지·애니메이션·타일 조회
등의 보조 서비스는 검사 환경에 맞춰 제공한다. Mirror Armor의 실제 스탯 하락과 Defiant·Competitive 반응,
Trace의 두 슬롯 및 Color Change, 가스의 거리·진영·이동·기절·억제를 확인한다.
풀스택 롬을 다시 빌드하거나 배포 결과물을 수정하지 않는다.
