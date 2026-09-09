---
name: humanize
description: AI가 쓴 한글 텍스트를 자연스럽게 윤문하는 진입 명령. humanize-korean 파이프라인을 Fast 모드(기본)로 실행하고 `--strict`면 정밀 3콜(진단→겨냥 윤문→finalize). 트리거 — "$humanize". **명시적 슬래시 호출 전용** — 자연어로 윤문을 요청받았을 때는 이 래퍼가 아니라 `humanize-korean` 오케스트레이터를 쓴다.
---

# $humanize — 한글 AI 티 제거

`humanize-korean` 스킬을 발동해 인자로 전달된 한글 텍스트(또는 파일)에 윤문을 실행한다.

Writes: `_workspace/{YYYY-MM-DD-NNN}/` (humanize-korean 작업 디렉터리)만 새로 만든다. 입력 파일 덮어쓰기는 Phase 3 규칙을 따른다.

## 입력
the invocation arguments

## Phase 1: 입력 해석

1. 인자가 비면: "윤문할 텍스트를 붙여넣어 주세요" 안내 후 종료.
2. 인자가 파일 경로(.txt/.md)면 `Read`로 본문 로드.
3. 인자가 텍스트면 그대로 입력으로 사용.

## Phase 2: 파이프라인 실행

`humanize-korean` 스킬 SKILL.md 절차(Phase 0 → 결과 전달)를 따른다 — 기본 **Fast 모드**,
`--strict` 시 정밀 3콜(진단→겨냥 윤문→finalize).

구조 게이트(`scripts/verify_gates.py`)의 **exit code 가 판정이다.** 0이면 PASS,
0이 아니면 FAIL이며 실패 코드를 그대로 사용자에게 보고한다. LLM 자체 점수로
PASS를 선언하지 않는다.

## Phase 3: 결과 전달

- 한 줄 상태(변경률 / 등급 / 게이트 PASS·FAIL)
- 윤문본 본문(마크다운 블록)
- 카테고리별 탐지 건수 before/after
- 주요 변경 하이라이트 3~5건
- 게이트 FAIL 또는 등급 B 이하면 → "`$humanize-redo`로 2차 윤문 가능" 안내

결과는 **응답으로 보여주는 것이 기본이다.** 사용자 파일에 덮어쓰기 전에는 반드시 먼저
묻는다 — "윤문 결과를 `<경로>`에 쓸까요?" (May I write this to the file?)

## 옵션 (인자 끝에 자연어로)
- `장르: 칼럼|리포트|블로그|공적` — 장르 명시 (생략 시 첫 300자로 자동 추정)
- `강도: 보수|기본|적극` — 윤문 강도 (기본값: 기본)
- `최소심각도: S1|S2|S3` — 탐지 임계값 (기본값: S2)
- `--strict` — 정밀 3콜(진단→겨냥 윤문→finalize) 강제

## 후속 작업 (Recommended next)
- 결과가 미흡하면 → `$humanize-redo`
- 오케스트레이터 전체 절차·장르별 허용 표 → `humanize-korean` SKILL.md

## 참고
- 분류 체계: `skills/humanize-korean/reference/ai-tell-taxonomy.md`
- 윤문 처방: `skills/humanize-korean/reference/rewriting-playbook.md`
