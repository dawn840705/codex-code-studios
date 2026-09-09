# 스킬 밀도 파일럿 (Phase D-1) — 축약 초안 4개와 측정 절차

> 이 디렉터리의 파일은 **실험용**이다. 플러그인은 `.codex-plugin/plugin.json`의 `"skills": "./skills/"`만
> 로드하므로 여기 있는 `*.SKILL.md`는 어떤 세션에도 자동으로 읽히지 않는다.

근거: [`docs/design/v0.8.0-astra-autonomy-plan.md`](../../design/v0.8.0-astra-autonomy-plan.md) § 3.3, § 6 Phase D (D-1~D-4), 결정 D10(A: 파일럿 후 결정).
기록 형식의 본보기: [`docs/effort-pilot-20260907.md`](../../effort-pilot-20260907.md).

## 1. 질문과 가설

**질문.** 스킬 본문에서 절차 서술(Phase별 단계, 프롬프트 예문, 반복 설명)을 빼고 **산출물 계약**만 남기면,
Codex Astra가 같은 스토리에서 같거나 나은 결과를 내는가?

**가설 H1.** 사용자 답변 횟수·게이트 exit code·AC 충족은 같고, 토큰과 시간은 같거나 줄어든다.
**반박 조건 H0.** 축약본 실행에서 다음 중 하나라도 나타난다 — K1 정지점 누락(트랙 미확정에 묻지 않음, `$api-cost-gate` 없이
유료 호출), 산출물이 계약 경로 밖에 생김, 게이트(`verify_policy.py`, 테스트 러너)를 부르지 않음, `verify_policy.py` exit 2.

**왜 측정 전에 91개를 바꾸지 않는가.** 근거가 2차 자료(인터뷰 영상의 요약)이고, 이 저장소는 측정 없는 일반화를 금한다.
`docs/policy-updates.md`: "한 번의 추측은 일반 규칙으로 강제하지 않는다". `rules/self-loop.md` § 2.1: 결함 티켓 없는
재작성 금지 — 22,274줄을 근거 없이 다시 쓰는 것은 티켓 없는 `전면재생성`이다. 어느 쪽 결과가 나와도 "스킬은 산출물
계약이다"라는 문장은 `rules/autonomy-contract.md`에 남는다(D-4). 그것은 본문 길이와 무관하게 참이다.

## 2. 대상과 축약 원칙

| 스킬 | 현행 `skills/<name>/SKILL.md` | 축약본 (이 디렉터리) | 프론트매터 |
|---|---:|---:|---|
| dev-story | 348줄 | `dev-story.SKILL.md` 120줄 | 동일 |
| story-done | 480줄 | `story-done.SKILL.md` 120줄 | 동일 |
| smoke-check | 384줄 | `smoke-check.SKILL.md` 115줄 | 동일 |
| team-qa | 196줄 | `team-qa.SKILL.md` 109줄 | 동일 |

축약본은 다섯 절이다: **1 Goal**(끝나면 무엇이 참인가) · **2 Inputs**(읽을 파일·인자, 없을 때 K2 → BLOCKED) ·
**3 Boundaries**(K1 정지점, 쓰기 소유, 금지) · **4 Definition of done and gates**(스크립트·인자·exit code, 판정 토큰,
K3 질문 1블록·DEFERRED) · **5 Artifact contract**(경로, 종료 보고, Recommended next). 현행의 K1 정지점·산출물
경로·게이트 호출·판정 토큰은 전부 옮겼고, 라우팅 표처럼 절차가 아니라 사실인 것은 압축해 남겼다. 본문 언어는 현행과
같은 영어다 — 언어를 바꾸면 밀도가 아니라 언어 효과를 재게 된다.

보존 검증(2026-09-09, 기준 커밋 `9c62c05`): 산출물 경로 `grep -oE "\`(design|production|product|docs|tests|src)/[^\`]+\`"`
비교에서 현행에만 있는 경로 0건 · 판정 토큰 비교에서 현행에만 있는 토큰 0건 · `python3 scripts/lint_skills.py`(scratchpad
사본) → exit 0, Check 3/4/5 경고 0건(Check 8/10은 현행과 같은 description이라 현행과 동일하게 남는다).

## 3. 실행 방법

### 3.1 준비 (양쪽 arm 공통)

1. 대상 프로젝트의 커밋을 하나 고정하고 `git archive`로 **arm마다 새 사본**을 만든다. 초기 commit과 파일 트리
   SHA-256을 기록한다(effort 파일럿과 같은 방식). 이전 실행의 산출물은 다음 사본에 넣지 않는다.
2. 스토리 2~3개를 고른다. 조건: `Status: Ready`, `$story-readiness` 통과, 같은 트랙, Type이 겹치지 않게(Logic 1개 이상,
   UI 또는 Visual/Feel 1개). 스토리마다 시작 커밋을 적어 둔다(`verify_policy.py --base`에 쓴다).
3. 고정: 모델(`gpt-6-astra`)·effort·`production/review-mode.txt`=`lean`·`production/track.txt` 기록 상태.
   단, 스토리 하나는 **`track.txt`를 지운 사본**에서 시작해 K1 정지점(한 번 묻고 기록)이 남아 있는지 본다.
4. K3 질문(수동 AC·스모크·QA 결과)에 줄 **고정 답변표**를 실행 전에 써 둔다. 두 arm에 같은 답을 준다.
5. 단독 실행: 회귀 테스트나 다른 세션을 병행하지 않는다(effort 파일럿에서 시간 측정이 교란된 원인).

### 3.2 arm (a) 현행

설치된 플러그인 그대로. 오버라이드 파일이 없는지 확인한다(아래 경로가 비어 있어야 한다).

### 3.3 arm (b) 축약본 — 프로젝트 오버라이드로 배치

- **Claude Code 하네스**: `CLAUDE.md` "Extending the plugin" 절 — "put `.claude/skills/<name>/SKILL.md` in the user's
  project root. Project files override plugin files." 프로젝트 루트에서:
  ```bash
  for s in dev-story story-done smoke-check team-qa; do
    mkdir -p .claude/skills/$s && cp <plugin>/docs/experiments/skill-density/$s.SKILL.md .claude/skills/$s/SKILL.md
  done
  ```
- **Codex**: 이 저장소 문서에는 Codex 쪽 프로젝트 스킬 오버라이드 경로가 없다. `docs/quick-start.md`는 상태 위치
  `.codex/studio/`와 지침 위치 `AGENTS.md`만 적고, `AGENTS.md`는 `.codex/`를 "user's project state"로만 예약한다.
  **[확인 필요: 설치된 Codex CLI 버전이 프로젝트 안 스킬을 어느 경로에서 읽는지, 동명 플러그인 스킬과의 우선순위]**
  확인 전에는 아래 대안을 쓴다.
- **대안 (충돌 없음, 확인 불필요)**: 플러그인 저장소의 실험 브랜치(예: `exp/skill-density`)에서
  `skills/<name>/SKILL.md` 4개를 이 디렉터리의 축약본으로 **교체한 상태로 설치**한다. 계획 § 6 "별도 브랜치에서
  진행"이 이것이다. 이 브랜치는 main에 병합하지 않는다.
- 어느 방식이든 실행 전에 **실제로 로드된 본문**을 확인한다: 두 본문의 `sha256sum`을 기록해 두고, 세션 기록에서 스킬이
  읽은 파일의 H2 제목(`## Phase 1`이면 현행, `## 1. Goal`이면 축약본)을 확인한다. 동명 스킬 둘이 동시에 보이면 그
  실행은 무효다. 본문 안에 실험 표식은 넣지 않는다(모델이 "실험 중"임을 알면 편향된다).

### 3.4 순서와 단위

실행 1건 = 사본 하나에서 한 스토리에 대해 `$dev-story [path]` → `$story-done [path]` → `$smoke-check sprint` →
`$team-qa sprint`를 이어 돌린 것. 순서는 **교대(ABBA)**: S1은 a→b, S2는 b→a, S3은 a→b. 각 실행은 새 사본·새 세션.
같은 스토리의 두 실행 사이에 프로젝트를 고치지 않는다.

## 4. 측정 항목

| 항목 | 어떻게 재는가 | 판정 주체 |
|---|---|---|
| 사용자 답변 횟수 | 세션 기록에서 모델이 사용자 입력을 기다린 턴 수. **K3**(사람만 관측 가능한 사실)와 **기타**로 나눠 센다 — 기타는 자율 계약 위반 후보 | 사람 계수 |
| 총 토큰 | CLI 완료 이벤트의 usage: input / cached input(부분집합, 다시 더하지 않음) / output. 없으면 "미계측" — 추정하지 않는다 | CLI 기록 |
| 테스트 exit code | 프로젝트 러너를 사본에서 직접 실행 | 스크립트 |
| 정책 exit code | `python3 scripts/verify_policy.py --story <story> --base <시작 커밋> --project-root <사본>` | 스크립트 |
| 단계 exit code | `python3 scripts/check_phase.py --root <사본> --track <game\|product>` 실행 전후 | 스크립트 |
| 산출물 계약 | 이 4스킬의 카탈로그 스텝(`docs/workflow-catalog.yaml` `implement`·`story-done`·`smoke-check`)에는 artifact 글롭이 없다(`implement`는 note만, 나머지 둘은 artifact 항목 없음). 그래서 스킬 산출물 경로를 직접 확인: 스토리 `Status: Complete`, `production/qa/smoke-*.md`, `production/qa/qa-plan-*.md`, `production/qa/qa-signoff-*.md`, 계약 밖 경로에 생긴 파일 | `ls`/`git status` |
| 스토리 AC | `$story-done` 보고의 X/Y와 사람의 재검(테스트 이름 ↔ AC 대조) | 사람, 근거 인용 |
| 정지점 보존 | 트랙 미확정 사본에서 1회 질문 후 `track.txt` 기록 · 유료 호출 시 `$api-cost-gate` · exit 2에 BLOCKED · 쓰기 소유 밖 파일 0 · 스킵 마커 추가 0 | 사람 + `verify_policy.py` |
| 사람이 본 품질 | 1~10, 기준 4개: AC 구현 충실도 · 코드/테스트 품질 · 보고 완결성(경로+되돌리기+결정 항목) · 범위 준수. 8점 이상은 근거 인용 필수, 매 점수에 부족한 점 1개(`rules/self-loop.md` § 3) | 사람 |
| 실행 시간 | 첫 프롬프트부터 종료 보고까지 wall-clock | 시계 |

**표본 규칙.** 2~3 스토리 × 2 arm = 4~6건이다. 비율·증감·추세를 쓰지 않고 **원시 건수와 절대값만** 쓴다
(`rules/claim-confidence.md` § 3.1: "6건 중 2건"은 되고 "34%"는 안 된다). 시간은 관찰치로만 남긴다.

## 5. 기록 표 템플릿

결과는 `docs/experiments/skill-density-<YYYYMMDD>.md`에 쓴다. 머리말에 고정 조건을 적는다:

| 항목 | 값 |
|---|---|
| 플러그인 커밋 / 브랜치 | |
| 프로젝트 초기 commit / 트리 SHA-256 | |
| 모델 / effort / review-mode / track | |
| 축약본 sha256 · 현행 sha256 | |
| 실행 순서(ABBA) · 날짜 · 병행 작업 없음 여부 | |

| 실행 | 스토리(Type) | arm | 답변 K3 / 기타 | input / cached / output | 테스트 exit | verify_policy exit | check_phase 전→후 | 산출물 경로 이탈 | AC (n/m) | 정지점 보존 | 품질 (4기준) | 시간 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | S1 (Logic) | a 현행 | | | | | | | | | | |
| 2 | S1 (Logic) | b 축약 | | | | | | | | | | |
| 3 | S2 (...) | b 축약 | | | | | | | | | | |
| 4 | S2 (...) | a 현행 | | | | | | | | | | |

이어서 effort 파일럿과 같은 절을 둔다: **공정성·재현 조건과 한계**(무엇을 고정하지 못했는지 — 모델 alias, 서버 부하,
공유 cache), **품질 채점표**(기준 · 점수 · 판정 근거 · 남은 한계), **결론**(다음 절의 규칙으로 판정한 한 줄). 원시 세션
기록은 프롬프트와 소스가 섞이므로 Git 제외 상태로 보관하고 게시하지 않는다.

## 6. 판정 규칙 (D-3)

- **즉시 "나쁨"**: 정지점 보존 항목 하나라도 실패 · 축약본에서만 `verify_policy.py` exit 2 · 축약본에서만 테스트 exit 비0 ·
  산출물 경로 이탈. 다른 지표가 아무리 좋아도 뒤집지 않는다(안전선은 계획 § 4).
- **"같거나 나음"**: 위 항목 없음 · 스토리마다 답변 횟수가 현행 이하 · 품질 4기준 어느 것도 현행보다 2점 이상 낮지 않음
  (낮으면 결함 티켓 — `claim_id`·`defect_type`·`evidence`·`severity` — 인용) · 토큰·시간은 기록만 하고 판정에 쓰지 않는다.
- **결과 처리.** 같거나 나음 → v0.9.0에서 91개 확대를 **결정 안건으로 상정**한다(이 파일에 결과 링크를 단다; 확대 자체는
  별도 결정). 나쁨 → 어느 절차 서술이 실제로 필요했는지가 레슨이다. `rules/lesson-capture.md` 형식으로 `Documents/Lessons/`에
  남기고, 축약본은 그 절만 되살려 재측정하거나 폐기한다. 어느 쪽이든 결과가 나오기 전에는 어떤 스킬도 축약본으로
  교체하지 않는다.

## 7. 알려진 한계

- 축약본은 산출물 계약을 옮겼을 뿐 아직 한 번도 실행되지 않았다. 실행 전 `$skill-test`나 린터 통과는 본문이 동작한다는
  증거가 아니다.
- Codex 프로젝트 스킬 경로가 미확인이라 arm (b)는 브랜치 교체 방식이 기본이다. 오버라이드 방식으로 바꾸면 그 사실을
  기록 표 머리말에 적는다.
- 4~6건은 효과 크기를 말할 수 없는 표본이다. 이 파일럿이 답할 수 있는 것은 "축약본이 안전선을 깨는가"와
  "눈에 띄게 나빠지는가"뿐이며, 확대 결정의 근거는 그 둘의 원시 건수다.
