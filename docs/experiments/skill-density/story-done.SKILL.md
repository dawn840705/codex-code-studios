---
name: story-done
description: "End-of-story completion review. Reads the story file, verifies each acceptance criterion against the implementation, checks for GDD/ADR deviations, prompts code review, updates story status to Complete, and surfaces the next ready story from the sprint."
---

# Story Done

## 1. Goal

When this skill ends, every acceptance criterion is verified — by a script, a human answer,
or marked `DEFERRED` — GDD/PRD and ADR deviations are recorded, `verify_policy.py` has run
with its exit code quoted, and on COMPLETE the story says `Status: Complete` with Completion
Notes, sprint status is updated, and the next ready story is surfaced. Track: game as
written; product checks the PRD (`product/prd/`, not `design/gdd/`) and the ADRs.

## 2. Inputs

| Input | Where | If missing |
|---|---|---|
| Track | `production/track.txt` or the session's `PROJECT_TYPE` | **K1** — ask once, write `production/track.txt`, continue; never infer from repository contents |
| Review mode | `--review [full\|lean\|solo]`, else `production/review-mode.txt`, else `lean` (`docs/director-gates.md`) | default `lean` |
| Story | argument path; else the active story in `production/session-state/active.md`; else the IN PROGRESS story in `production/sprint-status.yaml` or the newest plan in `production/sprints/` (several → most recently modified story file) | **K2** — ask for the path only when nothing resolves or two files share a timestamp |
| Story fields | name/ID, TR-ID(s), Manifest Version, ADR refs, every acceptance criterion, implementation files, `Type:`, engine notes, DoD, estimate, `## QA Test Cases`, Test Evidence path | no Type → ADVISORY (§ 4) |
| Requirement, ADR, manifest | `docs/architecture/tr-registry.yaml` — the *current* `requirement` per TR-ID, cross-checked against the GDD/PRD section's criteria and key rules, never the inline story quote · each ADR's Decision and Consequences · `docs/architecture/control-manifest.md` header `Manifest Version:` and forbidden patterns | manifest absent → skip the staleness check |
| Base commit | the commit the story started from (branch fork point), for `--base` | `$(git merge-base HEAD main)` |

## 3. Boundaries

**Stop (K1):** track unresolved, once. Nothing this skill writes is R4. **Ask only in the
exit report (K3):** criteria only a person can observe — subjective quality, gameplay
behaviour, performance with no profile on disk — go in one question block beneath the report,
`Does [criterion]?` Yes / No / Not tested yet. Unanswered or "Not tested yet" → `DEFERRED —
manual check pending`, appended to `production/human-actions.md`; only "No" fails a
criterion. Full-build-only scenarios → `DEFERRED — requires playtest session`.

**Writes** (R-grade, each reported with `git checkout -- <path>`): the story file,
`docs/tech-debt-register.md`, `production/sprint-status.yaml`, `production/session-state/active.md`,
`production/human-actions.md`. `src/` and `tests/` are read and run only.

**Do not:** rewrite code without a defect ticket — a FAIL with a ticket enters `$self-loop`
(`rules/self-loop.md` § 2.1) and re-runs verification each round; without one, report ·
override `verify_policy.py` exit `2` or record exit `3` as a pass · count DEFERRED as FAIL ·
skip the policy gate · spawn directors outside `full` mode.

**Director gates are advisory** (`docs/director-gates.md`; `solo`/`lean` skip and say so,
`full` spawns a separate reviewing subagent on the final state). **QL-TEST-COVERAGE**
(`qa-lead`: story, Type, test paths, `## QA Test Cases`, criteria; skipped for Config/Data):
ADEQUATE → proceed · GAPS → ADVISORY, follow-up story · INADEQUATE → BLOCKING.
**LP-CODE-REVIEW** (`lead-programmer`: implementation files, story, GDD/PRD section, ADR;
skipped without implementation files): CONCERNS → fix the ticketed items, record the rest as
accepted, proceed · REJECT → `$self-loop` with a ticket, else BLOCKED.

## 4. Definition of done and gates

**Per criterion.** Automatic first: file existence (Glob), run the test file via Bash and
quote its exit code, Grep `src/` for hardcoded numeric literals in gameplay paths and
player-facing strings that belong in config / localization, dependency existence. Then the
K3 list. Then the traceability table `| Criterion | Test | Status |` — COVERED by a test in
`tests/unit/` / `tests/integration/` or a manual "Yes"; UNTESTED otherwise; DEFERRED is
`PENDING (manual)`, excluded from the count. UNTESTED > 50% → **BLOCKING**; ≤ 50% → ADVISORY
plus the Completion Notes line "Untested criteria: [AC-N list]. Recommend adding tests in a
follow-up story."

**Evidence by Type** — check the exact Test Evidence path first, then the broad location:

| Type | Required | Gate |
|---|---|---|
| Logic | unit test in `tests/unit/[system]/` — exists and passes | BLOCKING |
| Integration | test in `tests/integration/[system]/` OR a playtest record in `production/session-logs/` | BLOCKING |
| Visual/Feel | screenshot + sign-off in `production/qa/evidence/` (`production/qa/evidence/[story-slug]-evidence.md`, test-evidence template) | ADVISORY |
| UI | walkthrough doc or interaction test in `production/qa/evidence/` | ADVISORY |
| Config/Data | a `production/qa/smoke-*.md` pass report (else "Run `$smoke-check`") | ADVISORY |
| not declared | "Add `Type:` to the story header" | ADVISORY |

**Deviations** (Grep the implemented files): current GDD/PRD requirement reflected · story
Manifest Version older than the manifest header → ADVISORY "Run $story-readiness" · ADR and
manifest forbidden patterns · hardcoded values · files outside "files to create/modify". Classes:
BLOCKING (contradicts GDD/PRD or ADR) / ADVISORY (equivalent drift → tech-debt register) / OUT OF SCOPE (extra files).

**Policy axis — independent of everything above; both axes are reported.** Run
`python3 ../../scripts/verify_policy.py --story [story-file-path] --base [story-start-commit]`
and read the exit code, never the prose (`docs/deterministic-gates.md`): `0` proceed · `1` WARN
(P3 track mixing / P4 path convention), does not block · `2` **BLOCKED** (P1 missing
evidence / P2 skip marker added), do not write the status · `3` "policy: NOT RUN", never
PASS. Quote it verbatim, naming the gate: `verify_policy.py → exit 2 (P2: tests/x_test.py
adds @pytest.mark.skip)`.

**Verdict.** COMPLETE — all criteria pass, no BLOCKING item, policy exit `0` ·
COMPLETE WITH NOTES — criteria pass or DEFERRED, ADVISORY items and/or policy exit `1` ·
BLOCKED — a failing criterion, a BLOCKING item, or policy exit `2`. The axes never cancel: a
completion PASS beside a policy FAIL is BLOCKED. Policy-axis BLOCKED is final; completion-axis
BLOCKED is advisory — the user may close anyway, the accepted risk recorded in Completion
Notes. Report BLOCKED only on hard_error/blocked (`rules/self-loop.md` § 4.1).

## 5. Artifact contract

Report `## Story Done: [Story Name]` — Story path, Date · **Acceptance Criteria [X/Y]**
(`[x]` auto-verified / confirmed, `[ ]` FAILS: reason, `[?]` DEFERRED) · **Test-Criterion
Traceability** table · **Test Evidence** (Type, required, found YES `path` / NO — BLOCKING /
NO — ADVISORY) · **Deviations** · **Scope** · **Two-axis verdict** table (Task completion PASS/FAIL
by this skill; Policy compliance PASS / WARN / FAIL / NOT RUN by `verify_policy.py` exit
code) · **Verdict** · the K3 question block beneath.

On COMPLETE or COMPLETE WITH NOTES, write and report each path with its revert command: the
story file → `Status: Complete` plus `## Completion Notes` (Completed, Criteria X/Y with
deferred items, Deviations, Test Evidence, Code Review Pending/Complete/Skipped) · advisory
deviations → `docs/tech-debt-register.md` (create if absent) · `production/sprint-status.yaml`
entry → `status: done`, `completed: [date]`, top-level `updated` · append to
`production/session-state/active.md` (create if absent, then "Session state updated"):
`## Session Extract — $story-done [date]` with Verdict, Story, Tech debt logged, Next.

**Next Up:** from `production/sprints/`, stories READY / NOT STARTED, unblocked, Must or
Should Have — name, one line, estimate; confirm with `$story-readiness [path]`. No Must Have
left → close-out: `$smoke-check sprint` → `$team-qa sprint` → `$gate-check` (its gate needs
the `$team-qa` sign-off APPROVED or APPROVED WITH CONDITIONS), with unstarted Should Haves
listed beside it. Must Haves still in progress → say so; continue those.

### Recommended next

`$story-readiness [next-story-path]` · all Must Haves complete → the close-out sequence · tech debt logged → `$tech-debt`.
