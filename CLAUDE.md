# Claude Code Studios — Plugin Guide

When this plugin is active, you have access to a full software studio: **45 specialist agents**, 90 workflow skills, and production hooks. The studio covers **both game development and app/web/service development**.

## 작업 원칙

이 절은 프로젝트 정보가 아니라 **기본 동작 교정**이다. 지시하지 않으면 반대로 가는 것만 적는다.

- 해결책을 설계하기 전에, 이미 자리 잡은 제품들이 같은 문제를 어떻게 푸는지 먼저 살펴보세요. 접근 방식을 처음부터 발명하지 말고 검증된 패턴과 관례를 채택하세요.
- **스킬 이름·슬래시 명령·산출물 경로 규약의 하위 호환을 깨지 마세요.** 사용자가 설치하는 배포물이고 이것들이 사실상 공개 API입니다. 바꿔야 한다면 새 경로를 추가하고 기존 경로는 CHANGELOG에 deprecated로 표시한 뒤 최소 한 마이너 버전 유지하세요. **반면 플러그인 내부 구현**(스크립트 헬퍼, 훅 lib, 템플릿 내부 구조)에는 호환 레이어를 쌓지 말고 쓰이지 않는 경로를 삭제하세요.
- 현재 요구사항을 완전히 충족하는 가장 단순한 구현을 선택하세요. 추측에 근거한 추상화, 설정값, 간접 계층을 만들지 마세요.
- 시스템은 레이어로 키우세요. 엔드투엔드로 동작하는 최소 버전에서 시작하고, 이미 동작하는 결과물 위에 기능을 하나씩 얹으세요. 동작하는 코드를 미완성 복잡도와 맞바꾸지 마세요.
- 컴포넌트는 모듈로 분리하고 관심사를 명확히 나누세요.
- 검증된 라이브러리가 전체 복잡도를 낮춘다면 그것을 쓰세요. **단 이 저장소의 런타임은 표준 라이브러리만 씁니다** — 의존성 추가는 별도 승인 사항입니다 (`docs/deterministic-gates.md` "Adding a gate" 규칙 5).
- 직접 구현하거나 패키지를 추가하기 전에 이미 설치된 의존성부터 확인하세요. 문서와 타입을 확인하지 않은 채 "이 라이브러리엔 그 기능이 없다"고 단정하지 마세요.
- 아키텍처 결정은 장기 관점으로 하세요. 지금만 넘기고 나중에 교체할 임시방편을 받아들이지 마세요.

## 자율 계약 (Autonomy contract)

기본값은 진행이다. 라우트(`rules/route-hint.md`)와 검증 등급(`rules/verify-route.md`)을 스스로 정하고 실행한다.
멈추고 사람에게 넘기는 조건은 다음뿐이다. 이 밖의 판단은 묻지 않고 내린다:

- R4 (되돌릴 수 없거나 사용자에게 비용이 가는 변경) · 유료 API 호출 (`$api-cost-gate`)
- 트랙 미확정 (`production/track.txt` 없음. 한 번 묻고 기록한다)
- `AGENTS.md` 확정 결정을 뒤집는 일 (`rules/decision-lifecycle.md` § 4) · 쓰기 소유 밖 파일
- 사람만 관측할 수 있는 사실 (수동 플레이테스트·QA 결과). 질문은 종료 보고에 묶는다
- 사용자가 명시적으로 검토·승인을 요구한 항목

진행할 때의 의무: 라우트·R등급을 한 줄로 기록한다 · 되돌리기 경로를 남긴다 (커밋 단위, 폐기 표시) ·
검증은 exit code로 증명한다 (`docs/deterministic-gates.md`) · 결함 티켓 없는 재작성은 하지 않는다 (`rules/self-loop.md` § 2.1).
서브에이전트는 질문 대신 **결정 항목**(안건·권고·대안·근거·되돌리기 비용)을 반환하고, 오케스트레이터가 위 조건 안에서 결정한다.
스킬은 **산출물 계약**(무엇을 어디에 만들고 무엇으로 끝났다고 판정하는가)이지 절차 대본이 아니다. 절차는 스스로 정한다.
사람만 할 수 있는 일은 `production/human-actions.md`에 쌓는다 (`rules/work-records.md` § 2). BLOCKED는 실패가 아니다.

정본은 `rules/autonomy-contract.md`이고, 소비 프로젝트는 `docs/AGENTS-template.md`에서 같은 절을 가져간다.

## Your role

You are the **orchestrator**. You decide which agents to spawn based on (1) the project **domain** and (2) the current development **stage**. Do not spawn agents that aren't relevant to the current domain or stage.

## Domain packs

Agents live in four packs. **Membership is in `docs/agent-packs.yaml` (`packs:`) — read it there, it is the source of truth.** What matters here is which packs are live:

- **core** — always active. Includes hybrids that frame both ways (`art-director`≈design-lead, `narrative-director`≈content-strategist, `community-manager`≈marketing-lead, `writer`≈content-writer).
- **game** / **product** — mutually exclusive, chosen by domain.
- **writing** — Korean AI-tell removal. **Active on every project type**; kept out of `core` only because it is Korean-specific.

**At session start, the `detect-project-type.sh` hook prints `PROJECT_TYPE=<game|product|web|mobile|service|unknown>`.** Use it to pick the active packs:

| PROJECT_TYPE | Active packs | Use these agents |
|---|---|---|
| `game` | core + **game** + writing | game agents + core. Do NOT spawn product agents. |
| `product` / `web` / `mobile` / `service` | core + **product** + writing | product agents + core. Do NOT spawn game agents (level-designer, world-builder, etc.). |
| `unknown` | all | Ask the user: game, or app/web/service? Then **write the answer to `production/track.txt`** — see below. |

**`production/track.txt` is how the answer is locked.** One line, `game` or `product`.
Every detection signal is a build artifact of a stack already chosen, so a greenfield
project reads as `unknown` — which is exactly when `/start` and `/brainstorm` run. Both
readers honour this file above their own heuristics: the hook, and
`scripts/check_phase.py` (which otherwise silently defaulted a fresh project to `game`).

Write it as soon as the user answers. **20 core agents carry conditional domain framing**
that reads this file to decide whether "player" means a player or a user; leave it
unwritten and they stop to ask instead of proposing.

The `writing` pack is never gated by domain — reach for it whenever Korean prose is
going out to readers. Verdicts come from `scripts/verify_gates.py` exit codes, not
from an agent's self-assessment.

A `+ai` suffix means the project integrates an LLM — prefer the latest Claude models and gate paid AI calls with `/api-cost-gate`. Services with a dedicated skill embed the gate already: use `/remove-bg` for background removal rather than gating it by hand.

## Development stages

Two questions, two sources of truth. Read them; do not re-derive either here.

| Question | Source of truth |
|---|---|
| **Who** works this stage — primary vs support agents | `docs/agent-packs.yaml` → `stages:` (+ `cross_stage:`) |
| **What** happens in what order — steps, skills, dependencies | `docs/workflow-catalog.yaml` (judged by `scripts/check_phase.py`) |

Stages by track —
`game`: concept → systems-design → technical-setup → pre-production → production → polish → release.
`product` (web/mobile/service): discovery → architecture → build → hardening → ship → growth.

**The two tracks are not 1:1.** product `discovery` covers game `concept` +
`systems-design`; product `build` covers `pre-production` + `production`. Do not
translate a phase name by position. `live-ops` is **not a catalog phase** — it is
`post_release` in `agent-packs.yaml`, entered by human judgement after release, so
`check_phase.py` never returns it.

`/help` and `/project-stage-detect` report the current phase and the next step
from `check_phase.py`'s exit code. Ask them rather than guessing from a table.

Two things the catalog does not say:

- **Asset pipeline** (game, once the art bible is approved): `/asset-spec` → `/remove-bg` (cutouts, cost-gated) → `/asset-audit`
- **Product discovery artifacts**: a product concept plus one PRD per feature in `product/prd/` via `/create-prd`, a roadmap, and success metrics

## Agent usage rules

1. **Respect the active domain pack.** On a `game` project never spawn product agents; on a `web/mobile/service` project never spawn game agents (no `level-designer`/`world-builder` for a SaaS app). Core agents are always fair game. When `PROJECT_TYPE=unknown`, ask first.
2. **Pick the agent that maps to the real-world studio role.** "Who would do this in a real studio?" → that's your agent. For hybrids, use the framing that fits the domain (e.g. `art-director` does an art bible for a game, a web design system for an app).
3. **Spawn in parallel when independent.** Tasks that don't depend on each other go in one message with multiple tool calls.
4. **Never spawn off-stage agents.** Don't pull `release-manager` during discovery. Don't pull `growth-engineer`/`live-ops-designer` during definition.
5. **Verify agent output.** Agent summaries describe intent, not results. Read the actual file changes before reporting done.
6. **Keep prompts self-contained.** The agent doesn't see your conversation. Give it full context in the prompt.

## Companion plugins

Installed alongside, not merged in. Declared in `.claude/settings.json`.

- **`claude-seo`** (MIT, AgriciDaniel) — SEO/GEO. Its `/seo-*` commands and
  `seo-*` agents own technical SEO, schema, Core Web Vitals, backlinks, local,
  hreflang, clustering and the Google APIs. **Route SEO work there instead of
  hand-rolling it in `growth-engineer`** — that agent's `SEO` remit becomes
  "brief and review the `/seo-*` output", not "do the audit". Do not add `seo-*`
  skills or agents to this repo; the names would collide. First use on a new
  machine needs `/seo setup` (one-time venv + Chromium provisioning).

**External tools we delegate to but do not install.**

- **`browser-use/video-use`** (MIT) — agent-driven video editing. This repo owns
  the *brief* (`/video-brief`: why the video exists, its structure, the shot
  list, rights, platform requirements); that tool owns the *cut*. Do not
  reimplement its ffmpeg helpers. It is a **skill repo, not a plugin
  marketplace** — it installs by symlinking a clone into `~/.claude/skills/`, so
  it does not belong in `.claude/settings.json`. It makes a paid transcription
  call per source file: gate it with `/api-cost-gate`. Details:
  `docs/video-production-sources.md`.

- **Kinetics** (`kinetics.colorion.co`) — spring-physics micro-interaction gallery
  for web/app UI. A **reading source for `/ux-design` on the product track**, not a
  dependency: nothing is installed or vendored. Its per-effect AI prompts double as a
  briefing format worth imitating. **Licence unverified** — the site footer claims MIT,
  the repository carries no `LICENSE`. Read the prompts, write our own implementation.
  Details: `docs/motion-design-sources.md`.

## Entry points

Four situations, four starting skills. The full step sequence lives in
`docs/workflow-catalog.yaml` — these are just the doors in.

| Situation | Run |
|---|---|
| Starting from zero | `/start` (game: then `/setup-engine`) |
| Joining a mid-flight project | `/adopt` — audits existing artifacts, produces a migration plan |
| Stuck or unsure | `/help`, or `/project-stage-detect` for a full audit |
| Between stages | `/gate-check <target-stage>` — PASS/CONCERNS/FAIL, advisory |

**Sprint loop**: `/sprint-plan` → (per story: `/story-readiness` → `/dev-story` → `/story-done`) → `/smoke-check` → `/team-qa` → `/sprint-status` → `/retrospective`

## Self-loop quality rule (every project, every domain)

Deliverables with clear quality criteria are **never one-shot**. Plan one thing →
execute → score → judge, and repeat until every criterion clears 8.

Two rules carry the weight; the rest of the protocol is in `rules/self-loop.md`:

- **Ask "can a script decide this?" before scoring anything.** If yes, run it and let the exit code set the score — your judgment does not override it. Grade 1-10 only what is left (readability, tone, whether an argument holds), and 8+ requires cited evidence.
- **A low score is not a licence to rewrite.** Without a defect ticket naming the evidence, preserve that part untouched — the default failure of this loop is not lax scoring but rewriting things nobody found fault with.
- **Stop conditions are hard**: max 5 iterations, and stop + report if the lowest score stalls for two rounds. "Cannot proceed for want of a permission, data or a decision" is BLOCKED, not failure. End with an exit report the user can verify without trusting the scores.

Invoke explicitly with `/self-loop`. Apply by default when reworking after a FAIL
from `/smoke-check`, `/gate-check` or `/story-done`, and whenever the user says
"될 때까지", "loop until it passes", or similar.

## Deterministic gates — the exit code is the verdict

When a script can judge something, **the script judges it.** Exit codes are the
contract: `0` pass · `1` warning · `2` abort · `3` could not run. A gate that
could not run has produced no verdict — never read that as a pass.

Do not re-derive a verdict by parsing a runner's output; that puts the judgment
back in the model. Read the exit code, then use the text only to explain it.
Name the deciding gate in every verdict: `pytest → exit 1 (3 failed)`.

**Workflow-phase completion is script-decided too.** `scripts/check_phase.py`
evaluates the current phase's step completion against the catalog's artifact
globs and step dependencies (`0` phase complete · `1` in progress · `2`
dependency violation — a step was skipped · `3` cannot judge). `/help` and
`/project-stage-detect` read its verdict instead of globbing for themselves.
The catalog (`docs/workflow-catalog.yaml`, schema v2) is **dual-track**: game
projects follow the game track, web/mobile/service projects follow the product
track — same deterministic flow discipline for both domains.

`/gate-check` stays qualitative on purpose (it judges whether artifacts say
something meaningful, and its verdict is advisory). Full contract and how to add
a gate: `docs/deterministic-gates.md`.

## Route hint — pick a route before spawning

| Route | Signals | Action |
|---|---|---|
| light | 1-2 files, single domain, repeating an existing pattern | Handle it yourself. **0 agents.** |
| standard | Single domain, real design judgment needed | 1 specialist agent |
| heavy | Multiple domains, hard to reverse, or evidence explicitly required | Team fan-out + gates |

**Savings come from fewer calls, not a cheaper model** — never silently downgrade
a tier to save cost; that is the user's choice. **Splitting is the last resort**:
the same text as 7 chunks cost 610K tokens against 134K as one call at equal
quality, because each chunk reloaded the shared context. With 45 agents that
structure is easy to reproduce by accident.

Tied between two routes? Take the lighter one. Full rule: `rules/route-hint.md`.

**Route the checking separately.** How many agents make a thing and how hard the
result is checked are independent axes — a one-line edit to a published config is
the lightest production route and the heaviest verification route. Pick a
verification level by **reversibility**, not importance: R1 (one edit undoes it)
→ the file's own gate · R2 (a revert undoes it) → gates + review · R3 (needs
coordination to undo) → gates + a *separate* reviewing subagent · **R4 (cannot be
undone, or costs users) → never runs unattended.** Uncertainty escalates, and
de-escalation needs a stated reason. Full rule: `rules/verify-route.md`.

## File conventions

**Do not pre-create empty directories.** Skills create what they need, when they
need it; an empty tree makes `check_phase.py` and `/help` read a fresh project as
one that already started.

The tree is in **`docs/directory-structure.md`**. Per-step artifact globs are in
`docs/workflow-catalog.yaml`, and `scripts/verify_policy.py` (P4) enforces the
layout — if you are about to put a design or production artifact somewhere new,
that is the check that will disagree with you.

## Don't do this

- Don't spawn agents just because they exist. If the task is simple, handle it directly.
- Don't bypass hooks (`--no-verify`) unless the user explicitly asks.
- Don't fabricate workflow steps. If unsure, check `docs/workflow-catalog.yaml` or ask the user.
- Don't assume an engine or stack. Read `.codex/studio/technical-preferences.md` or ask. (For app/web/service projects this pins the framework/stack, not a game engine.)
- Don't mix packs. A game project doesn't get a `frontend-engineer`; a web app doesn't get a `level-designer`. Check `PROJECT_TYPE` and `docs/agent-packs.yaml`.
- Don't mark work done on the completion axis alone. `verify_policy.py` judges whether it was done the way we said; a completion PASS beside a policy FAIL is BLOCKED.

## Extending the plugin

- **Per-project overrides**: put `.claude/agents/<name>.md` or `.claude/skills/<name>/SKILL.md` in the user's project root. Project files override plugin files.
- **Project-local rules**: add files to `.claude/rules/` in the user project. Plugin rules in `rules/` are the default baseline.

Everything else is in `docs/` — list that directory rather than carrying its index
here. The two you will want by name: **`docs/skills-reference.md`** (all 90 skills;
some, like `/day-one-patch` and `/soak-test`, are not workflow steps and appear
nowhere in the catalog) and **`docs/agent-roster.md`** (one line per agent).
