---
name: dev-story
description: "Read a story file and implement it. Loads the full context (story, GDD requirement, ADR guidelines, control manifest), routes to the right programmer agent for the system and engine, implements the code and test, and confirms each acceptance criterion. The core implementation skill — run after $story-readiness, before $code-review and $story-done."
---

> **Track check — this skill is game-framed.** Resolve `production/track.txt` (or the
> session's `PROJECT_TYPE` line) before Phase 0.
>
> - **`game`** — run as written.
> - **`product`** (web / mobile / service) — substitute as you read: player becomes user,
>   game becomes product, GDD becomes PRD (`design/gdd/` → `product/prd/`), engine becomes
>   the stack pinned in `.codex/studio/technical-preferences.md`. Read the PRD requirement in place of the GDD requirement, and use the **product** routing table in Phase 3 — the game table routes to `gameplay-programmer`, which this track must never spawn. There is no `Engine:` value; read the pinned stack instead.
> - **Unresolved** — ask once which track this is, write the answer to `production/track.txt`,
>   then continue. A greenfield project has no signal either way; do not infer one from the
>   repository contents.

# Dev Story

This skill bridges planning and code. It reads a story file in full, assembles
all the context a programmer needs, routes to the correct specialist agent, and
drives implementation to completion — including writing the test.

**The loop for every story:**
```
$qa-plan sprint           ← define test requirements before sprint begins
$story-readiness [path]   ← validate before starting
$dev-story [path]         ← implement it  (this skill)
$code-review [files]      ← review it
$story-done [path]        ← verify and close it
```

**After all sprint stories are done:** run `$team-qa sprint` to execute the full QA cycle and get a sign-off verdict before advancing the project stage.

**Output:** Source code + test file in the project's `src/` and `tests/` directories.

---

## Phase 1: Find the Story

**If a path is provided**: read that file directly.

**If no argument**: read `production/session-state/active.md`. The active story it
names is the story — continue it without asking. If it names none, ask: "Which story
are we implementing?" Glob `production/epics/**/*.md` and list stories with Status: Ready.

---

## Phase 2: Load Full Context

**Before loading any context, verify required files exist.** Extract the ADR path from the story's `ADR Governing Implementation` field, then check:

| File | Path | If missing |
|------|------|------------|
| TR registry | `docs/architecture/tr-registry.yaml` | **STOP** — "TR registry not found. Run `$create-epics` to generate it." |
| Governing ADR | path from story's ADR field | **STOP** — "ADR file [path] not found. Run `$architecture-decision` to create it, or correct the filename in the story's ADR field." |
| Control manifest | `docs/architecture/control-manifest.md` | **WARN and continue** — "Control manifest not found — layer rules cannot be checked. Run `$create-control-manifest`." |

If the TR registry or governing ADR is missing, set the story status to **BLOCKED** in the session state and do not spawn any programmer agent.

Read all of the following simultaneously — these are independent reads. Do not start implementation until all context is loaded:

### The story file
Extract and hold:
- **Story title, ID, layer, type** (Logic / Integration / Visual/Feel / UI / Config/Data)
- **TR-ID** — the GDD requirement identifier
- **Governing ADR** reference
- **Manifest Version** embedded in story header
- **Acceptance Criteria** — every checkbox item, verbatim
- **Implementation Notes** — the ADR guidance section in the story
- **Out of Scope** boundaries
- **Test Evidence** — the required test file path
- **Dependencies** — what must be DONE before this story

### The TR registry
Read `docs/architecture/tr-registry.yaml`. Look up the story's TR-ID.
Read the current `requirement` text — this is the source of truth for what the
GDD requires now. Do not rely on any inline text in the story file (may be stale).

### The governing ADR
Read `docs/architecture/[adr-file].md`. Extract:
- The full Decision section
- The Implementation Guidelines section (this is what the programmer follows)
- The Engine Compatibility section (post-cutoff APIs, known risks)
- The ADR Dependencies section

### The control manifest
Read `docs/architecture/control-manifest.md`. Extract the rules for this story's layer:
- Required patterns
- Forbidden patterns
- Performance guardrails

Check: does the story's embedded Manifest Version match the current manifest header date?
If they differ, take [A] unless a rule the story's Implementation Notes rely on was removed
or reversed in the diff. If you deviate, name the reason in the Phase 6 report.

- `[A]` Update the story's `Manifest Version:` field to the current date, read the manifest for new rules, and implement against them. Report the story path and the revert command (`git checkout -- [story-path]`).
- `[B]` Implement with the old rules; record the version mismatch in the Phase 6 summary under "Deviations".

### Dependency validation

After extracting the **Dependencies** list from the story file, validate each:

1. Glob `production/epics/**/*.md` to find each dependency story file.
2. Read its `Status:` field.
3. If any dependency has Status other than `Complete` or `Done`, take [A] unless the
   dependency's Completion Notes and test evidence show it is actually finished. If you
   deviate, name the reason in the report.
   - `[A]` Proceed. Record under "Deviations": "Implemented with incomplete dependency: [dependency title] — [status]."
   - `[B]` The dependency is done but its status is stale — set its `Status:` to Complete, report the path and revert command, and continue.

If a dependency story file cannot be found: **BLOCKED** — "Dependency story not found:
[path]." Name the file that must exist to resume (K2). Do not spawn any programmer agent.

---

### Engine reference
Read `.codex/studio/technical-preferences.md`:
- `Engine:` value — determines which programmer agents to use
- Naming conventions (class names, file names, signal/event names)
- Performance budgets (frame budget, memory ceiling)
- Forbidden patterns

---

## Phase 3: Route to the Right Programmer

Based on the story's **Layer**, **Type**, and **system name**, determine which
specialist to spawn as a Codex subagent.

**Config/Data stories — skip agent spawning entirely:**
If the story's Type is `Config/Data`, no programmer agent or engine specialist is needed. Jump directly to Phase 4 (Config/Data note). The implementation is a data file edit — no routing table evaluation, no engine specialist.

**Read the track first — the two tables below are not interchangeable.** Resolve
`production/track.txt` (or the session's `PROJECT_TYPE`). On a product project the
game table below routes to `gameplay-programmer`, a `game`-pack agent, which
`AGENTS.md` forbids. The header's track check resolved this once; never spawn from the
other track's table.

### Primary agent routing table — `game` track

| Story context | Primary agent |
|---|---|
| Foundation layer — any type | `engine-programmer` |
| Any layer — Type: UI | `ui-programmer` |
| Any layer — Type: Visual/Feel | `gameplay-programmer` (implements) |
| Core or Feature — gameplay mechanics | `gameplay-programmer` |
| Core or Feature — AI behaviour, pathfinding | `ai-programmer` |
| Core or Feature — networking, replication | `network-programmer` |
| Config/Data — no code | No agent needed (see Phase 4 Config note) |

### Primary agent routing table — `product` track (web / mobile / service)

| Story context | Primary agent |
|---|---|
| Foundation layer — data model, auth, infrastructure | `backend-engineer` |
| Any layer — Type: UI, web | `frontend-engineer` |
| Any layer — Type: UI, mobile | `mobile-engineer` |
| Core or Feature — API, server logic, persistence | `backend-engineer` |
| Core or Feature — LLM integration, prompt/response handling | `ai-programmer` (see `$web-ai-patterns`, gate paid calls with `$api-cost-gate`) |
| Core or Feature — event schema, pipeline, warehouse | `data-engineer` |
| Core or Feature — realtime, websockets, replication | `backend-engineer`, with `network-programmer` as secondary |
| Config/Data — no code | No agent needed (see Phase 4 Config note) |

Never spawn `gameplay-programmer`, `level-designer` or any other `game`-pack agent
on this track. `lead-programmer` remains available on both as the review/architecture
partner — it is core, not game.

### Engine specialist — always spawn as secondary for code stories

**Game track only.** On the product track there is no engine specialist; the stack
pinned in `.codex/studio/technical-preferences.md` (framework, hosting, data store)
plays that role, and the governing ADR carries the version risk. Skip to Phase 4.

Read the `Engine Specialists` section of `.codex/studio/technical-preferences.md`
to get the configured primary specialist. Spawn them alongside the primary agent
when the story involves engine-specific APIs, patterns, or the ADR has HIGH
engine risk.

| Engine | Specialist agents available |
|--------|----------------------------|
| Godot 4 | `godot-specialist`, `godot-gdscript-specialist`, `godot-shader-specialist` |
| Unity | `unity-specialist`, `unity-ui-specialist`, `unity-shader-specialist` |
| Unreal Engine | `unreal-specialist`, `ue-gas-specialist`, `ue-blueprint-specialist`, `ue-umg-specialist`, `ue-replication-specialist` |

**When engine risk is HIGH** (from the ADR or VERSION.md): always spawn the engine
specialist, even for non-engine-facing stories. High risk means the ADR records
assumptions about post-cutoff engine APIs that need expert verification.

---

## Phase 4: Implement

Spawn the chosen programmer agent(s) as a Codex subagent with the full context package:

Provide the agent with:
1. The complete story file content
2. The current GDD requirement text (from TR registry)
3. The ADR Decision + Implementation Guidelines (verbatim — do not summarise)
4. The control manifest rules for this layer
5. The engine naming conventions and performance budgets
6. Any engine-specific notes from the ADR Engine Compatibility section
7. The test file path that must be created
8. Explicit instruction: **implement this story and write the test**

The agent should:
- Create or modify files in `src/` and `tests/` following the ADR guidelines — these are its owned paths; it writes there without asking
- Respect all Required and Forbidden patterns from the control manifest
- Stay within the story's Out of Scope boundaries (do not touch unrelated files)
- Write clean, doc-commented public APIs
- Return the paths written, their status, and any **decision items** (agenda, recommendation, alternatives, evidence, revert cost) — not questions (`rules/subagent-collaboration.md` § 3.1). The orchestrator decides them inside `rules/autonomy-contract.md` and records the decision in Phase 6

### Config/Data stories (no agent needed)

For Type: Config/Data stories, no programmer agent is required. The implementation
is editing a data file. Read the story's acceptance criteria and make the specified
changes to the data file directly. Note which values were changed and what they
changed from/to.

### Visual/Feel stories

Spawn `gameplay-programmer` to implement the code/animation calls. Note that
Visual/Feel acceptance criteria cannot be auto-verified — the "does it feel right?"
check happens in `$story-done` via manual confirmation.

---

## Phase 5: Write the Test

For **Logic** and **Integration** stories, the test must be written as part of
this implementation — not deferred to later.

Remind the programmer agent:

> "The test file for this story is required at: `[path from Test Evidence section]`.
> The story cannot be closed via `$story-done` without it. Write the test
> alongside the implementation, not after."

Test requirements (from coding-standards.md):
- File name: `[system]_[feature]_test.[ext]`
- Function names: `test_[scenario]_[expected_outcome]`
- Each acceptance criterion must have at least one test function covering it
- No random seeds, no time-dependent assertions, no external I/O
- Test the formula bounds from the GDD Formulas section

For **Visual/Feel** and **UI** stories: no automated test. Remind the agent to
note in the implementation summary what manual evidence will be needed:
"Evidence doc required at `production/qa/evidence/[slug]-evidence.md`."

For **Config/Data** stories: no test file. A smoke check will serve as evidence.

---

## Phase 6: Collect and Summarise

After the programmer agent(s) complete, collect:

- Files created or modified (with paths)
- Test file created (path and number of test functions written)
- Any deviations from the story's Out of Scope boundary (flag these)
- Decision items or blockers the agent returned, and how each was decided
- Any engine-specific risks the specialist flagged

Present a concise implementation summary:

```
## Implementation Complete: [Story Title]

**Files changed**:
- `src/[path]` — created / modified ([brief description])
- `tests/[path]` — test file ([N] test functions)

**Acceptance criteria covered**:
- [x] [criterion] — implemented in [file:function]
- [x] [criterion] — covered by test [test_name]
- [ ] [criterion] — DEFERRED: requires playtest (Visual/Feel)

**Deviations from scope**: [None] or [list files touched outside story boundary]
**Decisions taken**: [route · R-grade · defaults applied or deviated from, with reasons · assumptions where the ADR was silent]
**Engine risks flagged**: [None] or [specialist finding]
**Blockers**: [None] or [describe — K1/K2 only]

Ready for: `$code-review [file1] [file2]` then `$story-done [story-path]`
```

---

## Phase 7: Update Session State

Silently append to `production/session-state/active.md`:

```
## Session Extract — $dev-story [date]
- Story: [story-path] — [story title]
- Files changed: [comma-separated list]
- Test written: [path, or "None — Visual/Feel/Config story"]
- Blockers: [None, or description]
- Next: $code-review [files] then $story-done [story-path]
```

Create `active.md` if it does not exist. Confirm: "Session state updated."

---

## Error Recovery Protocol

If any spawned agent (as a Codex subagent) returns BLOCKED, errors, or cannot complete:

1. **Surface immediately**: put "[AgentName]: BLOCKED — [reason]" in the report before continuing to dependent phases.
2. **Choose the narrowest recovery yourself**: retry with a narrower scope first; if that fails, skip the agent and record the gap. Name the choice in the report.
3. **BLOCKED only when** the missing output is required by a later phase and cannot be regenerated here (K1/K2). State what must exist to resume, and append it to `production/human-actions.md`.
4. **Always produce a partial report** — output whatever was completed. Never discard work because one agent blocked.

Common blockers:
- Input file missing (story not found, GDD absent) → BLOCKED (K2); name the skill that creates it
- ADR status is Proposed → do not implement; BLOCKED until `$architecture-decision` advances it
- Scope too large → split into two stories via `$create-stories`
- Conflicting instructions between ADR and story → the ADR wins; record the conflict under "Deviations"
- Manifest version mismatch → Phase 2 default [A]

## Collaborative Protocol

- **File writes are delegated** — source code, test files, and evidence docs are written by the spawned sub-agents inside their owned paths (`src/`, `tests/`, `production/qa/evidence/`); each returns the paths written and their status. This orchestrator writes only the story file (Phase 2), Config/Data files (Phase 4), and `production/session-state/active.md` (Phase 7).
- **Load before implementing** — do not start coding until all context is loaded
  (story, TR-ID, ADR, manifest, engine prefs). Incomplete context produces code
  that drifts from design.
- **The ADR is the law** — implementation must follow the ADR's Implementation
  Guidelines. If the guidelines conflict with what seems "better," flag it in the
  summary rather than silently deviating.
- **Stay in scope** — the Out of Scope section is a contract. If a criterion
  requires touching an out-of-scope file, make the smallest change that satisfies
  the criterion and record the file under "Deviations". If that change would alter
  another story's behaviour, leave it and record a follow-up story instead.
- **Test is not optional for Logic/Integration** — do not mark implementation
  complete without the test file existing
- **Visual/Feel criteria are deferred, not skipped** — mark them as DEFERRED
  in the summary; they will be manually verified in `$story-done`
- **Decide structural gaps and report them** — if the story requires an
  architectural pattern the ADR does not cover, state the assumption in the code
  and under "Decisions taken": "ADR-NNNN does not specify [case]; assumed [X]."
  Flag it for the ADR owner; do not stop.

---

## Recommended Next Steps

- Run `$code-review [file1] [file2]` to review the implementation before closing the story
- Run `$story-done [story-path]` to verify acceptance criteria and mark the story complete
- After all sprint stories are done: run `$team-qa sprint` for the full QA cycle before advancing the project stage
