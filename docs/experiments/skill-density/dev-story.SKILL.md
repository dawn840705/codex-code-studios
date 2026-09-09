---
name: dev-story
description: "Read a story file and implement it. Loads the full context (story, GDD requirement, ADR guidelines, control manifest), routes to the right programmer agent for the system and engine, implements the code and test, and confirms each acceptance criterion. The core implementation skill — run after $story-readiness, before $code-review and $story-done."
---

# Dev Story

## 1. Goal

When this skill ends, the story's code exists in `src/` and — for Logic and Integration
stories — its test exists at the story's Test Evidence path in `tests/`. Every acceptance
criterion is mapped to a file, a test, or `DEFERRED` (Visual/Feel only); the session extract
is in `production/session-state/active.md`; the exit report names every path written, its
revert command, and every decision taken. Track: game as written; product substitutes
player→user, GDD→PRD (`design/gdd/` → `product/prd/`), engine→the stack pinned in
`.codex/studio/technical-preferences.md`.

## 2. Inputs

| Input | Where | If missing |
|---|---|---|
| Track | `production/track.txt` or the session's `PROJECT_TYPE` | **K1** — ask once, write the answer to `production/track.txt`, continue. Never infer it from repository contents |
| Story | argument path; else the active story in `production/session-state/active.md` | **K2** — ask which story; list `production/epics/**/*.md` with Status: Ready |
| TR registry | `docs/architecture/tr-registry.yaml` — the *current* `requirement` for the story's TR-ID (inline story text may be stale) | **BLOCKED (K2)** — "Run `$create-epics`" |
| Governing ADR | path from the story's `ADR Governing Implementation` field: Decision, Implementation Guidelines, Engine Compatibility, ADR Dependencies (`docs/architecture/[adr-file].md`) | **BLOCKED (K2)** — "Run `$architecture-decision`" or fix the filename. Status `Proposed` → BLOCKED until advanced |
| Dependencies | each story under Dependencies, found by globbing `production/epics/**/*.md`; read `Status:` | **BLOCKED (K2)** if a file cannot be found — name it |
| Control manifest | `docs/architecture/control-manifest.md` — required / forbidden patterns and performance guardrails for the story's layer; compare its header date with the story's `Manifest Version` | WARN and continue — "Run `$create-control-manifest`" |
| Engine / stack | `.codex/studio/technical-preferences.md` — `Engine:` (game), naming conventions, performance budgets, forbidden patterns, `Engine Specialists` | product has no `Engine:` — read the pinned stack |

Hold from the story, verbatim: title, ID, layer, Type (Logic / Integration / Visual/Feel /
UI / Config/Data), TR-ID, Manifest Version, every acceptance criterion, Implementation Notes,
Out of Scope, Test Evidence path, Dependencies. Load all of it before implementing.

## 3. Boundaries

**Stop (K1):** track unresolved (once) · paid API calls — gate them with `$api-cost-gate` ·
R4 work (migrations on real data, deletions, anything published) returns as a decision
item, never as an action. Everything else proceeds and is reported.

**Write ownership.** Programmer subagents own `src/`, `tests/` and `production/qa/evidence/`
and write there without asking. This skill itself writes only the story file (`Manifest
Version:`, a stale dependency `Status:`), the data file of a Config/Data story,
`production/session-state/active.md`, and K1/K2 items to `production/human-actions.md`.

**Do not:** spawn from the other track's table (product never spawns `gameplay-programmer`
or any game-pack agent; `lead-programmer` is core on both) · touch files outside the story's
Out of Scope boundary — make the smallest change that satisfies the criterion and record it
under Deviations; if it would alter another story's behaviour, leave it and record a
follow-up story · skip or defer the test on a Logic/Integration story · deviate silently
from the ADR (the ADR beats the story; record the conflict) · retry a blocked agent more
than once, narrower · discard partial work.

**Defaults** (deviate only with a reason in the report): manifest version mismatch → set
the story's `Manifest Version:` to today, implement against the current rules, report
`git checkout -- [story-path]` — unless a rule the Implementation Notes rely on was removed
or reversed · a dependency not `Complete`/`Done` → proceed, record "Implemented with
incomplete dependency: [title] — [status]" — unless its Completion Notes and test evidence
show it finished, then set its `Status:` to Complete and report path + revert.

**Routing** (by layer, Type, system; Config/Data spawns nobody):

| Story context | `game` primary | `product` primary |
|---|---|---|
| Foundation layer, any type | `engine-programmer` | `backend-engineer` (data model, auth, infrastructure) |
| Type: UI | `ui-programmer` | `frontend-engineer` (web) · `mobile-engineer` (mobile) |
| Type: Visual/Feel | `gameplay-programmer` | — |
| Core/Feature — gameplay mechanics · API, server logic, persistence | `gameplay-programmer` | `backend-engineer` |
| Core/Feature — AI behaviour, pathfinding · LLM integration | `ai-programmer` | `ai-programmer` (`$web-ai-patterns`; paid calls behind `$api-cost-gate`) |
| Core/Feature — networking, replication · realtime, websockets | `network-programmer` | `backend-engineer` + `network-programmer` secondary |
| Core/Feature — event schema, pipeline, warehouse | — | `data-engineer` |

Engine specialist (game only) as secondary when the story touches engine APIs or the ADR's
engine risk is HIGH (then always): Godot 4 `godot-specialist` `godot-gdscript-specialist`
`godot-shader-specialist` · Unity `unity-specialist` `unity-ui-specialist`
`unity-shader-specialist` · Unreal `unreal-specialist` `ue-gas-specialist`
`ue-blueprint-specialist` `ue-umg-specialist` `ue-replication-specialist`.

## 4. Definition of done and gates

The subagent prompt carries the whole package: story file, current requirement text, ADR
Decision + Implementation Guidelines verbatim, manifest rules for the layer, naming and
budgets, engine notes, the required test path, and "implement this story and write the
test". It returns paths written with status, the test runner's exit code, and **decision
items** (agenda, recommendation, alternatives, evidence, revert cost) — not questions
(`rules/subagent-collaboration.md` § 3.1). Decide them inside `rules/autonomy-contract.md`
and record each decision in the report.

| Type | Evidence required for done |
|---|---|
| Logic, Integration | test file at the Test Evidence path: `[system]_[feature]_test.[ext]`, functions `test_[scenario]_[expected_outcome]`, ≥1 per criterion, no random seeds / time assertions / external I/O, GDD formula bounds covered. Quote the runner's exit code verbatim (`pytest tests/... → exit 0`); non-zero is not done; "not run" is NOT RUN, never PASS |
| Visual/Feel, UI | no automated test; criteria are `DEFERRED` to `$story-done`; note that `production/qa/evidence/[slug]-evidence.md` will be needed |
| Config/Data | edit the data file directly, record each value from → to; a smoke check is the evidence |

Verdict tokens: **Implementation Complete** — every criterion implemented, covered, or
DEFERRED (Visual/Feel only) and the required test file exists. **BLOCKED** — only K1/K2:
state what must exist to resume and append it to `production/human-actions.md`. A blocked or
erroring agent is surfaced as `[AgentName]: BLOCKED — [reason]`, retried once narrower, then
skipped with the gap recorded; the report is always produced, partial or not. Scope too large
→ split via `$create-stories`.

## 5. Artifact contract

Writes: `src/[path]` and `tests/[path]` via the subagent; the story file fields above; the
session extract appended to `production/session-state/active.md` (create it if absent, then
say "Session state updated") — `## Session Extract — $dev-story [date]` with Story
(path — title), Files changed, Test written (path, or "None — Visual/Feel/Config story"),
Blockers, Next (`$code-review [files]` then `$story-done [story-path]`).

Exit report `## Implementation Complete: [Story Title]`: **Files changed** (`src/[path]`,
`tests/[path]` with test-function count, each with its revert) · **Acceptance criteria
covered** (`[x]` implemented in file:function / covered by test, `[ ]` DEFERRED) ·
**Deviations from scope** · **Decisions taken** (route · R-grade · defaults applied or
deviated with reasons · assumptions where the ADR was silent: "ADR-NNNN does not specify
[case]; assumed [X]", flagged for the ADR owner) · **Engine risks flagged** · **Blockers**
(K1/K2 only).

### Recommended next

`$code-review [file1] [file2]` → `$story-done [story-path]`. After every sprint story is
done: `$team-qa sprint` before advancing the stage.
