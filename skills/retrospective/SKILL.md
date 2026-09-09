---
name: retrospective
description: "Generates a sprint or milestone retrospective by analyzing completed work, velocity, blockers, and patterns. Produces actionable insights for the next iteration."
---

Before Phase 1, inspect commits from the last two weeks.

## Phase 1: Parse Arguments

Determine whether this is a sprint retrospective (`sprint-N`) or a milestone retrospective (`milestone-name`).

---

## Phase 1b: Check for Existing Retrospective

Before loading any data, glob for an existing retrospective file:

- For sprint retrospectives: `production/retrospectives/retro-[sprint-slug]-*.md`
  (also check `production/sprints/sprint-[N]-retrospective.md` as an alternate location)
- For milestone retrospectives: `production/retrospectives/retro-[milestone-name]-*.md`

If a matching file is found, take [A] update unless `--fresh` was passed or the file covers a
different period; then take [B] start fresh (archive the old one as `<name>.prev.md`). If
you deviate, name the reason in the report.

- [A] Update — read the existing file, carry its content forward, revise sections with new data.
- [B] Start fresh — generate a new retrospective.

---

## Phase 2: Load Sprint or Milestone Data

Read the sprint or milestone plan from the appropriate location:

- Sprint plans: `production/sprints/`
- Milestone definitions: `production/milestones/`

**If the file does not exist or is empty**, that is K2. Verdict: **BLOCKED** — name the
missing path and what would resume the run: `$sprint-status` to generate the sprint data, or
the sprint tasks, dates and outcomes pasted into the invocation.

Extract: planned tasks, estimated effort, owners, and goals.

Read the git log for the period covered by the sprint or milestone to understand what was actually committed and when.

---

## Phase 3: Analyze Completion and Trends

Scan for completed and incomplete tasks by comparing the plan against actual deliverables. Check for:

- Tasks completed as planned
- Tasks completed but modified from the plan
- Tasks carried over (not completed)
- Tasks added mid-sprint (unplanned work)
- Tasks removed or descoped

Scan the codebase for TODO/FIXME trends:

- Count current TODO/FIXME/HACK comments
- Compare to previous sprint counts if available (check previous retrospectives)
- Note whether technical debt is growing or shrinking

Read previous retrospectives (if any) from `production/sprints/` or `production/milestones/` to check:

- Were previous action items addressed?
- Are the same problems recurring?
- How has velocity trended?

---

## Phase 4: Generate the Retrospective

```markdown
## Retrospective: [Sprint N / Milestone Name]
Period: [Start Date] -- [End Date]
Generated: [Date]

### Metrics

| Metric | Planned | Actual | Delta |
|--------|---------|--------|-------|
| Tasks | [X] | [Y] | [+/- Z] |
| Completion Rate | -- | [Z%] | -- |
| Story Points / Effort Days | [X] | [Y] | [+/- Z] |
| Bugs Found | -- | [N] | -- |
| Bugs Fixed | -- | [N] | -- |
| Unplanned Tasks Added | -- | [N] | -- |
| Commits | -- | [N] | -- |

### Velocity Trend

| Sprint | Planned | Completed | Rate |
|--------|---------|-----------|------|
| [N-2] | [X] | [Y] | [Z%] |
| [N-1] | [X] | [Y] | [Z%] |
| [N] (current) | [X] | [Y] | [Z%] |

**Trend**: [Increasing / Stable / Decreasing]
[One sentence explaining the trend]

### What Went Well
- [Observation backed by specific data or examples]
- [Another positive observation]
- [Recognize specific contributions or decisions that paid off]

### What Went Poorly
- [Specific issue with measurable impact -- e.g., "Feature X took 5 days
  instead of estimated 2, blocking tasks Y and Z"]
- [Another issue with impact]
- [Do not assign blame -- focus on systemic causes]

### Blockers Encountered

| Blocker | Duration | Resolution | Prevention |
|---------|----------|------------|------------|
| [What blocked progress] | [How long] | [How it was resolved] | [How to prevent recurrence] |

### Estimation Accuracy

| Task | Estimated | Actual | Variance | Likely Cause |
|------|-----------|--------|----------|--------------|
| [Most overestimated task] | [X] | [Y] | [+Z] | [Why] |
| [Most underestimated task] | [X] | [Y] | [-Z] | [Why] |

**Overall estimation accuracy**: [X%] of tasks within +/- 20% of estimate

[Analysis: Are we consistently over- or under-estimating? For which types of
tasks? What adjustment should we apply?]

### Carryover Analysis

| Task | Original Sprint | Times Carried | Reason | Action |
|------|----------------|---------------|--------|--------|
| [Task that was not completed] | [Sprint N-X] | [N] | [Why] | [Complete / Descope / Redesign] |

### Technical Debt Status
- Current TODO count: [N] (previous: [N])
- Current FIXME count: [N] (previous: [N])
- Current HACK count: [N] (previous: [N])
- Trend: [Growing / Stable / Shrinking]
- [Note any areas of concern]

### Previous Action Items Follow-Up

| Action Item (from Sprint N-1) | Status | Notes |
|-------------------------------|--------|-------|
| [Previous action] | [Done / In Progress / Not Started] | [Context] |

### Action Items for Next Iteration

| # | Action | Owner | Priority | Deadline |
|---|--------|-------|----------|----------|
| 1 | [Specific, measurable action] | [Who] | [High/Med/Low] | [When] |
| 2 | [Another action] | [Who] | [Priority] | [When] |

### Process Improvements
- [Specific change to how we work, with expected benefit]
- [Another improvement -- keep it to 2-3 actionable items, not a wish list]

### Summary
[2-3 sentence overall assessment: Was this a good sprint/milestone? What is
the single most important thing to change going forward?]
```

---

## Phase 5: Save Retrospective

Write the file to `production/sprints/sprint-[N]-retrospective.md` (or the milestone path),
creating the directory if needed. Report the path, the revert command (`git checkout -- <path>`),
and the top findings (completion rate, velocity trend, top blocker, most important action item).
Verdict: **COMPLETE** — retrospective saved.

---

## Phase 6: Next Steps

- Run `$sprint-plan` to incorporate the action items and velocity data into the next sprint.
- If this was a milestone retrospective, run `$gate-check` to formally assess readiness for the next phase.

### Guidelines

- Be honest and specific. Vague retrospectives ("communication could be better") produce vague improvements. Use data and examples.
- Focus on systemic issues, not individual blame.
- Limit action items to 3-5. More than that dilutes focus.
- Every action item must have an owner and a deadline.
- Check whether previous action items were completed. Recurring unaddressed items are a process smell.
- If this is a milestone retrospective, also evaluate whether the milestone goals were achieved and what that means for the overall project timeline.
