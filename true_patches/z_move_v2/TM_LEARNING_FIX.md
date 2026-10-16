# 던전 TM·HM 대상 선택 수정 (v27)

메가루카리오 혼자 있는 파티에서 칼춤 TM의 Use를 누르면 대상 이름이
빨갛게 표시되어 선택할 수 없는 상태가 사용자 DSS에서 재현됐다.
메가루카리오의 기술 목록이나 호환 설정이 원인은 아니었다.

`TeachItemHandler_EntryHook`은 TM Read·Z기술의 임시 기술칸을 복구한 뒤
원래 학습 함수로 돌아간다. 기존 코드는 r3/lr만 보존하여 복구 함수가
바꾼 r0(사용자 개체)·r1(아이템 포인터)을 학습 함수에 넘겼다.
첨부 상태에서는 실제 칼춤 번호181 대신 기술0으로 대상 검사를 하여
monster+0x161의 선택 가능 플래그가0으로 기록됐다. 메가 전용 결함은 아니다.

복구 호출 전후에 r0–r3/r12/lr를 보존한다. 호출 시 스택의8바이트 정렬과
기존 학습 함수의 스택 구성을 유지하며 임시 기술칸 복구 자체는 계속 실행한다.
적용 순서는 기존처럼 tm_read 다음 z_move_v2이며 새 문자열은 없다.

검증:

```powershell
.venv/Scripts/python.exe -B -m true_patches.z_move_v2.verify_tm_learning
.venv/Scripts/python.exe -B -m true_patches.z_move_v2.verify_tm_learning '<첨부 DSS 경로>'
.venv/Scripts/python.exe -B -m true_patches.z_move_v2.verify_partner_slot
.venv/Scripts/python.exe -B -m true_patches.z_move_v2.verify_handle_faint
```

회귀 검증은 실제 수정 소스에서 ARM 코드를 조립한다. DSS 검증은 원래
실행 중인 복구 함수·아이템/기술 목록·상태 판정과 대상 플래그 기록을 실행하여
수정 전 실패와 수정 후 성공을 비교한다. 일반/메가/이로치 루카리오의 두 성별,
이미 배운 기술·호환 불가 종·상태이상·변신 제한도 확인한다.
파일 읽기만 모델이며 화면 입력과 게임 내 학습 완료까지 검증한 것은 아니다.
원본 DSS와 롬은 변경하지 않고 풀스택도 빌드하지 않는다.
