---
name: team-qa
description: "Orchestrate the QA team through a full testing cycle. Coordinates qa-lead (strategy + test plan) and qa-tester (test case writing + bug reporting) to produce a complete QA package for a sprint or feature. Covers: test plan generation, test case writing, smoke check gate, manual QA execution, and sign-off report."
---

# Team QA

## 1. Goal

When this skill ends, a sprint or feature has a complete QA package: a strategy table with a
smoke verdict, a QA plan with test cases, manual QA results collected in one question, a bug
report for every FAIL, and a sign-off report whose verdict is APPROVED / APPROVED WITH
CONDITIONS / NOT APPROVED. The cycle itself ends COMPLETE, or BLOCKED with a partial report.

## 2. Inputs

| Input | Where | If missing |
|---|---|---|
| Scope | `sprint-NN` → every story in `production/sprints/[sprint]/` · `feature: [system]` → stories tagged for that system · none → infer the active sprint from `production/session-state/active.md` and `production/sprint-status.yaml` | **K2** — nothing resolves: ask for the sprint or feature |
| Stage | `production/stage.txt` | report "unknown" |
| Smoke scenarios | `tests/smoke/` | qa-lead reports what it could verify |
| Design criteria | GDD/PRD acceptance criteria for the system, when available | test cases from story criteria only |
| Bug numbering | existing `production/qa/bugs/` — next `BUG-[NNN]` | start at 001 |
| Unity projects | `docs/engine/unity-mcp-workflow.md` § 3.5–3.9, whatever the editor-control tool: rendered-state evidence, fixture / global-state isolation, user-scene preservation, queued input across modal transitions; product behaviour vs tool assertions | — |

Report before starting: "QA cycle starting for [scope]. Found [N] stories. Current stage:
[stage]."

## 3. Boundaries

**Team.** `qa-lead` — strategy, classification, sign-off. `qa-tester` — test cases, bug
reports. Spawn each as a Codex subagent with full context (story paths, QA plan path, scope
constraints); independent qa-tester tasks run in parallel.

**Proceed through phases autonomously.** Record each phase's decision and the alternatives
rejected in the final report; stop only on K1/K2 or a gate exit 2
(`rules/autonomy-contract.md`). A smoke check FAIL is that gate: Verdict **BLOCKED**, list
the failures, re-run `$team-qa` after they are fixed.

**Ask once (K3):** manual QA results are the one human input. After everything automatic
is done, one block — per story on the manual list, with its test-case reference: `PASS` ·
`PASS WITH NOTES (describe)` · `FAIL (describe)` · `BLOCKED (reason)`. No answer → every
manual story is DEFERRED and the block is repeated verbatim in the final report.

**Writes** (each reported with `git checkout -- <path>`): `production/qa/qa-plan-[sprint]-[date].md`,
`production/qa/bugs/BUG-[NNN]-[short-slug].md`, `production/qa/qa-signoff-[sprint]-[date].md`.
`src/` and `tests/` are not touched.

**Do not:** cancel the cycle for one blocked story — mark it SKIPPED (blocker) in plan and
sign-off and continue · turn an unwritable test case into a question — it is a story defect:
SKIPPED (no testable criteria) · guess at an ADR/story conflict — surface it · implement
against a Proposed ADR (`$architecture-decision` first) · split scope yourself
(`$create-stories`) · discard partial results. A blocked or erroring agent: record
`[AgentName]: BLOCKED — [reason]` and the phase, retry narrower or skip and note the gap;
BLOCKED only when a later phase needs the missing output (K1/K2); always a partial report.

## 4. Definition of done and gates

**Strategy (`qa-lead`):** classify each story Logic / Integration / Visual/Feel / UI /
Config/Data; automated evidence vs manual QA; blockers (missing criteria or evidence);
manual effort in sessions; a smoke verdict over `tests/smoke/` against the current build —
**PASS** / **PASS WITH WARNINGS [list]** / **FAIL [list]**. Output the table
`| Story | Type | Automated Required | Manual Required | Blocker? |` plus the smoke line.
FAIL → stop as above. Warnings → carried into the sign-off. Blocked stories → SKIPPED.

**Plan (this skill) and test cases (`qa-tester`, one per manual story — Visual/Feel, UI,
Integration without automated tests):** each case has Preconditions, numbered Steps,
Expected Result, blank Actual Result, blank Pass/Fail, and covers every criterion. Appended
under `## Test Cases` in the plan, grouped by story.

**Manual QA:** the K3 block. Every FAIL → `qa-tester` writes a formal bug report from the
description. Summarise counts: PASS · PASS WITH NOTES · FAIL (bug IDs) · BLOCKED · DEFERRED.

**Sign-off (`qa-lead`):** **APPROVED** — all stories PASS or PASS WITH NOTES, no S1/S2 open ·
**APPROVED WITH CONDITIONS** — S3/S4 open or PASS WITH NOTES documented, no S1/S2; any
DEFERRED story caps the verdict here, the condition being the pending manual QA ·
**NOT APPROVED** — any S1/S2 open, or a FAIL without a documented workaround.

**Cycle verdict:** **COMPLETE** — QA cycle finished · **BLOCKED** — smoke check failed
(gate) or a K1/K2 blocker prevented completion; partial report produced.

## 5. Artifact contract

**QA plan** `production/qa/qa-plan-[sprint]-[date].md`: Scope (name, story count, dates) ·
Story Classification table · Automated Test Requirements (stories needing test files and
their expected paths in `tests/`) · Manual QA Scope · Out of Scope, with why · Entry Criteria
(smoke pass, stable build) · Exit Criteria (every story PASS, or FAIL with bugs filed) ·
`## Test Cases`.

**Bug reports** `production/qa/bugs/BUG-[NNN]-[short-slug].md`, NNN incremented from the
directory.

**Sign-off** `production/qa/qa-signoff-[sprint]-[date].md`: `## QA Sign-Off Report:
[scope]`, Date, QA Lead sign-off · Test Coverage Summary `| Story | Type | Auto Test |
Manual QA | Result |` · Bugs Found `| ID | Story | Severity | Status |` · Verdict ·
Conditions · Next Step — APPROVED: "Run `$gate-check` to validate advancement" · WITH
CONDITIONS: "Resolve conditions before advancing; S3/S4 may be deferred to polish" ·
NOT APPROVED: "Resolve S1/S2 and re-run `$team-qa` or targeted manual QA".

**Final summary:** stories in scope · smoke result · manual QA results, or the unanswered
block verbatim · bugs filed with IDs and severities · each phase's decision and rejected
alternatives · every path written with its revert command · the sign-off verdict · the cycle
verdict.

### Recommended next

APPROVED or APPROVED WITH CONDITIONS → `$gate-check` · NOT APPROVED → fix S1/S2, `$bug-triage`
if the backlog grew, then `$team-qa` again · DEFERRED stories → collect the answers in
`production/human-actions.md` and re-issue the sign-off.
