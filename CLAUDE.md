# codex-code-studios — guidance for Claude Code

**You are in the source repository of a Codex plugin.** This tree builds
`codex-code-studios`; the studio it ships runs inside **Codex**, invoked as
`$skill-name`. [`AGENTS.md`](AGENTS.md) is the source of truth for this
repository — read it before changing anything, and prefer it over this file
wherever the two could be read differently.

This file exists because Claude Code loads it automatically. Its job is to stop
you acting on assumptions carried in from the sibling package, and to hand you
the right entry points.

## What is NOT here

The Claude-side studio does not exist in this tree. Specifically:

| You might assume | Actually |
|---|---|
| 45 agents in `agents/` | **No `agents/` directory.** The 45 role guides are `skills/studio-orchestrator/references/roles/*.md` — references the orchestrator loads, not installed agents. Do not spawn them as subagents. |
| Skills invoked as `/name` | Codex invokes `$name`. Write `$skill-name` when referring to an invocation. |
| `.claude/settings.json` holds project config | Project-owned config is `.codex/studio/technical-preferences.md`; layout overrides are `.codex/studio-layout.json`. |
| `.claude-plugin/` and this file are current | Both are a **transition-compatibility layer** kept for the 0.7 release (`AGENTS.md`). `.claude-plugin/plugin.json` is a frozen v0.6.4 copy still named `claude-code-studios`. Neither is a source of truth, and neither should be ported back to the sibling. |

The sibling package `claude-code-studios` (Claude Code, `/skill-name`, a real
`agents/` tree) is a **separate repository**. Nothing here installs it.

## Which runtime is working the project

This studio ships twice, and a user project may be worked by Codex alone, by
Claude Code alone, or by both at once. That choice changes whether this plugin
acts at all.

Read **`production/runtime.txt`** in the user's project — one line: `codex`
(full studio, the default here) · `claude` (**stand down**, the sibling owns the
work) · `split` (work only your partition, never a path the other runtime owns).
Absent means `codex`. **Never infer it** from a `CLAUDE.md` or `.claude/`
sighting — that proves Claude Code was configured there once, not that it is
working this task.

Full rule, including why `split` risks a silently lost edit: `rules/runtime-modes.md`.

## 작업 원칙

이 절은 프로젝트 정보가 아니라 **기본 동작 교정**이다. 지시하지 않으면 반대로 가는 것만 적는다.

- 해결책을 설계하기 전에, 이미 자리 잡은 제품들이 같은 문제를 어떻게 푸는지 먼저 살펴보세요. 접근 방식을 처음부터 발명하지 말고 검증된 패턴과 관례를 채택하세요.
- **스킬 이름·산출물 경로 규약의 하위 호환을 깨지 마세요.** 사용자가 설치하는 배포물이고 이것들이 사실상 공개 API입니다. 바꿔야 한다면 새 경로를 추가하고 기존 경로는 CHANGELOG에 deprecated로 표시한 뒤 최소 한 마이너 버전 유지하세요. **반면 플러그인 내부 구현**(스크립트 헬퍼, 훅 lib, 템플릿 내부 구조)에는 호환 레이어를 쌓지 말고 쓰이지 않는 경로를 삭제하세요.
- 현재 요구사항을 완전히 충족하는 가장 단순한 구현을 선택하세요. 추측에 근거한 추상화, 설정값, 간접 계층을 만들지 마세요.
- 시스템은 레이어로 키우세요. 엔드투엔드로 동작하는 최소 버전에서 시작하고, 이미 동작하는 결과물 위에 기능을 하나씩 얹으세요. 동작하는 코드를 미완성 복잡도와 맞바꾸지 마세요.
- 컴포넌트는 모듈로 분리하고 관심사를 명확히 나누세요.
- 검증된 라이브러리가 전체 복잡도를 낮춘다면 그것을 쓰세요. **단 이 저장소의 런타임은 표준 라이브러리만 씁니다** — 의존성 추가는 별도 승인 사항입니다 (`docs/deterministic-gates.md` "Adding a gate" 규칙 5).
- 직접 구현하거나 패키지를 추가하기 전에 이미 설치된 의존성부터 확인하세요. 문서와 타입을 확인하지 않은 채 "이 라이브러리엔 그 기능이 없다"고 단정하지 마세요.
- 아키텍처 결정은 장기 관점으로 하세요. 지금만 넘기고 나중에 교체할 임시방편을 받아들이지 마세요.

## The exit code is the verdict

When a script can judge something, **the script judges it.** Exit codes are the
contract: `0` pass · `1` warning · `2` abort · `3` could not run. **A gate that
could not run has produced no verdict — never read that as a pass.** Do not
re-derive a verdict by parsing a runner's output; read the exit code, then use
the text only to explain it. Name the deciding gate in every verdict:
`pytest → exit 1 (3 failed)`.

Contract and how to add a gate: `docs/deterministic-gates.md`.

Before release, run the full check set `AGENTS.md` § Change rules 5 lists — the
plugin validator, every skill validator, the skill linter, shell syntax checks,
and the test suite.

## Other rules that apply to you here

Do not re-derive these; they are written down.

| Question | Read |
|---|---|
| Iterating on a quality-gated deliverable | `rules/self-loop.md` |
| How many workers to spend on a task | `rules/route-hint.md` |
| How hard to verify a change | `rules/verify-route.md` |
| Full rule index | `docs/rules-reference.md` |
| Repository layout | `docs/directory-structure.md` |

**Do not pre-create empty directories.** Skills create what they need; an empty
tree makes phase detection read a fresh project as one that already started.

`docs/` holds everything else — list it rather than trusting an index carried in
a guide file.
