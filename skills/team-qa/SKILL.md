---
name: team-qa
description: "Orchestrate the QA team through a full testing cycle. Coordinates qa-lead (strategy + test plan) and qa-tester (test case writing + bug reporting) to produce a complete QA package for a sprint or feature. Covers: test plan generation, test case writing, smoke check gate, manual QA execution, and sign-off report."
---

When this skill is invoked, orchestrate the QA team through a structured testing cycle.

**Decision Points:** Proceed through phases autonomously. Record each phase's
decision and the alternatives rejected in the final report; stop only on K1/K2
or a gate exit 2 (`rules/autonomy-contract.md`). Manual QA results are the one
input only a human can give (K3): collect them in a single question block in
Phase 5, after everything automatic is done.

## Team Composition

- **qa-lead** — QA strategy, test plan generation, story classification, sign-off report
- **qa-tester** — Test case writing, bug report writing, manual QA documentation

## How to Delegate

Use the Codex subagent mechanism to spawn each team member as a subagent:
- `subagent_type: qa-lead` — Strategy, planning, classification, sign-off
- `subagent_type: qa-tester` — Test case writing and bug report writing

Always provide full context in each agent's prompt (story file paths, QA plan path, scope constraints). Launch independent qa-tester tasks in parallel where possible (e.g., multiple stories in Phase 4 can be scaffolded simultaneously).

## Pipeline

### Phase 1: Load Context

Before doing anything else, gather the full scope:

1. Detect the current sprint or feature scope from the argument:
   - If argument is a sprint identifier (e.g., `sprint-03`): read all story files in `production/sprints/[sprint]/`
   - If argument is `feature: [system-name]`: glob story files tagged for that system
   - If no argument: read `production/session-state/active.md` and `production/sprint-status.yaml` (if present) to infer the active sprint

2. Read `production/stage.txt` to confirm the current project phase.

   For Unity work, read [Unity state verification pitfalls](../../docs/engine/unity-mcp-workflow.md#35-static-batching--transform과-실제-화면을-함께-검증) (§ 3.5–3.9), regardless of the editor-control tool. Include rendered-state evidence, fixture/global-state isolation, user-scene preservation, and queued-input verification across modal transitions in the QA plan; distinguish product behavior from tool/package assertions.

3. Count stories found and report:
   > "QA cycle starting for [sprint/feature]. Found [N] stories. Current stage: [stage]."

### Phase 2: QA Strategy (qa-lead)

Spawn `qa-lead` as a Codex subagent to review all in-scope stories and produce a QA strategy.

Prompt the qa-lead to:
- Read each story file
- Classify each story by type: **Logic** / **Integration** / **Visual/Feel** / **UI** / **Config/Data**
- Identify which stories require automated test evidence vs. manual QA
- Flag any stories with missing acceptance criteria or missing test evidence that would block QA
- Estimate manual QA effort (number of test sessions needed)
- Check `tests/smoke/` for smoke test scenarios; for each, assess whether it can be verified given the current build. Produce a smoke check verdict: **PASS** / **PASS WITH WARNINGS [list]** / **FAIL [list of failures]**
- Produce a strategy summary table and smoke check result:

  | Story | Type | Automated Required | Manual Required | Blocker? |
  |-------|------|--------------------|-----------------|----------|

  **Smoke Check**: [PASS / PASS WITH WARNINGS / FAIL] — [details if not PASS]

If the smoke check result is **FAIL**, the qa-lead must list the failures prominently. QA cannot proceed past the strategy phase with a failed smoke check.

Record the qa-lead's strategy table in the final report, then:

If smoke check **FAIL**: do not proceed to Phase 3. Surface the failures and stop with Verdict: **BLOCKED** — smoke check failed (gate). Re-run `$team-qa` once they are fixed.
If smoke check **PASS WITH WARNINGS**: note the warnings for the sign-off report and continue.
If blockers are present: list them, mark those stories SKIPPED (blocker) in the plan and the sign-off report, and proceed with the rest. Do not cancel the cycle for a blocked story.

### Phase 3: Test Plan Generation

Using the strategy from Phase 2, produce a structured test plan document.

The test plan should cover:
- **Scope**: sprint/feature name, story count, dates
- **Story Classification Table**: from Phase 2 strategy
- **Automated Test Requirements**: which stories need test files, expected paths in `tests/`
- **Manual QA Scope**: which stories need manual walkthrough and what to validate
- **Out of Scope**: what is explicitly not being tested this cycle and why
- **Entry Criteria**: what must be true before QA can begin (smoke check pass, build stable)
- **Exit Criteria**: what constitutes a completed QA cycle (all stories PASS or FAIL with bugs filed)

Write the QA plan to `production/qa/qa-plan-[sprint]-[date].md`. Report the path and the revert command (`git checkout -- <path>`).

### Phase 4: Test Case Writing (qa-tester)

> **Smoke check** is performed as part of Phase 2 (QA Strategy). If the smoke check returned FAIL in Phase 2, the cycle was stopped there. This phase only runs when the Phase 2 smoke check was PASS or PASS WITH WARNINGS.

For each story requiring manual QA (Visual/Feel, UI, Integration without automated tests):

Spawn `qa-tester` as a Codex subagent for each story (run in parallel where possible), providing:
- The story file path
- The relevant section of the QA plan for that story
- The GDD acceptance criteria for the system being tested (if available)
- Instructions to write detailed test cases covering all acceptance criteria

Each test case set should include:
- **Preconditions**: game state required before testing begins
- **Steps**: numbered, unambiguous actions
- **Expected Result**: what should happen
- **Actual Result**: field left blank for the tester to fill in
- **Pass/Fail**: field left blank

Append the test cases to the QA plan under `## Test Cases`, grouped by story. A test case that cannot be written from the acceptance criteria and the GDD is a defect in the story, not a question: mark the story SKIPPED (no testable criteria) and note it in the sign-off report.

### Phase 5: Manual QA Execution (K3 — the one human input)

Finish everything automatic first: the plan, the test cases, and the automated-evidence rows of the sign-off table. Then ask **once**, in a single block listing every story on the manual QA list with its test-case reference:

```
question: "Manual QA results for [sprint/feature] — one line per story"
per story:
  - "PASS — all acceptance criteria verified"
  - "PASS WITH NOTES — minor issues found (describe)"
  - "FAIL — criteria not met (describe the failure)"
  - "BLOCKED — cannot test yet (reason)"
```

If no answer arrives, mark every manual story DEFERRED in the sign-off report and continue; the question block is repeated verbatim in the final report.

For each FAIL: spawn `qa-tester` as a Codex subagent with the failure description from the answer to write a formal bug report in `production/qa/bugs/`.

Bug report naming: `BUG-[NNN]-[short-slug].md` (increment NNN from existing bugs in the directory).

After collecting all results, summarize:
- Stories PASS: [count]
- Stories PASS WITH NOTES: [count]
- Stories FAIL: [count] — bugs filed: [IDs]
- Stories BLOCKED: [count]
- Stories DEFERRED (manual QA unanswered): [count]

### Phase 6: QA Sign-Off Report

Spawn `qa-lead` as a Codex subagent to produce the sign-off report using all results from Phases 2–5.

The sign-off report format:

```markdown
## QA Sign-Off Report: [Sprint/Feature]
**Date**: [date]
**QA Lead sign-off**: [pending]

### Test Coverage Summary
| Story | Type | Auto Test | Manual QA | Result |
|-------|------|-----------|-----------|--------|
| [title] | Logic | PASS | — | PASS |
| [title] | Visual | — | PASS | PASS |

### Bugs Found
| ID | Story | Severity | Status |
|----|-------|----------|--------|
| BUG-001 | [story] | S2 | Open |

### Verdict: APPROVED / APPROVED WITH CONDITIONS / NOT APPROVED

**Conditions** (if any): [list what must be fixed before the build advances]

### Next Step
[guidance based on verdict]
```

Verdict rules:
- **APPROVED**: All stories PASS or PASS WITH NOTES; no S1/S2 bugs open
- **APPROVED WITH CONDITIONS**: S3/S4 bugs open, or PASS WITH NOTES issues documented; no S1/S2 bugs
- **NOT APPROVED**: Any S1/S2 bugs open; or stories FAIL without documented workaround
- Any DEFERRED story caps the verdict at APPROVED WITH CONDITIONS; the condition is the pending manual QA

Next step guidance by verdict:
- APPROVED: "Build is ready for the next phase. Run `$gate-check` to validate advancement."
- APPROVED WITH CONDITIONS: "Resolve conditions before advancing. S3/S4 bugs may be deferred to polish."
- NOT APPROVED: "Resolve S1/S2 bugs and re-run `$team-qa` or targeted manual QA before advancing."

Write the sign-off report to `production/qa/qa-signoff-[sprint]-[date].md`. Report the path and the revert command (`git checkout -- <path>`).

## Error Recovery Protocol

If any spawned agent (as a Codex subagent) returns BLOCKED, errors, or cannot complete:

1. **Record it**: "[AgentName]: BLOCKED — [reason]" and the phase it interrupted, in the final report
2. **Choose the narrowest recovery yourself and report it**: retry with narrower scope, or skip the agent and note the gap
3. **BLOCKED only when the missing output is required by a later phase and cannot be reproduced** (K1/K2). Name what is needed to resume
4. **Always produce a partial report** — output whatever was completed. Never discard work because one agent blocked.

Common blockers:
- Input file missing (story not found, GDD absent) → redirect to the skill that creates it
- ADR status is Proposed → do not implement; run `$architecture-decision` first
- Scope too large → split into two stories via `$create-stories`
- Conflicting instructions between ADR and story → surface the conflict, do not guess

## Output

A summary covering: stories in scope, smoke check result, manual QA results (or the unanswered question block, verbatim), bugs filed (with IDs and severities), every path written with its revert command, and the final APPROVED / APPROVED WITH CONDITIONS / NOT APPROVED verdict.

Verdict: **COMPLETE** — QA cycle finished.
Verdict: **BLOCKED** — smoke check failed (gate) or a K1/K2 blocker prevented cycle completion; partial report produced.
