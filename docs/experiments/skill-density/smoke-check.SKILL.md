---
name: smoke-check
description: "Run the critical path smoke test gate before QA hand-off. Executes the automated test suite, verifies core functionality, and produces a PASS/FAIL report. Run after a sprint's stories are implemented and before manual QA begins. A failed smoke check means the build is not ready for QA."
---

# Smoke Check

## 1. Goal

When this skill ends, the automated suite has been run and its exit code — not its log —
has set the automated-test status; every sprint story has a coverage status; the manual
checks were asked once, in one block; and `production/qa/smoke-[date].md` records a verdict
of PASS / PASS WITH WARNINGS / FAIL. A build that fails smoke check does not go to QA.

## 2. Inputs

| Input | Where | If missing |
|---|---|---|
| Mode | first argument: `sprint` (default) · `quick` (skip the coverage scan and Batch 3) | `sprint` |
| Platform | `--platform pc\|console\|mobile\|all` — adds platform batches and a per-platform verdict table | none |
| Test directory | `tests/` | **BLOCKED (K2)** — "Run `$test-setup`, or create the directory if tests live elsewhere" |
| Engine / stack | `.codex/studio/technical-preferences.md` `Engine:` → runner command | "Run `$setup-engine`, then re-run `$smoke-check`" |
| CI | a workflow under `.github/workflows/` that references tests | report "CI configured: no" |
| QA plan | newest `production/qa/qa-plan-*.md` — Test Summary (expected test paths per story), Smoke Test Scope | note "Run `$qa-plan sprint` before smoke-checking for best results" |
| Smoke list | QA plan Smoke Test Scope → `production/qa/smoke-tests.md` → `tests/smoke/` → the standard batches below | standard batches |
| Story list | QA plan Test Summary → newest plan in `production/sprints/` | coverage table empty |

Report the environment first: engine, test directory found/not, CI yes/no, QA plan path.

## 3. Boundaries

**No K1 stop in this skill.** It is a read-only gate on `src/` and `tests/`: it never edits
them and never fixes a failure. Writes: the report to `production/qa/smoke-[date].md`;
DEFERRED items to `production/human-actions.md`. Nothing else.

**Ask once (K3):** after the automated part, one question block listing every batch item,
the platform items when `--platform` was given, and "Did the automated tests pass locally or
in CI?" when the runner recorded NOT RUN. Each item answers `PASS` · `FAIL: [what broke]` ·
`N/A` · nothing. No answer → **DEFERRED**: it appears in the report and in
`production/human-actions.md` and never counts as FAIL. Do not split the block.

**Do not:** read the runner log to decide the verdict (the exit code decides; the log only
explains) · treat NOT RUN as FAIL, or as PASS · collapse PASS / FAIL / NOT RUN into each
other · fix failures here — a failure with a defect ticket goes to `$self-loop`
(`rules/self-loop.md` § 2.1), then `$smoke-check` again; BLOCKED only on hard_error/blocked.

## 4. Definition of done and gates

**Runner by engine.** Append `; echo "EXIT=$?"` and record the value.

| Engine | Command / artifact |
|---|---|
| Godot 4 | `godot --headless --script tests/gdunit4_runner.gd 2>&1`; else `godot --headless -s addons/gdunit4/GdUnitRunner.gd 2>&1`; neither → "GDUnit4 runner not found — confirm the runner path" |
| Unity | no headless run; parse the newest result (`ls -t test-results/ 2>/dev/null \| head -5`, XML/JSON); none → NOT RUN, ask in the block |
| Unreal | `ls -t Saved/Logs/ 2>/dev/null \| grep -i "test\|automation" \| head -5`; none → NOT RUN, ask in the block |
| binary not on PATH | NOT RUN — "Automated tests could not be executed — engine binary not found on PATH" |

| Runner exit | Status |
|---|---|
| `0` | PASS — even if the log has warnings |
| non-zero | FAIL — immediately, no interpretation of the output |
| never ran | NOT RUN → contributes PASS WITH WARNINGS (`docs/deterministic-gates.md`) |

Parse the output only to explain: total / passing / failing counts, failing test names (up
to 10, else the count), runner crash output, and the exit code quoted in the report.

**Coverage per story** (skipped on `quick`: note "Coverage scan skipped — run
`$smoke-check sprint`"): slug from the path (`production/epics/combat/story-001.md` →
`combat`); glob `tests/unit/[system]/` and `tests/integration/[system]/` for the slug or a
related term; read the story's `Test file:` header or Test Evidence section. Status:
**COVERED** (test file found) · **MANUAL** (Visual/Feel or UI with an evidence doc) ·
**MISSING** (Logic/Integration, no test) · **EXPECTED** (Config/Data, none required) ·
**UNKNOWN** (story unreadable). MISSING is advisory here and must be resolved before the
story can be marked COMPLETE via `$story-done`.

**Manual batches** — tailor 2 and 3 to the sprint's real mechanics: **1 core stability**
(launches to main menu without crash · new game/session starts · main menu responds to all
inputs) · **2 sprint mechanic + regression** (primary mechanic · second notable change ·
previous sprint's features still work) · **3 data + performance**, skipped on `quick`
(save/load without data loss, N/A without a save system · no new frame drops or hitches) ·
**Platform**: PC keyboard across menus and gameplay · mouse input and cursor · windowed and
fullscreen · resolution changes; Console gamepad for all actions · TV safe zone · no
keyboard/mouse-only prompts · cold start with no save; Mobile touch for primary actions ·
orientation change · background/foreground · no thermal or performance issues.

**Verdict — first matching rule wins, counting only PASS and FAIL answers:**
**FAIL** if the runner exited non-zero (quote it: `pytest → exit 1`) or any Batch 1 or
Batch 2 item is FAIL (a platform FAIL contributes) ·
**PASS WITH WARNINGS** if tests are PASS or NOT RUN, no Batch 1/2 FAIL, and any story is
MISSING or any item is DEFERRED ·
**PASS** if tests PASS, every item PASS or N/A, nothing DEFERRED, nothing MISSING.

## 5. Artifact contract

Write the report to `production/qa/smoke-[date].md` and report the path and
`git checkout -- production/qa/smoke-[date].md`. Sections: header (Date, Sprint, Engine,
QA Plan, Argument) · **Automated Tests** (status with counts, failing tests, the Local/CI
answer or DEFERRED when NOT RUN) · **Test Coverage** table `| Story | Type | Test File |
Coverage Status |` (e.g. `tests/unit/[system]/[slug]_test.[ext]` COVERED,
`tests/evidence/[slug]-screenshots.md` MANUAL, `—` MISSING ⚠ / EXPECTED) with the
covered / manual / missing / expected summary · **Manual Smoke Checks** (`[x]` PASS, `[ ]`
FAIL: description, `[-]` DEFERRED) · **Missing Test Evidence** (story, path, expected
`tests/unit/[system]/[story-slug]_test.[ext]`; or "All Logic and Integration stories have
test coverage") · **Platform-Specific Results** table when `--platform` (checks / passed /
failed / verdict per platform, notes) · **Verdict**.

Gate message: **FAIL** → "Do not hand off to QA until these are resolved", the failing list,
`$self-loop` per ticketed failure, then re-gate · **PASS WITH WARNINGS** → ready for manual
QA; list the MISSING advisories to clear before `$story-done`; hand
`production/qa/qa-plan-[sprint].md` to the qa-tester · **PASS** → same hand-off, clean.

### Recommended next

`$team-qa sprint` for the full QA cycle · `$story-done` on stories listed as MISSING once
their tests exist · `$qa-plan sprint` if no QA plan was found.
