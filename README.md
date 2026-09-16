# Code Studios for Codex

> **실험적 effort 자동 선택:** 프로젝트별 관찰 모드와 제한된 CLI 전달기를 추가했습니다.
> 앱 부모 대화의 설정을 자동 변경한다고 보장하지 않습니다.
> [지원 범위·사용법·비교 실험](docs/reasoning-effort.md) · [검증 기록](docs/reasoning-effort-validation.md)

Codex 플러그인으로 패키징된 소프트웨어 스튜디오. **게임은 물론 앱/웹/서비스 개발까지** 커버합니다.

**전문 역할 가이드 45종** · **워크플로우 skill 91종** · **Codex lifecycle hooks** · **거버넌스/워크플로우 자산** · **도메인 팩 + 프로젝트 타입 자동 감지** — 프리프로덕션 → 프로덕션 → QA → 릴리스 → 라이브 옵스 전 단계를 다룹니다.

> **v0.7.0 Codex 전환:** `.codex-plugin/plugin.json`과 `.agents/plugins/marketplace.json`이 새 배포 기준입니다. Claude의 독립 `agents/` 정의는 `$studio-orchestrator`가 필요할 때만 읽는 역할 참고자료로 전환했고, 호출 문법은 `$skill-name`, 프로젝트 상태는 `.codex/studio/`, 훅은 Codex의 `apply_patch`·`SessionEnd`·JSON 출력 계약을 사용합니다. `.claude-plugin/`과 `CLAUDE.md`는 한 릴리스 동안 이전 설치를 식별하기 위한 호환 레이어로만 유지합니다.

> **v0.6.4 신규:** 결정적 게이트가 **자기가 도는 콘솔을 견디게** 됐습니다. 이 플러그인의 설계 원칙은 「종료 코드가 판정이다」인데, 그 종료 코드가 콘솔 인코딩 하나로 뒤집히고 있었습니다 — 게이트 리포트는 한국어인데 Windows 한국어 콘솔(cp949)이 em-dash 하나를 인코딩하지 못해 `UnicodeEncodeError` 로 죽었고, 그 죽음이 `exit 1` 로 나왔습니다. 규칙대로 종료 코드만 믿은 호출부는 **통과한 작업을 FAIL 로 읽었습니다.** `/humanize` · `/dev-story` · `/remove-bg` 가 각자의 게이트를 부르는 자리가 전부 그랬습니다.
>
> **수리보다 중요한 건 왜 못 잡았나입니다.** 기존 테스트는 검사 대상 스크립트를 `import` 해서 함수를 직접 불렀고, **`import` 경로에는 콘솔 인코딩이라는 것이 존재하지 않습니다.** 그래서 `verify_trajectory.py` 가 CLI 로는 죽는 순간에도 스위트는 초록이었습니다. 없던 층을 만들었습니다 — [tests/test_console_encoding.py](tests/test_console_encoding.py) 는 `scripts/*.py` 를 훑어 진입점을 찾고(목록 하드코딩 금지 — 하드코딩하면 다음 스크립트를 놓칩니다), cp949·ascii 로 **실제 실행 경로를** 태워 ①죽지 않는지 ②종료 코드가 인코딩과 무관한지 ③비ASCII 가 글자 그대로 살아 있는지를 봅니다. `--help` 만으로는 부족합니다 — `verify_gates` 는 `--help` 가 멀쩡하고 정상 실행에서 죽었습니다. 같은 병이 반대 방향으로도 있었습니다: 하네스가 훅 출력을 *디코딩*하다 죽어 한국어 Windows 에서 훅 테스트 21건이 통째로 죽어 있었고, `verify_policy.py` 는 한국어가 섞인 `git diff` 를 읽다 무너져 **커밋할 내용이 있을 때만** 판정을 못 냈습니다. 스위트 26 failed → **0 failed / 579 passed**.
>
> 그 밖에: Unity Animator 문자열 린트가 수신자 이름을 `animator` 로 못박아 뒀던 탓에 실제 쓰이는 5변형 중 1개만 잡던 것을 넓혔습니다(`_anim`·`playerAnimator` 등 — 대신 Material 셰이더 프로퍼티와 `EditorPrefs` 는 계속 통과). `detect-gaps` Check 5 는 production 경로만 override 체계 밖에 하드코딩돼 있어 계획 문서를 다른 데 두는 프로젝트가 매 세션 오경보를 끌 방법이 없었는데, `productionRoots` 키가 생겼습니다. 그리고 `/socratic` — 레슨을 **기록**하는 쪽만 있고 가르치는 쪽이 없었습니다.
>
> **v0.6.3:** `CLAUDE.md` 가 다시 **편향 교정 파일**이 됐습니다 (214 → 169줄). 214줄 중 약 90줄은 에이전트가 파일을 열어보면 알 수 있는 것들이었고, 그 줄들은 토큰만 쓰는 게 아니라 **정작 행동을 바꾸는 지시의 밀도를 떨어뜨립니다** — 컨텍스트 창에는 목차도 강조도 없으니까요. 스테이지별 담당 에이전트는 지운 게 아니라 [docs/agent-packs.yaml](docs/agent-packs.yaml) 로 **이관**했습니다(그 매핑은 CLAUDE.md 본문에만 있었고 카탈로그에는 없었습니다). 대신 그동안 없던 **구현 편향 교정 8줄**이 들어갔습니다 — 기존의 "하지 마라"는 전부 오케스트레이션 편향이었지, 이 파일이 라우팅하는 45개 에이전트가 실제로 쓰는 *코드*에 대한 것은 하나도 없었습니다.
>
> 그리고 결정적 게이트 계약의 구멍 넷을 막았습니다. **`scripts/verify_policy.py`** — 지금까지 모든 게이트는 "일이 끝났나"만 판정했고 "우리가 말한 방식대로 했나"는 아무도 안 봤습니다. 테스트를 skip 처리해 통과시킨 스토리는 정상 완료와 **기록상 구별되지 않았습니다**(unsafe-success). **`scripts/verify_trajectory.py`** — 이 플러그인의 라우팅은 카탈로그 × agent-packs 의 **조인**이라 어느 한쪽 한 줄이 바뀌면 그 phase 의 모든 스킬이 조용히 다르게 라우팅됩니다. 골든 궤적으로 잠갔습니다. **`scripts/gate_report.py`** — "출력을 파싱해 판정을 재도출하지 말라"는 v0.6.0 의 금지는 게이트가 산문만 뱉는 동안 **지킬 수가 없었습니다**. 4필드 공통 봉투(`status`/`reason`/`next_action`/`evidence`)로 그 나머지 반쪽을 채웠고, `status` 는 `exit_code` 의 순수 함수라 "ABORT 를 출력하며 0 으로 종료"가 표현 불가능해집니다. **[rules/verify-route.md](rules/verify-route.md)** — `route-hint` 는 *생산*만 라우팅했습니다. 검증은 **되돌릴 수 있는가**(R1~R4)로 라우팅하고, R4(되돌릴 수 없거나 사용자에게 비용이 가는 것)는 무인 실행하지 않습니다. 배경: [docs/design/v0.6.3-context-density-plan.md](docs/design/v0.6.3-context-density-plan.md).
>
> `hooks/validate-assets.sh` 는 "ERRORS (Blocking)" 을 출력하면서 `exit 1` 로 끝나고 있었습니다 — Claude Code 훅에서 차단은 `exit 2` 이고 1 은 Claude 에게 전달되지 않으므로, 그 분기는 **판정을 낸 적이 없었습니다.** 그리고 `$remove-bg` 합류.
>
> **v0.6.2:** hook 이 프로젝트 레이아웃을 읽습니다. 그동안 `detect-gaps.sh` · `validate-commit.sh` · `validate-assets.sh` 는 `src/` · `assets/` · `design/gdd/` 를 박아두고 있어서, `Assets/` 와 `ProjectSettings/` 를 강제하는 Unity 프로젝트에서는 스크립트 60개짜리 코드베이스를 "**NEW PROJECT**" 로 진단하거나(그 분기가 `exit 0` 이라 정작 갭 검사 1~5는 한 번도 못 돌았습니다) 커밋마다 아무것도 못 잡고 지나갔습니다. 감지를 [hooks/lib/detect-layout.sh](hooks/lib/detect-layout.sh) 한 곳으로 모으고, 코드 검사는 경로 대신 **확장자** 기준으로 바꿨습니다. 명명 규칙은 엔진별로 갈라집니다 — Unity 의 `PlayerController.cs` 는 클래스명과 맞춰야 하는 올바른 이름이므로 소문자 강제 대상이 아닙니다. 웹/일반 프로젝트 동작은 그대로이고, `.claude/studio-layout.json` 으로 덮어쓸 수 있습니다. PostToolUse matcher 에 `MultiEdit` 도 추가.
>
> **v0.6.1:** 결정론적 흐름이 **product 트랙까지** 확장됐습니다. `docs/workflow-catalog.yaml` 이 game/product **듀얼 트랙**(스키마 v2)이 되고, 스텝 간 의존이 `depends_on` 으로 명시되며, 단계 완료 판정은 새 게이트 **`scripts/check_phase.py`** 가 exit code 로 내립니다(`0` 완료 / `1` 진행중 / `2` 의존 위반 — 건너뛴 스텝 탐지 / `3` 판정불가). `$help` 와 `$project-stage-detect` 는 이제 직접 glob 하지 않고 이 판정을 읽습니다. 약속만 있던 **`$create-prd`** 도 합류 — product 트랙의 `$design-system` 대응물입니다.
>
> **v0.6.0:** 게이트가 더 이상 자기 채점이 아닙니다. 스크립트 **exit code 가 판정**이고(`0` 통과 / `1` 경고 / `2` 중단 / `3` 판정불가), 돌지 못한 게이트는 통과로 읽지 않습니다 — 계약: [docs/deterministic-gates.md](docs/deterministic-gates.md). `$self-loop` 은 채점 전에 "스크립트가 판정할 수 있는가"를 먼저 묻고, `$smoke-check` 은 러너 출력을 해석하는 대신 exit code 를 직접 읽습니다.
>
> 함께 들어온 것 — 한글 윤문 **writing 팩**(`$humanize-korean` · `$humanize` · `$humanize-redo` + 에이전트 4종, 전 프로젝트 타입에서 활성), **콜 수 라우팅 규칙**([rules/route-hint.md](rules/route-hint.md) — 절감은 모델 교체가 아니라 콜 수 축소에서 온다), 그리고 **리포 최초의 테스트와 CI**(pytest 185건 × Python 3.11/3.12/3.13 + SSOT drift 차단 + 스킬 구조 린트). 윤문 자산 출처: [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) (MIT — [NOTICE.md](NOTICE.md)). 설계 배경: [docs/design/v0.6.0-integration-plan.md](docs/design/v0.6.0-integration-plan.md).

> **v0.4.0 신규:** 에이전트가 `core` / `game` / `product` 3개 팩으로 분리됩니다. SessionStart 훅(`detect-project-type.sh`)이 프로젝트를 자동 감지(`game` / `web` / `mobile` / `service`)해 **해당 팩만 활성화** — 게임 프로젝트엔 게임 에이전트, 앱/웹 프로젝트엔 제품 에이전트(`product-manager`, `frontend/backend/mobile/data/growth-engineer`, `technical-writer`)만 라우팅됩니다. 분류 기준: [docs/agent-packs.yaml](docs/agent-packs.yaml). 설계 배경: [docs/design/v0.4.0-product-domain-pack.md](docs/design/v0.4.0-product-domain-pack.md).

실제 게임 스튜디오 구조를 그대로 모사: 디렉터(creative / technical / producer)가 부서장(design / programming / art / audio / narrative / QA)을 조율하고, 부서장이 다시 스페셜리스트(gameplay programmer / level designer / economy designer 등)를 조율합니다. 모든 디자인 에이전트와 템플릿은 검증된 게임 디자인 이론(MDA, Self-Determination Theory, Flow State, Bartle Player Types)에 기반합니다.

엔진 무관(Engine-agnostic). Godot, Unity, Unreal, GameMaker, 또는 커스텀 엔진 모두에서 동작합니다.

## 목차

- [무엇이 들어있나](#무엇이-들어있나)
- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [v0.2.0 신규 — 거버넌스/워크플로우 자산 사용 가이드](#v020-신규--거버넌스워크플로우-자산-사용-가이드)
- [권장 디렉터리 구조](#권장-디렉터리-구조)
- [커스터마이징](#커스터마이징)
- [라이선스](#라이선스)

---

## 무엇이 들어있나

### 역할 가이드 (45종)

디렉터 · 부서장 · 스페셜리스트 — 실제 스튜디오 조직도 그대로. **core**(전 도메인 공통) + **game**(게임 전용) + **product**(앱/웹/서비스 전용) + **writing**(한글 윤문, 전 타입 활성) 4팩:

- **product 팩 (v0.4.0 신규)**: `product-manager`, `frontend-engineer`, `backend-engineer`, `mobile-engineer`, `data-engineer`, `growth-engineer`, `technical-writer`
- **writing 팩 (v0.6.0 신규)**: `humanize-monolith`, `humanize-diagnostician`, `humanize-finalizer`, `korean-ai-tell-taxonomist` — 게임의 패치노트·GDD 에도, 제품의 릴리스 노트·랜딩 카피에도 똑같이 필요하므로 도메인으로 게이팅하지 않습니다

아래는 game/core 로스터:

- **디렉터**: `creative-director`, `technical-director`, `producer`
- **디자인**: `game-designer`, `systems-designer`, `economy-designer`, `level-designer`, `narrative-director`, `world-builder`, `writer`, `live-ops-designer`
- **프로그래밍**: `lead-programmer`, `gameplay-programmer`, `ui-programmer`, `ai-programmer`, `engine-programmer`, `network-programmer`, `tools-programmer`, `prototyper`
- **아트/오디오**: `art-director`, `technical-artist`, `audio-director`, `sound-designer`
- **QA/Ops**: `qa-lead`, `qa-tester`, `performance-analyst`, `security-engineer`, `accessibility-specialist`, `localization-lead`, `release-manager`, `devops-engineer`
- **UX/커뮤니티/분석**: `ux-designer`, `community-manager`, `analytics-engineer`

### Skill (91종)

개발 단계별로 정리:

- **프리프로덕션**: `$start`, `$brainstorm`, `$map-systems`, `$design-system`, `$review-all-gdds`, `$consistency-check`, `$create-architecture`, `$architecture-decision`, `$architecture-review`, `$create-control-manifest`, `$art-bible`, `$ux-design`, `$ux-review`, `$setup-engine`, `$adopt`, `$gate-check`
- **스프린트/프로덕션**: `$create-epics`, `$create-stories`, `$story-readiness`, `$dev-story`, `$story-done`, `$quick-design`, `$sprint-plan`, `$sprint-status`, `$scope-check`, `$estimate`, `$propagate-design-change`, `$reverse-document`, `$asset-spec`, `$remove-bg`, `$asset-audit`
- **코드 품질**: `$code-review`, `$tech-debt`, `$design-review`
- **QA**: `$qa-plan`, `$test-setup`, `$test-helpers`, `$test-evidence-review`, `$test-flakiness`, `$regression-suite`, `$smoke-check`, `$soak-test`, `$bug-report`, `$bug-triage`, `$balance-check`, `$playtest-report`, `$content-audit`
- **팀 오케스트레이션**: `$team-audio`, `$team-combat`, `$team-level`, `$team-live-ops`, `$team-narrative`, `$team-polish`, `$team-qa`, `$team-release`, `$team-ui`
- **릴리스/Ops**: `$release-checklist`, `$launch-checklist`, `$day-one-patch`, `$hotfix`, `$patch-notes`, `$changelog`, `$milestone-review`, `$retrospective`, `$security-audit`, `$perf-profile`, `$localize`, `$onboard`, `$project-stage-detect`, `$help`, `$prototype`, `$skill-test`, `$skill-improve`
- **메타 감사 (v0.2.0 신규)**: `$sot-audit` (다중 source-of-truth 정합성 감사), `$legacy-purge` (피봇/마이그레이션 잔재 청소), `$doc-relink` (문서 재편 시 링크 무파손 이동 — baseline → git mv → 스크립트 2패스 재계산, exit code 게이트)
- **공간 감사 (신규)**: `$spatial-audit` — 이미 만들어진 Unity 레벨을 건축 4렌즈(매싱·동선·조망은신·길찾기)로 감사. 읽기 전용, 장르별(`sp`/`pvp`/`open`) 판정
- **영상 (신규)**: `$video-brief` — 촬영 **전에** 결정한다. 목적·구조·샷 리스트·권리·플랫폼 요건(스토어 트레일러 / 제품 데모 / 숏폼 / 데브로그). 편집은 외부 도구에 위임([docs/video-production-sources.md](docs/video-production-sources.md))
- **거버넌스 (v0.2.0 신규)**: `$governance-bible-init` (사운드/아트/내러티브 등 도메인 Bible 부트스트랩), `$api-cost-gate` (유료 AI API 호출 전 4건 명시 승인 게이트)
- **product 트랙 (앱/웹/서비스)**: `$product-concept` (제품 단위 개념 — 문제·사용자·가치·범위 티어. `$create-prd` 가 이걸 읽고, 없으면 실패한다) → `$create-prd` (기능 단위 PRD) → `$ux-design` → `$gate-check architecture`
- **Codex 오케스트레이션**: `$studio-orchestrator` — 여러 전문 분야가 필요한 요청을 가장 작은 역할 조합으로 라우팅하고 Codex 서브에이전트 결과를 통합·검증

### Hooks

- `UserPromptSubmit`: 매 작업 전 모델 권고(결정적 작업은 모델 불필요, 판단 작업은 세션 모델 유지); opt-in effort 관찰
- `SessionStart`: 프로젝트 컨텍스트 로드 + 누락 문서 감지 + 프로젝트 타입 판별
- `PreToolUse` (`exec_command`/`Bash`): git 커밋/푸시 검증
- `PostToolUse` (`apply_patch` 및 편집 alias): 한 패치의 모든 변경 파일을 추출해 자산 명명·skill 변경·Unity 안전장치 검사
- `PreCompact/PostCompact/SessionEnd`: JSON 문맥 복구 및 실제 세션 종료 로깅
- `SubagentStart/Stop`: 에이전트 활동 로깅

#### 레이아웃 감지 (v0.6.2+)

경로를 건드리는 hook 은 [hooks/lib/detect-layout.sh](hooks/lib/detect-layout.sh) 에서 레이아웃을 받아옵니다. 엔진을 판별해(unity / godot / unreal / gamemaker / generic) 소스 루트·설계 문서 루트·자산 루트·명명 규칙을 정하고, `Library/` `Temp/` `node_modules/` 같은 생성물은 순회에서 뺍니다.

| | Unity | Godot | Unreal | 일반 |
|---|---|---|---|---|
| 소스 루트 | `Assets` | `.` | `Source` `Plugins` | `src` `lib` `app` `packages` |
| 설계 문서 | 존재하는 후보 전부 (`design/gdd` `Documents` `Docs` `docs/design` …) | | | `design/gdd` `product/prd` `docs/design` |
| 명명 규칙 | `pascal` | `snake` | `pascal` | `snake` |

`.codex/studio-layout.json`으로 덮어씁니다. `.claude/studio-layout.json`과 `.claude/settings.json`은 전환 기간의 읽기 전용 fallback입니다. 계약과 hook 추가 규칙: [docs/hooks-reference.md](docs/hooks-reference.md).

#### Unity opt-in (v0.2.0+)

플러그인이 Unity 프로젝트(`Assets/` + `ProjectSettings/` 존재)를 자동 감지하면 두 advisory hook 이 활성화됩니다:

- `unity-meta-check.sh` — `.cs`/`.shader`/`.prefab` 등을 짝 `.meta` 없이 작성한 경우 경고 (다른 머신에서 GUID 깨짐 방지)
- `unity-animator-string-lint.sh` — `Animator.SetBool("name", ...)` 같은 문자열 lookup 패턴 감지 시 경고 (`StringToHash` 캐싱 권고)

추가로 수동 opt-in git pre-commit 템플릿(`templates/githooks/unity-pre-commit`)이 있어 `.meta` 누락 커밋을 *차단*. 활성화는 [docs/engine/unity-setup.md](docs/engine/unity-setup.md) 참고.

비-Unity 프로젝트에서는 모두 즉시 종료(silent exit) — 영향 없음.

### 템플릿 & 룰 (v0.2.0 신규)

엔진/장르/플랫폼 무관하게 적용되는 워크플로우 자산:

| 자산 | 위치 | 용도 |
|---|---|---|
| 회의록 템플릿 | [docs/templates/meeting-template.md](docs/templates/meeting-template.md) | 헤더 메타박스 + D-table 결정 + 메모리화 프로토콜 |
| API CLI 템플릿 | [docs/templates/api-cli-template.py](docs/templates/api-cli-template.py) | pay-as-you-go 외부 AI API wrapper 스캐폴드 (env 로드 / 인증 / 비동기 폴링 / 동기 binary / 다운로드) |
| 제품 PRD 템플릿 | [docs/templates/product-requirements-document.md](docs/templates/product-requirements-document.md) | product 트랙 제품 단위 PRD — 문제·페르소나·코어 루프·MVP 범위·기능/비기능 요구사항·KPI·범위 외. `$create-prd` 의 기능 단위 PRD 와 층위가 다르다 |
| 사람 액션 큐 템플릿 | [docs/templates/human-action-queue.md](docs/templates/human-action-queue.md) | 에이전트가 대행 못 하는 일만 모으는 상시 큐. 실행(🔴)/판단(🟡) 분리 + "왜 사람인가" 열 + 완료는 삭제 아닌 강등. `production/human-actions.md` 에 두면 SessionStart 훅이 알린다 |
| 토큰 효율 룰 | [docs/rules/token-efficiency.md](docs/rules/token-efficiency.md) | R1~R6 (커밋 5~15줄 / 회의록 80줄 / 일괄 작업 보고 / 병렬 read / 메모리 규율 / 응답 길이) |
| 자산 정리 룰 | [docs/rules/artifact-organization.md](docs/rules/artifact-organization.md) | 3-zone 규율 (Workshop / Curated / Engine) + prefix 명명 규칙 + .prompt.txt 동반 룰 |

---

## 설치

### 옵션 1 — GitHub 마켓플레이스에서 설치 (권장)

```bash
codex plugin marketplace add dawn840705/codex-code-studios
codex plugin add codex-code-studios@code-studios
```

마켓플레이스 스냅샷을 새로 받으려면:

```bash
codex plugin marketplace upgrade code-studios
```

### 옵션 2 — 로컬 마켓플레이스 (개발 / 포크 시)

```bash
git clone https://github.com/dawn840705/codex-code-studios.git /path/to/codex-code-studios
codex plugin marketplace add /path/to/codex-code-studios
codex plugin add codex-code-studios@code-studios
```

설치 후 Codex가 `hooks/hooks.json`의 훅을 처음 실행할 때 신뢰 검토가 표시될 수 있습니다. 내용을 확인한 뒤 승인하세요.

### 옵션 3 — 개발 중 직접 검증

```bash
python3 /path/to/codex-code-studios/scripts/lint_skills.py \
  /path/to/codex-code-studios/skills \
  /path/to/codex-code-studios/skills/studio-orchestrator/references/roles
```

`rules/*.md`는 스킬이 읽는 워크플로우 자료입니다. Codex 명령 승인 정책인 `.codex/rules/*.rules`로 복사하지 마세요.

---

## 빠른 시작

설치 후 신규 게임 프로젝트에서:

1. `$start` — 첫 사용 onboarding. 현 위치 파악 후 적합한 워크플로우로 안내
2. `$setup-engine` — 엔진(Unity / Unreal / Godot / GameMaker / 커스텀) + 버전 핀
3. `$brainstorm` — 컨셉 0 에서 구조화된 게임 컨셉 문서까지 가이드
4. `$map-systems` — 컨셉을 시스템 단위로 분해, 우선순위 도출
5. `$design-system <system>` — 각 시스템의 GDD 작성
6. `$create-architecture` → `$create-epics` → `$create-stories` → `$dev-story`

진행 중인 프로젝트라면: `$adopt` 가 기존 자산을 감사하고 마이그레이션 계획을 만들어줍니다.

---

## v0.2.0 신규 — 거버넌스/워크플로우 자산 사용 가이드

v0.2.0 부터 추가된 자산은 *AI 생성 자산을 다루는 1인/소규모 개발 워크플로우*에 특히 유용합니다.

### 도메인 Bible 부트스트랩 (`$governance-bible-init`)

사운드 / 아트 / 내러티브 등 *창작 도메인* 마다 Anchor + Bible 패턴을 자동 부트스트랩:

```bash
$governance-bible-init sound chapter-1
$governance-bible-init art chapter-1
$governance-bible-init narrative chapter-1
```

→ `Documents/<도메인>Design/Anchors/` 폴더 + Bible README.md(톤 필터 + 명명 규칙 + 카테고리 표) 자동 생성. 첫 anchor 자산은 `Anchors/` 안에 `mus_*.mp3` / `char_*.png` 등 prefix 명명으로 저장 + 동명 `.prompt.txt` (재현 가능한 호출 명령) 동반.

이후 모든 신규 자산은 *Anchor 와 5~10초 A/B 비교 → 채택/재시도(1회)/기각* 의사결정 워크플로우 적용. 드리프트 방지의 핵심 메커니즘.

### 유료 API 호출 게이트 (`$api-cost-gate`)

Suno / ElevenLabs / Midjourney / Tripo / OpenAI 등 모든 pay-as-you-go AI 호출 *전*에 4건 disclosure 강제:

```bash
$api-cost-gate suno combat-bgm-30s
```

표시 항목:
1. 호출 종류 (정확한 endpoint / model / mode)
2. 비용 추정 (credits / characters / 달러 + 현재 잔액)
3. 목적 (무엇을 / 왜)
4. 활용 (어디에 저장 / 어떻게 평가 / 채택 기준)

→ 사용자 명시 OK 후에만 호출 실행. **Auto mode 도 우회 X.**

### 배경 제거 (`$remove-bg`)

[remove.bg API](https://www.remove.bg/api) 로 스프라이트·캐릭터·제품 이미지의 배경을 제거한다. 단일 파일 / 폴더 배치 / 에셋 매니페스트 연동을 모두 지원하며, 위의 4건 disclosure 게이트가 스킬 안에 내장돼 있다 — `$api-cost-gate` 를 따로 부를 필요가 없다.

```bash
export REMOVE_BG_API_KEY=<key>       # https://www.remove.bg/dashboard#api-key

$remove-bg design/assets/raw/hero.png            # 단일
$remove-bg design/assets/raw/ --type graphics    # 폴더 배치
$remove-bg manifest:tower-defense                # 매니페스트 연동
```

판정은 스크립트가 내린다 (`scripts/removebg.py`, 표준 라이브러리만 사용):

```bash
python3 scripts/removebg.py account                      # 잔액 조회 (무과금)
python3 scripts/removebg.py estimate <경로> --check-balance --json   # 견적 (무과금)
python3 scripts/removebg.py run <경로> --out <디렉터리> --max-calls 20
```

- **exit code 가 판정**: `0` 전건 성공 · `1` 부분 실패 · `2` 중단(전건 실패 / 402 크레딧 부족 / 403 인증 실패 / `--max-calls` 초과) · `3` 실행 불가(키 없음 — 통과 아님)
- **`--size preview` 가 기본값**: preview ≈ 0.25 크레딧, full ≈ 1 크레딧. 4배 차이라 리뷰용은 preview, 최종 프로덕션 아트만 full.
- **`--max-calls` 는 안전벨트**: 견적과 실행 사이에 입력이 늘어나면 승인 범위를 넘겨 과금하지 않고 중단한다.
- 확정 과금액은 응답 헤더 `X-Credits-Charged` 실측값으로 리포트(`removebg-report.json`)에 기록된다.
- API 키는 CLI 인자로 받지 않는다 (셸 히스토리·프로세스 목록 노출). 환경변수 또는 `--api-key-file` 만 허용.

### 다중 source-of-truth 감사 (`$sot-audit`)

FSM / 입력 바인딩 / 세이브 스키마 / 로컬라이제이션 / 오디오 mixer / 셰이더 uniform / 네트워크 메시지 등 *여러 곳에 정의가 흩어진* 시스템의 정합성을 N-witness 매트릭스로 감사:

```bash
$sot-audit player-fsm \
  doc=design/specs/player-fsm.md \
  enum=src/PlayerStateType.cs \
  asset=assets/animator/PlayerAnim.controller \
  callsites=src/PlayerController.cs
```

→ 심각도(🚨 High / ⚠️ Medium / ℹ️ Low) 분류된 mismatch 보고서. silent-fail 위험을 *런타임 사고 전*에 검출.

### 마이그레이션 잔재 청소 (`$legacy-purge`)

장르 피봇 / API deprecation / 플랫폼 변경 / 아키텍처 재작성 후 잔존하는 레거시 코드/문서/자산을 카테고리별 grep 으로 감사:

```bash
$legacy-purge mobile-vertical pc-horizontal "Assets/02.Scripts/**"
```

→ 카테고리별 발견 표 + 정책 문서 cross-reference. **자동 삭제 X** — 인간 검토 필수.

### 회의록 / API CLI 템플릿

새 회의 작성 / 새 외부 API wrapper 작성 시 즉시 사용 가능한 스캐폴드:

- `cp <plugin>/docs/templates/meeting-template.md Documents/Meetings/YYYY-MM-DD-<주제>.md`
- `cp <plugin>/docs/templates/api-cli-template.py Tools/<NewService>API/<service>.py`

각 템플릿 내부의 `⚠️ FIXME` 항목만 채우면 됩니다.

### 워크플로우 룰 핀

새 프로젝트의 `AGENTS.md`에 필요한 항목을 추가하면 Codex가 프로젝트 지침으로 읽습니다:

```markdown
## 워크플로우 룰

- 토큰 효율: docs/rules/token-efficiency.md (R1~R6)
- 자산 정리: docs/rules/artifact-organization.md (Workshop / Curated / Engine 3-zone + prefix 명명)
- 회의록: docs/templates/meeting-template.md 포맷 사용
```

---

## 권장 디렉터리 구조

에이전트와 skill 은 프로젝트 루트에 다음 구조를 가정합니다:

```
design/gdd/                # GDD 문서
production/sprints/        # 스프린트 계획
production/bugs/           # 버그 리포트
src/                       # 소스 코드 (엔진별)
tests/                     # 테스트 파일
.codex/                    # Code Studios 프로젝트 상태 (선택)
  └── studio/
      └── technical-preferences.md   # 엔진 + 버전 핀

# v0.2.0 자산 정리 룰 적용 시 (artifact-organization.md):
Tools/<Service>API/output/        # 작업장 (gitignore)
Documents/<Domain>Design/Anchors/ # 도메인별 Bible + anchor 자산
Documents/Meetings/               # 회의록
Documents/api-cost-log.md         # 유료 API 호출 누적 기록
```

skill 들이 진행에 따라 자동으로 폴더를 생성합니다.

---

## 커스터마이징

- **프로젝트 지침**: 프로젝트 루트의 `AGENTS.md`에 팀 규칙과 로컬 제약을 기록합니다.
- **전문 역할 추가**: `$studio-orchestrator`가 읽을 별도 역할 가이드를 프로젝트 문서에 두고, 위임 프롬프트에 필요한 부분만 포함합니다.
- **워크플로우 자료**: 이 플러그인의 `rules/*.md`는 스킬 참고자료이며 Codex execpolicy 파일이 아닙니다.

---

## 상태 & 단계

- 프리프로덕션 · 프로덕션 · 폴리시 & QA · 릴리스 · 라이브옵스 — 모든 단계 커버.
- `$studio-orchestrator`는 *현재 단계*와 관련된 역할 가이드만 읽어 Codex 서브에이전트에 전달합니다. 전체 매핑은 `docs/agent-packs.yaml` 참고.

---

## 변경 이력

자세한 버전별 변경 사항은 [CHANGELOG.md](CHANGELOG.md) 참고.

- **v0.3.0** (2026-05-17) — Unity UI/UX 영구 룰 5건 + `UIAutoSelectGuardian.cs` helper (`docs/engine/unity-ui-guidelines.md`, `templates/unity/`) + Unity scene-loading anti-pattern (`docs/engine/unity-scene-loading-patterns.md`) + Unity MCP workflow 패턴 (`docs/engine/unity-mcp-workflow.md`) + 서브 에이전트 병행 호출 룰 (`rules/subagent-collaboration.md`, `docs/templates/subagent-meeting-template.md`)
- **v0.2.0** (2026-05-04) — Unity opt-in 안전장치 + 메타 감사 skill (sot-audit, legacy-purge) + 거버넌스/워크플로우 자산 (governance-bible-init, api-cost-gate, 회의록/API CLI 템플릿, token-efficiency/artifact-organization 룰)
- **v0.1.0** (2026-04-22) — 초기 릴리스. 34 에이전트 + 72 skill + production hooks.

---

## 감사

Cannon Kingdom 프로젝트에서 만들어 검증한 후, 게임 프로젝트 간 이식성을 위해 독립 플러그인으로 추출. v0.2.0 의 거버넌스/워크플로우 자산은 StarDiver(Unity 6 PC/콘솔 로그라이트 커버 슈터) 프로덕션에서 누적된 노하우의 1차 회수.

---

## 라이선스

MIT
