# Changelog

## Unreleased

## v0.7.3 — 2026-09-17

### Added — pre-task model recommendation

- `UserPromptSubmit` now recommends a standard tool/script for deterministic
  work and retaining the current session model for judgment work.
- The recommendation is advisory only: it never switches models or changes
  settings, explicit user model choices win, and opt-in effort observation is
  unchanged.
- The prompt hook now invokes its Python entry point directly, avoiding a
  Windows failure where `bash` resolved to an unconfigured WSL launcher.

### Added — quota-efficiency tips from a third-party OpenAI Plus guide

- Reviewed a 2026-09-15 X post summarizing OpenAI Help documentation on
  ChatGPT Work/Codex shared-quota management (model tiers, reasoning effort,
  Fast mode, reference-doc scoping, upfront completion criteria). The
  underlying `help.openai.com` pages were not independently fetched — treated
  as a secondary source. Full review and what was deliberately not adopted:
  [docs/reasoning-effort.md](docs/reasoning-effort.md#2026-09-17-추가--astrasolterraluna-할당량-절약-팁-채택).
- Added `docs/rules/token-efficiency.md` **R7** (scope reference-doc reads to
  the scenario instead of reading everything every time) and **R8** (state
  completion criteria and delegation boundaries upfront instead of
  round-tripping on ambiguous micro-decisions).
- Reinforced `rules/route-hint.md`'s Model axis: pick the tier/effort lane
  before dispatching — downgrading mid-task doesn't refund already-spent
  quota, and a low-effort pass on a stronger model can beat a high-effort
  pass on a weaker one.

## v0.7.2 — 2026-09-12

### Added — 런타임 모드: 이 프로젝트를 누가 작업하는지

`claude-code-studios` 와 갈라진 뒤로 한 프로젝트는 Codex 단독, Claude 단독, 또는
둘이 분업 중 하나로 진행된다. 셋 다 "풀 스튜디오로 행동한다"가 정답이 아닌데 세션이
그걸 알아낼 방법이 없었다. `rules/runtime-modes.md` 가 그 자리를 만들고,
`AGENTS.md` 에 진입점을 달았다.

- **모드는 `production/runtime.txt` 한 줄이 정본이다** (`codex` · `claude` ·
  `split`, 없으면 `codex`). `CLAUDE.md` 나 `.claude/` 가 보인다는 건 Claude Code 가
  언젠가 거기 설정됐다는 뜻이지 지금 이 작업을 하고 있다는 뜻이 아니다.
- **분업 시 경로 단위 소유권 분할을 먼저 적는다.** 두 런타임은 세션·컨텍스트·도구
  로그를 공유하지 않으므로 덮어쓰기가 양쪽 모두에게 보이지 않고, 진 쪽도 성공했다고
  보고한다.
- **강점 분담은 미확정으로 남겼다** — 규칙이 그걸 지어내지 않는다.

### Fixed — 루트 `CLAUDE.md` 가 없는 에이전트 45개를 안내하고 있었다

`AGENTS.md` 는 `CLAUDE.md` 를 0.7 전환용 호환 껍데기로 규정했지만, 파일 내용은
`claude-code-studios` 의 옛 가이드가 거의 그대로 남아 `agents/` 45개 · `/skill`
호출 · `.claude/settings.json` 을 안내했다. 이 트리에 `agents/` 는 없다 — 45개 역할
가이드는 `skills/studio-orchestrator/references/roles/` 의 참조다. Claude Code 로 이
저장소를 열면 그대로 틀린 지시를 받았다.

225줄을 86줄로 줄이고, **무엇이 여기 없는지**를 표로 먼저 세웠다. 런타임 무관한
「작업 원칙」과 종료 코드 계약은 남기고, Claude 쪽 스튜디오 기계장치(도메인 팩·에이전트
스폰 규칙·진입점 목록)는 덜어냈다. 판정 권한은 `AGENTS.md` 에 있다고 명시했다.

### Changed — 공통 제작·검증 규칙 보강

- Unity 검증에서 저장 데이터의 부재와 유효한 빈 값을 구별하고, 런타임 초기화·입력
  주입·모달 복귀·배칭·셰이더·좌표 스케일을 실제 엔진 경로와 독립 기대값으로 확인하도록
  테스트 원칙을 보강했다.
- 거부 테스트가 의도한 실패 원인을 검증하고, 실패·해제 과정에서 변경한 전역 및 하위
  상태를 모두 복원하도록 회귀 절차를 강화했다.
- 원본 계측 증빙의 바이트 보존과 복구 검증, Blender 편집 원본의 작업 범위 격리,
  내보내기 이름 안정화와 Unity 반입 후 확인 절차를 공통 자산 규칙에 반영했다.

## v0.7.1 — 2026-09-07

### Added — anchor-based 3D art production

- Added the reviewed anchor → consistent views → generated model → Blender
  editing, rigging and animation workflow, connected to studio orchestration,
  asset specifications and read-only delivery audits.
- Required view/anatomy checks, saved-source reopening and independent export
  checks, including poses between baked samples. Initial evidence covers a
  stylized armored-creature pilot, not a universal production success rate.
- Kept asset-specific budgets, paid-call authorization, visual adoption and
  engine verification separate.

### Changed — shared project policy and asset recovery

- Recorded how validated project practices enter the plugin source and how
  source changes differ from installed-plugin updates.
- Strengthened generated-asset delivery, dependency recovery and cross-machine
  handoff guidance, plus preservation rules for inactive worktrees.

### Added — experimental reasoning effort observation

- Prepared a 27-run mechanical-task experiment with balanced arm order, local
  environment checks, explicit standalone execution and an account-headroom gate.
  Expanded live execution remains deferred; synthetic checks are not efficacy evidence.

- Added a frozen-snapshot three-arm pilot harness and exact-answer verifier.
  [First live pilot](docs/effort-pilot-20260907.md): three completed read-only
  runs; no efficacy or total-cost savings claim from this small, confounded sample.

- Project opt-in `UserPromptSubmit` observation, evidence-based effort selection,
  and a fixed-model, explicitly authorized read-only Codex CLI runner.
- Separate selected, dispatched and unconfirmed runtime effort records; no
  automatic retries, model switching, global config edits or reduced gates.
- Offline boundary/encoding tests and an opt-in loopback probe of real CLI
  request serialization. Live quality/cost comparison remains pending.
- [Capability research, usage and experiment protocol](docs/reasoning-effort.md).

### Changed — v0.7.0 Codex plugin migration

- Added the Codex manifest at `.codex-plugin/plugin.json` and the shareable
  marketplace entry at `.agents/plugins/marketplace.json` under the new
  `codex-code-studios` identity.
- Converted 90 existing workflows to Codex `SKILL.md` frontmatter and
  `$skill-name` invocation, then added `$studio-orchestrator` (91 total).
- Moved 45 Claude agent definitions into
  `skills/studio-orchestrator/references/roles/`. They now act as selectively
  loaded persona references for self-contained Codex subagent prompts.
- Added `hooks/hooks.json`; ported file validation to native `apply_patch`
  payloads, returned advisory context as JSON, changed shutdown logging from
  `Stop` to `SessionEnd`, and excluded the unsupported `Notification` event.
- Moved project-owned technical preferences to
  `.codex/studio/technical-preferences.md` and layout overrides to
  `.codex/studio-layout.json`. Legacy `.claude` layout files remain read-only
  fallbacks for the transition release.
- Updated installation, quick-start, hook, role, test, and CI documentation for
  Codex. `.claude-plugin/` and `CLAUDE.md` remain as one-release compatibility
  metadata, not as the new source of truth.

## v0.6.4 — 2026-08-26

### Fixed — cp949 콘솔에서 게이트가 거짓 FAIL: 「종료 코드가 판정이다」가 인코딩 하나로 뒤집혔다

`CLAUDE.md § Deterministic gates` 는 stdout 을 읽고 판정을 재해석하지 말라고
못박는다. 그런데 Windows 한국어 콘솔(cp949)에서 게이트 스크립트가 리포트의
em-dash(—) 를 인코딩하지 못해 `UnicodeEncodeError` 로 죽었고, 그 죽음이 `exit 1`
로 나왔다. 규칙대로 종료 코드를 믿은 호출자는 **통과한 작업을 FAIL 로 읽었다.**
`/humanize` · `/dev-story` · `/remove-bg` 가 각자의 게이트를 부르는 순간 그대로
맞는 자리였다 (`grep -rn PYTHONIOENCODING skills/` → 0건).

**증상 수리** — `scripts/console_encoding.py` 의 `force_utf8()` 을 CLI 진입점 12개
`main()` 첫 줄에서 부른다. 모듈 최상단이 아니라 `main()` 인 이유 = argparse 의
한국어 `--help` 도 같은 보호를 받아야 하고, 스크립트를 import 해서 `main()` 을
부르는 호출자도 같은 경로를 밟아야 한다. `errors="replace"` 는 인코딩을 바꿀 수
없는 예외 환경에서도 게이트가 「못 읽는 글자」때문에 판정을 못 내리는 일이
없게 하려는 것이다. 비ASCII 를 지우는 해법은 쓰지 않았다 — 출력이 한국어인 것은
사양이고, 글자를 없애면 사람이 게이트 리포트를 못 읽는다. 표준 라이브러리만 썼다.

**반대 방향의 같은 병** — 스크립트는 출력을 *인코딩*하다 죽고, 하네스는 자식
출력을 *디코딩*하다 죽었다. `subprocess.run(..., text=True)` 는
`locale.getencoding()` 을 타므로 `PYTHONIOENCODING=utf-8` 로는 고쳐지지 않는
**별개의 실패**다. `tests/` 와 `scripts/` 의 해당 호출 전부에 `encoding="utf-8"`
을 명시했다. 여기에는 배포 코드 인스턴스도 하나 있었다 — `verify_policy.py` 가
`git diff` 를 locale 인코딩으로 읽다가 리더 스레드가 죽어 `stdout` 이 `None` 이
됐고, 게이트는 판정 대신 `AttributeError` 로 무너졌다. 한국어가 섞인 diff 에서만
터지므로 **커밋할 내용이 있을 때만** 무너지는, 작업 트리가 깨끗한 동안에는
보이지 않는 결함이었다.

**재발 방지가 본체** — 기존 테스트는 이 버그를 못 잡았다. 검사 대상 스크립트를
`import` 해서 함수를 직접 불렀고, **import 경로에는 콘솔 인코딩이라는 것이
존재하지 않는다.** 그래서 `verify_trajectory.py` 가 CLI 로는 exit 1 로 죽는
순간에도 스위트는 초록이었다. 없던 층을 하나 만들었다 —
`tests/test_console_encoding.py` 는 `scripts/*.py` 를 훑어 진입점을 찾고(목록
하드코딩 금지 — 하드코딩하면 다음 스크립트를 놓친다), cp949 와 ascii 로 **실제
실행 경로를** 태워 ①죽지 않는지 ②종료 코드가 인코딩과 무관한지 ③비ASCII 가
글자 그대로 살아 있는지를 본다. `--help` 만 때리지 않는다 —
`verify_gates` · `verify_trajectory` 는 `--help` 는 멀쩡하고 정상 실행 경로에서
죽었다. 시나리오 없는 새 진입점은 그 자체로 실패한다.

역방향 검증: `force_utf8()` 호출을 되돌리면 이 층의 124건 중 64건이 FAIL 한다.

**부수 효과** — 스위트가 26 failed / 411 passed 에서 **0 failed / 562 passed** 로.
한국어 Windows 에서 통째로 죽어 있던 `test_hooks_layout.py` 21건이 살아났고,
그래야 bash 훅에 회귀 방어가 생긴다.

### Fixed — Animator 문자열 린트가 5개 중 1개만 잡았다

`hooks/unity-animator-string-lint.sh` 의 패턴이 수신자 이름을 `animator` 로
못박아 뒀다. 앞의 `\b` 때문에 밑줄·접두사가 붙은 이름에는 경계가 생기지 않아
`_anim` · `_animator` · `playerAnimator` · `playerAnim` 이 전부 통과했다. 훅이
조용했던 건 잘 잡아서가 아니라 잡을 게 없어서였다.

판단 축은 원래 수신자의 **타입**이 Animator 인가인데 bash 정규식은 타입을
모른다. 이름 휴리스틱(`anim` 을 포함하는 식별자)으로 넓히되 오탐을 두 가드로
막았다 — 첫 인자가 `"_` 로 시작하면 셰이더 프로퍼티로 보고 제외
(`animMaterial.SetFloat("_BaseColor")` 를 살린다), 수신자에 `anim` 이 없으면
애초에 안 잡힌다 (`EditorPrefs.SetBool`, `serializedObject.SetBool("m_...")`).
타입이 그 자리에 드러난 `GetComponent<Animator>()` 도 함께 잡는다. 권장 해법인
`Animator.StringToHash("...")` 와 해시 접근은 그대로 통과한다.
6변형 × 6부정 = 12건의 픽스처로 양방향을 건다.

### Fixed — `detect-gaps` Check 5 가 우회 불가였다

`lib/detect-layout.sh` 는 `srcRoots` · `designRoots` · `assetRoots` 를 덮을 수
있게 해뒀는데 production 경로만 그 체계 밖에 하드코딩돼 있었다. 계획 문서를 다른
데 두는 프로젝트는 매 세션 오경보를 받으면서 끌 방법이 없었다 — 같은 헬퍼가 그
프로젝트의 design 문서는 정확히 세는데도.

`productionRoots` 키를 같은 override 체계에 추가하고 Check 5 가 그것을 읽는다
(env `STUDIO_PRODUCTION_ROOTS` · `.claude/studio-layout.json` ·
`.claude/settings.json` 3경로 모두). 경고를 끄는 스위치가 아니라 **볼 곳을 바꾸는
것**이다 — 없는 디렉토리를 가리키면 그 경로를 이름 대며 여전히 경고한다.
⚠️ `jq` 없는 환경(Windows Git Bash 기본)에서는 배열 형식을 못 읽고 조용히
기본값으로 돌아간다. 콜론 구분 문자열을 쓸 것 —
`"productionRoots": "Documents:Documents/Queue"`. 이 제약은
`docs/hooks-reference.md` 에 실측과 함께 적었다.

### 함정 — 내용이 바뀌어도 version 이 그대로면 캐시가 안 따라온다

이 항목들은 `version` 을 올리지 않은 채 `0.6.3` 아래에 쌓인다 (이 저장소 관례 —
`test_manifest_sync.py` 가 CHANGELOG 최상단으로 `Unreleased` 를 허용한다).
**설치된 쪽은 자동으로 갱신되지 않는다.** 2026-08-26 StarDiver 가 4커밋 뒤처져
있던 이유가 정확히 이것이었다 — `plugin.json` 의 version 이 그대로여서 자동
업데이트가 안 걸렸다. 릴리스할 때 `plugin.json` 과 `marketplace.json` 의 version
을 같이 올릴 것. 그 전까지 소비자는 수동으로 당겨야 한다.

### Added — `/socratic`: 레슨을 기록하는 쪽만 있고 가르치는 쪽이 없었다

`bevibing/socrates-skill` (MIT, 원저작권 RoundTable02, 조회 시점 별 248) 을 읽고
이 저장소 규약으로 다시 썼다. 파일을 복사하지 않았으므로 vendoring 이 아니라
파생 저작물이고, 출처와 라이선스 전문은 `NOTICE.md` 에 있다.

**왜 이 저장소에 자리가 있는가.** `rules/lesson-capture.md` 는 모든 프로젝트를
강의 소스로 취급하는데, 있는 도구는 `/lesson-log` · `/lesson-review` 둘 다
**기록**이다. 기록한 레슨을 사람 머리에 되돌리는 경로가 없었다. 사장의 전역
원칙("사고는 AI 에 위임할 수 있어도 이해는 위임할 수 없다") 에 대응하는 실행
도구가 비어 있던 셈이다.

**원본에서 가져온 것**: 답을 절대 말하지 않는다는 비타협 규칙, 질문 5종
(clarifying / probing / connecting / counter / hypothetical), 답변 4분기, 금지
패턴 목록. 원본이 73줄로 견고했던 이유가 이 네 덩어리다 — 특히 "틀린 방향일 때
정정하지 않고 모순을 드러내는 질문만 던진다"가 AI 가 습관적으로 정답을 흘리는
경로를 구조로 막는다.

**원본에 없어서 더한 브레이크 둘.** 원본은 독립 튜터라 필요 없었지만 여기는
45 에이전트 프로덕션 플러그인 안이다.

- **안전 우회** — 데이터 손실·보안·돈·라이브 장애가 걸린 순간 튜터링을 멈추고
  사실을 직접 말한다. 이게 없으면 이 스킬이 전역 CLAUDE.md 의 race·partial
  write·idempotency 원칙보다 위에 서게 된다. 데이터를 날리기 직전인 사람에게
  사실을 숨기는 건 교육이 아니다.
- **에이전트 0** — `light` 경로 고정. 서브에이전트는 대화를 못 보므로 답을
  평문으로 반환하고, 그 순간 핵심 규칙이 깨지면서 세션이 끝난다.

**트리거는 좁혔다.** 원본은 "메시지에 socratic 이 있으면" 발동인데, 설계 문서가
소크라테스식 질문법을 *언급만* 해도 켜진다. 명시 호출과 "가르쳐 달라"는 분명한
요청으로 한정하고, 해제 조건("그만", 작업 지시로 복귀)을 본문에 박았다.

부수 갱신: 스킬 수 88 → 89 (`CLAUDE.md` 2곳, `docs/skills-reference.md`,
매니페스트 2개 — `test_manifest_sync.py` 가 파일시스템과 대조한다),
`rules/lesson-capture.md` 스킬 절에 되먹임 경로 한 줄.

### Added — 레벨 난이도를 형용사에서 산수로: RLD + 기승전결

레벨디자인 자료 아카이브(Marcelo Vianna)를 훑어 흡수했다. 커리어·포트폴리오 편은
플러그인과 무관해 버리고, 설계 기법 둘만 남겼다. **둘 다 문서 층이고 Unity 를
건드리지 않는다** — `hera exec` 의 `Debug.Log` 표면화 여부가 아직 미검증이라
2층 공간 스킬은 여전히 보류인데, 이 둘은 그 관문 뒤에 있지 않다.

**⑴ Rational Level Design — `docs/templates/player-metrics.md` 신설.**
Ubisoft 계보의 RLDD(Rational Level Design Document). 캐릭터 능력치를 **먼저 재고**,
모든 챌린지를 그 측정치에 대한 비율로 적는다. 3.9m 점프는 "어렵다"가 아니라
"측정된 4.1m 의 95%"다.

- 저장소에 이 근거가 없었다. `grep -i metric docs/templates/difficulty-curve.md`
  → 0건. 난이도 문서는 있는데 난이도를 판정할 수 있게 만드는 수치가 없었다.
- 절 구성: 측정 프로토콜(빌드 SHA 필수 — 빌드 없는 수치는 반증 불가) · 코어
  이동/전투 측정치 · **파생 상수**(자명·표준·도전·불가 간격, 최소 복도 폭, 최소
  아레나, 엄폐 높이) · 아톰 스코어링 · **무효화 표**.
- 무효화 표가 이 문서의 값을 치른다. 캐릭터 컨트롤러 튜닝은 국소 변경이 아니라
  게임 전체의 간격을 조용히 재분류한다 — 그 재분류를 플레이테스터가 레벨 하나씩
  발견하게 두지 않으려고 `/propagate-design-change`·`/sot-audit`·`/spatial-audit`
  로 연결했다.
- **동시 요구는 점수를 더하지 않는다**고 명시. 전투 압박 아래의 5점 간격은 10점이
  아니라 `5 (+ 전투 압박)` 이다. 없는 수를 지어내지 않기 위한 표기다.

**⑵ 기승전결(Kishōtenketsu) — 레벨 문서에 티칭 구조 절 신설.**
`difficulty-curve.md` 가 다루던 것은 **게임 전체**의 매크로 도입 순서였고, 레벨
단위 비트 구조는 공백이었다.

- 4비트(기: 실패 없는 격리 소개 · 승: 같은 기법, 높은 요구 · 전: 새 동사 없이
  재맥락화 · 결: 결합과 숙달 시험)를 `docs/templates/level-design-document.md`
  에 추가.
- 검사 가능한 규칙 둘: **전 비트는 새 동사를 도입하지 않는다**(도입하면 그것은
  전이 아니라 변장한 두 번째 기다), **도전 난이도는 결보다 앞에 오지 않는다**.
- **강요 금지를 같은 무게로 적었다.** 허브·샌드박스·순수 서사 구간에는 4비트를
  돌릴 기법이 없다. 예외를 명시하는 것이 올바른 산출이고, 아무것도 서술하지 않는
  채워진 표가 빈 표보다 나쁘다. (`/spatial-audit` 이 Lynch 5요소를 단일 복도에
  강요하지 말라고 한 것과 같은 판단이다.)
- `agents/level-designer.md` 에 두 기법 + 형태·색 심리학 금지선을 명시.
- `docs/templates/level-design-document.md` 에 `Metrics Basis` 필드와 파생 근거를
  적는 Traversal Challenges 표 추가. 근거 없는 점수는 `?` 로 적는다 — 빠진 것과
  틀린 것을 독자가 구분할 수 있게.

**아톰 점수 구간(≤40% → 1, ≤60% → 3 …)은 RLD 가 아니라 이 저장소의 관례**라고
명시했다. 출처가 있는 것은 *방법*(측정치 대비 비율로 채점한다)이고, 구체적
퍼센트는 프로젝트들이 같은 지점에서 출발하도록 우리가 고른 값이다. 게임이
동의하지 않으면 이 파일에서 바꾸고 이유를 적는다. 근거 없는 상수를 RLD 로
포장하는 것이 이 문서가 막으려는 바로 그 일이라 리뷰에서 되돌렸다.

출처는 `docs/level-design-sources.md` 에 링크만. 기승전결은 고전 서사 형식이라
누구의 것도 아니지만 **레벨 설계로의 적용**은 Hayashida 에게 귀속된다 — 다만
우리는 그 인터뷰를 직접 읽지 않았고 Brown 을 경유한 2차 정보라 `추정` 으로
표기했다.

### Added — `/video-brief`: 편집이 아니라 촬영 전 결정

영상 방법론을 스터디해 흡수했다. 저장소에 영상 관련 자산이 0건이었다.

**스킬 하나, 템플릿 하나, 출처 문서 하나.** 4종(스토어 트레일러 / 제품 데모 /
숏폼 / 데브로그·튜토리얼)을 `--kind` 로 가른다.

- 전제: **편집에서 고칠 수 없는 실패 둘**이 비용을 만든다. ⑴ 푸티지가 존재하지
  않는다(안 만들어진 기능·없는 세이브). ⑵ 플랫폼이 푸티지를 거부한다. Apple 은
  기기를 든 손이 나오는 오버더숄더 샷을 아무리 잘 잘라도 반려한다. 둘 다 촬영
  전에 결정된다.
- 샷 리스트의 `Exists?` 열이 이 문서의 값이다. 미구축 기능에 걸린 샷은 일정
  의존성이고 스프린트로 간다 — 오늘 존재하는 것만으로 짠 트레일러는 파는 게임이
  아니라 가진 게임을 보여준다.
- **권리 미해결은 CONCERNS 가 아니라 BLOCKED.** "음원은 아마 괜찮을 것"이 촬영
  예산을 쓴 뒤 스토어 반려로 발견되는 경로다.
- 편집 실행은 위임한다(`browser-use/video-use`, MIT). ffmpeg 헬퍼를 재구현하지
  않는다. 다만 **동반 플러그인이 아니다** — `~/.claude/skills/` 에 심링크하는
  스킬 저장소라 `.claude/settings.json` 에 들어가지 않는다. 소스 파일당 유료
  전사 호출이 있어 `/api-cost-gate` 로 감싼다.
- video-use 에서 가져온 것은 도구가 아니라 설계 원칙 셋: 텍스트 우선 + 필요할
  때만 시각, ask→confirm→execute→self-eval, 상한 있는 자기평가 루프. 셋 다 이
  저장소가 다른 곳에서 이미 도달한 결론이다.

**벤더 페이지를 못 읽으면 BLOCKED 다.** 초안은 CONCERNS 였는데 리뷰에서 걸렸다 —
`docs/deterministic-gates.md` 의 `exit 3` 규칙(판정을 못 낸 게이트는 판정이 없는
것이고, 없는 판정은 통과가 아니다)에 정면으로 어긋나고, 같은 파일 § 6 이 이미
"알 수 없는 사양에 대고 촬영하는 것이 푸티지를 버리는 경로"라고 적고 있었다.
`/spatial-audit` 이 센티널 부재를 BLOCKED 로 처리한 것과 같은 판단으로 통일했다.

**스폰은 도구를 좁혀서 한다.** 라우트를 **산출물** 기준으로 고쳤다 — 이 스킬의
산출물은 마크다운 브리프(R1/R2)지 공개된 영상이 아니다. 트레일러가 첫인상이라는
사실은 *더 세게 검증할* 이유이지 *에이전트를 더 붙일* 이유가 아니다
(`rules/route-hint.md`: 생산 축과 검증 축은 독립이며 서로에서 추론하지 않는다).
기본은 standard 1명, heavy 는 opt-in. `community-manager`·`art-director` 는 기본
`Write` 를 갖고 있으므로 스폰 시 `tools: Read, Glob, Grep` 로 좁히고, § 2.1 이
요구하는 쓰기 소유권 표를 스폰 **전에** 채운다.

**플랫폼 사양은 매 실행 벤더 페이지를 다시 읽는다.** 이건 신중함이 아니라 측정
결과다 — 이 파일을 쓰면서 서드파티 ASO 블로그에서 가져온 수치 **둘이 벤더 문서와
불일치**했다. "Google Play 영상 3개까지"(실제 **1개**), "Google Play 30–120초
요구"(벤더는 **길이 요구가 없다**. 30초 자동재생만 규정). 둘 다 리뷰에서 드러나지
않았을 오류다. `docs/video-production-sources.md` 에 판독일과 함께 기록.

덧붙여 `docs/skills-reference.md` 헤더의 "84 slash commands" 가 실제와
어긋나 있었다(88). 행 수가 명령 수보다 많은 이유(교차 게재)를 함께 적었다.

### Fixed — P4 허용 경로가 카탈로그를 따라오지 못했다

`verify_policy.py` P4 의 `CONVENTION_PREFIXES` 에 `design/art/` `design/ux/`
`production/playtests/` 가 없었다. 셋 다 `docs/workflow-catalog.yaml` 이
**정규 산출물 위치로 선언한** 경로다 — 게이트가 자기 규약에 오탐을 내고 있었다.
P4 docstring 자체가 "잘못 발화하는 게이트는 통째로 꺼진다"고 적은 그 경우다.
카탈로그와 동기화한다는 주석을 함께 달았다.

`/video-brief` 가 쓰는 `production/marketing/` 은 그 스킬 커밋에서 추가된다.

### Added — 토큰 라우팅 2종 (StarDiver 2026-08-13 문서 재편 실측에서 유입)

**⑴ `/doc-relink` 신설 + `scripts/doc_relink.py`.**
문서 재편에서 토큰이 새는 지점은 링크 재작성이다 — 수백 건을 모델이 손으로
훑으면 비싸고 틀린다. 실측(705개 md, 이동 106건)에서 링크 265건을 스크립트가
재계산해 **신규 파손 0** 이 나왔고, 그 절차를 스킬로 굳혔다.

- 절차 = baseline(`check --write-baseline`) → `git mv`(스테이지 유지) →
  `relink` 2패스(유입 링크 + 이동 파일 자신의 상향 링크, rename 매핑 기반) →
  `check --baseline` 게이트. **exit code 가 판정** (신규 파손 = FAIL) —
  기존에 썩어 있던 링크는 게이트 대상이 아니라서 재편이 남의 빚에 막히지 않는다.
- 스크립트가 못 다루는 것(꺾쇠 링크·폴더 링크·gitignore 파일·리포 밖 참조)은
  SKILL.md 가 모델 몫으로 명시 — 조용한 커버리지 공백을 남기지 않는다.

**⑵ `rules/route-hint.md` 에 모델 축(Model axis) 신설.**
기존 룰은 호출 수만 라우팅했고, 모델 티어는 "사용자 몫" 한 줄로 막아 뒀다.
그 원칙은 유지하되 — **사용자가 CLAUDE.md 에 상시 정책을 적어 두면** 그때부터
티어 라우팅은 재량이 아니라 복종이다. 권장 정책 표(기계적 스윕 = 하위 티어 /
탐색 = 중간 / 판단·리뷰 = 세션 모델 고정 / 결정론적 변환 = 모델 아닌 스크립트)와
가드 2개(모호하면 스윕이 아니다 · 하위 티어가 판단을 내리기 시작하면 라우팅
오류)를 함께 실었다.

### Fixed — product 트랙의 구멍 셋

v0.6.1 이 카탈로그를 듀얼 트랙으로 만들었지만, 그 트랙을 실제로 걸어갈 때 필요한
것 셋이 빠져 있었다. 세 구멍은 서로 무관해 보이지만 원인이 같다 — **카탈로그가
product 트랙을 선언한 뒤, 그것을 참조하는 쪽들이 따라오지 않았다.**

**⑴ `product/prd/product-concept.md` 를 쓰는 스킬이 없었다.**
`/create-prd` 는 이 문서를 읽고 **없으면 실패**하는데, 카탈로그의 `product-concept`
스텝은 `command: /brainstorm` 을 가리키고 있었다. 그런데 `/brainstorm` 은 MDA·
플레이어 타입·verb-first 로 짜인 **게임 발상 스킬**이고 산출물은
`design/gdd/game-concept.md` 다. product 트랙 시작점이 게임 문서를 쓰라고
지시하고 있었던 셈이다.

- **`/product-concept` 신설** — 9개 절(한 줄 정의 · 문제와 기회 · 타깃 사용자 ·
  가치와 차별점 · 코어 루프 · 범위 티어 · 성공 지표 · 리스크와 가정 · 범위 외).
  절 단위로 사용자와 합의하며 쓴다. 이 문서의 잘못된 가정은 이후 모든 기능 PRD 로
  전파되므로 통째로 생성하지 않는다.
- 카탈로그 `product-concept` 스텝의 `command` 를 `/product-concept` 로 교정.
  **스텝 id 는 그대로**라 `check_phase.py` 판정과 골든 궤적은 바뀌지 않는다.
- `/create-prd` 의 실패 안내문을 `/brainstorm` → `/product-concept` 로 교정.
- `/brainstorm` 상단에 게임 전용임을 명시. product 프로젝트에서 자유 탐색용으로
  쓰는 것은 여전히 유효하되, 게임 컨셉 문서를 쓰지 않도록 경계를 그었다.
- verdict 는 COMPLETE / CONCERNS / **BLOCKED** 셋. BLOCKED 는 문서를 억지로
  완성하지 않고 `production/human-actions.md` 에 남기고 멈춘다.

**⑵ `/gate-check` 가 game 트랙 phase 이름만 받았다.**
product 프로젝트에서 `/gate-check` 를 부르면 art bible·GDD·vertical slice 를
찾는 FAIL 이 나왔다 — 그 프로젝트가 애초에 가질 이유가 없는 산출물들이다.

- **product 게이트 5종 신설**: Discovery → Architecture → Build → Hardening →
  Ship → Growth.
- **트랙을 먼저 판별한다.** `PROJECT_TYPE` 이 `unknown` 이면 묻고, 디렉터리
  레이아웃으로 추측하지 않는다 — `design/` 폴더가 있는 product 프로젝트가 game
  게이트로 오라우팅되는 경로다. 다른 트랙의 phase 이름이 인자로 오면 **번역하지
  않고** 트랙과 선택지를 알린 뒤 묻는다.
- **두 트랙은 1:1 이 아니다**라고 스킬 본문에 명시. product `discovery` 는 game
  `concept` + `systems-design` 을, product `build` 는 `pre-production` +
  `production` 을 덮는다. 위치로 대응시키면 틀린다.
- 게임 게이트보다 **의도적으로 얇다.** 게임 쪽은 여러 릴리스를 거치며 쌓인
  검사이고, 이쪽은 카탈로그가 요구하는 것 + 스크립트가 판정 못 하는 판단만이다.
  대칭성이 아니라 **관측된 실패**로 늘릴 것.
- § 8 후속 조치도 트랙별로 갈랐다 — SaaS 프로젝트에 `/art-bible` 을 권하는 것이
  게이트가 신뢰를 잃는 방식이다.

**⑶ `CLAUDE.md` 스테이지 목록이 카탈로그와 어긋나 있었다.**
`product` 목록에서 `architecture` 가 빠져 있었고(6단계를 5단계로 적고 있었다),
`game` 목록은 `concept`·`systems-design`·`technical-setup` 셋이 빠진 채 카탈로그에
존재하지 않는 `live-ops` 를 포함하고 있었다. "product 트랙은 game 트랙을
stage-for-stage 미러한다"는 문장도 사실이 아니었다(7 대 6).

- 두 목록을 카탈로그와 일치시키고, **1:1 이 아니라는 사실**과 그 대응 관계를 적었다.
- `live-ops` 는 `agent-packs.yaml` 의 `post_release` 이지 카탈로그 phase 가
  아니다 — `check_phase.py` 는 이것을 반환하지 않는다. 이 사실을 명시했다.

**검증 중에 잡은 것**: 초안에서 `/prd-review` 를 참조했는데 그런 스킬은 없다.
카탈로그의 `prd-review` 스텝은 `command: /design-review` 다. 카탈로그의 모든
`command` 를 `skills/` 실제 디렉터리와 전수 대조해 교정했다(나머지는 전부 실재).

### Fixed — 훅과 게이트가 저장소를 잠그고 있었다 (`--no-optional-locks`)

`git diff` 는 읽기 명령처럼 보이지만 stat 캐시를 갱신하려고 `.git/index.lock` 을
쓴다. **삭제(unlink)가 거부되는 파일시스템**에서는 그 락이 지워지지 않고 남아
**그 저장소의 이후 모든 커밋이 실패**한다. 더 나쁜 것은 git 이 이 뒷정리 실패를
warning 으로 흘리고 **exit 0 을 낸다**는 점이다 — 훅은 성공을 보고하고, 락은
남는다.

실측 근거 (2026-08-06 상류 스캔):

| 저장소 | 관측 |
|---|---|
| SpecForge | 마지막 성공 커밋 `1c886a7`(08-02 09:20:23)과 `index.lock` mtime(09:20:28)이 **같은 초** — 크래시 잔재가 아니라 성공한 커밋의 뒷정리 실패다 |
| ReviewSupporter | 08-03 발생 후 **4일 연속** 미해소. 13개 파일·333줄이 커밋되지 못하고 워킹트리 체류 |
| StarDiver | 지울 수 없어 `mv` 로 치운 락 4종이 `_to_delete/` 에 남아 있다 |

- `scripts/verify_policy.py` 의 `_git` 헬퍼, `hooks/session-stop.sh`,
  `hooks/pre-compact.sh`, `hooks/validate-commit.sh`,
  `templates/githooks/unity-pre-commit` 의 git 읽기 호출에 `--no-optional-locks`
  를 붙였다. `session-start.sh`(`rev-parse`·`log`)와 `validate-push.sh` 는
  인덱스를 쓰지 않으므로 손대지 않았다.
- **완전한 해법이 아니다.** 쓰기 명령(`commit`·`update-ref`)은 여전히 락을
  만든다. 이 수정이 닫는 것은 **판정과 로깅이 저장소를 오염시키는 경로** 하나다.
  읽기 전용 판정이 인덱스를 건드릴 이유가 애초에 없었다.
- 정상 환경에서 동작 변화 없음. 플래그는 락 생성만 건너뛴다.

### Added — `rules/work-records.md` · 기록물 분류와 사람 전용 액션 큐

`self-loop.md` 는 **BLOCKED**(권한·데이터·결정이 없어 진행 불가)를 선언하게
한다. 선언할 곳은 있는데 **쌓아 둘 곳이 없었다.** 그래서 매 세션 같은 벽에
부딪히고, 사람은 세 번째로 같은 부탁을 받는다.

- **§ 1 기록물 분류표** — 커밋 / `session-state/active.md` / 회의록 / 레슨 /
  ADR / 리포트 / CHANGELOG 가 각각 무엇을 가져가고 무엇이 아닌지. 기존 규칙들은
  각 산출물을 개별 정의했지만 *겹칠 때 어디에 쓰는가*는 어디에도 없었다
  (`lesson-capture.md` 마지막 줄이 회의록↔레슨 한 쌍에 대해서만 풀고 있었다).
- **§ 2 `production/human-actions.md`** — 에이전트가 대행할 수 없는 일만 모으는
  상시 큐. 실행(🔴)과 판단(🟡)을 나누고, 각 항목에 **"왜 사람인가"**(권한·물리·
  계정·되돌릴 수 없음 중 하나)를 적는다. 여기 쓸 이유가 없으면 그것은 에이전트가
  할 수 있는 일이다. 완료 항목은 삭제가 아니라 강등. **왕복 프로토콜**이지
  단방향 TODO 가 아니다 — 사람이 결과를 적어 넣으면 다음 세션이 이어받는다.
- **§ 3 세션 진입 루틴** + `hooks/session-start.sh` 가 이 파일의 **존재만** 알린다
  (없으면 무음). 파일명을 `production/human-actions.md` 로 고정했으므로 글롭
  오탐이 없다 — 프로젝트마다 다른 파일명을 넓은 글롭으로 잡으려던 초안의 위험은
  경로를 못 박아 제거했다.
- 템플릿: `docs/templates/human-action-queue.md`.
  `verify_policy.py` 의 P4 `CONVENTION_FILES` 에 경로를 등록했다(신규 경로 추가일
  뿐 기존 규약 변경 없음).

**훅 동작을 문서로 확인하고 넣었다**: SessionStart 훅의 stdout 은 exit 0 일 때
모델 컨텍스트에 들어간다(대화형·비대화형 동일). 반면 PostToolUse 훅의 stderr 는
exit 0 에서 모델에 닿지 않는다 — 프로젝트 쪽 관측("훅 stderr 가 자율 실행 시 안
닿는다")은 **PostToolUse 에 한정된 사실이고 SessionStart 로 일반화되지 않는다.**
이 구별이 이 항목의 구현 형태(훅 vs 규칙)를 갈랐다.

### Added — `claim-confidence.md` § 3.1 · 표본이 작으면 비율을 쓰지 않는다

§ 1~3 은 **출처가 있느냐**를 다룬다. 이 절은 다른 축이다 — 출처가 실측이어도
표본이 작으면 그 수치는 문장으로 쓸 수 없다. "진입률 34%" 는 6건 중 2건일 때
거짓이 아니라 *해석 불가*이고, 다음 세션은 그것을 실측이라는 이유로 신뢰한다.

- **규칙은 관측이 아니라 서술을 막는다.** 세는 것은 언제나 한다.
- **임계값을 상수로 박지 않았다.** 관측된 임계(n<20 비율 금지 · n<5 인용 금지 ·
  누적 30건)는 한 프로젝트의 선택이지 통계적 필연이 아니다. 근거 없는 상수를
  규칙에 박으면 그 상수가 § 1 이 금지하는 무표기 추정치가 된다. 상류는 **정할
  것 넷**(비율 금지선·인용 금지선·노이즈 폭·정의 breakpoint)만 규정하고, 정하기
  전까지는 원시 건수만 쓰게 한다.
- 면제: **0 → 1 돌파**(존재 증명은 표본 크기를 요구하지 않는다). 조회 실패는
  침묵시키지 않고 "조회 실패(사유)"로 남긴다 — 빈칸은 다음 회차가 무변동으로
  오독한다.

### Added — 레슨 대체(`supersedes`)와 오진 사례 보존

- `templates/lesson.md` 프론트매터에 선택 필드 `supersedes:` 추가. 기존 레슨은
  전부 그대로 유효하고 `/lesson-log`·`/lesson-review` 출력 형식은 바뀌지 않는다.
- `rules/lesson-capture.md` 에 정정 절차 신설 — 레슨이 **틀린 것으로 드러나면**
  고치거나 지우지 않고 새 레슨에 `supersedes` 를 건다. 옛 레슨은 그 자리에 두고
  INDEX 에 `⚠️ 오진 사례로 보존` 을 표시한다. `/lesson-review` 가 INDEX 를
  재생성하므로 표기가 규약이 아니면 대체 관계가 재생성 때 사라진다.
- 근거: 같은 사건을 두 번 진단해 첫 진단이 틀린 실사례(위 git 락 건이 바로 그
  사건이다 — 첫 진단은 "죽은 프로세스의 잔재"였고 그럴듯했지만 틀렸다).
  **틀린 진단은 절차의 한계를 가르치는 유일한 재료다.** 지우면 정답만 남는다.
- 대체가 아니라 *보강*이면 이 필드를 쓰지 않는다. 선행 판단이 틀렸을 때만이다.

### Added — product 트랙 `feature-viability` 스텝 (growth)

출시된 기능마다 **유지 / 확대 / 보완 / 폐기**를 결정한다 — 운영 원가, 운영 부담,
움직인 지표, 정책·스토어 리스크. 카탈로그의 어느 트랙에도 "만들고 나서 접는"
경로가 없었고, 그래서 아무것도 폐기되지 않고 운영 비용만 누적된다.

- `required: false`, `repeatable: true` — **기존 프로젝트의 phase 판정에 영향이
  없다.** `check_phase.py` 는 required 스텝만 진행을 막는다.
- 산출물 글롭 `product/prd/viability-*.md` (신규 경로 추가, 기존 규약 변경 없음).
- `verify_trajectory.py` 골든을 같은 변경 안에서 재기록했다
  (`product.growth.steps: +['feature-viability']`).
- **"긴급 수정도 축약 적용, 임의 배포 금지"는 넣지 않았다** — 검토 결과
  `/hotfix`(Phase 2 기록 → Phase 5 3인 승인 → Phase 5b QA 재진입 게이트)와
  `/day-one-patch`(Approvals Required Before Deploy)가 이미 같은 것을 강제한다.
  중복 문장을 얹지 않는다.

### Added — `J-3` 줄표 결정적 게이트 (P5)

한국어 필자들이 클로드 글에서 지목하는 세 가지가 Em dash, 가운뎃점, 통일된 어미다.
가운뎃점은 J-5 로 들어왔고(아래), 나머지 둘을 이번에 처리했다.

| 코퍼스 | 한글자 | 산문 삽입 줄표 | /1000자 |
|---|---|---|---|
| 한국어 위키백과 11편 | 220,229 | **0** | 0.0 |
| 이 저장소의 클로드 작성 한글 문서 7종 (`3a9ec01`) | 15,910 | **180** | 11.31 |

**G²=971**, 종전 최대인 C-8 대구(41.7)의 23배. 인간 쪽은 11편 전부 0회다. 관측이
0이라 **배수는 정의되지 않는다** — 분모가 0인 비율은 표본을 하나 넣을 때마다
자릿수가 바뀐다. 크기는 G² 로만 읽을 것.

- **`J-3` 심각도 S1 확정.** 기존 "원문에 이미 있던 대시는 보존" 예외는 그대로 둔다.
- **`verify_gates.py` P5 신설** — 4축에서 5축으로. **절대치가 아니라 before/after 로
  판정한다.** (a) 원문 3회 이상인데 윤문본이 2회 초과면 미달, (b) 윤문본이 원문보다
  늘었으면 개수와 무관하게 역방향 삽입 — D 카테고리의 역방향 삽입 금지(v2.0.1)와
  같은 실패 모드를 부호 층위로 옮긴 것. 다만 before/after 설계가 보존 예외를 **완전히**
  면제하지는 않는다: 원문 산문 줄표가 3회 이상이면 보존해도 (a)에 걸린다. 실측상
  그런 한국어 원문은 22.0만 자에 0건이고, 걸려도 WARN 이지 채택 금지가 아니다.
- **baseline 셀은 두지 않았다.** 판정이 before/after 라 절대 임계가 필요 없고,
  없는 셀에 placeholder 를 채우면 판정에 쓰이지도 않는 수치가 근거처럼 읽힌다.

#### 1차 측정을 폐기하고 계수기를 다시 만들었다

첫 보고는 **619배·G²=2290** 이었다. 그 계수는 "줄 첫머리가 아닌 U+2014" 였는데,
잡힌 것을 표본으로 뜯어 보니 **74.5%가 마크다운 구조 문법**이었다(불릿 48.5% ·
헤딩 19.5% · 인용 3.5% · 표 2.9%). 헤딩 부제 `## 제목 — 부제` 는 `#` 이 앞서므로
"줄 첫머리" 예외에 걸리지도 않았다. 인간 코퍼스는 렌더된 평문이라 그 형태를
**구조상 만들 수 없으므로**, 1차 수치는 한국어 글쓰기 습관이 아니라 문서 포맷을
재고 있었다. 분모도 어긋나 있었다 — 분자에 영문 전용 줄이 39.8% 섞였는데 분모는
한글자였다.

`em_dash_count` 를 산문 전용으로 다시 구현했다. 코드블록(펜스·들여쓰기)·헤딩
(ATX·setext)·표·수평선은 제외하고, 목록과 인용 표지는 떼되 **그 안의 한국어 문장은
산문으로 계상**한다 — 불릿이나 인용 안의 문장은 포맷이 아니라 산문이다. 한글 없는
문단은 제외. **줄을 문단으로 합친 뒤 센다** — 줄 단위로 세면 하드랩 재배치만으로
수치가 흔들리고(정상 윤문이 "역방향 삽입"으로 오탐), 줄표를 줄머리로 미는 것만으로
계수를 피할 수 있다. 렌더 결과가 같으면 값도 같아야 한다. 같은 이유로 **문단 첫 글자
줄표도 면제하지 않는다** — 면제하면 빈 줄 하나로 문단을 쪼개 계수를 피할 수 있고,
반대로 문단을 합치기만 한 윤문이 삽입으로 오탐된다.

초안 계수기로는 헤딩·표·코드블록을 **보존한** 윤문이 전부 exit 1 이었다. exit 1 은
finalize 승급을 부르므로 오탐 1건당 LLM 콜이 1회 더 나간다 —
`docs/deterministic-gates.md` 가 경고하는 "잘못 울려서 통째로 꺼지는 게이트" 다.
회귀 테스트로 세 형태를 모두 고정했다.

**결론(S1 확정·게이트 신설)은 유지되지만 수치는 전부 교체됐다.** J-5 회차에 이어
두 번째로 첫 계수 설계가 틀렸다. 새 지표를 만들 때 **잡힌 것을 표본으로 뜯어 무엇이
잡혔는지 분류하는 단계**를 건너뛰지 말 것.

### Changed — `E-7` 장르 경계 명시 (축은 그대로)

세 번째 프롬프트("해요체와 습니다체 비율을 5:5로")가 `E-7` 과 부딪치는 것처럼 보였다.
E-7 은 "청자 등급(해라/하게/해요/합쇼) 하나를 정해 일관 유지" 를 처방한다.

**충돌이 아니었다.** E-7 의 장르 가드는 처음부터 **대화·구어 텍스트 한정**이고
블로그 산문은 그 밖이다. 축을 높임/낮춤 이진으로 접는 안을 냈다가 **되돌렸다** —
그렇게 하면 하오체·하게체가 축에서 사라지고(둘 다 어느 층위인지 런타임 산출물에
적히지도 않는다), 소설 대화·인터뷰에서 같은 화자가 합쇼↔해요를 오가는 말투 붕괴를
놓친다. 이미 가드가 막고 있던 오탐을 근거로 축을 좁히면서 가드가 실제로 허용하는
장르의 검출력을 버리는 거래였다.

- **`E-7` 은 패턴 ID·이름·심각도·검출 임계·처방·`estimated` 전부 불변.** 오독이
  반복되는 지점이라 "블로그·카피·에세이 산문에는 적용하지 않는다" 를 항목에 명시만
  했다.
- 블로그의 합쇼↔해요 교체가 규범이라는 것은 **결함 목록에 넣을 성질이 아니어서**
  `rewriting-playbook.md` §4 장르표로 보냈다. 블로그 행에 "문장마다 오가기" 를 허용,
  "종결을 한쪽으로 통일" 을 금기로 적었다(실측 합쇼 5 : 해요 7, 해라체 0문장).
  같은 절에 소설 대화·인터뷰는 E-7 적용 범위이므로 이 규칙을 끌어다 쓰지 말라는
  경계도 붙였다.

### Added — `J-5` 가운뎃점(·) 나열: taxonomy J 카테고리의 마지막 구멍

J 카테고리는 볼드(J-1) · 따옴표(J-2) · 대시(J-3) · 괄호(J-4)를 덮고 있었지만
**가운뎃점은 692줄 어디에도 없었다.** 한국어 필자들이 클로드 글에서 반복해서
지목하는 세 가지가 Em dash, 가운뎃점, 통일된 어미인데 나머지 둘은 각각 J-3 과
E-2/E-7 로 들어와 있었고 이것만 비어 있었다.

- **`J-5` 가운뎃점(·) 나열 남용 [S3 · estimated], `quick: false`** — 가운뎃점을
  "그리고/또는"의 범용 대체물로 삼아 문서 전반에 깔아 놓는 습관. **개별 사용은
  판정 대상이 아니고**, 블로그·마케팅 카피·에세이에서 문단마다 반복될 때만 발동한다.
  백과·법령·보도·학술은 가운뎃점을 관례적으로 쓰므로 장르 가드로 제외했다
  (C-1 · E-6 · E-7 선례). J-3(대시)와 같은 형태 — 문서 레벨 산문 규칙, metric 없음.
- **metric 을 만들었다가 측정으로 기각했다.** 초안은 "가운뎃점은 쉼표보다 세게
  묶으므로 한국어는 항목을 1~2음절 약칭으로 줄여 쓴다"를 전제로 항목 길이를
  임계로 삼았다. **그 전제가 틀렸다** — 축약을 요구하는 것은 맞춤법 규정의 공통
  성분 생략 용법뿐이고, 열거(사과·배·복숭아)와 짝 결합(동사·형용사, 대법원장·대법관)은
  항목 길이를 제한하지 않는다. 3음절 한자어가 한국어 최빈 명사 형태라, 어떤 길이
  임계도 정상 표기를 삼킨다.

  | 대조군 | 결과 |
  |---|---|
  | 한국어 위키백과 8편(18만 자), 가운뎃점 런 268건 | **160건(59.7%) 양성** |
  | 국립국어원 「문장 부호의 이해」 용례 10건 | **9건 오탐** |

  `interpunct_list_rate` · `decoration` baseline 축 · 관련 테스트를 전량 철회했다.
  근거와 재시도 금지 사유는 `empirical-validation.md` 「J-5 길이 임계 기각」에 남겼다
  — 임계 조정으로 고쳐지는 실패가 아니라 축 자체에 판별력이 없는 경우이고, 다시
  잰다면 개별 런 분류가 아니라 장르 baseline 대비 밀도 z-score 여야 한다.
- **부수 발견: 한국어 지표에서 조사 사전 방식은 쓰지 말 것.** 형태소 분석 없이는
  "에세이"의 `이` 와 "사회를"의 `를` 을 구분할 수 없어 멀쩡한 명사를 깎는다
  (실측: 에세이 → 에세). 이 저장소 런타임은 표준 라이브러리만 쓴다.
- **`estimated` 플래그** — 측정이 확인한 것은 "길이 임계가 틀렸다"까지이고 밀도
  자체의 판별력(AI/인간 배수, G²)은 미상이다. **S3 고정, S2 이상 승격 금지.**
- **발동 조건은 세는 것 하나로 좁혔다** — "한 문단에 가운뎃점 2회 이상". 초안은
  "규정 세 용법에 해당하지 않는 자유 키워드 묶음일 때" 였는데, 모든 가운뎃점 나열은
  어떤 의미로든 열거라서 그 조건은 답이 정해지지 않는다. 판정을 모델 재량으로
  되돌리는 서술이었다. 처방도 "그 문단에서 하나만" 으로 상한을 박았다.
- **가드가 런타임에 도달하는지까지 확인했다.** 진단 콜은 taxonomy 가 아니라 생성물
  `diagnosis-rules.md` 를 읽고, 거기서 패턴 설명은 42자로 잘린다. J-5 는 정확성이
  가드에 얹혀 있는 패턴이라 잘린 뒤에도 가드가 남도록 `- 패턴:` 첫 줄 자체를
  "블로그·카피에서 한 문단 2회+ 반복될 때만. 개별 사용은 정상" 으로 썼다.
  `rewriting-playbook.md` 장르 표에도 백과·법령·보도·학술 행을 추가했다.
- taxonomy v2.4 로 버전 갱신, `diagnosis-rules.md` 재생성(패턴 71 → 72).
  그 머리말의 패턴 수가 하드코딩돼 있어 `--check` 가 드리프트를 못 잡던 것도 함께
  고쳤다 — 이제 빌더가 실제 개수로 렌더한다. (`quick-rules.md` 는 J-5 가
  `quick: false` 라 내용 변화 없음.)

### Added — `/spatial-audit`: 지어진 레벨을 건축 4렌즈로 감사

이 저장소에 레벨을 *만드는* 경로는 있었지만(`/team-level`, `level-designer`,
`level-design-document.md`) 이미 만든 공간을 **읽어서 판정하는** 것은 없었다.
블록아웃이 걸어다녀진다는 것과 공간이 작동한다는 것은 다른 말인데, 그 차이를
보는 도구가 없으니 플레이테스트 결과가 "재미없다"로만 돌아왔다.

- **`skills/spatial-audit/SKILL.md`** — 매싱 · 동선 · 조망-은신 · 길찾기 4렌즈.
  읽기 전용이고 **재미는 판정하지 않는다** — 재미는 `/playtest-report` 의 몫이고,
  이 스킬은 그 결과를 해석 가능하게 만드는 성질(가독성·항행성·공정성)만 본다.
  장르 인자(`sp`/`pvp`/`open`)가 장식이 아니다: 막다른 길은 pvp 에서 결함이고
  sp 에서는 대개 의도다.
- **침묵 실패 계약이 이 스킬의 핵심이다.** `hera-agent-unity exec` 는 에디터
  메인 스레드가 막히면(모달·라이선스·도메인 리로드) **아무것도 출력하지 않는다.**
  무출력과 "찾은 게 없음" 이 구별되지 않으므로, 그걸 "엄폐물이 없다" 로 읽는 것이
  이 스킬이 낼 수 있는 최악의 산출이다. 그래서 모든 스니펫은 `__SPATIAL_AUDIT_OK__`
  센티널을 찍고 끝내고, **센티널이 없으면 판정은 BLOCKED — PASS 도 "발견 없음"도
  아니다.** `docs/deterministic-gates.md` 의 "돌지 못한 게이트는 통과가 아니다" 를
  산문으로 옮긴 것이다. 단 **이 스킬은 exit code 를 내지 않는다** — 센티널은 모델
  측 확인이지 게이트가 아니고, 그렇게 부르면 stdout 파싱을 게이트 판정으로
  세탁하는 셈이 된다(같은 문서가 금지하는 것).
- **에디터가 닫힌 것과 막힌 것은 다르게 라우팅한다.** 닫힘은 정상 조건이라 채널 B
  로 내려가고, 막힘(센티널 부재)은 결함이라 BLOCKED 로 세운다. 후자를 조용히 파일
  감사로 대체하면 고장을 덮는다.
- 추출(Bash)과 판정(에이전트)을 분리했다. `level-designer` 는 `disallowedTools: Bash`
  라 hera 를 못 부른다 — 메인 Claude 가 뽑아서 숫자를 넘긴다. 병렬 스폰 시 쓰기
  소유는 `rules/subagent-collaboration.md` § 2.1 을 따른다.
- 에디터가 없어도 씬 YAML 로 동작한다. 단 NavMesh·레이캐스트·카메라 시야는 볼 수
  없으므로 해당 발견은 전부 `추정 — 파일 기반` 으로 표기한다
  (`rules/claim-confidence.md`).
- **`docs/level-design-sources.md`** (신규) — 출처 목록. The Level Design Book 은
  **CC BY-NC-SA 4.0** 이라 본문을 이 저장소에 넣지 않는다: ShareAlike 가 파생물을
  같은 라이선스로 묶어 이 플러그인의 **MIT 와 충돌**하고, NonCommercial 은 상용
  게임 개발에 쓰이는 툴킷에 그대로 걸린다. 링크와 자체 표현으로만 쓴다 —
  claude-seo 를 vendor-in 하지 않은 것과 같은 판단이다.
- **형태·색 심리학은 명시적으로 배제했다.** "둥글면 안전" 류는 근거가 없고, 원전이
  해당 페이지 제목에서 직접 그렇게 부른다. 형태 주장은 시선거리·이동비용·실루엣
  변별처럼 **측정 가능한 결과로 환원될 때만** 채택한다.
- `docs/templates/spatial-audit-report.md` (신규) — 판정 박스에 추출 채널과 센티널
  상태를 먼저 적는다. 리포트를 읽는 사람이 "빈 섹션"과 "결함 없음"을 구별해야 한다.

스킬 수 85 → 86. `tests/test_manifest_sync.py` 가 매니페스트 3곳의 광고 숫자를
잡아냈다 — 그 게이트가 의도대로 작동했다.

### Added — 상류 흡수 1차: 제품 PRD 템플릿 + 전역 룰 3건

출처는 `.upstream-scan/2026-08-05.md` — 이 플러그인을 쓰는 8개 프로젝트를 훑어
**상류에 없으면서 2개 이상 프로젝트에 반복되는** 것만 추린 리포트다. 9건 중
"신규 파일·절 추가뿐이라 기존 규약을 건드리지 않는" 4건을 먼저 넣었다. 나머지
5건(아카이브 경로 규약, 세션 진입 루틴, 커밋 규율, 계측·인수인계 템플릿)은
선행 결정이나 반복도 확인이 필요해 보류했고 사유는 리포트에 있다.

- **`docs/templates/product-requirements-document.md`** (신규) — product 트랙의
  **제품 단위** PRD. 5개 프로젝트(SpecForge · InvestLog · TossMiniApp · MindCare ·
  ReviewSupporter)가 거의 같은 절 구성으로 수렴해 있었는데, 상류 템플릿 39종은
  전부 게임 쪽이라 받을 자리가 없었다. `game-concept.md` · `pitch-document.md` 는
  발상 단계 산출물이라 기능/비기능 요구사항, 페르소나, KPI, Out of Scope 가
  통째로 없다.
  **`/create-prd` 에는 연결하지 않았다.** 그쪽은 `product/prd/prd-<feature>.md`
  에 쓰는 *기능 단위* PRD 이고 이건 제품 단위다. 두 층위를 한 스킬에 밀어넣지
  않는다 — 산출 경로도 겹치지 않게 `product/prd/product-requirements.md` 를
  권장 경로로 적어 두었다.
- **`rules/subagent-collaboration.md` § 2.1** (절 추가) — **쓰기 영역을 스폰
  전에 나눈다.** 45개 에이전트를 병렬로 부르는 플러그인에 쓰기 충돌면 분할이
  없었다. Edit 은 마지막에 쓴 쪽이 이기고 진 쪽은 "완료" 를 보고하므로, § 5 의
  안티패턴 중 유일하게 **조용히** 실패한다. 소유 표(에이전트 × 쓰기 경로 ×
  읽기 전용 × 금지)를 채우지 못하면 아직 부를 준비가 안 된 것으로 본다.
  소유가 겹치면 병렬 대신 직렬 — § 5 의 "직렬 호출 안티패턴" 은 *독립* 작업에만
  해당한다는 점을 명시했다. 근거: StarDiver · SpecForge · CorpProject_10th ·
  TossMiniApp 4개 프로젝트가 각자 같은 규칙을 재발명해 두고 있었다.
- **`rules/decision-lifecycle.md`** (신규, 전역) — 확정된 결정은 다시 열지
  않는다. 사람은 회의를 기억하지만 **새 세션의 에이전트는 기억하지 않으므로**,
  폐기된 대안이 문서에 남지 않으면 매번 신선한 아이디어로 보인다. 확정 항목은
  결정 문장 + 근거 링크 + **재검토 트리거** 3요소를 갖춘다 (트리거 없는 확정은
  교착이다). 폐기된 값은 지우지 말고 **본문에** 폐기 표시 — 판단 기준은 "이
  파일만 읽은 에이전트가 옛 값을 정본으로 착각할 수 있는가". ADR 과 겹치지
  않게 기술 결정 / 제품·운영 결정의 경계도 표로 나눴다.
- **`rules/claim-confidence.md`** (신규, 전역) — 확인한 것 · 추정한 것 · 모르는
  것을 구별해 표기한다(무표기+출처 / `(추정)`+계산식 / `[확인 필요]`). 법조항,
  과태료, 가격, 수수료율, 경쟁사 사실, API 시그니처는 기억에서 쓰지 않는다.
  정직성 이전에 **전파** 문제다 — 표시되지 않은 추정치는 문서를 건널 때마다
  확신이 올라간다. `self-loop.md` 는 *채점 근거*의 인용을 요구하고 이쪽은
  *산출물 본문*의 사실 표기라 축이 다르며, 본문의 무표기 추정치는 그 자체로
  `self-loop.md` § 2.1 의 결함 티켓 요건을 충족한다.

하위 호환: **깨는 것 없음.** 스킬 이름 · 슬래시 명령 · 산출물 경로 규약 변경이
없고, 기존 파일 수정은 `subagent-collaboration.md` 절 추가·§ 5 항목 2건과
인덱스 3곳(`docs/rules-reference.md` · `docs/quick-start.md` · `README.md`)
갱신뿐이다. 게이트: pytest 413 passed · `verify_policy` exit 0 ·
`verify_trajectory` exit 0 · `lint_skills --baseline` exit 0 ·
`check_phase --validate` exit 0.

리뷰에서 드러난, **이 변경이 만든 게 아니라 부딪힌** 기존 구멍 셋. 고치지
않았고 다음 스캔 항목으로 남긴다:

- `product/prd/product-concept.md` 를 **쓰는 스킬이 없다.** 카탈로그
  (`docs/workflow-catalog.yaml:456-458`) 는 그 단계에 `/brainstorm` 을
  걸어놨지만 `skills/brainstorm/SKILL.md` 는 `design/gdd/game-concept.md` 만
  쓴다. product 트랙 discovery 가 정상 경로로는 완료될 수 없다.
- **`/gate-check` 는 game 트랙 phase 이름만 받는다** (`SKILL.md:4`). product
  트랙(discovery → architecture → build → hardening → ship → growth) 에는
  쓸 수 없어서, 새 템플릿은 `/project-stage-detect` 로 안내한다.
- `CLAUDE.md:54` 의 product 스테이지 목록에 `architecture` 가 빠져 있다
  (카탈로그 `:444` 의 `next_phase` 와 불일치).

### Added — `claude-seo` as a companion plugin (병합 아님)

SEO 는 이 저장소가 직접 다루지 않던 공백이었다. `growth-engineer` 의 remit 에
"SEO" 라는 단어만 있고 그것을 어떻게 하는지는 없었으므로, 실제로는 매번
즉흥적으로 감사를 짜는 결과가 났다.

- **`.claude/settings.json`** (신규) — `AgriciDaniel/claude-seo` (MIT, v2.2.4)
  를 `extraKnownMarketplaces` 로 선언하고 `enabledPlugins` 로 켠다.
  `autoUpdate: false` — 서드파티 마켓플레이스의 기본값이고, 훅과 네트워크
  fetcher 를 가진 플러그인을 조용히 갱신시키지 않는다.
- **vendor-in 하지 않았다.** 25 스킬 · 18 에이전트를 이 저장소로 복사하면
  업스트림 업데이트가 전부 수동 머지가 되고, 게임 프로젝트에서도 팩 게이팅
  없이 노출된다. 별도 플러그인으로 두면 업데이트는 업스트림에서 오고 이름
  충돌도 없다 (`seo-*` 는 기존 85 스킬 · 45 에이전트 어디와도 겹치지 않는다).
- **`CLAUDE.md` → "Companion plugins"** — 라우팅 교정 한 절. SEO 작업은
  `/seo-*` 로 보내고 `growth-engineer` 는 브리핑·리뷰만 한다. 이 저장소에
  `seo-*` 스킬/에이전트를 새로 만들지 않는다.
- `.gitignore` 에 `.claude/settings.local.json` — 머신별 trust 승인 기록.

주의: 설치는 자동이 아니다. 세션 시작 시 신뢰(trust) 프롬프트가 뜨고 사용자가
승인해야 로드된다. 새 머신에서 첫 사용 시 `/seo setup` 1회 필요 (venv +
Chromium 프로비저닝). claude-seo 의 `PostToolUse` 훅은 Edit|Write 전체를
matcher 로 받지만 스크립트가 JSON-LD 포함 여부를 먼저 확인하므로 이 저장소의
`.md`/`.py` 편집에는 개입하지 않는다.

## v0.6.3 — 2026-08-04

### Added — `gate_report.py`: one machine-readable shape for every gate verdict

`docs/deterministic-gates.md` has forbidden re-deriving a verdict by parsing a
runner's output since v0.6.0 — "read the exit code, use the text only to explain
it". But every gate then printed free prose, so a caller who needed *why* had
exactly one option: parse the prose. **The rule was unfollowable, which is worse
than absent — it looked like it was holding.**

- **`scripts/gate_report.py`** — four fields, identical across gates: `status`
  (what), `reason` (why), `next_action` (what to do about it), `evidence` (the
  findings as data), plus `gate` and `exit_code`. A skill reads `status`, a human
  reads `reason`, a follow-up reads `next_action`, a report cites `evidence`, and
  nothing is left to interpret.
- **`status` is a pure function of `exit_code`** and cannot be passed in. A gate
  can no longer print ABORT while exiting 0 — which is not hypothetical:
  `validate-assets.sh` shipped printing "ERRORS (Blocking)" and exiting 1, a code
  Claude never receives. Deriving one from the other makes that state
  unrepresentable rather than merely discouraged. An off-contract exit code
  raises instead of being silently coerced.
- `--json` added to `verify_policy.py` and `verify_trajectory.py`.
- For `verify_gates.py` and `check_phase.py` the envelope is **additive** — a new
  `gate_report` key beside the existing output, whose shape is unchanged.
  `/project-stage-detect` already consumes those keys, and per `CLAUDE.md`
  작업 원칙 that is a contract, not an implementation detail. A test asserts the
  original keys survive.
- `verify_gates.py` excludes its P4 axis (sentence touch rate) from `evidence`:
  it is reporting-only and does not move the exit code. Citing a signal that did
  not contribute to the verdict invites the reader to think it did.
- Tests: `tests/test_gate_report.py`, 13 cases — including that `build()` has no
  `status` parameter (the invariant is structural, not documentary), that a
  hand-forged `status` fails validation, and that the `exit 3` path conforms too,
  since that is precisely the path most likely to be misread as a pass.

### Added — `rules/verify-route.md`: routing the checking, not the making

`route-hint.md` routes **production** — how many agents make the thing. Nothing
routed **verification**, so it ran at whatever weight each skill happened to
hardcode. That fails in both directions at once: a comment typo pulls the full
`/team-qa` fan-out because the sprint loop says so, while a data migration passes
on a single `/smoke-check` because nothing said to do more.

- **Route by reversibility, not importance.** "Important" is a feeling and it
  inflates; *"if this is wrong, what does it take to undo?"* is a property of the
  change. R1 (one edit undoes it) → the file's own gate · R2 (a revert undoes it)
  → gates + review · R3 (needs coordination or a re-release) → gates + a
  **separate** reviewing subagent + `/gate-check` · **R4 (cannot be undone, or
  costs users) → never runs unattended.**
- Only the last row takes the decision away from the agent. Escalation is "add
  this named check", not "be more careful".
- **Uncertainty escalates** — guessing high costs one extra check, guessing low
  costs whatever the change breaks. De-escalation requires a stated reason in the
  output, because an unexplained one is indistinguishable from a skipped check.
- **At R3+ the reviewer is not the author**, and receives the final state rather
  than the narrative of how it was produced. An agent asked to check its own work
  defends it — not from dishonesty, but because the same context reaches the same
  conclusions twice.
- `exit 3` at R3+ is itself an escalation trigger: you now know less than planned.
- Cross-referenced from `route-hint.md`, `subagent-collaboration.md` (new § 8),
  `CLAUDE.md` and `docs/rules-reference.md`. The two axes are explicitly
  independent — a one-line edit to a published config is the lightest production
  route and the heaviest verification route.

### Added — `verify_trajectory.py`: the plugin's own routing is now regression-tested

`/regression-suite` manages tests for the *user's product*. Nothing tested **this
plugin's own behaviour** — and that behaviour lives in no single file. It is a
join: `check_phase.py` reads `workflow-catalog.yaml` for the phase, and the
orchestrator looks that phase up in `agent-packs.yaml` for the staffing.

One line changed in either file silently re-routes every skill running in that
phase. A renamed phase, a deleted step, a support role quietly promoted to
primary — none of it failed a test, and none of it was visible in review unless
someone happened to hold both files in their head at once.

- **`scripts/verify_trajectory.py`** — records the derived routing (steps in
  order, required steps, `depends_on` edges, primary/support agents) per track
  and phase as a golden trajectory. `0` match · `2` drift · `3` cannot judge.
  **Never `1`** — a routing change is not a soft signal.
- **`tests/trajectories/routing.json`** — 2 tracks, 13 phases. A deliberate
  change is `--update` in the same commit, which turns an invisible drift into an
  explicit diff a reviewer reads.
- **Labels, descriptions and prose are excluded on purpose.** They change often
  and mean nothing to routing; including them makes the gate noisy, and a noisy
  gate gets `--update`d without being read — the same as having no gate.
- Tests: `tests/test_verify_trajectory.py`, 19 cases, both directions — every
  drift shape is detected (added/removed phase, membership change, **step
  reordering**, dependency edge change) and an unchanged tree does not false-fire.
  Also asserts the golden is current, since a stale golden passes while guarding
  nothing.
- CI: added to the `policy` job.

### Changed — `self-loop` defends a third failure mode: rewriting without evidence

The rule guarded two traps — score inflation and runaway loops — and both are
about *stopping*. It had nothing about the opposite pull. "Fix the lowest score
first" is all the licence a model needs to rewrite a section nobody found fault
with, and the 5-iteration cap does not catch it: each round dutifully changes
something while the deliverable keeps moving.

- **`rules/self-loop.md` § 2.1 — the default is preserve, not revise.** Scoring
  now emits a **defect ticket** (`claim_id` / `defect_type` / `evidence` /
  `severity`) and only what a ticket names may be touched. Default severity is
  `국소수정`; `전면재생성` is for structural defects. **No ticket → no edit.**
- **Verifier ladder: deterministic → tool → model.** If a script settled it, the
  lower rungs are not used. On the `heavy` route, scoring goes to a *separate*
  subagent — the agent that produced the work defends the work.
- **§ 2.2 — iteration input does not accumulate.** From round 2, re-inject four
  things only: previous output, this round's tickets, the violated criteria with
  allowed values, and what must be preserved. Re-feeding the whole context makes
  the model reinterpret the task and undo earlier agreements.
- **§ 4.1 — failures are classified.** `retryable` consumes a round;
  `hard_error` (schema, permission, policy `exit 2`) terminates immediately,
  because the same input yields the same result.
- **§ 4.2 — three terminal states, not two.** `완료` / `실패` / **`보류`**.
  Collapsing them recorded "cannot proceed without a permission or a decision" as
  a failure, and those need opposite responses: one is fixed, the other is
  escalated. The policy axis also gains standalone blocking power — all criteria
  at 10 with `verify_policy.py → exit 2` is not DONE.
- Exit report gains a **판정 주체** column: which script and exit code decided
  each row, or "모델". A blank means that row was never verified.
- § 1-§ 6 numbering is unchanged (new material is § 2.1/2.2, § 4.1/4.2) so
  existing citations still resolve. `skills/self-loop/SKILL.md`,
  `docs/rules-reference.md` and `CLAUDE.md` updated to match.
- `scripts/lint_baseline.json`: the `self-loop` entry loses `Check 3: no verdict
  keyword` — adding `BLOCKED` as a terminal state incidentally satisfied it. The
  remaining `Check 4` entry (Write/Edit without ask-before-write) stays
  baselined deliberately: this skill's contract is to iterate autonomously and
  it says so explicitly, so asking before each write would contradict its design.

### Changed — `CLAUDE.md` is a bias-correction file again (214 → 169 lines)

A context file is not a knowledge store; it is the set of instructions that
correct what the model would otherwise do by default. Roughly 90 of `CLAUDE.md`'s
214 lines were things an agent can find by opening a file — stage tables, the
workflow list, a directory tree, an index of `docs/`. Those lines do not merely
waste tokens: they dilute the instructions that actually change behaviour, and a
context window has no table of contents to compensate.

- **New `## 작업 원칙` (8 items).** Every prior "don't do this" in `CLAUDE.md`
  corrected *orchestration* bias — don't over-spawn, don't bypass hooks, don't
  trust an agent's summary. There was **nothing about implementation bias**, yet
  the 45 agents this file routes write code. The eight cover research-before-
  designing, simplest-sufficient implementation, growing in layers, not
  reimplementing, checking installed dependencies, and refusing stopgaps.
- **Backward compatibility is inverted from the usual advice, on purpose.** The
  common form of this rule is "delete unused paths, don't keep compatibility
  layers". This repo is an installed distributable: skill names, slash commands
  and artifact paths are effectively public API, so those must not break — while
  *internal* implementation (script helpers, hook libs) follows the delete-freely
  rule. Getting this backwards would break user projects on upgrade.
- **Stage → agent assignments moved to `docs/agent-packs.yaml` (`stages:`), not
  deleted.** The audit assumed `workflow-catalog.yaml` was their source of truth.
  It is not — the catalog carries steps and skills but essentially no agent
  information (`grep -c agent` → 2), and `agent-packs.yaml` had no stage
  information. That mapping existed *only* in `CLAUDE.md` prose and would not
  have been recoverable. It is a team decision, so it moved to the routing SoT.
- **`tests/test_agent_packs_stages.py` (6 cases) locks the join.** `CLAUDE.md` now
  says "ask `check_phase.py` for the phase, look that phase up in
  `agent-packs.yaml`". A verification pass caught that the first draft listed only
  5 stages while the catalog defines 7 game phases and 6 product phases — so
  `concept`, `systems-design`, `technical-setup` and `architecture` had no
  staffing and the lookup would have silently returned nothing. Those four are now
  staffed; game `live-ops` moved to `post_release:` because the catalog has no
  such phase; and the test fails if either side drifts again, in both directions.
- Compressed with pointers, not deletions: `## Development stages` (59 → 21, now a
  two-SoT table), `## Entry points` (19 → 14), `## File conventions` (20 → 11, now
  pointing at `docs/directory-structure.md`, which the tree had been duplicating),
  `## Reference docs` (11 → folded into `## Extending the plugin`), plus trims to
  the domain-pack member lists and the self-loop protocol, both of which restate
  files that already hold the full version.
- Untouched by design: `## Deterministic gates`, `## Route hint`, `## Agent usage
  rules`, `## Don't do this` — the bias-correction core.

**The 130-line target was dropped rather than met.** It was computed assuming the
stage tables could be deleted; once they had to be relocated instead, the pointer
section plus the new principles account for the difference. Line count is a proxy
for density, and gating on a proxy invites damaging the thing it stands for — so
the completion gate is now `test_agent_packs_stages.py`, which judges information
loss directly. Reasoning in full: `docs/design/v0.6.3-context-density-plan.md`.

### Added — `verify_policy.py`: the policy axis `/story-done` was missing

Every gate in this plugin judged the same question — *did the work get done?*
`/story-done` verifies acceptance criteria, `/smoke-check` runs the suite,
`check_phase.py` checks artifacts exist. All completion axis.

Nothing asked the second question: *was it done the way we said?* A story that
reached `Status: Complete` by adding `@pytest.mark.skip`, or by scattering
artifacts outside the documented tree, recorded exactly the same `exit 0` as one
that did the work properly. `CLAUDE.md` has a "Don't do this" section, but it is
prose — no script had ever read it, so nothing enforced it.

That failure mode is **unsafe-success**, and it is worse than a plain failure: a
plain failure is visible and gets fixed, while an unsafe success is
indistinguishable from a real one in every record we keep — and the next
session's agent reads those records as the normal way to work.

- **`scripts/verify_policy.py`** — stdlib-only, 4-code contract:
  `0` compliant · `1` warning · `2` abort · `3` cannot judge (not a git repo).
  - **P1** — story is `Complete` but its declared test evidence does not exist,
    or the evidence block still reads "Not yet created". **ABORT.**
  - **P2** — the diff *adds* a test-skip marker (pytest, unittest, jest, NUnit,
    Go, Rust). Pre-existing markers are not flagged; only additions. **ABORT.**
  - **P3** — `design/gdd/*.md` and `product/prd/*.md` both present, i.e. the
    pack mixing `CLAUDE.md` warns against. **WARNING.**
  - **P4** — new files under `design/`/`production/` outside the documented
    layout. **WARNING.**
- **P1/P2 abort, P3/P4 warn, deliberately.** P1 and P2 are mechanical and
  unambiguous. P3 and P4 have legitimate exceptions, and a gate that fires
  wrongly gets disabled wholesale — which costs more than the check ever earned.
  Promote them once the false-positive rate is known, not before.
- **Two-axis verdict in `/story-done`** (new Phase 5b). The axes never cancel
  each other: a completion PASS beside a policy FAIL is still BLOCKED, and a
  policy `exit 3` is recorded as "NOT RUN", never as "PASS".
- **P2 judges code files only.** Its first run on this repo flagged
  `skills/story-done/SKILL.md` for *explaining what P2 catches* — prose that
  names a marker is documentation, not a skipped test. P2 now checks an
  extension allowlist plus a greppable file-level opt-out
  (`policy-allow-file: skip-marker`) for the gate's own fixtures.
- CI: new `policy` job in `.github/workflows/test.yml` — runs `--self-test`
  first, then judges the repo against its own conventions.
- Tests: `tests/test_verify_policy.py`, 28 cases, including
  `test_this_repository_passes_its_own_gate` (a plugin that breaks its own
  policy has no business shipping the gate) and both directions of the P2
  opt-out, so the escape hatch cannot silently widen.

### Changed — Subagent collaboration is a contract, not just a call

`rules/subagent-collaboration.md` specified what to *send* a subagent and how to
merge results, but nothing about isolation. The point of a subagent is that it
holds its own conversation — yet with no return boundary, agents summarised their
discarded candidates and failed attempts back into main context. The thing being
isolated came straight back, so the fan-out cost was paid and the benefit lost.

- **§3 gains obligations 6 and 7** — *금지 영역* (what not to read, modify or
  spawn) and *반환 경계* (what goes back to main context and what does not).
  New §3.1 explains why, with a two-column default table.
- **Returns are Artifacts, not summaries** — an agent that wrote a file returns
  `path — status`, not 400 lines of prose the orchestrator then carries forever.
- **Read-only agents get read-only tools.** For `qa-lead`, `security-engineer`
  and `performance-analyst`, narrow `tools` to Read/Glob/Grep rather than
  relying on a sentence in the prompt — a permission is a stronger guarantee.
- **§2 is no longer game-only.** The standard four roles now come in a game set
  and a product set (`product-manager` / `ux-designer` / `frontend-engineer` /
  `backend-engineer`); the product pack shipped in v0.4.0 and this rule never
  followed. Also notes that four is a convention, not a quota.
- **§5 gains two antipatterns** — narrating the whole search back (the
  orchestrator ends up persuaded by length rather than content), and spawning
  across tracks.

### Fixed — `validate-assets.sh` printed "Blocking" and did not block

The hook detected invalid JSON, printed `=== Asset Validation: ERRORS (Blocking) ===`,
and exited **1**. In a Claude Code hook only `exit 2` feeds stderr back to Claude;
`exit 1` surfaces to the user and is otherwise ignored. Because this is a
*PostToolUse* hook the write has already landed, so exit 2 was the only path by
which Claude could learn it must fix the file it just wrote — the "blocking"
branch had never rendered a verdict at all.

`validate-commit.sh` and `validate-push.sh` were already correct at `exit 2`, and
`docs/deterministic-gates.md` had declared `2 = abort` since v0.6.0. This was a
contract violation, not a new policy.

- **`hooks/validate-assets.sh`** — `exit 1` → `exit 2` on invalid JSON. Naming
  violations stay advisory (`exit 0`), unchanged.
- **`docs/hooks-reference.md`** — rule 3 for adding a hook now names the code
  (`exit 2`, and why `exit 1` is not a verdict) instead of saying "non-zero".
- **New: "Which hooks can actually block" table** — only three of the sixteen
  hooks render a verdict. The rest exit 0 unconditionally, and a hook that has
  never judged anything must not be read as a green light. Same rule
  `deterministic-gates.md` states for gates, applied to hooks.
- Tests: `tests/test_hooks_layout.py` — the two existing invalid-JSON tests now
  assert `2`, plus `test_blocking_exit_is_2_not_1` (regression guard) and
  `test_naming_violations_never_block` (the other half of the contract).

**Upgrade note:** invalid JSON under an asset root now actually stops Claude. A
project carrying a pre-existing malformed JSON file will see this surface for the
first time.

### Added — `lint_skills.py` judges `description` as a routing rule (Checks 8-10)

`description` is not documentation. It is the text Claude reads when deciding
whether to auto-invoke a skill or spawn an agent, and this plugin ships 85 skills
+ 45 agents — 130 choices resolved from description text alone. The linter
checked only that the field was *non-empty*, so misrouting (a skill firing on the
wrong task, or the right skill never firing) had no detector.

- **Check 8** — description never says when *not* to use this. WARNING.
- **Check 9** — description is a near-duplicate of another entry's. WARNING.
- **Check 10** — description has no explicit trigger clause; it describes rather
  than routes. WARNING.
- Checks 8 and 10 recognise Korean as well as English phrasing.
- **All three are warnings, and warnings never enter `lint_baseline.json`** — so
  this landed with zero baseline churn. Current roster: 118 of 130 files warn.
  Run `--strict` to see the backlog; CI stays green and a *new* skill lands with
  the defect visible.
- **`NEAR_DUPLICATE_THRESHOLD = 0.30`**, measured not guessed. Over all 8385
  pairs in the v0.6.2 roster: max 0.438, p99.9 0.216, p99 0.121, median 0.000.
  The first value tried was 0.60 and it never fired once — a check that cannot
  fire is worse than no check, because silence reads as "no confusables exist".
  At 0.30 it selects exactly the pairs a human agrees are confusable, led by
  `create-prd` ~ `design-system` (0.44), which is the product-track/game-track
  pack mixing `CLAUDE.md` explicitly warns against.
- Tests: `tests/test_skill_lint.py` — 13 new cases including
  `test_threshold_can_actually_fire_on_the_real_roster`, which fails if the
  threshold is ever raised back out of range.

Rationale and the wider plan: `docs/design/v0.6.3-context-density-plan.md`,
sourced from `docs/design/ax-labs-blog-audit.md`.

### Added — `/remove-bg`: background removal as a deterministic, cost-gated skill

The plugin had `/api-cost-gate` (a disclosure format) and `/asset-spec` (which
produces asset rows) but nothing that actually *did* image work. Background
removal is the most common cutout task in both tracks — game sprites and product
photography — and it is billable, which makes it a useful shape to get right.

- **`scripts/removebg.py`** — stdlib-only [remove.bg](https://www.remove.bg/api)
  client with three subcommands: `account` (balance), `estimate` (plan + cost,
  **zero** billable calls), `run` (execute). Single file, folder batch,
  recursive, and `http(s)` URL inputs. Emits a JSON report whose
  `credits_charged_total` is the measured `X-Credits-Charged` sum, not the
  estimate.
- **Exit code is the verdict**, per `docs/deterministic-gates.md`: `0` all
  processed · `1` partial failure or everything skipped · `2` all failed / `402`
  insufficient credits / `403` auth failure / `--max-calls` ceiling tripped ·
  `3` cannot run (no key, bad path — nothing called, nothing charged).
  `402`/`403` abort the whole batch rather than failing per-image, because
  continuing there only spends money badly.
- **`skills/remove-bg/SKILL.md`** — embeds the `/api-cost-gate` 4-point
  disclosure (Phases 2-3) rather than delegating to it, backs point 2 with a real
  balance lookup, and writes results back to `design/assets/asset-manifest.md` at
  status `In Progress` (a cutout is a processing step, not an approval).
- **Cost discipline is structural, not advisory**: `--size preview` (≈0.25
  credits) is the default against `full` (≈1 credit); `--max-calls` aborts if the
  input set grew between estimate and run; failed images are never auto-retried.
- **Keys are never CLI arguments** — environment variable or `--api-key-file`
  only, so nothing lands in shell history or the process list.
- Docs: entries in `docs/skills-reference.md` (Art & Asset Pipeline + Creative &
  Content), a remove.bg row and a "use the dedicated skill" note in
  `skills/api-cost-gate/SKILL.md`, a third reference implementation in
  `docs/deterministic-gates.md`, and a README section.

## v0.6.2 — 2026-07-31

### Fixed — Hooks stopped assuming a lowercase web layout

Three of the four path-sensitive hooks hardcoded `src/`, `assets/` and
`design/gdd/`. Unity forces `Assets/` + `ProjectSettings/` and keeps code under
`Assets/**/*.cs`, so on a real Unity project they either never fired or fired on
nothing. Shipping `unity-meta-check.sh` and `unity-animator-string-lint.sh` said
Unity was a first-class target; the rest of the hook set said otherwise.
Measured on a live Unity 6 project (60+ scripts, 80+ design docs, six observed
commits):

- **`detect-gaps.sh` called a mature project a fresh start.** All three
  freshness tests looked at non-Unity paths, and the branch `exit 0`s — so
  checks 1-5, the actual purpose of the hook, had never run on a Unity project.
  Freshness now also clears on an engine scaffold, on 3+ design docs under any
  detected design root, and on a non-empty `production/` tree (which is why this
  very repo, having no `src/` at all, was also reporting `NEW PROJECT`). Checks
  1-5 resolve `core`/`gameplay` directories by **name** rather than by a fixed
  `src/gameplay` path, so Unity's `Assets/02.Scripts/Gameplay/Combat/` resolves.
- **`validate-commit.sh` passed silently on every commit.** Its four staged-file
  filters were all `^src/…`-shaped. Code checks now select files by
  **extension**, which is portable across engines; document and JSON checks use
  the detected design and asset roots. Per-file findings collapse into one
  summary line (5 files named, then a count) so a large Unity commit cannot bury
  the warning, and the scan is capped at 200 files to stay inside the 15s
  PreToolUse budget. Also fixed: matched lines used to leak onto stdout because
  the `grep` guards were missing `-q`.
- **`validate-assets.sh` had two bugs hiding each other.** The path filter
  matched lowercase `assets/` only, so Unity files never reached the naming
  rule — which hardcoded lowercase-with-underscores and would have rejected
  `PlayerController.cs`, `CARD_MaxHP.asset` and `Monster_Base.prefab`, all of
  them correct Unity names (a C# file name must match its class name). Fixing
  the path alone would have warned on essentially every Unity file. The
  convention is now per-engine: `pascal` for Unity/Unreal flags only whitespace
  and hyphens, `snake` for web/Godot is unchanged, and `any` disables the check.
- **`plugin.json`** — the PostToolUse matcher was `Write|Edit`, so `.meta`
  checks and the Animator lint were skipped wherever MultiEdit is active. Now
  `Write|Edit|MultiEdit`.

`unity-meta-check.sh`, `unity-animator-string-lint.sh`, `validate-push.sh` and
`detect-project-type.sh` were already correct and are untouched; regression
tests pin the first three.

### Added — `hooks/lib/detect-layout.sh`

One place decides the layout, because copy-pasting the same engine test per hook
is how they diverged. Exports `STUDIO_ENGINE` (unity/godot/unreal/gamemaker/
generic), source roots and extensions, design roots, asset roots and the naming
convention, plus helpers (`studio_count_sources`, `studio_find_subdir`,
`studio_naming_violation`, …). Generated trees (`Library/`, `Temp/`,
`node_modules/`, `Intermediate/`, …) are pruned from every walk — Unity's
`Library/` alone would blow the SessionStart timeout.

- **Backward compatible by construction.** `generic` reproduces the old web
  layout; `lib`/`app`/`packages` are additive and only apply when they exist.
- **Overridable** via environment, `.claude/studio-layout.json`, or a
  `studio.layout` block in `.claude/settings.json` — a project whose docs live
  somewhere unusual (`Documents/Specs/`) can say so. Unreadable config falls
  through to detection, never to an empty layout.
- **Degrades, never dies.** Every consumer guards the `source` with `-f` and
  keeps a legacy fallback; a missing helper cannot fail a session or a commit.
- `docs/hooks-reference.md` — layout contract, the override schema, and five
  rules for adding a hook (source the helper; select by extension; stay
  advisory; `grep -E` only; test both directions).

### Added — `tests/test_hooks_layout.py`

69 tests, the repo's first coverage of hook behaviour: engine detection for four
engines, layout resolution and override precedence (including the jq-less grep
fallback), the `NEW PROJECT` misfire in both directions, Unity vs. web naming,
JSON blocking on both layouts, and a guard proving the source globs are not
shell-expanded before `find` sees them. Suite: 226 → 295 passed.

### Fixed — the marketplace manifest had been advertising v0.6.0

`.claude-plugin/marketplace.json` — the file the marketplace actually reads —
still said `0.6.0` and "83 workflow skills". Both the v0.6.1 and v0.6.2 release
commits updated `plugin.json` and forgot its twin, so users were being offered a
two-release-old build. Now `0.6.2` / 84 skills, matching the filesystem.

`tests/test_manifest_sync.py` (9 tests) makes the next omission unmergeable:
the two manifests must agree on version, license and author; the advertised
skill and agent counts are checked against the filesystem rather than against
each other (so adding a skill without touching the description also fails); and
the CHANGELOG's top section must name the current version or be `Unreleased`.

## v0.6.1 — 2026-07-30

### Changed — The deterministic flow now covers both tracks

The workflow catalog claimed to serve the whole studio but only encoded the game track — on a `web`/`mobile`/`service` project, `/help` walked users through art bibles and playtests. The premise of a deterministic flow (every project passes the same steps, produces the same artifacts, in the same order) held for exactly one of the two domains this plugin supports. Prompted by [a pattern analysis of large skill plugins](https://thakicloud.com/tech-blog/ko/dev/agentops/agent-plugin-158-skills-deterministic-flow/): the flow, not the model, owns format/order/dependencies — so the flow has to exist for every domain.

- `docs/workflow-catalog.yaml` — **schema v2, dual-track**. `tracks: game` (the v1 flow, unchanged step-for-step) and `tracks: product` (discovery → architecture → build → hardening → ship → growth, mirroring the CLAUDE.md product stages with real artifact globs: `product/prd/prd-*.md`, ADR minimums, `tests/regression-suite.md`, …). Track selection follows `PROJECT_TYPE`.
- **Explicit step dependencies** — steps now declare `depends_on` (qualified as `phase:step` where ids repeat). Order is no longer implied by list position alone; a skipped step is now *detectable* rather than inferable.

### Added — `scripts/check_phase.py`: phase completion is script-decided

`/help` used to decide step completion by having the model glob for artifacts and count matches — exactly the kind of judgment `docs/deterministic-gates.md` says a script must own (globs + `min_count` + text pattern are 100% mechanical). New gate, same contract:

- Exit codes: `0` phase complete · `1` in progress · `2` **dependency violation** (a completed step's required dependency is missing — a step was skipped) · `3` cannot judge (catalog unreadable, or both game and product markers present with no `--track`). Code 3 is never a pass.
- Resolves track (marker-based, mirroring `detect-project-type.sh`), phase (`production/stage.txt` first, artifact inference second), then evaluates every step. `--json` for machine consumption, `--validate` for CI schema checking (broken globs, dangling `depends_on` → unmergeable).
- Standard library only, including the catalog parser — a purpose-built YAML-subset reader rather than a PyYAML dependency, keeping the vendored runtime at zero third-party deps.
- `skills/help/SKILL.md` — runs the gate in its context block; the model now narrates the script's verdicts instead of producing its own. Model-side globbing survives only as the documented exit-3 fallback, labeled as such. `skills/project-stage-detect/SKILL.md` — same, as its new first step.
- `tests/test_check_phase.py` — 21 tests: the real catalog parses and validates, v1 game flow survived the restructure intact, artifact/pattern/min_count semantics, all four exit codes exercised via the CLI.

### Added — `/create-prd`

Promised for v0.4.1 ("until then use `/design-system` framed as a PRD"), never shipped. Now real: guided section-by-section PRD authoring to `product/prd/prd-<feature>.md` — 8 required sections with a self-check that success metrics carry numbers + measurement sources, acceptance criteria map to FRs, and the MoSCoW *Won't* list is non-empty (an empty Won't list means scope was not decided). Retrofit mode mirrors `/design-system` (fills gaps, never touches existing content). The catalog's `discovery:create-prd` step points at it; the CLAUDE.md workaround note is gone. Skill count: 83 → 84.

## v0.6.0 — 2026-07-30

### Changed — Gates stopped grading themselves

Every quality gate in this plugin used to end with an LLM declaring PASS or FAIL. `/self-loop` already defended against that (8+ requires quoted evidence, 5-iteration cap, stall detection) — but every one of those defenses was the same kind: asking the model to doubt itself. This release moves the verdict out of the model.

- `docs/deterministic-gates.md` — exit-code contract as a repo standard: `0` converged / `1` warning / `2` abort / `3` **could not judge**. A gate that did not run has produced no verdict, and "no verdict" is never "pass". Reference implementation is `scripts/verify_gates.py`. Four caller rules (the exit code overrides the model; never re-derive a verdict from stdout; keep PASS/FAIL/NOT RUN distinct; name the deciding gate) plus how to add a gate.
- `skills/self-loop/SKILL.md` — scoring now asks **"can a script decide this?"** first. If yes, the exit code sets the score and model judgment does not override it. Self-scoring is the fallback for the irreducibly qualitative (readability, tone, whether an argument holds), not the default.
- `skills/smoke-check/SKILL.md` — reads the runner's **exit code** instead of parsing its output. Non-zero is FAIL even if the log looks harmless; zero is PASS even if it contains scary warnings. The NOT RUN → PASS WITH WARNINGS policy stays (deliberate, for environments with no engine binary) but the three states are never collapsed.
- `/gate-check` is deliberately untouched — it judges whether artifacts say something *meaningful*, which is irreducibly qualitative, and its verdict is documented as advisory.

### Added — Korean humanize (`writing` pack)

Strips AI tells from Korean prose — translationese, mechanical parallelism, passive overuse, emoji/bullet excess — without changing a single point of meaning. Vendored from [`epoko77-ai/im-not-ai`](https://github.com/epoko77-ai/im-not-ai) @ `53e24e8` (MIT; full notice in `NOTICE.md`).

- **3 skills** — `/humanize-korean` (orchestrator; routes to 1/2/3+ calls by measured severity), `/humanize` (Fast entry, `--strict` forces the precision path), `/humanize-redo` (second pass by category/paragraph/strength, rollback via `final_prev.md`).
- **4 agents** — `humanize-monolith`, `humanize-diagnostician`, `humanize-finalizer`, `korean-ai-tell-taxonomist`. `tools` is declared narrowly on purpose: upstream enforces its tool-call cap by prompt instruction; narrowing the schema makes the same limit structural.
- **New `writing` pack, active on every `PROJECT_TYPE`** — patch notes and GDDs need this as much as release notes and landing copy. Kept out of `core` only because it is Korean-specific, so dropping it later means one line in `activation`.
- `humanize-redo` shipped upstream referencing agents retired in v2.1 (`korean-style-rewriter`, `content-fidelity-auditor`) and reading artifacts that do not exist. Repaired here against the real call path — a candidate to send back upstream.

### Added — Call-count routing (`rules/route-hint.md`)

`CLAUDE.md` already said "don't spawn agents just because they exist", with no way to act on it. Upstream measurement prices that instinct: the same 10,000-character text cost **610K tokens as 7 chunks vs. 134K as a single call, at equal quality** — the waste was reloading shared context per chunk, not the model tier. With 45 agents that structure is easy to reproduce by accident.

- Three routes — **light** (orchestrator handles it, 0 agents) / **standard** (1 specialist) / **heavy** (fan-out + gates), with a tiebreaker: when torn, take the lighter one.
- Two principles carried over verbatim: **savings come from fewer calls, not a cheaper model** (never silently downgrade a tier — that is the user's choice) and **splitting is the last resort**.

### Added — First tests and CI in this repo

- `tests/` — 27 files: 12 `test_*.py`, golden fixtures (2 sets), `checks.py`. The ported suite reproduces the upstream baseline exactly (**185 passed, 1 skipped, 12 subtests**); with the linter's own tests the repo now runs **205 passed**.
- `scripts/` — 6 deterministic gate/build scripts. Standard library only; **zero third-party dependencies**.
- `scripts/lint_skills.py` — the 7 static checks from `skills/skill-test/SKILL.md` as runnable code. That skill is a linter an LLM reads and performs, so it could never run in CI. It found 11 real pre-existing violations; those are pinned in `scripts/lint_baseline.json` so CI blocks *new* violations without demanding the backlog be cleared first. `tests/test_skill_lint.py` covers it in both directions — a baselined failure stays tolerated, a new one fails the build — including a regression test for the stale-entry guard.
- `.github/workflows/test.yml` — pytest × Python 3.11/3.12/3.13, SSOT drift checks (`quick-rules.md` and `diagnosis-rules.md` are *built* from the taxonomy — hand-editing them is now unmergeable), and the skill/agent structure lint.
- `LICENSE` — the repo declared MIT in `plugin.json` without ever shipping the text. Fixed.

### Added — Self-loop quality rule (all projects)

- `rules/self-loop.md` — global, path-independent rule: deliverables with clear quality criteria are never one-shot. Protocol per iteration: plan → execute → score each criterion 1-10 → judge (all ≥ 8 → done, else fix lowest first). Includes defenses for the two classic traps of self-scoring loops: **score inflation** (criteria must be objectively verifiable; scores of 8+ require quoted evidence; every score names a remaining weakness) and **runaway loops** (max 5 iterations by default; stop + report after 2 consecutive stalled rounds). Ends with a verifiable exit report so the user can check the result without trusting the scores.
- `skills/self-loop/SKILL.md` — `/self-loop [target] [--criteria "..."] [--max N]`, the executable form of the rule. Default entry point when reworking after a FAIL from `/smoke-check`, `/gate-check`, or `/story-done`, or when the user asks to "loop until it passes" / "될 때까지 반복".
- `hooks/session-start.sh` — now prints a compact Self-Loop Rule reminder at every session start, so the rule reaches every project using the plugin.
- `CLAUDE.md` — new "Self-loop quality rule" section in the orchestrator guide; `docs/rules-reference.md` gained a Global Rules section; `docs/skills-reference.md` updated (skill count corrected to match the repo — previously undocumented skills are now listed).

## v0.5.0 — 2026-07-15

### Added — Lesson Ledger (교육용 노하우 원장)

Every studio project doubles as **teaching material** for a game-designer vibe-coding course. This release makes knowledge capture a first-class, auto-propagating workflow: update the plugin once, every project gets it.

- `skills/lesson-log` — `/lesson-log [topic]` extracts lecture-worthy lessons from recent work into `Documents/Lessons/LES-YYYYMMDD-NN-<slug>.md` (standard format) and updates `INDEX.md`. The "what we tried and why it failed" section is mandatory — failure narratives are the teaching asset.
- `skills/lesson-review` — `/lesson-review [period]` retrospective-scans commits/meeting-notes for missed lessons, regenerates INDEX + curriculum map (category counts, difficulty distribution, lecture-module suggestions).
- `templates/lesson.md` — lesson format: frontmatter (id/category/difficulty/teachable-moment) + 6 sections (Context → Problem → What we tried → Resolution → Lesson → Teaching notes).
- `rules/lesson-capture.md` — 5 standing capture triggers: repeated trap ×2 / design hole exposed by user feedback / assumption overturned by verification / tooling pitfall / design-decision pattern locked by data.
- `hooks/session-start.sh` — Lesson Ledger status line at every session start (count + latest, or initialization nudge). This is the auto-propagation mechanism: no per-project setup needed.

Categories (curriculum axes): `vibe-coding` / `game-design` / `engine-tech` / `test-balancing` / `production-ops`. Seed ledger lives in the StarDiver repo (`Documents/Lessons/`).

## v0.4.0 — 2026-06-19

### Added — Product pack (app / web / service expansion)

The studio is no longer game-only. A **domain-pack architecture** splits agents into `core` (always active), `game`, and `product`, so only the relevant pack activates per project. Routing source of truth: `docs/agent-packs.yaml`.

- **7 new product-pack agents** — `product-manager`, `frontend-engineer`, `backend-engineer`, `mobile-engineer`, `data-engineer`, `growth-engineer`, `technical-writer`. (Total agents: 34 → 41.)
- `hooks/detect-project-type.sh` (SessionStart) — auto-detects `PROJECT_TYPE=game|web|mobile|service|unknown` (+`ai` flag) from engine/framework signals, handling monorepos (scans `apps/*`, `packages/*`). The orchestrator uses it to activate `core+game` or `core+product` and avoid spawning off-domain agents. Verified against the owner's real projects (Unity / Next.js / React Native / Firebase).
- `docs/agent-packs.yaml` — pack classification + activation rules + neutral-name mapping for hybrid agents (`art-director`→design-lead, `narrative-director`→content-strategist, `community-manager`→marketing-lead, `writer`→content-writer).
- `docs/design/v0.4.0-product-domain-pack.md` — design doc: portfolio analysis, decisions, roadmap, pre-implementation checks.

### Changed

- `CLAUDE.md` — orchestrator guide restructured around **two stage tracks** (GAME and PRODUCT) plus a Domain packs section and a pack-routing table. Agent usage rules now lead with "respect the active domain pack."
- `.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` — version `0.3.0` → `0.4.0`; description and keywords broadened to game + app/web/service.

### Roadmap (next)

- v0.4.1 — product workflow skills (`/create-prd`, `/usability-test`, `/ab-experiment`, `/data-model`, `/user-flow`) + stack scaffolds (`/scaffold-nextjs`, `/firebase-setup`, `/stripe-integration`, `/llm-integration`) + stack presets.
- v0.5.0 — plugin/marketplace rename to "Claude Code Studios", full doc rebrand, `customer-support` agent, web/RN opt-in hooks.

---

## v0.3.0 — 2026-05-17

### Added — Unity UI/UX guidelines (5 permanent rules)

- `docs/engine/unity-ui-guidelines.md` — uGUI + Input System 1.x 의 UI/UX 5 영구 룰 통합 spec. 게임패드 + KBM 동시 대응 시 *반드시* 적용:
  1. **UI 활성 시 첫 selectable 자동 select** — Coroutine 1프레임 지연 + `Selectable.Select()` (직접 `EventSystem.SetSelectedGameObject` 호출은 1프레임 늦은 refresh 로 무시됨)
  2. **O 버튼 / Escape = popup 닫기** — `InputSystemUIInputModule.cancel.action.performed` 구독
  3. **게임패드 + KBM 동시 대응** — UI action 의 양쪽 binding + EventSystem actionsAsset + 4 action ref
  4. **UI 생성 default** — TMP Text placeholder 자동 채우기 + 중앙 정렬 (`TextAlignmentOptions.Center`)
  5. **Device-aware auto-select (최종 spec)** — 마지막 *실제* 입력 장치 추적 (`InputSystem.onEvent` + significant input deadzone). `InputDevice.lastUpdateTime` 단독 비교는 stick drift 로 false positive
- `templates/unity/UIAutoSelectGuardian.cs` — Rule 5 helper class. panel root 부착 + fallback Selectable 지정. 양방향 전환 (게임패드 ↔ 마우스) 자동 처리

### Added — Unity scene-loading patterns

- `docs/engine/unity-scene-loading-patterns.md` — `SceneManager.sceneLoaded` 이벤트가 *이미 로드된 씬* 에는 발화 X 함정. 단독 Play 시 FadeManager 검은 화면 사고 + `Start()` fallback 패턴. Boot 씬 진입 시 skip 룰 (중복 fade 깜빡임 회피)

### Added — Unity MCP workflow patterns

- `docs/engine/unity-mcp-workflow.md` — Claude Code + CoplayDev/unity-mcp 통한 Unity Editor 자동화 패턴:
  - 도구 선택 기준 (manage_scene / manage_gameobject / manage_components / manage_prefabs / execute_code / batch_execute)
  - **batch_execute** — N 명령 1회 호출로 latency 10~100x 향상 (UI widget 일괄 생성 시 필수)
  - **execute_code** — reflection / sub-asset 매핑 / nested SerializedField array set (`manage_components.set_property` 가 못 하는 영역)
  - 회귀 사고 cluster (nested array set 실패 / Component 매핑 자동 reset / Play mode 중 EditorSceneManager / MCP session stale)

### Added — Subagent parallel collaboration rules

- `rules/subagent-collaboration.md` — *광범위 + 깊은 디자인 결정* 영역에 다수 서브 에이전트 병행 호출 패턴. 사람 팀 협업 모사:
  - 단일 message 안 4 Agent tool call → N 배 빠른 병행
  - 표준 4 분야 — game-designer / ux-designer / ui-programmer / gameplay-programmer
  - 각 에이전트 prompt 의무 항목 (self-contained 컨텍스트)
  - 결과 통합 패턴 (결정 안건 매트릭스 + 회의록 + agentId 보존)
- `docs/templates/subagent-meeting-template.md` — 4 에이전트 결과 통합 회의록 template (메타 박스 + 결정 안건 § + 작업 계획 § + agentId 보존)

### Changed

- `.claude-plugin/plugin.json` — version `0.2.0` → `0.3.0`. description 갱신
- `README.md` — v0.3.0 자산 link 추가

### Compatibility

- Unity UI guidelines: Unity 6 / 2022 LTS + Input System 1.x + uGUI 검증. UI Toolkit (UXML/USS) 별도 (본 가이드 X)
- Scene loading patterns: Unity 일반
- MCP workflow: CoplayDev/unity-mcp v9.6+ 정합. Other Unity MCP 호환 가능
- Subagent collaboration: Claude Code 일반 (모든 프로젝트)

### Origin

Distilled from StarDiver Unity 6 PC/콘솔 게임 프로젝트 (5-15~5-17, 17 commit cluster). 5 회귀 사고 + UI/UX 영구 룰 cluster 채택 과정에서 surfaced 패턴들. 모든 자산이 *engine / genre / platform agnostic* (Unity UI 룰만 Unity 특정).

---

## v0.2.0 — 2026-05-04

### Added — Opt-in Unity safeguards

- `hooks/unity-meta-check.sh` (PostToolUse, Write/Edit) — advisory warning when a Unity asset (`.cs`/`.shader`/`.asset`/`.prefab`/`.mat`/`.controller`) is written without its paired `.meta`. Auto-detects Unity projects via `Assets/` + `ProjectSettings/`; exits silently elsewhere.
- `hooks/unity-animator-string-lint.sh` (PostToolUse, Write/Edit) — advisory warning when `.cs` files use `Animator.SetBool("name", ...)` style string lookups. Recommends `Animator.StringToHash` caching.
- `templates/githooks/unity-pre-commit` — manual opt-in git pre-commit template that *blocks* commits with missing `.meta` (zero-tolerance enforcement for shared repos / CI).
- `docs/engine/unity-setup.md` — activation guide, troubleshooting, disable instructions.

### Added — Engine-agnostic meta-audit skills

- `skills/sot-audit` — N-witness consistency audit for any multi-witness specification (FSM, input bindings, save schemas, localization, audio mixer, shader uniforms, network messages). Produces severity-classified mismatch matrix; advisory only.
- `skills/legacy-purge` — categorized residue audit after a pivot or migration (genre change, API deprecation, platform swap, architecture rewrite). Cross-references policy docs to filter intentional retention; advisory only.

### Added — Governance & workflow assets (engine/genre/platform agnostic)

- `skills/governance-bible-init` — bootstraps a domain Bible (Sound / Art / Narrative / UI / etc.) with the **Anchor + Bible** pattern: text spec + reference assets + decision protocol. Designed for solo devs and small teams managing AI-generated assets at scale.
- `skills/api-cost-gate` — pre-flight 4-point disclosure (call type / cost / purpose / use plan) gate for paid AI APIs (Suno, ElevenLabs, Midjourney, Tripo, OpenAI, etc.). Auto-mode does not bypass.
- `docs/templates/meeting-template.md` — meeting note template with mandatory header metadata table, D-table for decisions, and memorialization protocol.
- `docs/templates/api-cli-template.py` — reusable Python CLI scaffold for wrapping a new pay-as-you-go AI service (env loading, auth headers, async polling, sync binary, file downloads, subcommand argparse).
- `docs/rules/token-efficiency.md` — six rules (R1 commit length / R2 meeting length / R3 bulk operation reporting / R4 parallel reads / R5 memory-write discipline / R6 acknowledgement length) for keeping agent collaboration efficient on multi-month projects.
- `docs/rules/artifact-organization.md` — three-zone discipline (Workshop / Curated / Engine import), prefix naming convention, companion `.prompt.txt` rule. The structural layer underneath governance Bibles.

### Changed

- `.claude-plugin/plugin.json` — version bumped `0.1.0` → `0.2.0`. PostToolUse Write|Edit chain extended with the two new Unity advisory hooks.
- `README.md` — Hooks section documents Unity auto-opt-in + manual pre-commit template.

### Compatibility

- Unity safeguards: tested on Unity 2022 LTS / Unity 6 (6000.x). Zero impact on Godot/Unreal/GameMaker/non-Unity projects (auto-opt-in via filesystem detection).
- Meta-audit skills + governance assets + workflow rules: engine, genre, and platform agnostic. Apply equally to 2D / 3D / mobile / PC / console / web projects, across solo and team workflows.
- No new dependencies (`jq` optional, falls back to `grep`).

### Origin

Distilled from production use on a multi-month Unity 6 PC/console game project. Patterns surfaced after repeated incidents — `.meta`-corruption near-misses, asset tone drift across sessions, surprise paid-API spend, mid-batch verification gaps. Promoted to plugin tier when the patterns proved reusable across domains (sound vs art vs narrative) and across services (Suno vs ElevenLabs vs Midjourney vs Tripo).

## v0.1.0 — 2026-04-22

Initial release. 34 specialist agents, 72 workflow skills, production hooks (SessionStart/PreToolUse/PostToolUse/Notification/PreCompact/PostCompact/Stop/SubagentStart/SubagentStop). Engine-agnostic.
