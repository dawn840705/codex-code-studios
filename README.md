# Code Studios for Codex

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Codex plugin](https://img.shields.io/badge/Codex-plugin-blue)](.codex-plugin/plugin.json)

A software studio packaged as a [Codex CLI](https://github.com/openai/codex) plugin — **for game development and for app/web/service development.**

**45 specialist role guides** · **91 workflow skills** · **Codex lifecycle hooks** · **governance/workflow assets** · **domain packs with automatic project-type detection** — covering every stage from pre-production through production, QA, release, and live-ops.

> **Looking for the Claude Code version instead of Codex CLI?** See [`claude-code-studios`](https://github.com/dawn840705/claude-code-studios) — same studio, packaged for Claude Code's agent/skill format. If your project uses both CLIs, `production/runtime.txt` (`codex` / `claude` / `split`) tells each session which one is actually driving so they don't silently overwrite each other's work.

Built by a solo developer with 15+ years of production/PM and game-design experience in the games industry, and updated roughly weekly. Every role guide, skill, and gate here is first applied on a real, shipping project — *StarDiver*, a Unity 6 PC/console roguelite cover shooter — then validated there before it's folded back into the plugin. See [Origin & How This Gets Validated](#origin--how-this-gets-validated) for the full story.

It mirrors how a real studio is organized: directors (creative / technical / producer) coordinate department leads (design / programming / art / audio / narrative / QA), who in turn coordinate specialists (gameplay programmer, level designer, economy designer, and so on). Every design agent and template is grounded in established game design theory — MDA Framework, Self-Determination Theory, Flow State, Bartle Player Types.

Engine-agnostic: works with Godot, Unity, Unreal, GameMaker, or a custom engine.

> **Latest (v0.7.2):** added `rules/runtime-modes.md` so a project worked on by both Codex and Claude Code declares who's actually driving in `production/runtime.txt` — the two CLIs don't share sessions or tool logs, so an overwrite is invisible to both sides until it's already happened. v0.7.1 added an anchor-based 3D art pipeline (reviewed anchor → consistent views → generated model → Blender rig/animation). v0.7.0 migrated the whole plugin from Claude Code's format to a native Codex plugin — `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` are now the install manifests, skills use `$skill-name` invocation, and hooks use Codex's `apply_patch`/`SessionEnd`/JSON output contract. Full version history, including the v0.6.4 fix for a gate that silently flipped PASS to FAIL on Korean-locale Windows consoles, is in [CHANGELOG.md](CHANGELOG.md).

## Table of Contents

- [Origin & How This Gets Validated](#origin--how-this-gets-validated)
- [What's Inside](#whats-inside)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Governance & Workflow Assets](#governance--workflow-assets)
- [Recommended Directory Structure](#recommended-directory-structure)
- [Customization](#customization)
- [Status & Stages](#status--stages)
- [Changelog](#changelog)
- [License](#license)

---

## Origin & How This Gets Validated

This isn't a plugin written from theory and shipped once. I've spent 15+ years in the games industry across production, PM, and game design, and this repo is where that know-how gets encoded into a repeatable process — then re-tested on real work, roughly weekly.

The loop: a process or rule that mattered on a real production (crunch triage, a scope-creep pattern, a review checklist that actually caught something) gets written up as a role guide, skill, or gate here. It's applied on *StarDiver*, a Unity 6 PC/console roguelite cover shooter currently in production, as the testbed. If it holds up against a real shipping project, it stays and gets sharpened; if it doesn't, it gets cut or rewritten. The [Changelog](#changelog) is largely that loop's paper trail — most releases exist because something broke or fell short on StarDiver first.

That's also why the deterministic-gate work (`docs/deterministic-gates.md`) exists at all: "the agent says it's done" wasn't good enough once real production stakes were on the line, so verdicts moved to script exit codes wherever a script could actually judge the outcome.

---

## What's Inside

### Role guides (45)

Directors, department leads, and specialists — mirroring a real studio's org chart. Four domain packs: **core** (every project), **game** (game-only), **product** (app/web/service-only), and **writing** (Korean copy editing, active on every project type).

- **Product pack**: `product-manager`, `frontend-engineer`, `backend-engineer`, `mobile-engineer`, `data-engineer`, `growth-engineer`, `technical-writer`
- **Game/core roster**: directors (`creative-director`, `technical-director`, `producer`), design (`game-designer`, `systems-designer`, `economy-designer`, `level-designer`, `narrative-director`, `world-builder`, `writer`, `live-ops-designer`), programming (`lead-programmer`, `gameplay-programmer`, `ui-programmer`, `ai-programmer`, `engine-programmer`, `network-programmer`, `tools-programmer`, `prototyper`), art/audio (`art-director`, `technical-artist`, `audio-director`, `sound-designer`), QA/ops (`qa-lead`, `qa-tester`, `performance-analyst`, `security-engineer`, `accessibility-specialist`, `localization-lead`, `release-manager`, `devops-engineer`), UX/community/analytics (`ux-designer`, `community-manager`, `analytics-engineer`)
- **Writing pack**: `humanize-monolith`, `humanize-diagnostician`, `humanize-finalizer`, `korean-ai-tell-taxonomist` (Korean-specific — natural-language editing for patch notes, GDDs, release notes, and landing copy)

Full roster and reporting lines: [docs/agent-roster.md](docs/agent-roster.md).

### Skills (91)

Organized by development stage — pre-production, sprint/production, code quality, QA, team orchestration, release/ops, meta-audit, and a dedicated product track (`$product-concept` → `$create-prd` → `$ux-design` → `$gate-check architecture`). Invoke one explicitly as `$skill-name` in Codex; `$studio-orchestrator` routes multi-discipline requests to the smallest useful set of role guides.

Full command list with descriptions: [docs/skills-reference.md](docs/skills-reference.md). New to the project? Start with [docs/quick-start.md](docs/quick-start.md).

### Hooks

- `UserPromptSubmit` — recommends a tool/script for deterministic work or the current session model for judgment work; runs opt-in effort observation
- `SessionStart` — loads project context, flags missing docs, detects project type
- `PreToolUse` (`exec_command`/`Bash`) — validates git commit/push
- `PostToolUse` (`apply_patch` and edit aliases) — checks asset naming, skill changes, and Unity safeguards across every file touched by a patch
- `PreCompact` / `PostCompact` / `SessionEnd` — JSON context recovery and session-end logging
- `SubagentStart` / `SubagentStop` — agent activity logging

Hooks that touch paths read the project layout from [hooks/lib/detect-layout.sh](hooks/lib/detect-layout.sh), which detects the engine (Unity / Godot / Unreal / GameMaker / generic) and picks the right source root, design-doc root, asset root, and naming convention — while excluding build output like `Library/`, `Temp/`, `node_modules/`. Override with `.codex/studio-layout.json`. Contract and how to add a hook: [docs/hooks-reference.md](docs/hooks-reference.md).

If the plugin detects a Unity project (`Assets/` + `ProjectSettings/`), two advisory hooks turn on automatically: a `.meta`-file check and an Animator string-lookup lint. A stricter opt-in git pre-commit hook (`templates/githooks/unity-pre-commit`) can *block* commits missing `.meta` files — see [docs/engine/unity-setup.md](docs/engine/unity-setup.md). On non-Unity projects, both exit silently with no effect.

### Templates & rules

Engine/genre/platform-agnostic workflow assets:

| Asset | Location | Purpose |
|---|---|---|
| Meeting notes template | [docs/templates/meeting-template.md](docs/templates/meeting-template.md) | Header metadata box + decision table + memory-write protocol |
| API CLI template | [docs/templates/api-cli-template.py](docs/templates/api-cli-template.py) | Scaffold for a pay-as-you-go external AI API wrapper (env loading, auth, async polling, sync binary, download) |
| Product PRD template | [docs/templates/product-requirements-document.md](docs/templates/product-requirements-document.md) | Product-level PRD for the product track — problem, personas, core loop, MVP scope, requirements, KPIs, out-of-scope |
| Human action queue template | [docs/templates/human-action-queue.md](docs/templates/human-action-queue.md) | A standing queue for things only a human can do — separates execution (🔴) from judgment (🟡), keeps a "why a human" column, demotes rather than deletes on completion |
| Token efficiency rules | [docs/rules/token-efficiency.md](docs/rules/token-efficiency.md) | R1–R8: commit message length, meeting-notes length, batch reporting, parallel reads, memory discipline, response length, scoped reference reads, upfront completion criteria |
| Artifact organization rules | [docs/rules/artifact-organization.md](docs/rules/artifact-organization.md) | Three-zone discipline (Workshop / Curated / Engine) + prefix naming + `.prompt.txt` companion rule |

---

## Installation

### Option 1 — install from the GitHub marketplace (recommended)

```bash
codex plugin marketplace add dawn840705/codex-code-studios
codex plugin add codex-code-studios@code-studios
```

To pull a fresh marketplace snapshot:

```bash
codex plugin marketplace upgrade code-studios
```

### Option 2 — local marketplace (for development or forks)

```bash
git clone https://github.com/dawn840705/codex-code-studios.git /path/to/codex-code-studios
codex plugin marketplace add /path/to/codex-code-studios
codex plugin add codex-code-studios@code-studios
```

The first time Codex runs a hook from `hooks/hooks.json`, it may show a trust review. Read it, then approve.

### Option 3 — validate locally without installing

```bash
python3 /path/to/codex-code-studios/scripts/lint_skills.py \
  /path/to/codex-code-studios/skills \
  /path/to/codex-code-studios/skills/studio-orchestrator/references/roles
```

`rules/*.md` is workflow reference material that skills read — don't copy it into `.codex/rules/*.rules`, which is Codex's own command-approval policy.

---

## Quick Start

After installing, in a new game project:

1. `$start` — first-time onboarding; figures out where you are and routes you to the right workflow
2. `$setup-engine` — pin your engine (Unity / Unreal / Godot / GameMaker / custom) and version
3. `$brainstorm` — guided ideation from zero to a structured game concept document
4. `$map-systems` — break the concept into systems and prioritize them
5. `$design-system <system>` — write a GDD for each system
6. `$create-architecture` → `$create-epics` → `$create-stories` → `$dev-story`

Joining an in-progress project instead? `$adopt` audits existing artifacts and produces a migration plan.

For an app/web/service project, the equivalent path is `$start` → `$product-concept` → `$create-prd` → `$ux-design` → `$create-architecture`.

---

## Governance & Workflow Assets

These are especially useful for a solo or small team handling a lot of AI-generated assets.

### Domain Bible bootstrap (`$governance-bible-init`)

Bootstraps an Anchor + Bible pattern per creative domain (sound / art / narrative):

```bash
$governance-bible-init sound chapter-1
$governance-bible-init art chapter-1
$governance-bible-init narrative chapter-1
```

Creates a `Documents/<Domain>Design/Anchors/` folder plus a Bible `README.md` (tone filter, naming convention, category table). The first anchor asset is saved under `Anchors/` with prefix naming (`mus_*.mp3`, `char_*.png`, …) alongside a matching `.prompt.txt` for reproducible regeneration. Every new asset afterward goes through an anchor-comparison decision loop (accept / retry once / reject) — the core mechanism against style drift.

### Paid API cost gate (`$api-cost-gate`)

Forces a 4-point disclosure before *any* pay-as-you-go AI call (Suno, ElevenLabs, Midjourney, Tripo, OpenAI, etc.):

```bash
$api-cost-gate suno combat-bgm-30s
```

Shown before the call: (1) exact call type — endpoint/model/mode, (2) cost estimate in credits/characters/dollars plus current balance, (3) purpose, (4) how the result will be used and judged. The call runs only after explicit user approval — **auto mode does not bypass this.**

### Background removal (`$remove-bg`)

Removes backgrounds from sprites, characters, or product images via the [remove.bg API](https://www.remove.bg/api). Supports a single file, a folder batch, or an asset-manifest run, with the cost-disclosure gate above already built in.

```bash
export REMOVE_BG_API_KEY=<key>       # https://www.remove.bg/dashboard#api-key

$remove-bg design/assets/raw/hero.png            # single file
$remove-bg design/assets/raw/ --type graphics    # folder batch
$remove-bg manifest:tower-defense                # asset manifest
```

The verdict comes from a script (`scripts/removebg.py`, standard library only):

```bash
python3 scripts/removebg.py account                      # check balance, no charge
python3 scripts/removebg.py estimate <path> --check-balance --json   # estimate, no charge
python3 scripts/removebg.py run <path> --out <dir> --max-calls 20
```

- **Exit code is the verdict**: `0` all succeeded · `1` partial failure · `2` aborted (all failed / 402 insufficient credit / 403 auth failure / `--max-calls` exceeded) · `3` could not run (no key — not a pass)
- **`--size preview` is the default**: preview ≈ 0.25 credits, full ≈ 1 credit (4x). Use preview for review passes, full only for final production art.
- **`--max-calls` is a seatbelt**: if the input set grows between estimate and run, it aborts instead of billing past what was approved.
- Actual charges are logged to `removebg-report.json` from the measured `X-Credits-Charged` response header.
- The API key is never accepted as a CLI argument (shell history / process list exposure). Environment variable or `--api-key-file` only.

### Multi-source-of-truth audit (`$sot-audit`)

Audits consistency for systems whose definition is scattered across multiple places — FSMs, input bindings, save schemas, localization, audio mixers, shader uniforms, network messages — via an N-witness matrix:

```bash
$sot-audit player-fsm \
  doc=design/specs/player-fsm.md \
  enum=src/PlayerStateType.cs \
  asset=assets/animator/PlayerAnim.controller \
  callsites=src/PlayerController.cs
```

Produces a severity-classified mismatch report (🚨 High / ⚠️ Medium / ℹ️ Low) — catches silent-fail risk before it ships.

### Migration debris cleanup (`$legacy-purge`)

After a genre pivot, API deprecation, platform change, or architecture rewrite, greps for leftover legacy code/docs/assets by category:

```bash
$legacy-purge mobile-vertical pc-horizontal "Assets/02.Scripts/**"
```

Produces a findings table cross-referenced against policy docs. **Never deletes automatically** — human review required.

### Meeting notes / API CLI templates

Ready-to-use scaffolds for a new meeting or a new external API wrapper:

```bash
cp <plugin>/docs/templates/meeting-template.md Documents/Meetings/YYYY-MM-DD-<topic>.md
cp <plugin>/docs/templates/api-cli-template.py Tools/<NewService>API/<service>.py
```

Fill in the `⚠️ FIXME` markers inside each template.

### Pinning workflow rules

Add the assets you need to your project's `AGENTS.md` so Codex reads them as project instructions:

```markdown
## Workflow rules

- Token efficiency: docs/rules/token-efficiency.md (R1–R8)
- Artifact organization: docs/rules/artifact-organization.md (Workshop / Curated / Engine three-zone + prefix naming)
- Meeting notes: use the docs/templates/meeting-template.md format
```

---

## Recommended Directory Structure

Agents and skills assume the following layout at the project root:

```
design/gdd/                # GDD documents
production/sprints/        # sprint plans
production/bugs/           # bug reports
src/                       # source code (per engine)
tests/                     # test files
.codex/                    # Code Studios project state (optional)
  └── studio/
      └── technical-preferences.md   # engine + version pin

# When applying the v0.2.0 artifact-organization rules:
Tools/<Service>API/output/        # workshop (gitignored)
Documents/<Domain>Design/Anchors/ # per-domain Bible + anchor assets
Documents/Meetings/               # meeting notes
Documents/api-cost-log.md         # cumulative paid-API call log
```

Skills create these folders automatically as work progresses.

---

## Customization

- **Project instructions**: record team rules and local constraints in your project's `AGENTS.md`.
- **Adding a specialist role**: place a separate role guide for `$studio-orchestrator` to read in your project docs, and include only the relevant excerpt in delegation prompts.
- **Workflow material**: this plugin's `rules/*.md` is skill reference material, not a Codex execpolicy file.

---

## Status & Stages

- Covers every stage: pre-production · production · polish & QA · release · live-ops.
- `$studio-orchestrator` reads only the role guides relevant to the *current* stage before handing context to Codex subagents. Full mapping: `docs/agent-packs.yaml`.

---

## Changelog

Full per-version history is in [CHANGELOG.md](CHANGELOG.md).

- **v0.7.2** — `rules/runtime-modes.md`: a project worked by both Codex and Claude Code declares who's driving in `production/runtime.txt`, since the two CLIs share no session/context/tool log and a losing side can report success while silently overwriting the other's work.
- **v0.7.1** — anchor-based 3D art pipeline (reviewed anchor → consistent views → generated model → Blender rig/animation), wired into orchestration, asset specs, and read-only delivery audits.
- **v0.7.0** — migrated from a Claude Code plugin to a native Codex plugin (`.codex-plugin/plugin.json`, `$skill-name` invocation, `.codex/studio/` state, Codex-native hooks). `.claude-plugin/` and `CLAUDE.md` remain only as a compatibility layer to identify prior installs.
- **v0.6.4** — deterministic gates now survive the console they run in (a Korean-locale Windows console was silently flipping gate PASS results to FAIL via a `UnicodeEncodeError`); broadened the Unity Animator string lint; `detect-gaps` gained a `productionRoots` override.
- **v0.6.0–v0.6.3** — gates became script-judged by exit code rather than self-graded (`docs/deterministic-gates.md`); closed four gaps in that contract (unsafe-success on skipped tests, silent routing drift, prose-only gate output, unrouted verification risk); added the Korean writing pack and the repo's first test suite/CI (585+ tests).
- **v0.4.0–v0.5.0** — split agents into `core` / `game` / `product` domain packs with automatic project-type detection.
- **v0.2.0–v0.3.0** — added governance/workflow assets (`$governance-bible-init`, `$api-cost-gate`, `$sot-audit`, `$legacy-purge`) and Unity-specific safeguards.
- **v0.1.0** (2026-04-22) — initial release: 34 agents + 72 skills + production hooks.

> **Experimental:** a project-scoped, opt-in reasoning-effort observation mode is in progress (auto-detects task complexity, does not change parent-conversation settings). Not yet validated for efficacy or cost savings. Details: [docs/reasoning-effort.md](docs/reasoning-effort.md) · [validation log](docs/reasoning-effort-validation.md).

---

## Acknowledgments

Originally built and validated on the Cannon Kingdom project, then extracted into a standalone, portable plugin. See [Origin & How This Gets Validated](#origin--how-this-gets-validated) for how it keeps getting validated today.

---

## License

MIT
