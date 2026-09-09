---
name: humanize-redo
description: 가장 최근 윤문 결과를 2차로 다시 다듬는다 — 특정 카테고리·문단·강도 조정도 가능. humanize-korean 의 윤문 콜을 기존 run_id 에 재실행해 잔존 finding 을 처리한다. 트리거 — "$humanize-redo". **명시적 슬래시 호출 전용** — 자연어 후속 요청은 `humanize-korean` 오케스트레이터가 받는다.
---

# $humanize-redo — 2차 윤문 / 부분 재실행

cwd 기준 가장 최근 `_workspace/{run_id}/`를 찾아 `humanize-korean` 의 윤문 콜부터 재호출한다.

## 사용자 지시
the invocation arguments

## Phase 1: 이전 실행 식별

`Glob`으로 `_workspace/YYYY-MM-DD-*/final.md`(또는 `01_input.txt`)를 매칭해 최신 `run_id`를
식별한다. 없으면 "이전 실행이 없습니다. `$humanize`로 시작하세요" 안내 후 종료.

## Phase 2: 지시 파싱

- **카테고리 지정**("번역투만", "관용구만", "이모지만") → 해당 카테고리 finding만 재윤문
- **문단 지정**("이 문단만", "두 번째 문단만") → 해당 범위 finding만
- **강도 조정**("강도 낮춰"·"보수적으로" → S1만, "강도 높여" → S1+S2+S3)
- **롤백 요청**("이 변경 되돌려줘") → `final_prev.md`(직전 백업)에서 해당 구간을 복원한다.
  전체 롤백이면 `final_prev.md`를 `final.md`로 되돌린다.
- 지시 없음·"2차 윤문해줘" → 잔존 finding 전체 대상 round 2

## Phase 3: 재윤문 실행

`humanize-monolith`를 재호출한다. 입력은 이전 실행의 산출물에서 가져온다.

- 진단이 있으면 `02_diagnosis.md`의 잔존 패턴
- finalize를 거쳤으면 `09_finalize.json`의 미해결 항목
- 사용자 지시는 `target_filter`로 함께 전달

강도를 높였거나 의미 보존 확인이 필요하면 `humanize-finalizer`를 1콜 추가한다.

## Phase 4: 산출물 버전 분리

- 새 결과는 `final.md`로 쓰고, **직전 결과는 먼저 `final_prev.md`로 백업한다.**
- 원래 입력이 파일이었으면 `humanize-korean`의 "파일 쓰기 규약"대로 다시 반영한다 —
  git 추적 중이고 깨끗하면 제자리에 쓰고 diff 요약과 `git checkout -- <경로>`를 보고,
  아니면 `<이름>.humanized.<확장자>`를 갱신하고 경로를 보고한다.

## Phase 5: 판정과 보고

`scripts/verify_gates.py`를 재실행하고 **exit code로 판정한다** — 0이면 PASS,
아니면 FAIL과 실패 코드를 그대로 보고한다. 변경 비교 표(round N-1 → N)와 신규 등급을
함께 낸다.

## 루프 한도

최대 round 3. 그 이상 미해결이면 `hold_and_report`로 사람 검토를 권고한다.
같은 finding이 2 round 연속 해결되지 않으면 더 돌리지 않고 그 사실을 보고한다.

## 후속 작업 (Recommended next)
- 풀 파이프라인 신규 실행은 `$humanize`
- 반복해서 잡히는 새 패턴이면 → `korean-ai-tell-taxonomist`로 SSOT 승격 검토

## 참고
- 분류 체계: `skills/humanize-korean/reference/ai-tell-taxonomy.md`
