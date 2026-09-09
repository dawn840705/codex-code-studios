---
name: smoke-check
description: "Run the critical path smoke test gate before QA hand-off. Executes the automated test suite, verifies core functionality, and produces a PASS/FAIL report. Run after a sprint's stories are implemented and before manual QA begins. A failed smoke check means the build is not ready for QA."
---

# Smoke Check

This skill is the gate between "implementation done" and "ready for QA
hand-off". It runs the automated test suite, checks for test coverage gaps,
asks the developer for the manual checks in one block, and produces a PASS/FAIL
report. It writes only `production/qa/smoke-[date].md` (and DEFERRED items to
`production/human-actions.md`); it never edits `src/` or `tests/`.

The rule is simple: **a build that fails smoke check does not go to QA.**
Handing a broken build to QA wastes their time and demoralises the team.

**Output:** `production/qa/smoke-[date].md`

---

## Parse Arguments

Arguments can be combined: `$smoke-check sprint --platform console`

**Base mode** (first argument, default: `sprint`):
- `sprint` — full smoke check against the current sprint's stories
- `quick` — skip coverage scan (Phase 3) and Batch 3; use for rapid re-checks

**Platform flag** (`--platform`, default: none):
- `--platform pc` — add PC-specific checks (keyboard, mouse, windowed mode)
- `--platform console` — add console-specific checks (gamepad, TV safe zones,
  platform certification requirements)
- `--platform mobile` — add mobile-specific checks (touch, portrait/landscape,
  battery/thermal behaviour)
- `--platform all` — add all platform variants; output per-platform verdict table

If `--platform` is provided, Phase 4 adds platform-specific batches and
Phase 5 outputs a per-platform verdict table in addition to the overall verdict.

---

## Phase 1: Detect Test Setup

Before running anything, understand the environment:

1. **Test framework check**: verify `tests/` directory exists.
   If it does not: "No test directory found at `tests/`. Run `$test-setup`
   to scaffold the testing infrastructure, or create the directory manually
   if tests live elsewhere." Then stop.

2. **CI check**: check whether `.github/workflows/` contains a workflow file
   referencing tests. Note in the report whether CI is configured.

3. **Engine detection**: read `.codex/studio/technical-preferences.md` and
   extract the `Engine:` value. Store this for test command selection in
   Phase 2.

4. **Smoke test list**: check whether `production/qa/smoke-tests.md` or
   `tests/smoke/` exists. If a smoke test list is found, load it for use in
   Phase 4. If neither exists, smoke tests will be drawn from the current QA
   plan (Phase 4 fallback).

5. **QA plan check**: glob `production/qa/qa-plan-*.md` and take the most
   recently modified file. If found, note the path — it will be used in
   Phase 3 and Phase 4. If not found, note: "No QA plan found. Run
   `$qa-plan sprint` before smoke-checking for best results."

Report findings before proceeding: "Environment: [engine]. Test directory:
[found / not found]. CI configured: [yes / no]. QA plan: [path / not found]."

---

## Phase 2: Run Automated Tests

Attempt to run the test suite via Bash. Select the command based on the engine
detected in Phase 1:

**Godot 4:**
```bash
godot --headless --script tests/gdunit4_runner.gd 2>&1
```
If the GDUnit4 runner script does not exist at that path, try:
```bash
godot --headless -s addons/gdunit4/GdUnitRunner.gd 2>&1
```
If neither path exists, note: "GDUnit4 runner not found — confirm the runner
path for your test framework."

**Unity:**
Unity tests require the editor and cannot be run headlessly via shell in most
environments. Check for recent test result artifacts:
```bash
ls -t test-results/ 2>/dev/null | head -5
```
If test result files exist (XML or JSON), read the most recent one and parse
PASS/FAIL counts. If no artifacts exist, record NOT RUN — the Phase 4 block asks
for the editor/CI result.

**Unreal Engine:**
```bash
ls -t Saved/Logs/ 2>/dev/null | grep -i "test\|automation" | head -5
```
If no matching log found, record NOT RUN — the Phase 4 block asks for the Session
Frontend/CI result.

**Unknown engine / not configured:**
"Engine not configured in `.codex/studio/technical-preferences.md`. Run
`$setup-engine` to specify the engine, then re-run `$smoke-check`."

**If the test runner is not available in this environment** (engine binary not
on PATH, runner script not found, etc.), report clearly:

"Automated tests could not be executed — engine binary not found on PATH.
Status recorded as NOT RUN. Unconfirmed NOT RUN is treated as PASS WITH WARNINGS,
not FAIL."

Do not treat NOT RUN as an automatic FAIL. Record it as a warning. The developer's
answer in the Phase 4 block ("did the tests pass locally or in CI?") can resolve it.

### The exit code is the verdict

**Capture the runner's exit code and let it decide.** Append `; echo "EXIT=$?"`
to the command (or check `$?` immediately) and record the value.

| Runner exit | Automated-test status |
|---|---|
| `0` | PASS |
| non-zero | **FAIL — immediately, with no interpretation of the output** |
| never ran (binary missing, no runner) | NOT RUN → PASS WITH WARNINGS |

Do not read the output and form your own opinion about whether the failures
"really matter". A non-zero exit is a FAIL even if the log looks harmless to
you; a zero exit is a PASS even if the log contains scary-looking warnings.
See [`../../docs/deterministic-gates.md`](../../docs/deterministic-gates.md).

Keep the three states distinct and never collapse them: **PASS** (ran, exit 0)
· **FAIL** (ran, non-zero) · **NOT RUN** (did not run). NOT RUN being tolerated
is a deliberate policy for environments without an engine binary — it is not
permission to guess at a verdict.

Then parse the output — **to explain the verdict, not to set it**:
- Total tests run
- Passing count
- Failing count
- Names of any failing tests (up to 10; if more, note the count)
- Any crash or error output from the runner itself
- The exit code itself, quoted in the report

---

## Phase 3: Check Test Coverage

Draw the story list from, in priority order:
1. The QA plan found in Phase 1 (its Test Summary table lists expected test
   file paths per story)
2. The current sprint plan from `production/sprints/` (most recently modified
   file)
3. If the `quick` argument was passed, skip this phase entirely and note:
   "Coverage scan skipped — run `$smoke-check sprint` for full coverage
   analysis."

For each story in scope:

1. Extract the system slug from the story's file path
   (e.g., `production/epics/combat/story-001.md` → `combat`)
2. Glob `tests/unit/[system]/` and `tests/integration/[system]/` for files
   whose name contains the story slug or a closely related term
3. Check the story file itself for a `Test file:` header field or a
   "Test Evidence" section

Assign a coverage status to each story:

| Status | Meaning |
|--------|---------|
| **COVERED** | A test file was found matching this story's system and scope |
| **MANUAL** | Story type is Visual/Feel or UI; a test evidence document was found |
| **MISSING** | Logic or Integration story with no matching test file |
| **EXPECTED** | Config/Data story — no test file required; spot-check is sufficient |
| **UNKNOWN** | Story file missing or unreadable |

MISSING entries are advisory gaps. They do not cause a FAIL verdict but must
appear prominently in the report and must be resolved before `$story-done` can
fully close those stories.

---

## Phase 4: Manual Smoke Checks (K3 — one question block)

Draw the smoke test checklist from, in priority order:
1. The QA plan's "Smoke Test Scope" section (if QA plan was found in Phase 1)
2. `production/qa/smoke-tests.md` (if it exists)
3. `tests/smoke/` directory contents (if it exists)
4. The standard fallback list below (used only when none of the above exist)

Tailor batches 2 and 3 to the actual systems identified from the sprint or QA
plan. Replace bracketed placeholders with real mechanic names from the current
sprint's stories.

Finish Phases 1–3 first. Then ask **one question block** that lists every item
below — the batches, the platform batches if `--platform` was given, and "Did the
automated tests pass locally or in CI?" when Phase 2 recorded NOT RUN. Do not split
it into several calls. Each item takes one of: `PASS` · `FAIL: [what broke]` · `N/A`
· no answer.

**Batch 1 — Core stability (always):**
- Game launches to main menu without crash
- New game / session starts successfully
- Main menu responds to all inputs

**Batch 2 — Sprint mechanic and regression (always):**
- [Primary mechanic this sprint]
- [Second notable change this sprint, if any]
- Previous sprint's features still work (no regressions)

**Batch 3 — Data integrity and performance (skip on `quick`):**
- Save / load completes without data loss (N/A if no save system yet)
- No new frame rate drops or hitches

**Platform batches** *(only with `--platform`)*:
- PC: keyboard controls across menus and gameplay · mouse input and cursor visibility · windowed and fullscreen modes · resolution changes apply
- Console: gamepad input for all actions · UI inside TV safe zone · no keyboard/mouse-only prompts shown to gamepad users · cold start with no prior save
- Mobile: touch controls for primary actions · orientation change · background/foreground transitions · no thermal or performance issues on the target device

Record each answer verbatim for the Phase 5 report. An unanswered item is
**DEFERRED**: it appears in the report and in `production/human-actions.md`, and it
never counts as FAIL. The Phase 5 verdict rules count only PASS and FAIL answers.

---

## Phase 5: Generate Report

Assemble the full smoke check report:

````markdown
## Smoke Check Report
**Date**: [date]
**Sprint**: [sprint name / number, or "Not identified"]
**Engine**: [engine]
**QA Plan**: [path, or "Not found — run $qa-plan first"]
**Argument**: [sprint | quick | blank]

---

### Automated Tests

**Status**: [PASS ([N] tests, [N] passing) | FAIL ([N] failures) |
NOT RUN ([reason])]

[If FAIL, list failing tests:]
- `[test name]` — [brief failure description from runner output]

[If NOT RUN:] "Local/CI result: [answer from the Phase 4 block, or DEFERRED]."

---

### Test Coverage

| Story | Type | Test File | Coverage Status |
|-------|------|-----------|----------------|
| [title] | Logic | `tests/unit/[system]/[slug]_test.[ext]` | COVERED |
| [title] | Visual/Feel | `tests/evidence/[slug]-screenshots.md` | MANUAL |
| [title] | Logic | — | MISSING ⚠ |
| [title] | Config/Data | — | EXPECTED |

**Summary**: [N] covered, [N] manual, [N] missing, [N] expected.

---

### Manual Smoke Checks

- [x] Game launches without crash — PASS
- [x] New game starts — PASS
- [x] [Core mechanic] — PASS
- [ ] [Other check] — FAIL: [user's description]
- [x] Save / load — PASS
- [-] Performance — DEFERRED (no answer)

---

### Missing Test Evidence

Stories that must have test evidence before they can be marked COMPLETE via
`$story-done`:

- **[story title]** (`[path]`) — Logic story has no test file.
  Expected location: `tests/unit/[system]/[story-slug]_test.[ext]`

[If none:] "All Logic and Integration stories have test coverage."

---

### Platform-Specific Results *(only if `--platform` was provided)*

| Platform | Checks Run | Passed | Failed | Platform Verdict |
|----------|-----------|--------|--------|-----------------|
| PC | [N] | [N] | [N] | PASS / FAIL |
| Console | [N] | [N] | [N] | PASS / FAIL |
| Mobile | [N] | [N] | [N] | PASS / FAIL |

**Platform notes**: [any platform-specific observations not captured in pass/fail]

Any platform with one or more FAIL checks contributes to the overall FAIL verdict.

---

### Verdict: [PASS | PASS WITH WARNINGS | FAIL]

[Verdict rules — first matching rule wins:]

**FAIL** if ANY of:
- **The test runner exited non-zero** (Phase 2). This is decided by the exit
  code, not by reading the log — quote the code in the report:
  `pytest → exit 1`.
- Any Batch 1 (core stability) check returned FAIL
- Any Batch 2 (primary sprint mechanic or regression check) returned FAIL

**PASS WITH WARNINGS** if ALL of:
- Automated tests PASS or NOT RUN (developer has not yet confirmed)
- No Batch 1 or Batch 2 check returned FAIL (DEFERRED is allowed)
- One or more Logic/Integration stories have MISSING test evidence, or any check is DEFERRED

**PASS** if ALL of:
- Automated tests PASS
- All smoke checks in all batches PASS or N/A — none DEFERRED
- No MISSING test evidence entries
````

---

## Phase 6: Write and Gate

Present the full report in conversation. Write it to
`production/qa/smoke-[date].md` and report the path and the revert command
(`git checkout -- production/qa/smoke-[date].md`). Append any DEFERRED items to
`production/human-actions.md`.

Then deliver the gate verdict:

**If verdict is FAIL:**

"The smoke check failed. Do not hand off to QA until these failures are
resolved:

[List each failing automated test or smoke check with a one-line description]

This skill does not fix them. For each failure with a defect ticket, run
`$self-loop` (`rules/self-loop.md` § 2.1), then `$smoke-check` again to re-gate.
BLOCKED is reported only on hard_error/blocked."

**If verdict is PASS WITH WARNINGS:**

"Smoke check passed with warnings. The build is ready for manual QA.

Advisory items to resolve before running `$story-done` on affected stories:
[list MISSING test evidence entries]

QA hand-off: share `production/qa/qa-plan-[sprint].md` with the qa-tester
agent to begin manual verification."

**If verdict is PASS:**

"Smoke check passed cleanly. The build is ready for manual QA.

QA hand-off: share `production/qa/qa-plan-[sprint].md` with the qa-tester
agent to begin manual verification."

---

## Collaborative Protocol

- **Never treat NOT RUN as automatic FAIL** — record it as NOT RUN and let
  the developer confirm status manually. Unconfirmed NOT RUN contributes to
  PASS WITH WARNINGS, not FAIL.
- **This skill does not fix failures** — it is a read-only gate on `src/` and
  `tests/`. On FAIL with a defect ticket, recommend `$self-loop`; report BLOCKED
  only on hard_error/blocked.
- **PASS WITH WARNINGS does not block QA hand-off** — it records advisory
  gaps for `$story-done` to follow up on.
- **`quick` argument** skips Phase 3 (coverage scan) and Phase 4 Batch 3.
  Use it for rapid re-checks after fixing a specific failure.
- **Manual checks are one question block** after the automated phases;
  unanswered items are DEFERRED, never FAIL.
- **The report is written without asking** — it is an R-grade artifact; the path
  and revert command are in the output.
